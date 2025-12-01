import onnx
import onnxruntime as ort
import os
from typing import Dict, Any
from .base_optimizer import BaseOptimizer

class ONNXOptimizer(BaseOptimizer):
    def __init__(self, optimized_models_base_path: str = "app/data/optimized_models"):
        super().__init__(optimized_models_base_path) 
        self.formats =["onnx", "pb"]
        
    def can_optimize(self, model_type: str, model_format: str) -> bool:
        return model_type.lower() == "cv" and model_format.lower() in self.formats
    
    def optimize(self, original_model_path: str, device_info: Dict, **kwargs) -> Dict[str, Any]:
        try:
            self.logger.info(f"Оптимизация ONNX модели для устройства {device_info['architecture']}")
            
            model = onnx.load(original_model_path)
            
            strategy = self._select_optimization_strategy(device_info)
           
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
    
    def _select_optimization_strategy(self, device_info: Dict) -> Dict:
        return {
            'graph_optimization': True,
            'memory_optimization': device_info.get('ram_gb', 4) < 4
        }
    
    def _apply_onnx_optimizations(self, model, strategy: Dict, original_model_path: str) -> str:
        optimized_model = model
        optimized_path = self.save_optimized_model(optimized_model.SerializeToString(), original_model_path, "onnx")
        return optimized_path