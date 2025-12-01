from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import uuid
import logging

class BaseOptimizer(ABC):
    def __init__(self, optimized_models_base_path: str = "app/data/optimized_models"):
        self.optimized_models_base_path = optimized_models_base_path
        self.logger = logging.getLogger(__name__)
        self._ensure_optimized_models_dir()
    

    def _ensure_optimized_models_dir(self):
        os.makedirs(self.optimized_models_base_path, exist_ok=True)
         
    def generate_optimized_model_path(self, original_path: str,  file_extension: str) -> str:
        original_filename = os.path.basename(original_path)
        name_without_ext = os.path.splitext(original_filename)[0]
        unique_id = str(uuid.uuid4())[:8]
        
        optimized_filename = f"{name_without_ext}_{unique_id}.{file_extension}"
        optimized_path = os.path.join(self.optimized_models_base_path, optimized_filename)
        
        return optimized_path
    
    def save_optimized_model(self, model_data: bytes, original_path: str, file_extension: str) -> str:
        optimized_path = self.generate_optimized_model_path(original_path, file_extension)
        
        with open(optimized_path, 'wb') as f:
            f.write(model_data)
        
        self.logger.info(f"Оптимизированная модель сохранена: {optimized_path}")
        return optimized_path
    
    
    @abstractmethod
    def optimize(self, model_path: str, device_info: Dict, **kwargs) -> Dict[str, Any]:
      
        pass
    
    @abstractmethod
    def can_optimize(self, model_type: str, model_format: str) -> bool:
       pass


    def get_model_details(self, model_repository, model_id: int) -> Optional[Dict]:
        try:
            return model_repository.get_model_type_and_format(model_id)
        except Exception as e:
            self.logger.error(f"Ошибка получения деталей модели: {e}")
            return None
    
    def can_optimize_by_id(self, model_repository, model_id: int) -> bool:
        model_details = self.get_model_details(model_repository, model_id)
        if not model_details:
            return False
        
        return self.can_optimize(
            model_details['model_type'], 
            model_details['model_format']
        )