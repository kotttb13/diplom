from typing import Optional
from .tensorflow_optimizer import TensorFlowOptimizer
from .onnx_optimizer import ONNXOptimizer
from .base_optimizer import BaseOptimizer

class OptimizerFactory:
    
    @staticmethod
    def get_optimizer_by_model_id(model_repository, model_id: int) -> Optional[BaseOptimizer]:
        
        optimizers = [
            TensorFlowOptimizer(),
            ONNXOptimizer()
        ]
        
        for optimizer in optimizers:
            if optimizer.can_optimize_by_id(model_repository, model_id):
                return optimizer
                
        return None