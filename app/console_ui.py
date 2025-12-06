import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from core.database.initialization_db import initialize_database, get_session
from core.repositories.device_repository import DeviceRepository
from core.repositories.model_repository import ModelRepository
from core.repositories.deployment_repository import DeploymentRepository
from core.repositories.optimized_model_repository import OptimizedModelRepository
from core.repositories.optimization_record_repository import OptimizationRecordRepository
from core.services import OptimizationService, UniversalDeviceService, ModelValidationService
class ConsoleUI:
    def __init__(self):
        # Инициализация БД и репозиториев
        self.engine = initialize_database()
        self.session = get_session(self.engine)
        
        self.device_repo = DeviceRepository(self.session)
        self.model_repo = ModelRepository(self.session)
        self.optimized_model_repo = OptimizedModelRepository(self.session)
        self.optimization_record_repo = OptimizationRecordRepository(self.session)
        self.deployment_repo = DeploymentRepository(self.session)

        self.optimization_service = OptimizationService(
            self.device_repo,
            self.model_repo,
            self.optimized_model_repo
        )
        self.validation_service = ModelValidationService(self.optimization_record_repo)
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
            print("7. Развернуть OTA обновление")  # НОВАЯ ОПЦИЯ
            print("8. Показать историю развертываний")  
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
            elif choice == "7":  # НОВОЕ
                self.deploy_ota_update()
            elif choice == "8":  # НОВОЕ
                self.show_deployment_history()
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
        
        x_test_data_path = input("введите путь к тестовым данным: ")
        y_test_data_path = input("введите путь к тестовым меткам: ")

        try:
            x_test_data = np.load(x_test_data_path)
            y_test_data = np.load(y_test_data_path)
        except Exception as e:
            print(f" Ошибка! тестовые данные не найдены: {e}")

        print(f"\n Запуск оптимизации модели ID:{model_id} для устройства ID:{device_id}...")
        
        # Запускаем оптимизацию
        result = self.optimization_service.optimize_model_by_id(
            model_id=int(model_id),
            device_id=int(device_id)
        )
        
        if result['success']:
            print(" Оптимизация завершена успешно!")
            original_model_path = self.model_repo.get_path_by_id(model_id)[0]
            original_model_format = original_model_path.split('.')[-1].lower()
            optimized_model_format = result['optimized_model_path'].split('.')[-1].lower()
            success = self.validation_service.validate_model_pair(original_model_path, result['optimized_model_path'], x_test_data, y_test_data, original_model_format, optimized_model_format )
            print(f" Оптимизированная модель: {result['optimized_model_path']}")
            print(f" Размер: {result.get('model_size_mb', 0):.2f} MB")
            print(f" Стратегия: {result.get('strategy', {})}")
            if success["success"]:
                print("="*80)
                print("Отчет проверки качества модели")
                print(f" Точность до оптимизации: {success["accuracy_before"]}")
                print(f" Точность после оптимизации: {success["accuracy_after"]}")
                print(f" Потери до оптимизации: {success["loss_before"]}")
                print(f" Потери после оптимизации: {success["loss_after"]}")
                self.validation_service._save_optimization_result(model_id, result['optimized_model_id'], success)
            else:
                print(f" Не получилось проверить качество оптимизироваанной модели: {success["erorr"]}")

            if 'optimized_model_id' in result:
                print(f" ID оптимизированной модели: {result['optimized_model_id']}")
            print("="*80)
        else:
            print(f" Ошибка оптимизации: {result.get('error', 'Неизвестная ошибка')}")
    
    def show_optimization_history(self):
        """Показать историю оптимизаций"""
        print("\n ИСТОРИЯ ОПТИМИЗАЦИЙ:")
        print("-" * 80)
        
        records = self.optimization_record_repo.get_recent_records(limit=10)
        
        if not records:
            print("❌ Записи оптимизации не найдены")
            return
        
        for record in records:
            print(f"ID: {record.id} | Модель ID: {record.original_model_id} | "
                  f"Статус: {record.status} | "
                  f"Точность до: {record.accuracy_before or 'N/A'} | "
                  f"Точность после: {record.accuracy_after or 'N/A'}")
        print("-" * 80)
    
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


    def deploy_ota_update(self):
        """Развертывание OTA обновления на устройство"""
        print("\n" + "="*50)
        print("РАЗВЕРТЫВАНИЕ OTA ОБНОВЛЕНИЯ")
        print("="*50)
        
        # 1. Показываем оптимизированные модели
        print("\n1. Выберите оптимизированную модель:")
        self.show_optimized_models()
        
        try:
            model_id = int(input("\nВведите ID оптимизированной модели: ").strip())
        except ValueError:
            print(" Неверный ID модели")
            return
        
        # Получаем модель
        optimized_model = self.optimized_model_repo.get_by_id(model_id)
        if not optimized_model:
            print(" Оптимизированная модель не найдена")
            return
        
        # 2. Показываем устройства
        print("\n2. Выберите устройство:")
        self.show_devices()
        
        try:
            device_id = int(input("\nВведите ID устройства: ").strip())
        except ValueError:
            print(" Неверный ID устройства")
            return
        
        # Проверяем устройство
        device = self.device_repo.get_by_id(device_id)
        if not device:
            print(" Устройство не найдено")
            return
        
        # 3. Секрет для шифрования
        print("\n3. Настройки шифрования:")
        secret = input("Введите секретную фразу для шифрования (или Enter для автоматической): ").strip()
        if not secret:
            secret = None
        
        # 4. Подтверждение
        print("\n" + "="*50)
        print("ПОДТВЕРЖДЕНИЕ РАЗВЕРТЫВАНИЯ:")
        print(f"Модель: {optimized_model.path}")
        print(f"Устройство: {device.ip_address} (ID: {device.id})")
        print(f"Тип: {device.type}")
        print("="*50)
        
        confirm = input("\nПодтвердить развертывание? (y/N): ").strip().lower()
        if confirm != 'y':
            print(" Развертывание отменено")
            return
        
        # 5. Создаем запись о развертывании
        deployment = self.deployment_repo.create_deployment(
            optimized_model_id=model_id,
            device_id=device_id,
            status="starting"
        )
        
    
       
        # 6. Подключаемся к устройству (если нужно)
        print("🔌 Проверка подключения к устройству...")
        
        # Здесь нужно получить параметры подключения для устройства
        # Предполагаем, что они сохранены где-то или запрашиваем
        print("Введите параметры подключения к устройству:")
        host = input(f"IP адрес [{device.ip_address}]: ").strip() or device.ip_address
        username = input("Имя пользователя: ").strip()
        password = input("Пароль: ").strip()
        port = input("Порт [8022]: ").strip() or "8022"
        
        connection_params = {
            'host': host,
            'username': username,
            'password': password,
            'port': int(port)
        }
        
        # Подключаемся
        connect_result = self.device_service.connect_device(
            device_type="android",  # или получаем из device.type
            **connection_params
        )
        
        if not connect_result.get('success'):
            self.deployment_repo.update_status(deployment.id, "connection_failed")
            print(f"❌ Ошибка подключения: {connect_result.get('error')}")
            return
        
        print("✅ Успешное подключение к устройству")
        
        # 7. Запускаем развертывание
        print("🚀 Запуск развертывания OTA...")
        self.deployment_repo.update_status(deployment.id, "deploying")
        
        result = self.device_service.deploy_ota_update(
            model_path=optimized_model.path,
            model_id=model_id,
            device_id=device_id,
            secret=secret,
            remote_dir="~/ota_updates/"
        )
        
        # 8. Обновляем статус развертывания
        if result.get('success'):
            self.deployment_repo.update_status(deployment.id, "success")
            print("\n" + "="*50)
            print("✅ OTA ОБНОВЛЕНИЕ УСПЕШНО РАЗВЕРНУТО!")
            print("="*50)
            print(f"ID развертывания: {deployment.id}")
            print(f"Файл на устройстве: {result.get('output_file')}")
            print(f"Контрольная сумма: {result.get('checksum')[:16]}...")
            print(f"Размер файла: {result.get('original_size')} байт")
            
            # Сохраняем дополнительную информацию
            print("\n📝 Для проверки на устройстве выполните:")
            print(f"  ls -la {result.get('output_file')}")
            print(f"  file {result.get('output_file')}")
            
        else:
            self.deployment_repo.update_status(deployment.id, "failed")
            print("\n❌ ОШИБКА РАЗВЕРТЫВАНИЯ OTA")
            print(f"Ошибка: {result.get('error')}")
            
            # Показываем дополнительные детали если есть
            if 'command_output' in result:
                print(f"Вывод команды: {result.get('command_output')}")
        
        print("="*50)
    

    def show_optimized_models(self):
            """Показать оптимизированные модели"""
            print("\n СПИСОК ОПТИМИЗИРОВАННЫХ МОДЕЛЕЙ:")
            print("-" * 80)
            models = self.optimized_model_repo.get_all()
            
            if not models:
                print(" Оптимизированные модели не найдены")
                return
            
            for model in models:
                # Получаем информацию об оригинальной модели
                original_model = self.model_repo.get_by_id(model.original_model_id)
                original_name = original_model.name if original_model else f"ID:{model.original_model_id}"
                
                print(f"ID: {model.id} | Оригинал: {original_name} | "
                    f"Путь: {model.path} | "
                    f"Размер: {model.size:.2f} MB | ")
            print("-" * 80)


    def show_deployment_history(self):
        """Показать историю развертываний"""
        print("\n ИСТОРИЯ РАЗВЕРТЫВАНИЙ OTA:")
        print("-" * 100)
        
        deployments = self.deployment_repo.get_all()
        
        if not deployments:
            print(" Записи развертываний не найдены")
            return
        
        print(f"{'ID':<5} {'Модель':<15} {'Устройство':<15} {'Статус':<15} {'Дата':<20}")
        print("-" * 100)
        
        for dep in deployments:
            # Получаем информацию о модели
            optimized_model = self.optimized_model_repo.get_by_id(dep.optimized_model_id)
            model_info = f"Model {dep.optimized_model_id}"
            if optimized_model:
                # Получаем оригинальное имя
                original_model = self.model_repo.get_by_id(optimized_model.original_model_id)
                if original_model:
                    model_info = original_model.name[:15]
            
            # Получаем информацию об устройстве
            device = self.device_repo.get_by_id(dep.device_id)
            device_info = f"Device {dep.device_id}"
            if device:
                device_info = device.ip_address[:15]
            
            # Иконка статуса
            status_icon = "✅" if dep.status == "success" else "❌" if "fail" in dep.status else "🔄"
            
            print(f"{dep.id:<5} {model_info:<15} {device_info:<15} "
                  f"{status_icon} {dep.status:<12} {dep.deployment_date.strftime('%Y-%m-%d %H:%M:%S'):<20}")
        
        print("-" * 100)
        









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