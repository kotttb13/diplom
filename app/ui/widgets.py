from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit, QComboBox,
    QTextEdit, QGroupBox, QScrollArea, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QDateTime
from PyQt5.QtGui import QFont, QColor, QPainter, QPen

from .styles import WarframeStyles

class WarframeButton(QPushButton):
    """Кнопка в стиле Warframe с анимацией"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        
        # Анимация наведения
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._reset_hover)
        
    def _reset_hover(self):
        pass  # Можно добавить анимацию

class StatusLabel(QLabel):
    """Метка статуса с иконкой"""
    
    STATUS_COLORS = {
        'success': WarframeStyles.COLORS['accent_success'],
        'error': WarframeStyles.COLORS['error'],
        'warning': WarframeStyles.COLORS['warning'],
        'info': WarframeStyles.COLORS['accent_primary'],
        'processing': WarframeStyles.COLORS['accent_primary']
    }
    
    def __init__(self, text="", status="info", parent=None):
        super().__init__(text, parent)
        self.status = status
        self.update_style()
    
    def set_status(self, status):
        """Установить статус"""
        self.status = status
        self.update_style()
    
    def update_style(self):
        """Обновить стиль в зависимости от статуса"""
        color = self.STATUS_COLORS.get(self.status, WarframeStyles.COLORS['text_primary'])
        self.setStyleSheet(f"color: {color.name()}; font-weight: bold;")

class ConsoleOutputWidget(QTextEdit):
    """Виджет вывода консоли в стиле Warframe"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(200)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #121620;
                color: #00B7EB;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #32363C;
                border-radius: 3px;
            }
        """)
    
    def add_message(self, message, msg_type="info"):
        """Добавить сообщение"""
        colors = {
            'info': '#00B7EB',
            'success': '#2ECC71',
            'warning': '#F1C40F',
            'error': '#E74C3C',
            'command': '#FFFFFF'
        }
        
        color = colors.get(msg_type, '#00B7EB')
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        
        html = f'<font color="#666666">[{timestamp}]</font> <font color="{color}">{message}</font><br>'
        
        self.append(html)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

class DeviceSelector(QWidget):
    """Виджет выбора устройства"""
    
    device_selected = pyqtSignal(int)  # Сигнал с ID устройства
    
    def __init__(self, device_repo, parent=None):
        super().__init__(parent)
        self.device_repo = device_repo
        self.init_ui()
        self.load_devices()
    
    def init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("ВЫБОР EDGE-УСТРОЙСТВА")
        title.setFont(WarframeStyles.get_font(14, True))
        title.setStyleSheet("color: #00B7EB;")
        layout.addWidget(title)
        
        # Список устройств
        self.device_combo = QComboBox()
        self.device_combo.setMinimumHeight(35)
        layout.addWidget(self.device_combo)
        
        # Информация о выбранном устройстве
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("""
            QFrame {
                background-color: #1A1E24;
                border: 1px solid #32363C;
                border-radius: 3px;
                padding: 10px;
            }
        """)
        
        info_layout = QVBoxLayout(self.info_frame)
        self.info_label = QLabel("Выберите устройство")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        
        layout.addWidget(self.info_frame)
        
        # Кнопка обновления
        refresh_btn = WarframeButton("Обновить список")
        refresh_btn.clicked.connect(self.load_devices)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
        
        # Подключаем сигналы
        self.device_combo.currentIndexChanged.connect(self.on_device_selected)
    
    def load_devices(self):
        """Загрузить список устройств"""
        self.device_combo.clear()
        devices = self.device_repo.get_all()
        
        for device in devices:
            self.device_combo.addItem(
                f"{device.ip_address} ({device.architecture})", 
                device.id
            )
    
    def on_device_selected(self, index):
        """Обработчик выбора устройства"""
        if index >= 0:
            device_id = self.device_combo.currentData()
            device = self.device_repo.get_by_id(device_id)
            
            if device:
                info_text = f"""
                <b>IP:</b> {device.ip_address}<br>
                <b>Архитектура:</b> {device.architecture}<br>
                <b>RAM:</b> {device.ram_gb} GB<br>
                <b>CPU:</b> {device.cpu_core} ядер<br>
                <b>Тип:</b> {device.type}
                """
                self.info_label.setText(info_text)
                self.device_selected.emit(device_id)

class ProgressDialog(QFrame):
    """Диалог прогресса в стиле Warframe"""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QFrame {
                background-color: #0A0E14;
                border: 2px solid #00B7EB;
                border-radius: 5px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel(title)
        title_label.setFont(WarframeStyles.get_font(16, True))
        title_label.setStyleSheet("color: #00B7EB;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Сообщение
        self.message_label = QLabel("Подождите, пожалуйста, идет процесс загрузки")
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Время ожидания
        self.time_label = QLabel("Примерное время ожидания - N минут")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: #999999;")
        layout.addWidget(self.time_label)
        
        # Кнопка отмены
        self.cancel_button = WarframeButton("Отмена")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #EB4B4B;
                color: #0A0E14;
            }
        """)
        layout.addWidget(self.cancel_button)
        
        self.setLayout(layout)
    
    def update_progress(self, value, message=""):
        """Обновить прогресс"""
        self.progress_bar.setValue(value)
        if message:
            self.message_label.setText(message)
    
    def set_time_estimate(self, minutes):
        """Установить время ожидания"""
        self.time_label.setText(f"Примерное время ожидания - {minutes} минут")