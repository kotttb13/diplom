import tensorflow as tf
import os
from typing import Dict, Any, Optional, Tuple
import shutil
from .base_optimizer import BaseOptimizer
from .benchmarker import Benchmarker

class TensorFlowOptimizer(BaseOptimizer):
    def __init__(self, optimized_models_base_path: str = "app/data/optimized_models"):
        super().__init__(optimized_models_base_path) 
        self.formats = ["h5", "hdf5", "keras", "tflite", "lite"]
    
    def can_optimize(self, model_format: str) -> bool:
        return model_format.lower() in self.formats
    
    def optimize(self, original_model_path: str, device_info: Dict, **kwargs) -> Dict[str, Any]:
        try:
            self.logger.info(f"Оптимизация TensorFlow модели для устройства {device_info['architecture']}")
            options = kwargs.get("options", {}) or {}
            test_data: Optional[Tuple[Any, Any]] = kwargs.get("test_data")
            source_format = os.path.splitext(original_model_path)[1].lower().lstrip(".")
            strategy = self._select_optimization_strategy(device_info, None)
            strategy.update(options)

            if source_format in ["tflite", "lite"]:
                optimized_path = self.generate_optimized_model_path(original_model_path, "tflite")
                shutil.copyfile(original_model_path, optimized_path)
            else:
                model = tf.keras.models.load_model(original_model_path)
                optimized_path = self._apply_tensorflow_optimizations(
                    model, strategy, original_model_path, test_data=test_data
                )

            original_bytes = os.path.getsize(original_model_path) if os.path.exists(original_model_path) else 0
            optimized_bytes = os.path.getsize(optimized_path) if os.path.exists(optimized_path) else 0

            quant_note = None
            quant_metrics = {"size_before_bytes": original_bytes, "size_after_bytes": optimized_bytes}
            if test_data is not None and test_data[0] is not None:
                try:
                    x_test = test_data[0]
                    bm = Benchmarker()
                    if source_format in ["tflite", "lite"]:
                        interpreter_before = tf.lite.Interpreter(model_path=original_model_path)
                        interpreter_before.allocate_tensors()
                        quant_metrics["inference_before_ms"] = bm.measure_inference_time(
                            interpreter_before, x_test[:1].astype("float32")
                        )
                    else:
                        sample = x_test[:1]
                        for _ in range(3):
                            _ = model(sample, training=False)
                        import time
                        start = time.perf_counter()
                        runs = 30
                        for _ in range(runs):
                            _ = model(sample, training=False)
                        quant_metrics["inference_before_ms"] = (time.perf_counter() - start) * 1000 / runs

                    interpreter_after = tf.lite.Interpreter(model_path=optimized_path)
                    interpreter_after.allocate_tensors()
                    quant_metrics["inference_after_ms"] = bm.measure_inference_time(
                        interpreter_after, x_test[:1].astype("float32")
                    )
                except Exception as e:
                    quant_note = f"Не удалось измерить inference time: {e}"

            return {
                'success': True,
                'optimized_model_path': optimized_path,
                'strategy': strategy,
                'model_size_mb': os.path.getsize(optimized_path) / (1024 * 1024),
                'format': 'tflite',
                'quantization_applied': strategy.get("quantization_mode", "none") != "none",
                'quantization_note': quant_note,
                'quantization_metrics': quant_metrics,
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка оптимизации TensorFlow: {e}")
            return {'success': False, 'error': str(e)}
    
    def _select_optimization_strategy(self, device_info: Dict, model) -> Dict:
       
        strategy = {
            'convert_to_tflite': True,
            'optimize_latency': False,
            'reduce_model_size': False,
            'use_float16': False,
            'quantization_mode': 'none',
        }
        
        ram_gb = float(device_info.get('ram_gb', 4) or 4)
        cpu_cores = int(device_info.get('cpu_core', 4) or 4)
        
        if ram_gb < 3 or cpu_cores < 4:
            strategy['optimize_latency'] = True
            strategy['reduce_model_size'] = True
            strategy['quantization_mode'] = 'dynamic'
        elif ram_gb >= 8 and cpu_cores >= 6:
            strategy['use_float16'] = True
            
        return strategy
    
    def _apply_tensorflow_optimizations(self, model, strategy: Dict, original_model_path: str,
                                        test_data: Optional[Tuple[Any, Any]] = None) -> str:

        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        
        quantization_mode = strategy.get("quantization_mode", "none")
        if quantization_mode in ["dynamic", "static", "int8"] or strategy.get('optimize_latency', False):
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
        if strategy.get("use_float16", False):
            converter.target_spec.supported_types = [tf.float16]
        if quantization_mode in ["static", "int8"]:
            if test_data is not None and test_data[0] is not None:
                x_calib = test_data[0]

                def representative_dataset():
                    import numpy as np
                    xs = np.asarray(x_calib)
                    n = min(len(xs), 128)
                    for i in range(n):
                        yield [xs[i:i + 1].astype("float32")]

                converter.representative_dataset = representative_dataset
                converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
                # Full integer IO only for explicit "int8" mode.
                if quantization_mode == "int8":
                    converter.inference_input_type = tf.int8
                    converter.inference_output_type = tf.int8
            else:
                # Without calibration data, static/int8 cannot be applied properly; fall back to dynamic.
                strategy["quantization_mode"] = "dynamic"
        
        tflite_model = converter.convert()
        
        optimized_path = self.save_optimized_model(tflite_model, original_model_path, "tflite")
            
         
        return optimized_path
