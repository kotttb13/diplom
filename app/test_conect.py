from core.services.device_service.device_service import UniversalDeviceService
from core.repositories import DeviceRepository, ModelRepository
from core.database.initialization_db import initialize_database, get_session


config = {
        'host': '192.168.0.169',      # IP из вашей диагностики
        'username': 'u0_a398',        # ЗАМЕНИТЕ на результат команды 'whoami' в Termux
        'password': '1111',  # ЗАМЕНИТЕ на пароль, установленный в Termux
        'port': 8022                  # Порт из диагностики
    }
engine = initialize_database()
session = get_session(engine)
repo = DeviceRepository(session)
device = UniversalDeviceService(repo)
try:
    print("Запуск подключения к Android...")
    success = device.connect_device("android", **config)
    if not success:
        print("\n Не удалось подключиться к Android")
    print(success) 
    inf = device.get_and_save_device_info()


    modelrepo = ModelRepository(session)

    print("программа дошла до конца")
except Exception as e:
             print(f"error: {e}")


