import tensorflow as tf
import os
from typing import Dict, Any
from .base_optimizer import BaseOptimizer

class TensorFlowOptimizer(BaseOptimizer):
    def __init__(self, optimized_models_base_path: str = "app/data/optimized_models"):
        super().__init__(optimized_models_base_path) 
        self.formats = ["h5", "hdf5", "keras", "tflite", "lite"]
    
    def can_optimize(self, model_type: str, model_format: str) -> bool:
        return model_type.lower() == "cv" and model_format.lower() in self.formats
    
    def optimize(self, original_model_path: str, device_info: Dict, **kwargs) -> Dict[str, Any]:
        try:
            self.logger.info(f"Оптимизация TensorFlow модели для устройства {device_info['architecture']}")
            
            model = tf.keras.models.load_model(original_model_path)
            
            strategy = self._select_optimization_strategy(device_info, model)
            
            optimized_path = self._apply_tensorflow_optimizations(model, strategy, original_model_path)
            
            return {
                'success': True,
                'optimized_model_path': optimized_path,
                'strategy': strategy,
                'model_size_mb': os.path.getsize(optimized_path) / (1024 * 1024),
                'format': 'tflite'
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка оптимизации TensorFlow: {e}")
            return {'success': False, 'error': str(e)}
    
    def _select_optimization_strategy(self, device_info: Dict, model) -> Dict:
       
        strategy = {
            'convert_to_tflite': True,
            'optimize_latency': False,
            'reduce_model_size': False
        }
        
        ram_gb = device_info.get('ram_gb', 4)
        cpu_cores = device_info.get('cpu_core', 4)
        
        if ram_gb < 3 or cpu_cores < 4:
            strategy['optimize_latency'] = True
            strategy['reduce_model_size'] = True
            
        return strategy
    
    def _apply_tensorflow_optimizations(self, model, strategy: Dict, original_model_path: str) -> str:

        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        
        if strategy.get('optimize_latency', False):
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        tflite_model = converter.convert()
        
        optimized_path = self.save_optimized_model(tflite_model, original_model_path, "tflite")
            
         
        return optimized_path
