import onnx
import onnxruntime as ort
import os
from typing import Dict, Any
from .base_optimizer import BaseOptimizer

class ONNXOptimizer(BaseOptimizer):
    def __init__(self, optimized_models_base_path: str = "app/data/optimized_models"):
        super().__init__(optimized_models_base_path) 
        self.formats =["onnx", "pb"]
        
    def can_optimize(self, model_format: str) -> bool:
        return model_format.lower() in self.formats
    
    def optimize(self, original_model_path: str, device_info: Dict, **kwargs) -> Dict[str, Any]:
        try:
            self.logger.info(f"Оптимизация ONNX модели для устройства {device_info['architecture']}")
            options = kwargs.get("options", {}) or {}
            
            model = onnx.load(original_model_path)
            
            strategy = self._select_optimization_strategy(device_info, options)
           
            optimized_path = self._apply_onnx_optimizations(model, strategy, original_model_path)

            
            
            return {
                'success': True,
                'optimized_model_path': optimized_path,
                'strategy': strategy,
                'model_size_mb': os.path.getsize(optimized_path) / (1024 * 1024),
                'format': 'onnx'
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка оптимизации ONNX: {e}")
            return {'success': False, 'error': str(e)}
    
    def _select_optimization_strategy(self, device_info: Dict, options: Dict) -> Dict:
        profile = options.get("optimization_level", "balanced")
        ort_level = "ORT_ENABLE_EXTENDED"
        if profile == "performance":
            ort_level = "ORT_ENABLE_ALL"
        elif profile == "size":
            ort_level = "ORT_ENABLE_BASIC"
        # FP16 conversion is opt-in: it can break/disable some quantized graphs and is not always smaller on disk.
        convert_to_fp16 = bool(options.get("fp16", False))
        if options.get("apply_quantization"):
            convert_to_fp16 = False
        return {
            'graph_optimization': True,
            'memory_optimization': device_info.get('ram_gb', 4) < 4 or profile == "size",
            'convert_to_fp16': convert_to_fp16,
            'ort_graph_level': ort_level,
            'profile': profile,
        }
    
    def _apply_onnx_optimizations(self, model, strategy: Dict, original_model_path: str) -> str:
        profile = strategy.get("profile", "balanced")
        if profile == "performance":
            ort_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        elif profile == "size":
            ort_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        else:
            ort_level = ort.GraphOptimizationLevel.ORT_ENABLE_EXTENDED

        optimized_path = self.generate_optimized_model_path(original_model_path, "onnx")
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort_level
        session_options.optimized_model_filepath = optimized_path
        ort.InferenceSession(original_model_path, sess_options=session_options, providers=["CPUExecutionProvider"])

        if strategy.get("convert_to_fp16"):
            try:
                from onnxconverter_common import float16  # optional dependency

                model_optimized = onnx.load(optimized_path)
                model_fp16 = float16.convert_float_to_float16(model_optimized, keep_io_types=True)
                fp16_path = self.generate_optimized_model_path(original_model_path, "onnx")
                onnx.save(model_fp16, fp16_path)
                return fp16_path
            except Exception:
                # Keep ORT-optimized fp32 graph if fp16 conversion is unavailable.
                return optimized_path

        return optimized_path