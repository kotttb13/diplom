import pytest
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.database import initialize_database, get_session
from core.database.models.device import Device
from core.database.models.neural_model import NeuralModel
from core.database.models.optimized_model import OptimizedModel
from core.database.models.optimization_record import OptimizationRecord
from core.database.models.deployment_record import DeploymentRecord
from core.database.models.device_type import DeviceType
from core.database.models.model_format import ModelFormat
initialize_database()
class TestCRUDOperations:
    """Тесты CRUD операций для всех моделей"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.engine = initialize_database()
        self.session = get_session(self.engine)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        self.session.close()
    
    def test_create_device(self):
        """Тест создания устройства"""
        # Получаем существующий тип устройства
        device_type = self.session.query(DeviceType).first()
        
        # Создаем устройство
        device = Device(
            type=device_type.id,
            name="Test Device",
            ip_address="192.168.1.100",
            architecture="x86_64",
            memory=8192,
            processor="Intel i7",
            gpu=True,
            last_seen = datetime.now()  
        )
        
        self.session.add(device)
        self.session.commit()
        
        # Проверяем что устройство создано
        saved_device = self.session.query(Device).filter_by(name="Test Device").first()
        assert saved_device is not None
        assert saved_device.ip_address == "192.168.1.100"
        assert saved_device.gpu == True
    
    def test_create_neural_model(self):
        """Тест создания нейросетевой модели"""
        # Получаем существующий формат модели
        model_format = self.session.query(ModelFormat).first()
        
        model = NeuralModel(
            name="Test Neural Network",
            orginal_path="/models/test_model.pth",
            format=model_format.id,
            size=250.5
        )
        
        self.session.add(model)
        self.session.commit()
        
        saved_model = self.session.query(NeuralModel).filter_by(name="Test Neural Network").first()
        assert saved_model is not None
        assert saved_model.size == 250.5
    
    def test_create_optimized_model(self):
        """Тест создания оптимизированной модели"""
        # Создаем необходимые зависимости
        device_type = self.session.query(DeviceType).first()
        model_format = self.session.query(ModelFormat).first()
        
        device = Device(
            type=device_type.id,
            name="Test Device for Optimization",
            ip_address="192.168.1.200",
            architecture="ARM64",
            memory=4096,
            processor="Cortex-A78",
            gpu=False,
            last_seen = datetime.now()  

        )
        
        neural_model = NeuralModel(
            name="Model to Optimize",
            orginal_path="/models/to_optimize.pth",
            format=model_format.id,
            size=300.0
        )
        
        self.session.add_all([device, neural_model])
        self.session.commit()
        
        # Создаем оптимизированную модель
        optimized_model = OptimizedModel(
            original_model_id=neural_model.id,
            device_id=device.id,
            path="/optimized/models/optimized_v1.tflite",
            size=45.2,
            optimization_params='{"quantization": "int8", "pruning": 0.3}'
        )
        
        self.session.add(optimized_model)
        self.session.commit()
        
        saved_optimized = self.session.query(OptimizedModel).filter_by(
            original_model_id=neural_model.id
        ).first()
        
        assert saved_optimized is not None
        assert saved_optimized.size == 45.2
    
    def test_create_optimization_record(self):
        """Тест создания записи оптимизации"""
        # Создаем необходимые данные
        device_type = self.session.query(DeviceType).first()
        model_format = self.session.query(ModelFormat).first()
        
        device = Device(
            type=device_type.id,
            name="Device for Optimization Record",
            ip_address="192.168.1.150",
            architecture="x86_64",
            memory=16384,
            processor="Xeon",
            gpu=True, 
            last_seen = datetime.now()  

        )
        
        neural_model = NeuralModel(
            name="Model for Optimization Record",
            orginal_path="/models/for_record.pth",
            format=model_format.id,
            size=500.0
        )
        
        optimized_model = OptimizedModel(
            original_model_id=neural_model.id,
            device_id=device.id,
            path="/optimized/record_model.trt",
            size=120.5,
            optimization_params='{"precision": "FP16"}'
        )
        
        self.session.add_all([device, neural_model, optimized_model])
        self.session.commit()
        
        # Создаем запись оптимизации
        optimization_record = OptimizationRecord(
            optimized_model_id=optimized_model.id,
            original_model_id=neural_model.id,
            accuracy_before=0.95,
            accuracy_after=0.94,
            loss_before=0.1,
            loss_after=0.12,
            status="completed"
        )
        
        self.session.add(optimization_record)
        self.session.commit()
        
        saved_record = self.session.query(OptimizationRecord).filter_by(
            optimized_model_id=optimized_model.id
        ).first()
        
        assert saved_record is not None
        assert saved_record.accuracy_before == 0.95
        assert saved_record.status == "completed"
    
    def test_create_deployment_record(self):
        """Тест создания записи деплоя"""
        # Создаем необходимые данные
        device_type = self.session.query(DeviceType).first()
        model_format = self.session.query(ModelFormat).first()
        
        device = Device(
            type=device_type.id,
            name="Device for Deployment",
            ip_address="192.168.1.250",
            architecture="ARM64",
            memory=2048,
            processor="Cortex-A53",
            gpu=False,
            last_seen = datetime.now()  
        )
        
        neural_model = NeuralModel(
            name="Model for Deployment",
            orginal_path="/models/deploy.pth",
            format=model_format.id,
            size=150.0
        )
        
        optimized_model = OptimizedModel(
            original_model_id=neural_model.id,
            device_id=device.id,
            path="/deployed/model.onnx",
            size=35.7,
            optimization_params='{"quantization": "dynamic"}'
        )
        
        self.session.add_all([device, neural_model, optimized_model])
        self.session.commit()
        
        # Создаем запись деплоя
        deployment_record = DeploymentRecord(
            optimized_model_id=optimized_model.id,
            device_id=device.id,
            status="deployed"
        )
        
        self.session.add(deployment_record)
        self.session.commit()
        
        saved_deployment = self.session.query(DeploymentRecord).filter_by(
            optimized_model_id=optimized_model.id
        ).first()
        
        assert saved_deployment is not None
        assert saved_deployment.status == "deployed"
        assert saved_deployment.deployment_date is not None
    
    def test_read_operations(self):
        """Тесты операций чтения"""
        # Проверяем существующие типы устройств
        device_types = self.session.query(DeviceType).all()
        assert len(device_types) >= 2  # Должны быть предзаполненные данные
        
        # Проверяем существующие форматы моделей
        model_formats = self.session.query(ModelFormat).all()
        assert len(model_formats) >= 2  # Должны быть предзаполненные данные
        
        # Проверяем что можем фильтровать
        onnx_format = self.session.query(ModelFormat).filter_by(name="ONNX").first()
        assert onnx_format is not None
    
    def test_update_operations(self):
        """Тесты операций обновления"""
        # Создаем тестовое устройство
        device_type = self.session.query(DeviceType).first()
        
        device = Device(
            type=device_type.id,
            name="Device to Update",
            ip_address="192.168.1.50",
            architecture="x86_64",
            memory=4096,
            processor="Intel i5",
            gpu=False,
            last_seen = datetime.now()  
        )
        
        self.session.add(device)
        self.session.commit()
        
        # Обновляем устройство
        device.memory = 8192
        device.processor = "Intel i7"
        self.session.commit()
        
        # Проверяем обновление
        updated_device = self.session.query(Device).filter_by(name="Device to Update").first()
        assert updated_device.memory == 8192
        assert updated_device.processor == "Intel i7"
    
    def test_delete_operations(self):
        """Тесты операций удаления"""
        # Создаем тестовую модель
        model_format = self.session.query(ModelFormat).first()
        
        model = NeuralModel(
            name="Model to Delete",
            orginal_path="/models/delete_me.pth",
            format=model_format.id,
            size=100.0
        )
        
        self.session.add(model)
        self.session.commit()
        
        # Удаляем модель
        self.session.delete(model)
        self.session.commit()
        
        # Проверяем что модель удалена
        deleted_model = self.session.query(NeuralModel).filter_by(name="Model to Delete").first()
        assert deleted_model is None

if __name__ == "__main__":
    # Запуск тестов
    test_class = TestCRUDOperations()
    
    print("🧪 Запуск CRUD тестов...")
    
    test_class.setup_method()
    
    try:
        n =1
        test_class.test_create_device()
        print("✅ test_create_device - PASSED")
        n+=1
        test_class.test_create_neural_model()
        print("✅ test_create_neural_model - PASSED")
        n+=1
        test_class.test_create_optimized_model()
        print("✅ test_create_optimized_model - PASSED")
        n+=1
        test_class.test_create_optimization_record()
        print("✅ test_create_optimization_record - PASSED")
        n+=1
        test_class.test_create_deployment_record()
        print("✅ test_create_deployment_record - PASSED")
        n+=1
        test_class.test_read_operations()
        print("✅ test_read_operations - PASSED")
        n+=1
        test_class.test_update_operations()
        print("✅ test_update_operations - PASSED")
        n+=1
        test_class.test_delete_operations()
        print("✅ test_delete_operations - PASSED")
        
        print("\n🎉 Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"❌ Тест {n} упал с ошибкой: {e}")
        raise
    finally:
        test_class.teardown_method()