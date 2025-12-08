
import sys
import os

# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ДЛЯ WINDOWS
# Принудительно добавляем пути к DLL

# 1. Добавляем путь к .venv в PATH
venv_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
venv_scripts = os.path.join(venv_path, ".venv", "Scripts")

if venv_scripts not in os.environ.get('PATH', ''):
    os.environ['PATH'] = venv_scripts + os.pathsep + os.environ.get('PATH', '')
    print(f"Added to PATH: {venv_scripts}")

# 2. Добавляем пути к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 3. Проверяем TensorFlow ДО PyQt5
try:
    import tensorflow as tf
    print(f"✅ TensorFlow {tf.__version__} loaded from: {tf.__file__}")
except ImportError as e:
    print(f"❌ TensorFlow import error: {e}")
    
    # Проверяем DLL пути
    import ctypes
    import ctypes.util
    
    # Попробуем найти DLL вручную
    dll_path = ctypes.util.find_library("_pywrap_tensorflow_internal")
    print(f"DLL search result: {dll_path}")
    
    sys.exit(1)

# 4. Только теперь импортируем PyQt5
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QFontDatabase, QIcon


# Добавляем путь к core модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.windows import MainWindow

def setup_application():
    """Настройка приложения в стиле Warframe"""
    app = QApplication(sys.argv)
    app.setApplicationName("Neuro-Optimizer")
    app.setOrganizationName("TennoCorp")
    
    # Устанавливаем High DPI поддержку
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Загружаем шрифты Warframe (если есть)
    font_paths = [
        "resources/fonts/Digitall.ttf",
        "resources/fonts/Rajdhani-Regular.ttf",
        "resources/fonts/Rajdhani-Bold.ttf"
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)
    
    # Создаем и показываем главное окно
    window = MainWindow()
    window.show()
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(setup_application())