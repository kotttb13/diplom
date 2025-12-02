import tensorflow as tf
import numpy as np
import onnxruntime as ort
from typing import Dict, Any, Tuple, Optional
import logging
import time
from core.database.models import NeuralModel, OptimizedModel, OptimizationRecord

class ModelValidationService:
    def __init__(self, optimization_record_repository ):
        self.optimization_record_repo = optimization_record_repository
        self.logger = logging.getLogger(__name__)
    
    def validate_single_model(self,
                            model_path: str,
                            x_test: np.ndarray,
                            y_test: np.ndarray,
                            model_format: str) -> Dict[str, Any]:
        try:
            if model_format.lower() in ['tensorflow', 'h5', 'keras']:
                return self._validate_tensorflow_model(model_path, x_test, y_test)
            elif model_format.lower() == 'tflite':
                return self._validate_tflite_model(model_path, x_test, y_test)
            elif model_format.lower() in ["pb", 'onnx']:
                return self._validate_onnx_model(model_path, x_test, y_test)
            else:
                raise ValueError(f"Неподдерживаемый формат: {model_format}")
                
        except Exception as e:
            self.logger.error(f"Ошибка валидации {model_format} модели: {e}")
            return {'error': str(e), 'loss': None, 'accuracy': None}
    
    def _validate_tensorflow_model(self,
                                 model_path: str,
                                 x_test: np.ndarray,
                                 y_test: np.ndarray) -> Dict[str, Any]:
        model = tf.keras.models.load_model(model_path)
        
        loss, accuracy = model.evaluate(x_test, y_test, verbose=0)
        
        return {
            'loss': float(loss),
            'accuracy': float(accuracy),
            'model_size_mb': self._get_file_size_mb(model_path),
            'format': 'tensorflow'
        }
    
    def _validate_tflite_model(self,
                             model_path: str,
                             x_test: np.ndarray,
                             y_test: np.ndarray) -> Dict[str, Any]:

        interpreter = tf.lite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        correct_predictions = 0
        total_loss = 0.0
        total_samples = len(x_test)
        
        for i in range(total_samples):
            input_data = x_test[i:i+1].astype(np.float32)
            interpreter.set_tensor(input_details[0]['index'], input_data)
            
            interpreter.invoke()
            
            output_data = interpreter.get_tensor(output_details[0]['index'])
            predicted_class = np.argmax(output_data[0])
            true_class = y_test[i]
            
            if predicted_class == true_class:
                correct_predictions += 1

            predicted_probs = output_data[0]
            true_one_hot = np.zeros_like(predicted_probs)
            true_one_hot[true_class] = 1.0
            
            epsilon = 1e-7
            predicted_probs = np.clip(predicted_probs, epsilon, 1.0 - epsilon)
            sample_loss = -np.sum(true_one_hot * np.log(predicted_probs))
            total_loss += sample_loss
        
        accuracy = correct_predictions / total_samples
        avg_loss = total_loss / total_samples if total_samples > 0 else 0.0
        
        return {
            'loss': float(avg_loss),
            'accuracy': float(accuracy),
            'model_size_mb': self._get_file_size_mb(model_path),
            'format': 'tflite'
        }
    
    def _validate_onnx_model(self,
                           model_path: str,
                           x_test: np.ndarray,
                           y_test: np.ndarray) -> Dict[str, Any]:
        
        session = ort.InferenceSession(model_path)
        
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        
        correct_predictions = 0
        total_loss = 0.0
        total_samples = len(x_test)
        
        for i in range(total_samples):
            input_data = x_test[i:i+1].astype(np.float32)
            outputs = session.run([output_name], {input_name: input_data})
            predicted_probs = outputs[0][0]
            
            predicted_class = np.argmax(predicted_probs)
            true_class = y_test[i]
            
            if predicted_class == true_class:
                correct_predictions += 1
            
            true_one_hot = np.zeros_like(predicted_probs)
            true_one_hot[true_class] = 1.0
            
            epsilon = 1e-7
            predicted_probs = np.clip(predicted_probs, epsilon, 1.0 - epsilon)
            sample_loss = -np.sum(true_one_hot * np.log(predicted_probs))
            total_loss += sample_loss
        
        accuracy = correct_predictions / total_samples
        avg_loss = total_loss / total_samples if total_samples > 0 else 0.0
        
        return {
            'loss': float(avg_loss),
            'accuracy': float(accuracy),
            'model_size_mb': self._get_file_size_mb(model_path),
            'format': 'onnx'
        }
    
    def validate_model_pair(self,
                          original_model_path: str,
                          optimized_model_path: str,
                          x_test: np.ndarray,
                          y_test: np.ndarray,
                          original_format: str,
                          optimized_format: str) -> Dict[str, Any]:
  
        try:
            original_metrics = self.validate_single_model(
                original_model_path, x_test, y_test, original_format
            )
            
            optimized_metrics = self.validate_single_model(
                optimized_model_path, x_test, y_test, optimized_format
            )
            
           
            return {
                'success': True,
                'accuracy_before': original_metrics["accuracy"],
                'accuracy_after':  optimized_metrics["accuracy"],
                'loss_before': original_metrics["loss"],
                'loss_after':  optimized_metrics["loss"],
                
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации пары моделей: {e}")
            return { 'succes': False, 'error': str(e)}
    

    
    def _get_file_size_mb(self, file_path: str) -> float:
        import os
        return os.path.getsize(file_path) / (1024 * 1024)
    


    def _save_optimization_result(self,
                                original_model_id: int,
                                optimized_model_id: int,
                                validation_result: Dict) -> Dict[str, Any]:
        try:
            
            optimization_record = OptimizationRecord(
                optimized_model_id=optimized_model_id,
                original_model_id=original_model_id,
                accuracy_before=validation_result["accuracy_before"],
                accuracy_after=validation_result["accuracy_after"],
                loss_before= validation_result["loss_before"],
                loss_after =  validation_result["loss_after"],
                status='completed'
            )
            self.optimization_record_repo.save(optimization_record)
            
            self.logger.info(f"Созданы записи: OptimizedModel ID:{optimized_model_id}, "
                           f"OptimizationRecord ID:{optimization_record.id}")
            
            return {
                'optimization_record_id': optimization_record.id
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения результатов валидации: {e}")
      
            return {}