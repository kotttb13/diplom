import sys
import os

print(f"Executable: {sys.executable}")
print(f"Base prefix: {sys.base_prefix}")
print(f"Executable name: {os.path.basename(sys.executable)}")

if "pythonw" in sys.executable.lower():
    print("⚠️ Запущено через pythonw.exe - это может быть проблемой!")
    
# Проверка переменных окружения
print(f"\nPATH начало: {os.environ.get('PATH', '')[:200]}...")