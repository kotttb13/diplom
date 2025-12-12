
import sys
import os


venv_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
venv_scripts = os.path.join(venv_path, ".venv", "Scripts")

if venv_scripts not in os.environ.get('PATH', ''):
    os.environ['PATH'] = venv_scripts + os.pathsep + os.environ.get('PATH', '')
    print(f"Added to PATH: {venv_scripts}")


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


try:
    import tensorflow as tf
    print(f"TensorFlow {tf.__version__} loaded from: {tf.__file__}")
except ImportError as e:
    print(f"TensorFlow import error: {e}")
    
    import ctypes
    import ctypes.util
    
    dll_path = ctypes.util.find_library("_pywrap_tensorflow_internal")
    print(f"DLL search result: {dll_path}")
    
    sys.exit(1)


from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QFontDatabase, QIcon



sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.windows import MainWindow

def setup_application():
    
    app = QApplication(sys.argv)
    app.setApplicationName("Neuro-Optimizer")
    app.setOrganizationName("TennoCorp")
    
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    font_paths = [
        "resources/fonts/Digitall.ttf",
        "resources/fonts/Rajdhani-Regular.ttf",
        "resources/fonts/Rajdhani-Bold.ttf"
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)
    
    window = MainWindow()
    window.show()
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(setup_application())
