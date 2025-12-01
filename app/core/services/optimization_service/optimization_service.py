import logging
from typing import Dict, Any, Optional
import os

from .optimizer_factory import OptimizerFactory
from core.database.models import NeuralModel, OptimizedModel, OptimizationRecord, Device

class OptimizationService:
    def __init__(self, 
                 device_repository, 
                 model_repository,
                 optimized_model_repository,
                 optimization_record_repository):
        self.device_repo = device_repository
        self.model_repo = model_repository
        self.optimized_model_repo = optimized_model_repository
        self.optimization_record_repo = optimization_record_repository
        self.logger = logging.getLogger(__name__)
      
    
    def optimize_model_by_id(self,
                           model_id: int,
                           device_id: int,
                           test_data: Optional[Any] = None) -> Dict[str, Any]:
        try:
            self.logger.info(f"Запуск оптимизации модели ID:{model_id} для устройства ID:{device_id}")
            
            model = self.model_repo.get_by_id(model_id)
            device = self.device_repo.get_by_id(device_id)
            
            if not model:
                return {'success': False, 'error': f'Модель с ID {model_id} не найдена'}
            if not device:
                return {'success': False, 'error': f'Устройство с ID {device_id} не найдена'}
            
            optimizer = OptimizerFactory.get_optimizer_by_model_id(self.model_repo, model_id)
            if not optimizer:
                return {'success': False, 'error': f'Нет подходящего оптимизатора для модели ID {model_id}'}
            
            device_info = self._prepare_device_info(device)
            
            result = optimizer.optimize(model.original_path, device_info)
            
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
                size=optimization_result.get('model_size_mb', 0),
                optimization_params=str(optimization_result.get('strategy', {}))
            )
            self.optimized_model_repo.save(optimized_model)
            #нужно сделать валидацию!
            # optimization_record = OptimizationRecord(
            #     optimized_model_id=optimized_model.id,
            #     original_model_id=original_model.id,
            #     accuracy_before=optimization_result.get('quality_metrics', {}).get('original_accuracy', 0),
            #     accuracy_after=optimization_result.get('quality_metrics', {}).get('optimized_accuracy', 0),
            #     status='completed'
            # )
            # self.optimization_record_repo.save(optimization_record)
            
            # self.logger.info(f"Созданы записи: OptimizedModel ID:{optimized_model.id}, "
            #                f"OptimizationRecord ID:{optimization_record.id}")
            
            return {
                'optimized_model_id': optimized_model.id
                # 'optimization_record_id': optimization_record.id
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения результатов оптимизации: {e}")
      
            return {}