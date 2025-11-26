# import json
# import time
# from device_manager import SSHManager
# import os
# import sys
# from device_manager import AndroidSSHManager


# sys.path.append(os.path.dirname(__file__))
# def dd(host, username, password, port):
#     config = {
#         'host': host,      
#         'username': username,
#         'password': password,
#         'port': port
#     }
#     android = AndroidSSHManager()
#     try:
#         success = android.connect_android(**config)
#     except Exception as e:
#         return e
        

        


# def main():
#     # Создаем менеджер устройств
#     android = AndroidSSHManager()
    
#     # Конфигурация - ЗАПОЛНИТЕ ЭТИ ДАННЫЕ!
#     config = {
#         'host': '192.168.0.169',      # IP из вашей диагностики
#         'username': 'u0_a398',        # ЗАМЕНИТЕ на результат команды 'whoami' в Termux
#         'password': '1111',  # ЗАМЕНИТЕ на пароль, установленный в Termux
#         'port': 8022                  # Порт из диагностики
#     }
    
#     try:
#         # Подключение
#         print("🚀 Запуск подключения к Android...")
#         success = android.connect_android(**config)
        
#         if not success:
#             print("\n❌ Не удалось подключиться к Android")
#             print("\n🔧 Проверьте:")
#             print("   1. Что Termux запущен на Android")
#             print("   2. Что в Termux выполнили: sshd")
#             print("   3. Что пароль установлен: passwd")
#             print("   4. Что Wi-Fi сети совпадают")
#             return
        
#         # Получение информации
#         print("\n" + "="*60)
#         print("📊 ИНФОРМАЦИЯ ОБ ANDROID УСТРОЙСТВЕ")
#         print("="*60)
        
#         info = android.get_android_info()
#         for key, value in info.items():
#             print(f"  {key}: {value}")
        
#         # Тестирование команд
#         print("\n" + "="*60)
#         print("🧪 ТЕСТИРОВАНИЕ КОМАНД")
#         print("="*60)
        
#         test_commands = [
#             "pwd",
#             "ls -la",
#             "whoami",
#             "id",
#             "uname -a",
#             "date",
#         ]
        
#         for cmd in test_commands:
#             print(f"\n>>> {cmd}")
#             result = android.execute_command(cmd)
#             if result['success']:
#                 print(f"✅ Успех: {result['output']}")
#             else:
#                 print(f"❌ Ошибка: {result.get('error', 'Unknown error')}")
#     except KeyboardInterrupt:
#         print("\n\n⏹️  Программа прервана пользователем")
#     except Exception as e:
#         print(f"\n\n💥 Критическая ошибка: {e}")
#     finally:
#         # Всегда закрываем соединения
#         print("\n🔌 Закрываем соединения...")
#         android.close()

# if __name__ == "__main__":
#     main()  