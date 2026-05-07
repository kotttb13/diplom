import logging
from typing import Dict, Any, Optional
import os
import json
from .onnx_quantizer import ONNXQuantizer

from .optimizer_factory import OptimizerFactory
from core.database.models import NeuralModel, OptimizedModel, OptimizationRecord, Device

class OptimizationService:
    def __init__(self, 
                 device_repository, 
                 model_repository,
                 optimized_model_repository):
        self.device_repo = device_repository
        self.model_repo = model_repository
        self.optimized_model_repo = optimized_model_repository
       
        self.logger = logging.getLogger(__name__)
      
    
    def optimize_model_by_id(self,
                           model_id: int,
                           device_id: int,
                           test_data: Optional[Any] = None,
                           apply_quantization: bool = False,
                           quantization_type: str = "dynamic",
                           optimization_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            self.logger.info(f"Запуск оптимизации модели ID:{model_id} для устройства ID:{device_id}")
            
            model = self.model_repo.get_by_id(model_id)
            device = self.device_repo.get_by_id(device_id)
            
            if not model:
                return {'success': False, 'error': f'Модель с ID {model_id} не найдена'}
            if not device:
                return {'success': False, 'error': f'Устройство с ID {device_id} не найдена'}
            
            model_details = self.model_repo.get_model_type_and_format(model_id)
            if model_details and model_details.get("model_format") in ["pt", "pth"]:
                try:
                    onnx_path = self._convert_pytorch_to_onnx(model.original_path)
                    model.original_path = onnx_path
                    model_details["model_format"] = "onnx"
                except Exception as e:
                    # Если формат подписан неверно.
                    try:
                        import onnx
                        onnx.load(model.original_path)
                        model_details["model_format"] = "onnx"
                    except Exception:
                        raise e

            options = optimization_options or {}
            # Передаём флаги оптимизатору.
            options["apply_quantization"] = bool(apply_quantization)
            target_format = str(options.get("target_format", "auto")).lower()
            source_format = str(model_details.get("model_format", "")).lower() if model_details else ""
            if target_format != "auto":
                compatibility = {
                    "tflite": {"h5", "keras", "hdf5", "tflite", "lite"},
                    "onnx": {"onnx", "pb", "pt", "pth"},
                }
                if source_format not in compatibility.get(target_format, set()):
                    return {
                        "success": False,
                        "error": f"Целевой формат '{target_format}' несовместим с исходным форматом '{source_format}'"
                    }
            if target_format in ["onnx", "tflite"]:
                optimizer = OptimizerFactory.get_optimizer_by_format(target_format)
            elif model_details and model_details.get("model_format") == "onnx":
                optimizer = OptimizerFactory.get_optimizer_by_format("onnx")
            else:
                optimizer = OptimizerFactory.get_optimizer_by_model_id(self.model_repo, model_id)
            if not optimizer:
                return {'success': False, 'error': f'Нет подходящего оптимизатора для модели ID {model_id}'}
            
            device_info = self._prepare_device_info(device)
            
            result = optimizer.optimize(model.original_path, device_info, options=options, test_data=test_data)
            if result.get("success") and apply_quantization:
                result = self._apply_post_quantization(result, quantization_type, test_data)
            original_size_mb = os.path.getsize(model.original_path) / (1024 * 1024) if os.path.exists(model.original_path) else 0
            optimized_size_mb = os.path.getsize(result["optimized_model_path"]) / (1024 * 1024) if result.get("optimized_model_path") and os.path.exists(result["optimized_model_path"]) else 0
            result["original_model_size_mb"] = original_size_mb
            result["optimized_model_size_mb"] = optimized_size_mb
            if result.get("success"):
                strategy = result.get("strategy", {})
                strategy.update({
                    "apply_quantization": apply_quantization,
                    "quantization_type": quantization_type,
                    "quantization_applied": result.get("quantization_applied", False),
                    "quantization_note": result.get("quantization_note"),
                    "quantization_metrics": result.get("quantization_metrics"),
                    "target_format": options.get("target_format", "auto"),
                    "optimization_level": options.get("optimization_level", "balanced"),
                    "original_model_size_mb": round(original_size_mb, 4),
                    "optimized_model_size_mb": round(optimized_size_mb, 4),
                })
                result["strategy"] = strategy
            
            if result['success']:
                self.logger.info(f"Оптимизация завершена успешно")
                optimization_result = self._save_optimization_result(model, device, result)
                result.update(optimization_result)

            else:
                self.logger.error(f"Ошибка оптимизации: {result.get('error')}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка в сервисе оптимизации: {e}")
            return {'success': False, 'error': str(e)}

    def _apply_post_quantization(self, result: Dict[str, Any], quantization_type: str, test_data: Optional[Any]) -> Dict[str, Any]:
        result_format = str(result.get("format", "")).lower()
        if result_format == "onnx":
            quantizer = ONNXQuantizer()
            original_path = result["optimized_model_path"]
            try:
                if quantization_type == "static":
                    try:
                        quantized = quantizer.static_quantization(original_path, calibration_data=test_data)
                    except Exception as e:
                        # Резервно пробуем динамический режим.
                        result["quantization_note"] = f"Static-квантование не удалось ({e}); пробуем dynamic."
                        quantized = quantizer.dynamic_quantization(original_path)
                else:
                    quantized = quantizer.dynamic_quantization(original_path)
                result["optimized_model_path"] = quantized
                result["quantization_metrics"] = quantizer.compare_metrics(
                    original_path, quantized, test_data[0] if test_data else None
                )
                result["quantization_applied"] = True
            except Exception as e:
                result["quantization_applied"] = False
                result["quantization_note"] = f"Квантование ONNX пропущено: {e}"
            return result

        if result_format == "tflite":
            result["quantization_applied"] = True
            result["quantization_note"] = "Квантование применено на этапе конвертации TensorFlow -> TFLite"
            return result

        result["quantization_applied"] = False
        result["quantization_note"] = f"Формат {result_format or 'unknown'} не поддерживает post-quantization в текущем пайплайне"
        return result

    def _convert_pytorch_to_onnx(self, model_path: str) -> str:
        import os
        import torch.nn as nn
        from .pytorch_model_loader import PyTorchModelLoader
        from .pytorch_to_onnx_converter import PyTorchToONNXConverter
        loader = PyTorchModelLoader()
        converter = PyTorchToONNXConverter()
        model = loader.load_model(model_path)
        if isinstance(model, dict):
            raise ValueError("Файл .pt/.pth содержит state_dict. Нужна сериализованная модель для автоконвертации.")
        if not isinstance(model, nn.Module):
            raise ValueError("Неподдерживаемый PyTorch артефакт.")
        out_path = os.path.splitext(model_path)[0] + "_from_pytorch.onnx"
        last_error = None
        for shape in [(1, 3, 32, 32), (1, 3, 224, 224), (1, 1, 28, 28)]:
            try:
                dummy = loader.prepare_dummy_input(shape)
                converter.convert(model, out_path, dummy)
                return out_path
            except Exception as e:
                last_error = e
        raise ValueError(f"Не удалось конвертировать PyTorch в ONNX автоматически: {last_error}")
    
    def _prepare_device_info(self, device: Device) -> Dict[str, Any]:
         return {
            'architecture': device.architecture,
            'memory_gb': device.memory_gb,
            'ram_gb': device.ram_gb,
            'cpu_core': device.cpu_core,
            'type': device.type_device.name if device.type_device else 'Unknown'
        }

    def _save_optimization_result(self,
                                original_model: NeuralModel,
                                device: Device,
                                optimization_result: Dict) -> Dict[str, Any]:
        try:
            
            optimized_model = OptimizedModel(
                original_model_id=original_model.id,
                device_id=device.id,
                path=optimization_result['optimized_model_path'],
                size=optimization_result.get('optimized_model_size_mb', optimization_result.get('model_size_mb', 0)),
                optimization_params=json.dumps(optimization_result.get('strategy', {}), ensure_ascii=False)
            )
            self.optimized_model_repo.save(optimized_model)
            
            
            return {
                'optimized_model_id': optimized_model.id
                # Идентификатор отчета оптимизации.
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения результатов оптимизации: {e}")
      
            return {}
