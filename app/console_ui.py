import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database.initialization_db import initialize_database, get_session
from core.repositories.device_repository import DeviceRepository
from core.repositories.model_repository import ModelRepository
from core.repositories.optimized_model_repository import OptimizedModelRepository
from core.repositories.optimization_record_repository import OptimizationRecordRepository
from core.services.optimization_service.optimization_service import OptimizationService
from core.services.device_service.device_service import UniversalDeviceService

class ConsoleUI:
    def __init__(self):
        # Инициализация БД и репозиториев
        self.engine = initialize_database()
        self.session = get_session(self.engine)
        
        self.device_repo = DeviceRepository(self.session)
        self.model_repo = ModelRepository(self.session)
        self.optimized_model_repo = OptimizedModelRepository(self.session)
        self.optimization_record_repo = OptimizationRecordRepository(self.session)
        
        self.optimization_service = OptimizationService(
            self.device_repo,
            self.model_repo,
            self.optimized_model_repo,
            self.optimization_record_repo
        )

        self.device_service = UniversalDeviceService(self.device_repo)
    
    def show_main_menu(self):
        """Главное меню"""
        while True:
            print("\n" + "="*50)
            print("СИСТЕМА ОПТИМИЗАЦИИ НЕЙРОСЕТЕЙ")
            print("="*50)
            print("1. Показать все модели")
            print("2. Показать все устройства") 
            print("3. Оптимизировать модель")
            print("4. Показать историю оптимизаций")
            print("5. Добавить модель")
            print("6. Добавить устройство")
            print("0. Выход")
            print("="*50)
            
            choice = input("Выберите действие: ").strip()
            
            if choice == "1":
                self.show_models()
            elif choice == "2":
                self.show_devices()
            elif choice == "3":
                self.optimize_model()
            elif choice == "4":
                self.show_optimization_history()
            elif choice == "5":
                self.add_model()
            elif choice == "6":
                self.add_device()
            elif choice == "0":
                print("Выход из программы...")
                self.session.close()
                break
            else:
                print(" Неверный выбор!")
    
    def show_models(self):
        """Показать все модели"""
        print("\n СПИСОК МОДЕЛЕЙ:")
        print("-" * 80)
        models = self.model_repo.get_all()
        
        if not models:
            print(" Модели не найдены")
            return
        
        for model in models:
            model_details = self.model_repo.get_model_type_and_format(model.id)
            print(f"ID: {model.id} | Название: {model.name} | "
                  f"Тип: {model_details['model_type'] if model_details else 'N/A'} | "
                  f"Формат: {model_details['model_format'] if model_details else 'N/A'} | "
                  f"Путь: {model.original_path}")
        print("-" * 80)
    
    def show_devices(self):
        """Показать все устройства"""
        print("\n СПИСОК УСТРОЙСТВ:")
        print("-" * 80)
        devices = self.device_repo.get_all()
        
        if not devices:
            print(" Устройства не найдены")
            return
        
        for device in devices:
            print(f"ID: {device.id} | IP: {device.ip_address} | "
                  f"Архитектура: {device.architecture} | "
                  f"RAM: {device.ram_gb} GB | CPU: {device.cpu_core} ядер")
        print("-" * 80)
    
    def optimize_model(self):
        """Оптимизировать модель"""
        print("\n ОПТИМИЗАЦИЯ МОДЕЛИ")
        
        # Показываем доступные модели
        self.show_models()
        model_id = input("\nВведите ID модели для оптимизации: ").strip()
        
        if not model_id.isdigit():
            print(" Неверный ID модели")
            return
        
        # Показываем доступные устройства
        self.show_devices()
        device_id = input("Введите ID устройства: ").strip()
        
        if not device_id.isdigit():
            print(" Неверный ID устройства")
            return
        
        print(f"\n Запуск оптимизации модели ID:{model_id} для устройства ID:{device_id}...")
        
        # Запускаем оптимизацию
        result = self.optimization_service.optimize_model_by_id(
            model_id=int(model_id),
            device_id=int(device_id)
        )
        
        if result['success']:
            print(" Оптимизация завершена успешно!")
            print(f" Оптимизированная модель: {result['optimized_model_path']}")
            print(f" Размер: {result.get('model_size_mb', 0):.2f} MB")
            print(f" Стратегия: {result.get('strategy', {})}")
            
            if 'optimized_model_id' in result:
                print(f" ID оптимизированной модели: {result['optimized_model_id']}")
        else:
            print(f" Ошибка оптимизации: {result.get('error', 'Неизвестная ошибка')}")
    
    def show_optimization_history(self):
        """Показать историю оптимизаций"""
        print("\n ИСТОРИЯ ОПТИМИЗАЦИЙ:")
        print("-" * 80)
        
        # records = self.optimization_record_repo.get_recent_records(limit=10)
        
        # if not records:
        #     print("❌ Записи оптимизации не найдены")
        #     return
        
        # for record in records:
        #     print(f"ID: {record.id} | Модель ID: {record.original_model_id} | "
        #           f"Статус: {record.status} | "
        #           f"Точность до: {record.accuracy_before or 'N/A'} | "
        #           f"Точность после: {record.accuracy_after or 'N/A'}")
        # print("-" * 80)
    
    def add_model(self):
        """Добавить новую модель"""
        print("\n ДОБАВЛЕНИЕ НОВОЙ МОДЕЛИ")
        
        name = input("Название модели: ").strip()
        path = input("Путь к файлу модели: ").strip()
        model_type = input("Тип модели (cv/nlp/audio): ").strip().lower()
        
        # Автоматическое определение формата из расширения файла
        file_extension = path.split('.')[-1].lower()
        format_name = file_extension if file_extension in ['h5', 'keras', 'onnx', 'pb', 'tflite'] else 'unknown'
        
        try:
            model = self.model_repo.create_model(
                name=name,
                original_path=path,
                model_type_name=model_type,
                format_name=format_name
            )
            print(f" Модель '{name}' успешно добавлена с ID: {model.id}")
        except Exception as e:
            print(f" Ошибка добавления модели: {e}")
    
    def add_device(self):
        """Добавить новое устройство"""
        print("\n ДОБАВЛЕНИЕ НОВОГО УСТРОЙСТВА")
        print("test : 'host': '192.168.0.169',      # IP из вашей диагностики\n'username': 'u0_a398',        # ЗАМЕНИТЕ на результат команды 'whoami' в Termux\n'password': '1111',  # ЗАМЕНИТЕ на пароль, установленный в Termux\n'port': 8022   ")
        ip = input("введите ip адрес устройства: ")
        username = input("введите имя пользователя устройства: ")
        password = input("введите пароль устройства: ")
        port = input("введите порт устройства: ")
        config = {
        'host': ip,      # IP из вашей диагностики
        'username': username,        # ЗАМЕНИТЕ на результат команды 'whoami' в Termux
        'password': password,  # ЗАМЕНИТЕ на пароль, установленный в Termux
        'port': port                  # Порт из диагностики
    }
        try:
            success = self.device_service.connect_device("android", **config)
            if not success:
                print("\n Не удалось подключиться к Android")
            print(success) 
            inf = self.device_service.get_and_save_device_info()
            print(f" Устройство {ip} успешно добавлено")
        except Exception as e:
            print(f" Ошибка добавления устройства: {e}")

def main():
    """Точка входа в приложение"""
    try:
        ui = ConsoleUI()
        ui.show_main_menu()
    except Exception as e:
        print(f" Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()