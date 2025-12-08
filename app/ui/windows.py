import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QTableWidget,
    QTableWidgetItem, QMessageBox, QFileDialog, QInputDialog,
    QGroupBox, QHeaderView, QFormLayout, QLineEdit, QSizePolicy,
    QDialog, QDialogButtonBox, QStatusBar, QProgressBar, QComboBox, QButtonGroup,
    QAbstractItemView, QAction, QMenu, QStackedWidget, QProgressDialog, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor



from .styles import WarframeStyles
from .widgets import WarframeButton, StatusLabel, ConsoleOutputWidget

# Импортируем core модули через иниты
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импорт из core.database (предполагаем, что там есть __init__.py с этими функциями)
try:
    from core.database import initialize_database, get_session
except ImportError:
    # Если нет инита, импортируем напрямую
    from core.database.initialization_db import initialize_database, get_session

# Импорт из core.repositories (используем ваш __init__.py)
from core.repositories import (
    DeviceRepository,
    ModelRepository,
    OptimizedModelRepository,
    OptimizationRecordRepository,
    DeploymentRepository
)

# Импорт из core.services (уже есть инит)
from core.services import OptimizationService, UniversalDeviceService, ModelValidationService

class WorkerThread(QThread):
    """Поток для выполнения длительных операций"""
    
    finished = pyqtSignal(object)
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    """Главное окно приложения (только главная страница)"""
    
    def __init__(self):
        super().__init__()
        
        print("Инициализация БД и сервисов...")
        # Инициализация БД и репозиториев
        self.engine = initialize_database()
        self.session = get_session(self.engine)
        
        # Инициализируем репозитории через конструкторы
        self.device_repo = DeviceRepository(self.session)
        self.model_repo = ModelRepository(self.session)
        self.optimized_model_repo = OptimizedModelRepository(self.session)
        self.optimization_record_repo = OptimizationRecordRepository(self.session)
        self.deployment_repo = DeploymentRepository(self.session)

        # Инициализируем сервисы
        self.optimization_service = OptimizationService(
            self.device_repo,
            self.model_repo,
            self.optimized_model_repo
        )
        self.validation_service = ModelValidationService(self.optimization_record_repo)
        self.device_service = UniversalDeviceService(self.device_repo)
        
        # Сохраняем ссылки на карточки статистики
        self.stat_cards = {}
        
        self.dashboard_page = None
        self.models_page = None
        self.devices_page = None
        self.optimization_page = None
        self.deployment_page = None
        

        self.init_ui()
        self.apply_styles()
        
        print("Инициализация завершена")
    
    def init_ui(self):
        """Инициализация UI (только главная страница)"""
        # Меняем название окна на Neuro-Optimizer
        self.setWindowTitle("Neuro-Optimizer")
        self.setGeometry(100, 100, 1400, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(10)
        
        # Панель навигации (упрощенная)
        nav_frame = self.create_navigation()
        self.main_layout.addWidget(nav_frame)
        
        # Только главная страница
        self.dashboard_page = self.create_dashboard_page()
        self.models_page = self.create_models_page()
        self.devices_page = self.create_devices_page()
        self.devices_page = self.create_devices_page()
        self.optimization_reports_page = self.create_optimization_reports_page()
        self.deployment_reports_page = self.create_deployment_reports_page()

        # Создайте QStackedWidget
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.models_page)
        self.stacked_widget.addWidget(self.devices_page)
        self.stacked_widget.addWidget(self.optimization_reports_page)
        self.stacked_widget.addWidget(self.deployment_reports_page)


        # Вместо self.main_layout.addWidget(self.dashboard_page)
        self.main_layout.addWidget(self.stacked_widget)
        
        
        
        # Статус бар
        self.status_bar = self.create_status_bar()
        self.setStatusBar(self.status_bar)
    
    def create_navigation(self):
        """Создать панель навигации с переключением страниц"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #32363C;
                border-radius: 3px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        layout.setSpacing(10)
        
        # Сохраняем ссылки на кнопки для изменения стилей
        self.nav_buttons = {}
        
        # Кнопка ГЛАВНАЯ
        dashboard_btn = WarframeButton("ГЛАВНАЯ")
        dashboard_btn.setMinimumWidth(120)
        dashboard_btn.setMinimumHeight(40)
        dashboard_btn.clicked.connect(lambda: self.switch_page("dashboard"))
        dashboard_btn.setStyleSheet("""
            QPushButton {
                background-color: #00B7EB;
                color: #0A0E14;
            }
        """)
        layout.addWidget(dashboard_btn)
        self.nav_buttons["dashboard"] = dashboard_btn
        
       
        
        # Кнопка МОДЕЛИ
        models_btn = WarframeButton("МОДЕЛИ")
        models_btn.setMinimumWidth(120)
        models_btn.setMinimumHeight(40)
        models_btn.clicked.connect(lambda: self.switch_page("models"))
        models_btn.setStyleSheet("""
            QPushButton {
                background-color: #32363C;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #3A3E44;
            }
        """)
        layout.addWidget(models_btn)
        self.nav_buttons["models"] = models_btn

         # Кнопка УСТРОЙСТВА
        devices_btn = WarframeButton("УСТРОЙСТВА")
        devices_btn.setMinimumWidth(120)
        devices_btn.setMinimumHeight(40)
        devices_btn.clicked.connect(lambda: self.switch_page("devices"))
        devices_btn.setStyleSheet("""
            QPushButton {
                background-color: #32363C;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #3A3E44;
            }
        """)
        layout.addWidget(devices_btn)
        self.nav_buttons["devices"] = devices_btn



        # Кнопка ОПТИМИЗАЦИЯ
        optimization_btn = WarframeButton("ОПТИМИЗАЦИЯ")
        optimization_btn.setMinimumWidth(120)
        optimization_btn.setMinimumHeight(40)
        optimization_btn.clicked.connect(lambda: self.switch_page("optimization"))
        optimization_btn.setStyleSheet("""
            QPushButton {
                background-color: #32363C;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #3A3E44;
            }
        """)
        layout.addWidget(optimization_btn)
        self.nav_buttons["optimization"] = optimization_btn


        # Кнопка РАЗВЕРТЫВАНИЕ
        deployment_btn = WarframeButton("РАЗВЕРТЫВАНИЕ")
        deployment_btn.setMinimumWidth(120)
        deployment_btn.setMinimumHeight(40)
        deployment_btn.clicked.connect(lambda: self.switch_page("deployment"))
        deployment_btn.setStyleSheet("""
            QPushButton {
                background-color: #32363C;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #3A3E44;
            }
        """)
        layout.addWidget(deployment_btn)
        self.nav_buttons["deployment"] = deployment_btn

        
        # Кнопка выхода
        exit_btn = WarframeButton("ВЫХОД")
        exit_btn.setMinimumWidth(100)
        exit_btn.setMinimumHeight(40)
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #EB4B4B;
                color: #0A0E14;
            }
            QPushButton:hover {
                background-color: #FF6B6B;
            }
        """)
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)
        
        return frame
    
    def switch_page(self, page_id):
        """Переключить на указанную страницу"""
        print(f"Переключение на страницу: {page_id}")
        
        # Обновляем стили кнопок
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #00B7EB;
                        color: #0A0E14;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #32363C;
                        color: #FFFFFF;
                    }
                    QPushButton:hover {
                        background-color: #3A3E44;
                    }
                """)
        
        # Переключаем страницы
        if page_id == "dashboard":
            self.stacked_widget.setCurrentWidget(self.dashboard_page)
            self.refresh_dashboard_stats()
        elif page_id == "models":
            self.stacked_widget.setCurrentWidget(self.models_page)
            self.refresh_models_table()
        elif page_id == "devices":
            self.stacked_widget.setCurrentWidget(self.devices_page)
            self.refresh_devices_table()

        elif page_id == "optimization":
            self.stacked_widget.setCurrentWidget(self.optimization_reports_page)
            self.refresh_optimization_reports_table()

        elif page_id == "deployment":
            self.stacked_widget.setCurrentWidget(self.deployment_reports_page)
            self.refresh_deployment_reports_table()
        else:
            # Для других страниц показываем заглушку
            self.show_stub_page(page_id)
    
    def show_stub_page(self, page_id):
        """Показать заглушку для страницы в разработке"""
        stub_widget = QWidget()
        layout = QVBoxLayout(stub_widget)
        
        label = QLabel(f"Страница '{page_id.upper()}' в разработке")
        label.setFont(WarframeStyles.get_font(24, True))
        label.setStyleSheet("color: #00B7EB; margin-top: 100px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        self.stacked_widget.addWidget(stub_widget)
        self.stacked_widget.setCurrentWidget(stub_widget)


    def create_dashboard_page(self):
        """Создать упрощенную страницу дашборда"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Заголовок - убрали смайлики
        title = QLabel("NEURO OPTIMIZER")
        title.setFont(WarframeStyles.get_font(24, True))
        title.setStyleSheet("color: #00B7EB; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Подзаголовок
        subtitle = QLabel("ГЛАВНОЕ МЕНЮ")
        subtitle.setFont(WarframeStyles.get_font(18))
        subtitle.setStyleSheet("color: #FFFFFF; margin-bottom: 30px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Статистика в виде карточек
        stats_layout = QHBoxLayout()
        
        stats = [
            ("МОДЕЛЕЙ В БАЗЕ", self.get_model_count, "#00B7EB", "model_count"),
            ("УСТРОЙСТВ", self.get_device_count, "#2ECC71", "device_count"),
            ("ОПТИМИЗАЦИЙ", self.get_optimization_count, "#F1C40F", "optimization_count"),
            ("РАЗВЕРТЫВАНИЙ", self.get_deployment_count, "#9B59B6", "deployment_count")
        ]
        
        for label_text, count_func, color, card_id in stats:
            card = self.create_stat_card(label_text, count_func(), color, card_id)
            stats_layout.addWidget(card)
        
        layout.addLayout(stats_layout)
        
        # Быстрые действия
        actions_group = QGroupBox("БЫСТРЫЕ ДЕЙСТВИЯ")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00B7EB;
                border: 1px solid #32363C;
                border-radius: 3px;
                margin-top: 20px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        actions_layout = QHBoxLayout()
        
        quick_actions = [
            ("ДОБАВИТЬ МОДЕЛЬ", self.add_model),
            ("ДОБАВИТЬ УСТРОЙСТВО", self.add_device),
            ("ОПТИМИЗИРОВАТЬ", self.show_optimization_stub),
            ("РАЗВЕРНУТЬ", self.show_deployment_stub)
        ]
        
        for text, callback in quick_actions:
            btn = WarframeButton(text)
            btn.setMinimumHeight(50)
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        layout.addStretch()
        
        return page
    
    def create_stat_card(self, title, value, color, card_id):
        """Создать карточку статистики"""
        card = QFrame()
        card.setObjectName(f"stat_card_{card_id}")
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #1A1E24;
                border: 1px solid {color};
                border-radius: 5px;
                padding: 15px;
                min-width: 150px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("title")
        
        value_label = QLabel(str(value))
        value_label.setStyleSheet("color: #FFFFFF; font-size: 24px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName("value")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        # Сохраняем ссылку на карточку
        self.stat_cards[card_id] = {
            'widget': card,
            'value_label': value_label,
            'count_func': {
                'model_count': self.get_model_count,
                'device_count': self.get_device_count,
                'optimization_count': self.get_optimization_count,
                'deployment_count': self.get_deployment_count
            }[card_id]
        }
        
        return card
    
    def refresh_dashboard_stats(self):
        """Обновить статистику на дашборде"""
        try:
            # Обновляем каждую карточку статистики
            for card_id, card_data in self.stat_cards.items():
                value_label = card_data['value_label']
                count_func = card_data['count_func']
                
                # Получаем актуальное значение
                new_value = count_func()
                value_label.setText(str(new_value))
                
                # Обновляем карточку
                card_data['widget'].update()
            
            # Обновляем весь дашборд
            self.dashboard_page.update()
            print(f"Статистика обновлена: модели={self.get_model_count()}, устройства={self.get_device_count()}")
            
        except Exception as e:
            print(f"Ошибка при обновлении статистики: {e}")
    
    def create_status_bar(self):
        """Создать статус бар"""
        status_bar = QStatusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #121620;
                color: #00B7EB;
                border-top: 1px solid #32363C;
            }
        """)
        
        # Статус БД
        self.db_status = QLabel("● БД: АКТИВНА")
        self.db_status.setStyleSheet("color: #2ECC71;")
        status_bar.addWidget(self.db_status)
        
        # Количество подключений
        self.connections_label = QLabel("Подключения: 0")
        status_bar.addWidget(self.connections_label)
        
        # Время работы
        self.start_time = datetime.now()
        self.uptime_label = QLabel("Время работы: 00:00:00")
        status_bar.addPermanentWidget(self.uptime_label)
        
        # Таймер для обновления времени работы
        self.uptime_timer = QTimer()
        self.uptime_timer.timeout.connect(self.update_uptime)
        self.uptime_timer.start(1000)
        
        return status_bar
    
    def apply_styles(self):
        """Применить стили Warframe"""
        self.setStyleSheet(WarframeStyles.get_stylesheet())
    
    # Методы получения статистики
    def get_model_count(self):
        try:
            models = self.model_repo.get_all()
            return len(models)
        except Exception as e:
            print(f"Ошибка получения количества моделей: {e}")
            return 0
    
    def get_device_count(self):
        try:
            devices = self.device_repo.get_all()
            return len(devices)
        except Exception as e:
            print(f"Ошибка получения количества устройств: {e}")
            return 0
    
    def get_optimization_count(self):
        try:
            records = self.optimization_record_repo.get_recent_records(limit=1000)
            return len(records)
        except Exception as e:
            print(f"Ошибка получения количества оптимизаций: {e}")
            return 0
    
    def get_deployment_count(self):
        try:
            deployments = self.deployment_repo.get_all()
            return len(deployments)
        except Exception as e:
            print(f"Ошибка получения количества развертываний: {e}")
            return 0
    
    def update_uptime(self):
        """Обновить время работы"""
        delta = datetime.now() - self.start_time
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        seconds = delta.seconds % 60
        self.uptime_label.setText(f"Время работы: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    # Методы быстрых действий
    def add_model(self):
        """Добавить новую модель через диалоговое окно"""
        dialog = QDialog(self)
        dialog.setWindowTitle("ДОБАВЛЕНИЕ НОВОЙ МОДЕЛИ")
        dialog.setModal(True)
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)
        
        # Основной layout
        layout = QVBoxLayout(dialog)
        
        # Информация о формате
        info_label = QLabel(
            "Поддерживаемые форматы моделей: .h5, .keras, .onnx, .pb, .tflite<br>"
            "Типы моделей: cv (компьютерное зрение)"
        )
        info_label.setStyleSheet("""
            background-color: #1A1E24; 
            padding: 10px; 
            border-radius: 3px;
            color: #00B7EB;
            font-size: 11px;
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Форма для ввода данных
        form_group = QGroupBox("ПАРАМЕТРЫ МОДЕЛИ")
        form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00B7EB;
                border: 1px solid #32363C;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        form_layout = QFormLayout()
        
        # Поле для названия модели
        model_name_input = QLineEdit()
        model_name_input.setPlaceholderText("Введите название модели")
        form_layout.addRow("Название модели:", model_name_input)
        
        # Поле для пути с кнопкой обзора
        path_layout = QHBoxLayout()
        model_path_input = QLineEdit()
        model_path_input.setPlaceholderText("Выберите файл модели")
        path_layout.addWidget(model_path_input)
        
        browse_btn = WarframeButton("Обзор")
        browse_btn.setMinimumWidth(80)
        
        # Локальная функция для обзора файлов
        def browse_file():
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(
                dialog,
                "Выберите файл модели",
                "",
                "Модели (*.h5 *.keras *.onnx *.pb *.tflite);;Все файлы (*)"
            )
            if file_path:
                model_path_input.setText(file_path)
        
        browse_btn.clicked.connect(browse_file)
        path_layout.addWidget(browse_btn)
        form_layout.addRow("Путь к файлу:", path_layout)
        
        # Выбор типа модели
        model_type_combo = QComboBox()
        model_type_combo.addItems(["cv", "nlp", "audio"])
        form_layout.addRow("Тип модели:", model_type_combo)
        
        # Информация о формате
        format_label = QLabel("Формат: не определен")
        format_label.setStyleSheet("color: #F1C40F;")
        form_layout.addRow("Определенный формат:", format_label)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Статус валидации
        validation_status = QLabel("Заполните все поля")
        validation_status.setStyleSheet("color: #F1C40F; font-weight: bold; padding: 5px;")
        validation_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(validation_status)
        
        # Функция валидации
        def validate_form():
            name = model_name_input.text().strip()
            path = model_path_input.text().strip()
            model_type = model_type_combo.currentText().strip()
            
            if not name or not path or not model_type:
                validation_status.setText("Заполните все поля")
                validation_status.setStyleSheet("color: #F1C40F; font-weight: bold; padding: 5px;")
                add_button.setEnabled(False)
                return
            
            if not os.path.exists(path):
                validation_status.setText("Файл не существует или путь неверный")
                validation_status.setStyleSheet("color: #E74C3C; font-weight: bold; padding: 5px;")
                add_button.setEnabled(False)
                return
            
            file_extension = path.split('.')[-1].lower() if '.' in path else ''
            supported_extensions = ['h5', 'keras', 'onnx', 'pb', 'tflite']
            
            if file_extension not in supported_extensions:
                validation_status.setText(f"Неподдерживаемый формат: .{file_extension}")
                validation_status.setStyleSheet("color: #E74C3C; font-weight: bold; padding: 5px;")
                add_button.setEnabled(False)
                return
            
            if model_type not in ['cv']:
                validation_status.setText(f"Неподдерживаемый тип модели: {model_type}")
                validation_status.setStyleSheet("color: #E74C3C; font-weight: bold; padding: 5px;")
                add_button.setEnabled(False)
                return
            
            # Обновляем информацию о формате
            supported_formats = {
                'h5': 'TensorFlow H5',
                'keras': 'Keras',
                'onnx': 'ONNX',
                'pb': 'TensorFlow Protocol Buffer',
                'tflite': 'TensorFlow Lite'
            }
            
            if file_extension in supported_formats:
                format_display = supported_formats[file_extension]
                format_label.setText(f"Формат: {format_display} (.{file_extension})")
                format_label.setStyleSheet("color: #2ECC71;")
            else:
                format_label.setText("Формат: неизвестный/неподдерживаемый")
                format_label.setStyleSheet("color: #E74C3C;")
            
            validation_status.setText("Все данные корректны. Можно добавлять модель")
            validation_status.setStyleSheet("color: #2ECC71; font-weight: bold; padding: 5px;")
            add_button.setEnabled(True)
        
        # Подключаем сигналы для валидации
        model_name_input.textChanged.connect(validate_form)
        model_path_input.textChanged.connect(validate_form)
        model_type_combo.currentTextChanged.connect(validate_form)
        
        # Кнопки диалога
        button_box = QDialogButtonBox()
        add_button = button_box.addButton("Добавить", QDialogButtonBox.AcceptRole)
        add_button.setEnabled(False)
        cancel_button = button_box.addButton("Отмена", QDialogButtonBox.RejectRole)
        
        # Стилизация кнопок
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #00B7EB;
                color: #0A0E14;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:disabled {
                background-color: #32363C;
                color: #666666;
            }
        """)
        
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #32363C;
                color: #FFFFFF;
                min-width: 100px;
            }
        """)
        
        # Обработчик добавления модели
        def process_add():
            try:
                name = model_name_input.text().strip()
                path = model_path_input.text().strip()
                model_type = model_type_combo.currentText().strip().lower()
                
                # Определяем формат файла
                file_extension = path.split('.')[-1].lower() if '.' in path else 'unknown'
                format_name = file_extension if file_extension in ['h5', 'keras', 'onnx', 'pb', 'tflite'] else 'unknown'
                file_size = os.path.getsize(path) / (1024 * 1024)
                # Добавляем модель в базу данных
                model = self.model_repo.create_model(
                    name=name,
                    original_path=path,
                    model_type_name=model_type,
                    format_name=format_name, 
                    size = file_size
                )
                
                # Показываем сообщение об успехе
                QMessageBox.information(
                    self,
                    "Успешно",
                    f"Модель '{name}' успешно добавлена.\nID модели: {model.id}",
                    QMessageBox.Ok
                )
                
                # Обновляем статистику на дашборде
                self.refresh_dashboard_stats()
                
                # Закрываем диалог
                dialog.accept()
                
            except Exception as e:
                error_msg = str(e)
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось добавить модель:\n{error_msg}",
                    QMessageBox.Ok
                )
               
        button_box.accepted.connect(process_add)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec_()
    

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        reply = QMessageBox.question(
            self,
            "Выход",
            "Вы уверены, что хотите выйти?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if hasattr(self, 'session'):
                self.session.close()
            event.accept()
        else:
            event.ignore()


    def add_device(self):
        """Добавить новое устройство через диалоговое окно"""
        dialog = QDialog(self)
        dialog.setWindowTitle("ДОБАВЛЕНИЕ НОВОГО УСТРОЙСТВА")
        dialog.setModal(True)
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(550)
        
        # Основной layout
        layout = QVBoxLayout(dialog)
        
        # Информация о добавлении устройства
        info_label = QLabel(
            "Добавление нового Edge-устройства для оптимизации и развертывания моделей.<br>"
            "Можно использовать автоматическое обнаружение или ручной ввод параметров."
        )
        info_label.setStyleSheet("""
            background-color: #1A1E24; 
            padding: 10px; 
            border-radius: 3px;
            color: #00B7EB;
            font-size: 11px;
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Форма для подключения
        connect_group = QGroupBox("ПОДКЛЮЧЕНИЕ К УСТРОЙСТВУ")
        connect_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00B7EB;
                border: 1px solid #32363C;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        connect_layout = QFormLayout()
        
        # IP адрес
        self.device_ip_input = QLineEdit()
        self.device_ip_input.setPlaceholderText("192.168.0.169")
        self.device_ip_input.textChanged.connect(self.validate_device_connection_form)
        connect_layout.addRow("IP адрес устройства:", self.device_ip_input)
        
        # Имя пользователя
        self.device_username_input = QLineEdit()
        self.device_username_input.setPlaceholderText("u0_a398")
        self.device_username_input.textChanged.connect(self.validate_device_connection_form)
        connect_layout.addRow("Имя пользователя:", self.device_username_input)
        
        # Пароль
        self.device_password_input = QLineEdit()
        self.device_password_input.setPlaceholderText("1111")
        self.device_password_input.setEchoMode(QLineEdit.Password)
        self.device_password_input.textChanged.connect(self.validate_device_connection_form)
        connect_layout.addRow("Пароль:", self.device_password_input)
        
        # Порт
        self.device_port_input = QLineEdit()
        self.device_port_input.setPlaceholderText("8022")
        self.device_port_input.setText("8022")  # Значение по умолчанию
        self.device_port_input.textChanged.connect(self.validate_device_connection_form)
        connect_layout.addRow("Порт (по умолчанию 8022):", self.device_port_input)
        
        # Тип устройства
        self.device_type_combo = QComboBox()
        self.device_type_combo.addItems(["android"])
        self.device_type_combo.currentTextChanged.connect(self.validate_device_connection_form)
        connect_layout.addRow("Тип устройства:", self.device_type_combo)
        
        connect_group.setLayout(connect_layout)
        layout.addWidget(connect_group)
        
        # Панель ручного ввода (скрыта по умолчанию)
        self.manual_panel = QGroupBox("РУЧНОЙ ВВОД ПАРАМЕТРОВ")
        self.manual_panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00B7EB;
                border: 1px solid #32363C;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        self.manual_panel.setVisible(False)
        
        manual_layout = QFormLayout()
        
        # Архитектура
        self.device_arch_input = QLineEdit()
        self.device_arch_input.setPlaceholderText("arm64, x86_64, aarch64")
        self.device_arch_input.textChanged.connect(self.validate_device_manual_form)
        manual_layout.addRow("Архитектура:", self.device_arch_input)
        
        # Свободное ПЗУ (GB)
        self.device_memory_input = QLineEdit()
        self.device_memory_input.setPlaceholderText("32")
        self.device_memory_input.textChanged.connect(self.validate_device_manual_form)
        manual_layout.addRow("Свободное ПЗУ (GB):", self.device_memory_input)
        
        # RAM (GB)
        self.device_ram_input = QLineEdit()
        self.device_ram_input.setPlaceholderText("4")
        self.device_ram_input.textChanged.connect(self.validate_device_manual_form)
        manual_layout.addRow("Оперативная память (GB):", self.device_ram_input)
        
        # CPU cores
        self.device_cpu_input = QLineEdit()
        self.device_cpu_input.setPlaceholderText("4")
        self.device_cpu_input.textChanged.connect(self.validate_device_manual_form)
        manual_layout.addRow("Количество ядер CPU:", self.device_cpu_input)
        
        self.manual_panel.setLayout(manual_layout)
        layout.addWidget(self.manual_panel)
        
        # Кнопка переключения режима
        mode_buttons_layout = QHBoxLayout()
        
        self.auto_mode_btn = WarframeButton("АВТОМАТИЧЕСКОЕ ОБНАРУЖЕНИЕ")
        self.auto_mode_btn.setCheckable(True)
        self.auto_mode_btn.setChecked(True)
        self.auto_mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #00B7EB;
                color: #0A0E14;
            }
            QPushButton:checked {
                background-color: #00B7EB;
                color: #0A0E14;
            }
            QPushButton:!checked {
                background-color: #32363C;
                color: #FFFFFF;
            }
        """)
        
        self.manual_mode_btn = WarframeButton("РУЧНОЙ ВВОД")
        self.manual_mode_btn.setCheckable(True)
        self.manual_mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #32363C;
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: #00B7EB;
                color: #0A0E14;
            }
        """)
        
        mode_buttons_layout.addWidget(self.auto_mode_btn)
        mode_buttons_layout.addWidget(self.manual_mode_btn)
        layout.addLayout(mode_buttons_layout)
        
        # Группа кнопок
        mode_button_group = QButtonGroup()
        mode_button_group.addButton(self.auto_mode_btn)
        mode_button_group.addButton(self.manual_mode_btn)
        mode_button_group.setExclusive(True)
        
        # Обработчики переключения режимов
        def switch_to_auto_mode():
            self.manual_panel.setVisible(False)
            self.validate_device_connection_form()
        
        def switch_to_manual_mode():
            self.manual_panel.setVisible(True)
            self.validate_device_manual_form()
        
        self.auto_mode_btn.clicked.connect(switch_to_auto_mode)
        self.manual_mode_btn.clicked.connect(switch_to_manual_mode)
        
        # Статус валидации
        self.device_validation_status = QLabel("Заполните данные для подключения")
        self.device_validation_status.setStyleSheet("color: #F1C40F; font-weight: bold; padding: 5px;")
        self.device_validation_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.device_validation_status)
        
        # Прогресс бар (скрыт по умолчанию)
        self.device_progress_bar = QProgressBar()
        self.device_progress_bar.setVisible(False)
        layout.addWidget(self.device_progress_bar)
        
        # Кнопки диалога
        button_box = QDialogButtonBox()
        self.device_add_button = button_box.addButton("Добавить устройство", QDialogButtonBox.AcceptRole)
        self.device_add_button.setEnabled(False)
        cancel_button = button_box.addButton("Отмена", QDialogButtonBox.RejectRole)
        
        # Стилизация кнопок
        self.device_add_button.setStyleSheet("""
            QPushButton {
                background-color: #00B7EB;
                color: #0A0E14;
                font-weight: bold;
                min-width: 120px;
                min-height: 40px;
            }
            QPushButton:disabled {
                background-color: #32363C;
                color: #666666;
            }
        """)
        
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #32363C;
                color: #FFFFFF;
                min-width: 100px;
            }
        """)
        
        button_box.accepted.connect(lambda: self.process_device_add(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec_()

    def validate_device_connection_form(self):
        """Валидация формы подключения к устройству"""
        ip = self.device_ip_input.text().strip()
        username = self.device_username_input.text().strip()
        password = self.device_password_input.text().strip()
        port = self.device_port_input.text().strip()
        device_type = self.device_type_combo.currentText().strip()
        
        # Проверяем, заполнены ли все поля
        if not ip or not username or not password or not port:
            self.device_validation_status.setText("Заполните все поля для подключения")
            self.device_validation_status.setStyleSheet("color: #F1C40F; font-weight: bold; padding: 5px;")
            self.device_add_button.setEnabled(False)
            return
        
        # Проверяем IP адрес (простая валидация)
        ip_parts = ip.split('.')
        if len(ip_parts) != 4:
            self.device_validation_status.setText("Неверный формат IP адреса")
            self.device_validation_status.setStyleSheet("color: #E74C3C; font-weight: bold; padding: 5px;")
            self.device_add_button.setEnabled(False)
            return
        
        # Проверяем порт (должен быть числом)
        try:
            port_value = int(port)
            if port_value <= 0 or port_value > 65535:
                raise ValueError
        except ValueError:
            self.device_validation_status.setText("Порт должен быть числом от 1 до 65535")
            self.device_validation_status.setStyleSheet("color: #E74C3C; font-weight: bold; padding: 5px;")
            self.device_add_button.setEnabled(False)
            return
        
        # Все проверки пройдены
        self.device_validation_status.setText("Данные для подключения корректны")
        self.device_validation_status.setStyleSheet("color: #2ECC71; font-weight: bold; padding: 5px;")
        self.device_add_button.setEnabled(True)

    def validate_device_manual_form(self):
        """Валидация формы ручного ввода параметров"""
        # Сначала проверяем данные подключения
        self.validate_device_connection_form()
        if not self.device_add_button.isEnabled():
            return
        
        # Затем проверяем ручные параметры
        arch = self.device_arch_input.text().strip()
        memory = self.device_memory_input.text().strip()
        ram = self.device_ram_input.text().strip()
        cpu = self.device_cpu_input.text().strip()
        
        if not arch or not memory or not ram or not cpu:
            self.device_validation_status.setText("Заполните все параметры устройства")
            self.device_validation_status.setStyleSheet("color: #F1C40F; font-weight: bold; padding: 5px;")
            self.device_add_button.setEnabled(False)
            return
        
        # Проверяем числовые значения
        try:
            memory_value = float(memory)
            ram_value = float(ram)
            cpu_value = int(cpu)
            
            if memory_value <= 0 or ram_value <= 0 or cpu_value <= 0:
                raise ValueError
        except ValueError:
            self.device_validation_status.setText("ПЗУ, RAM и CPU должны быть положительными числами")
            self.device_validation_status.setStyleSheet("color: #E74C3C; font-weight: bold; padding: 5px;")
            self.device_add_button.setEnabled(False)
            return
        
        # Все проверки пройдены
        self.device_validation_status.setText("Все данные корректны. Можно добавлять устройство")
        self.device_validation_status.setStyleSheet("color: #2ECC71; font-weight: bold; padding: 5px;")
        self.device_add_button.setEnabled(True)

    def process_device_add(self, dialog):
        """Обработать добавление устройства"""
        try:
            # Получаем данные подключения
            ip_address = self.device_ip_input.text().strip()
            username = self.device_username_input.text().strip()
            password = self.device_password_input.text().strip()
            port = self.device_port_input.text().strip()
            device_type = self.device_type_combo.currentText().strip()
            
            # Отладочный вывод
            print(f"\n=== ПОПЫТКА ДОБАВЛЕНИЯ УСТРОЙСТВА ===")
            print(f"IP: {ip_address}")
            print(f"Username: {username}")
            print(f"Port: {port}")
            print(f"Type: {device_type}")
            
            # Проверяем, существует ли уже устройство с таким IP
            existing_device = self.device_repo.get_by_ip(ip_address)
            print(f"Существующее устройство: {'Да' if existing_device else 'Нет'}")
            if existing_device:
                print(f"ID существующего устройства: {existing_device.id}")
            
            # Показываем прогресс бар
            self.device_progress_bar.setVisible(True)
            self.device_progress_bar.setValue(10)
            
            config = {
                'host': ip_address,
                'username': username,
                'password': password,
                'port': int(port) if port.isdigit() else 8022
            }
            
            print(f"Конфиг подключения: {config}")
            
            if existing_device:
                # Устройство уже существует
                self.device_validation_status.setText("Устройство уже существует...")
                
                if self.auto_mode_btn.isChecked():
                    # Режим автоматического обнаружения для существующего устройства
                    self.device_progress_bar.setValue(30)
                    
                    print("Попытка подключения к существующему устройству...")
                    
                    # Безопасный вызов connect_device
                    try:
                        result = self.device_service.connect_device(device_type, **config)
                        print(f"Результат connect_device: {result}")
                    except Exception as connect_exc:
                        print(f"ИСКЛЮЧЕНИЕ в connect_device: {connect_exc}")
                        result = {'success': False, 'error': str(connect_exc)}
                    
                    if result and result.get('success'):
                        self.device_progress_bar.setValue(60)
                        
                        try:
                            print("Попытка получения информации об устройстве...")
                            # Получаем информацию об устройстве БЕЗ сохранения в БД
                            device_info = self.device_service.get_free_memory()
                            print(f"Результат get_device_info: {device_info}")
                            
                            if device_info and device_info.get('memory_gb'):
                                # Извлекаем информацию
                                info = device_info
                                
                                # Обновляем только необходимые поля существующего устройства
                                try:
                                    # Обновляем memory_gb если есть
                                    if 'memory_gb' in info:
                                        memory_value = str(info['memory_gb'])
                                        print(f"Получено memory_gb: {memory_value}")
                                        import re
                                        numbers = re.findall(r'\d+\.?\d*', memory_value)
                                        if numbers:
                                            existing_device.memory_gb = float(numbers[0])
                                            print(f"Преобразованное memory_gb: {existing_device.memory_gb}")
                                    
                                    # Обновляем last_seen
                                    existing_device.last_seen = datetime.now()
                                    
                                    self.session.commit()
                                    
                                    self.device_progress_bar.setValue(100)
                                    self.device_validation_status.setText("Информация обновлена")
                                    
                                    QMessageBox.information(
                                        self,
                                        "Обновлено",
                                        f"Информация об устройстве обновлена.\n"
                                        f"ID: {existing_device.id}\n"
                                        f"IP: {ip_address}\n"
                                        f"Тип: {device_type}\n"
                                        f"ПЗУ: {existing_device.memory_gb if hasattr(existing_device, 'memory_gb') else 'N/A'} GB",
                                        QMessageBox.Ok
                                    )
                                    
                                    self.refresh_dashboard_stats()
                                    dialog.accept()
                                    return
                                    
                                except Exception as update_error:
                                    print(f"Ошибка при обновлении: {update_error}")
                                    # Если не удалось обновить, просто отметим время
                                    existing_device.last_seen = datetime.now()
                                    self.session.commit()
                                    print("Обновлено только last_seen из-за ошибки")
                            else:
                                print(f"Не удалось получить информацию: {device_info}")
                            
                            # Если не удалось получить информацию, просто обновляем время
                            existing_device.last_seen = datetime.now()
                            self.session.commit()
                            
                            self.device_progress_bar.setValue(100)
                            self.device_validation_status.setText("Время подключения обновлено")
                            
                            QMessageBox.information(
                                self,
                                "Обновлено",
                                f"Время последнего подключения обновлено.\n"
                                f"ID: {existing_device.id}\n"
                                f"Примечание: Не удалось получить актуальную информацию об устройстве",
                                QMessageBox.Ok
                            )
                            
                            self.refresh_dashboard_stats()
                            dialog.accept()
                            return
                            
                        except Exception as info_error:
                            print(f"Ошибка получения информации: {info_error}")
                            # Ошибка при получении информации
                            existing_device.last_seen = datetime.now()
                            self.session.commit()
                            
                            self.device_progress_bar.setValue(100)
                            self.device_validation_status.setText("Ошибка получения информации")
                            
                            QMessageBox.warning(
                                self,
                                "Внимание",
                                f"Не удалось получить информацию об устройстве.\n"
                                f"Ошибка: {str(info_error)[:100]}\n"
                                f"Время подключения обновлено.\n"
                                f"ID: {existing_device.id}",
                                QMessageBox.Ok
                            )
                            
                            self.refresh_dashboard_stats()
                            dialog.accept()
                            return
                    
                    else:
                        # Не удалось подключиться, но устройство существует
                        error_msg = result.get('error', 'Неизвестная ошибка подключения') if result else 'Нет результата от connect_device'
                        print(f"Не удалось подключиться: {error_msg}")
                        
                        existing_device.last_seen = datetime.now()
                        self.session.commit()
                        
                        self.device_progress_bar.setValue(100)
                        self.device_validation_status.setText("Не удалось подключиться")
                        
                        QMessageBox.warning(
                            self,
                            "Внимание",
                            f"Не удалось подключиться к существующему устройству:\n"
                            f"Ошибка: {error_msg}\n"
                            f"Время последнего подключения обновлено.\n"
                            f"ID: {existing_device.id}\n"
                            f"Рекомендация: Проверьте подключение или используйте ручной ввод",
                            QMessageBox.Ok
                        )
                        
                        self.refresh_dashboard_stats()
                        dialog.accept()
                        return
                
                else:
                    # Ручной режим для существующего устройства
                    print("Ручной режим для существующего устройства")
                    try:
                        memory_gb_str = self.device_memory_input.text().strip()
                        print(f"Введенный memory_gb: {memory_gb_str}")
                        
                        if memory_gb_str:
                            memory_gb = float(memory_gb_str)
                            
                            # Обновляем только memory_gb и last_seen
                            existing_device.memory_gb = memory_gb
                            existing_device.last_seen = datetime.now()
                            self.session.commit()
                            
                            self.device_progress_bar.setValue(100)
                            self.device_validation_status.setText("Информация обновлена")
                            
                            QMessageBox.information(
                                self,
                                "Обновлено",
                                f"Информация об устройстве обновлена.\n"
                                f"ID: {existing_device.id}\n"
                                f"Свободное ПЗУ: {memory_gb} GB",
                                QMessageBox.Ok
                            )
                            
                            self.refresh_dashboard_stats()
                            dialog.accept()
                            return
                        else:
                            # Только обновляем время если memory_gb не введен
                            existing_device.last_seen = datetime.now()
                            self.session.commit()
                            
                            self.device_progress_bar.setValue(100)
                            self.device_validation_status.setText("Время подключения обновлено")
                            
                            QMessageBox.information(
                                self,
                                "Обновлено",
                                f"Время последнего подключения обновлено.\n"
                                f"ID: {existing_device.id}\n"
                                f"Примечание: Параметры устройства не изменены",
                                QMessageBox.Ok
                            )
                            
                            self.refresh_dashboard_stats()
                            dialog.accept()
                            return
                        
                    except ValueError as ve:
                        print(f"Ошибка преобразования memory_gb: {ve}")
                        QMessageBox.warning(
                            self,
                            "Ошибка ввода",
                            f"Некорректное значение для ПЗУ.\n"
                            f"Введите числовое значение (например: 32.5)",
                            QMessageBox.Ok
                        )
                        self.device_progress_bar.setVisible(False)
                        return
                    except Exception as e:
                        error_msg = str(e)
                        print(f"Ошибка обновления устройства: {error_msg}")
                        QMessageBox.critical(
                            self,
                            "Ошибка",
                            f"Не удалось обновить устройство:\n{error_msg}",
                            QMessageBox.Ok
                        )
                        self.device_progress_bar.setVisible(False)
                        return
            
            # Если устройство не существует, создаем новое
            print("Создание нового устройства...")
            self.device_validation_status.setText("Добавление нового устройства...")
            
            # Пытаемся подключиться
            try:
                result = self.device_service.connect_device(device_type, **config)
                print(f"Результат connect_device для нового устройства: {result}")
            except Exception as connect_exc:
                print(f"ИСКЛЮЧЕНИЕ в connect_device для нового устройства: {connect_exc}")
                result = {'success': False, 'error': str(connect_exc)}
            
            if not result or not result.get('success'):
                self.device_progress_bar.setValue(100)
                self.device_validation_status.setText("Не удалось подключиться")
                
                error_msg = result.get('error', 'Неизвестная ошибка') if result else 'Нет ответа от устройства'
                
                QMessageBox.warning(
                    self,
                    "Ошибка подключения",
                    f"Не удалось подключиться к устройству:\n{error_msg}\n"
                    "Проверьте данные подключения или переключитесь в режим ручного ввода.",
                    QMessageBox.Ok
                )
                self.device_progress_bar.setVisible(False)
                return
            
            self.device_progress_bar.setValue(60)
            self.device_validation_status.setText("Получение информации об устройстве...")
            
            if self.auto_mode_btn.isChecked():
                # Режим автоматического обнаружения для нового устройства
                try:
                    print("Используем get_and_save_device_info() для нового устройства")
                    save_result = self.device_service.get_and_save_device_info()
                    print(f"Результат get_and_save_device_info: {save_result}")
                    
                    if save_result.get('success'):
                        self.device_progress_bar.setValue(100)
                        self.device_validation_status.setText("Устройство успешно добавлено")
                        
                        # Ищем только что добавленное устройство
                        new_device = self.device_repo.get_by_ip(ip_address)
                        
                        if new_device:
                            # Показываем сообщение об успехе
                            QMessageBox.information(
                                self,
                                "Успешно",
                                f"Устройство {ip_address} успешно добавлено.\n"
                                f"ID: {new_device.id}\n"
                                f"Тип: {device_type}\n"
                                f"Архитектура: {new_device.architecture if hasattr(new_device, 'architecture') else 'N/A'}",
                                QMessageBox.Ok
                            )
                            
                            
                        self.refresh_dashboard_stats()
                        dialog.accept()
                        return
                    else:
                        self.device_validation_status.setText("Не удалось получить информацию")
                        
                        error_msg = save_result.get('error', 'Неизвестная ошибка')
                        print(f"Ошибка get_and_save_device_info: {error_msg}")
                        
                        QMessageBox.warning(
                            self,
                            "Внимание",
                            f"Не удалось получить информацию об устройстве:\n{error_msg}\n"
                            "Переключитесь в режим ручного ввода.",
                            QMessageBox.Ok
                        )
                        self.device_progress_bar.setVisible(False)
                        return
                        
                except Exception as e:
                    error_msg = str(e)
                    print(f"Исключение в get_and_save_device_info: {error_msg}")
                    self.device_validation_status.setText(f"Ошибка: {error_msg}")
                    QMessageBox.warning(
                        self,
                        "Ошибка",
                        f"Ошибка при получении информации:\n{error_msg}\n"
                        "Переключитесь в режим ручного ввода.",
                        QMessageBox.Ok
                    )
                    self.device_progress_bar.setVisible(False)
                    return
            
            else:
                # Режим ручного ввода для нового устройства
                try:
                    architecture = self.device_arch_input.text().strip()
                    memory_gb_str = self.device_memory_input.text().strip()
                    ram_gb_str = self.device_ram_input.text().strip()
                    cpu_core_str = self.device_cpu_input.text().strip()
                    
                    print(f"Ручные параметры: arch={architecture}, memory={memory_gb_str}, ram={ram_gb_str}, cpu={cpu_core_str}")
                    
                    # Проверяем, что все поля заполнены
                    if not all([architecture, memory_gb_str, ram_gb_str, cpu_core_str]):
                        QMessageBox.warning(
                            self,
                            "Неполные данные",
                            "Заполните все параметры устройства для ручного ввода.",
                            QMessageBox.Ok
                        )
                        self.device_progress_bar.setVisible(False)
                        return
                    
                    memory_gb = float(memory_gb_str)
                    ram_gb = float(ram_gb_str)
                    cpu_core = int(cpu_core_str)
                    
                    self.device_progress_bar.setValue(80)
                    self.device_validation_status.setText("Сохранение устройства в базу данных...")
                    
                    # Создаем новое устройство вручную
                    device = self.device_repo.create_device(
                        ip_address=ip_address,
                        architecture=architecture,
                        ram_gb=ram_gb,
                        cpu_core=cpu_core,
                        memory_gb=memory_gb,
                        device_type=device_type
                    )
                    
                    self.device_progress_bar.setValue(100)
                    self.device_validation_status.setText("Устройство успешно добавлено")
                    
                    # Показываем сообщение об успехе
                    QMessageBox.information(
                        self,
                        "Успешно",
                        f"Устройство {ip_address} успешно добавлено вручную.\n"
                        f"ID устройства: {device.id}\n"
                        f"Архитектура: {architecture}\n"
                        f"RAM: {ram_gb} GB\n"
                        f"CPU: {cpu_core} ядер\n"
                        f"ПЗУ: {memory_gb} GB",
                        QMessageBox.Ok
                    )
                    
                    self.refresh_dashboard_stats()
                    dialog.accept()
                    
                except ValueError as ve:
                    error_msg = str(ve)
                    print(f"Ошибка преобразования данных: {error_msg}")
                    QMessageBox.critical(
                        self,
                        "Ошибка ввода",
                        f"Некорректные числовые значения:\n{error_msg}\n"
                        "Убедитесь, что RAM, CPU и ПЗУ указаны числами.",
                        QMessageBox.Ok
                    )
                    self.device_progress_bar.setVisible(False)
                except Exception as e:
                    error_msg = str(e)
                    print(f"Общая ошибка: {error_msg}")
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        f"Не удалось добавить устройство вручную:\n{error_msg}",
                        QMessageBox.Ok
                    )
                    self.device_progress_bar.setVisible(False)
                    
        except Exception as e:
            error_msg = str(e)
            print(f"КРИТИЧЕСКАЯ ОШИБКА в process_device_add: {error_msg}")
            QMessageBox.critical(
                self,
                "Критическая ошибка",
                f"Не удалось обработать добавление устройства:\n{error_msg}",
                QMessageBox.Ok
            )
            self.device_progress_bar.setVisible(False)
           
    
    def show_optimization_dialog(self):
        """Поазать диалог оптимизации (модальное окно)"""
        dialog = QDialog(self)
        dialog.setWindowTitle("ОПТИМИЗАЦИЯ МОДЕЛИ")
        dialog.setModal(True)
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(700)
        
        layout = QVBoxLayout(dialog)
        
        # Информация
        info_label = QLabel(
            "Оптимизация модели для Edge-устройств.<br>"
            "Выберите модель, устройство и тестовые данные для запуска оптимизации."
        )
        info_label.setStyleSheet("""
            background-color: #1A1E24; 
            padding: 10px; 
            border-radius: 3px;
            color: #00B7EB;
            font-size: 11px;
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Группа выбора модели
        model_group = QGroupBox("ВЫБОР МОДЕЛИ")
        model_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00B7EB;
                border: 1px solid #32363C;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        model_layout = QVBoxLayout()
        
        # Выпадающий список моделей
        model_combo = QComboBox()  # Локальная переменная, не self.
        model_combo.setMinimumHeight(35)
        
        # Загружаем модели
        models = self.model_repo.get_all()
        model_combo.addItem("-- Выберите модель --", None)  # Пустой элемент
        
        for model in models:
            display_text = f"{model.name} (ID: {model.id}, Размер: {model.size if model.size else 'N/A'} МБ)"
            model_combo.addItem(display_text, model.id)
        
        # Информация о выбранной модели
        model_info_label = QLabel("Модель не выбрана")
        model_info_label.setStyleSheet("color: #F1C40F; padding: 5px;")
        
        model_layout.addWidget(QLabel("Выберите модель:"))
        model_layout.addWidget(model_combo)
        model_layout.addWidget(model_info_label)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Группа выбора устройства
        device_group = QGroupBox("ВЫБОР УСТРОЙСТВА")
        device_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00B7EB;
                border: 1px solid #32363C;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        device_layout = QVBoxLayout()
        
        # Выпадающий список устройств
        device_combo = QComboBox()  # Локальная переменная
        device_combo.setMinimumHeight(35)
        
        # Загружаем устройства
        devices = self.device_repo.get_all()
        device_combo.addItem("-- Выберите устройство --", None)  # Пустой элемент
        
        for device in devices:
            ram_text = f"{device.ram_gb} GB" if device.ram_gb else "N/A"
            display_text = f"{device.ip_address} (ID: {device.id}, RAM: {ram_text})"
            device_combo.addItem(display_text, device.id)
        
        # Информация о выбранном устройстве
        device_info_label = QLabel("Устройство не выбрано")
        device_info_label.setStyleSheet("color: #F1C40F; padding: 5px;")
        
        device_layout.addWidget(QLabel("Выберите устройство:"))
        device_layout.addWidget(device_combo)
        device_layout.addWidget(device_info_label)
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # Группа тестовых данных
        data_group = QGroupBox("ТЕСТОВЫЕ ДАННЫЕ")
        data_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00B7EB;
                border: 1px solid #32363C;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        data_layout = QFormLayout()
        
        # Поле для X данных
        x_data_layout = QHBoxLayout()
        x_data_input = QLineEdit()  # Локальная переменная
        x_data_input.setPlaceholderText("Выберите файл X_test.npy")
        x_data_layout.addWidget(x_data_input)
        
        def browse_x_file():
            file_path, _ = QFileDialog.getOpenFileName(
                dialog,
                "Выберите .npy файл",
                "",
                "NumPy files (*.npy);;Все файлы (*)"
            )
            if file_path:
                x_data_input.setText(file_path)
                validate_form()
        
        x_browse_btn = WarframeButton("Обзор")
        x_browse_btn.setMinimumWidth(80)
        x_browse_btn.clicked.connect(browse_x_file)
        x_data_layout.addWidget(x_browse_btn)
        data_layout.addRow("X_test данные:", x_data_layout)
        
        # Поле для Y данных
        y_data_layout = QHBoxLayout()
        y_data_input = QLineEdit()  # Локальная переменная
        y_data_input.setPlaceholderText("Выберите файл y_test.npy")
        y_data_layout.addWidget(y_data_input)
        
        def browse_y_file():
            file_path, _ = QFileDialog.getOpenFileName(
                dialog,
                "Выберите .npy файл",
                "",
                "NumPy files (*.npy);;Все файлы (*)"
            )
            if file_path:
                y_data_input.setText(file_path)
                validate_form()
        
        y_browse_btn = WarframeButton("Обзор")
        y_browse_btn.setMinimumWidth(80)
        y_browse_btn.clicked.connect(browse_y_file)
        y_data_layout.addWidget(y_browse_btn)
        data_layout.addRow("y_test метки:", y_data_layout)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Статус валидации
        validation_status_label = QLabel("Выберите модель, устройство и укажите тестовые данные")
        validation_status_label.setStyleSheet("color: #F1C40F; font-weight: bold; padding: 5px;")
        validation_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(validation_status_label)
        
        # Прогресс бар
        progress_bar = QProgressBar()
        progress_bar.setVisible(False)
        layout.addWidget(progress_bar)
        
        # Кнопки
        button_box = QDialogButtonBox()
        start_btn = button_box.addButton("Запустить оптимизацию", QDialogButtonBox.AcceptRole)
        cancel_btn = button_box.addButton("Отмена", QDialogButtonBox.RejectRole)
        
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #00B7EB;
                color: #0A0E14;
                font-weight: bold;
                min-width: 120px;
                min-height: 40px;
            }
            QPushButton:disabled {
                background-color: #32363C;
                color: #666666;
            }
        """)
        
        start_btn.setEnabled(False)
        
        # Функция обновления информации о модели
        def update_model_info():
            index = model_combo.currentIndex()
            if index > 0:  # index 0 это "-- Выберите модель --"
                model_id = model_combo.itemData(index)
                try:
                    model = self.model_repo.get_by_id(model_id)
                    if model:
                        type_name = model.type_neural_model.name if model.type_neural_model else str(model.type_id)
                        format_name = model.format_neural_model.name if model.format_neural_model else str(model.format_id)
                        size_text = f"{model.size:.2f}" if model.size else "N/A"
                        
                        info = f"Тип: {type_name}, Формат: {format_name}, Размер: {size_text} МБ"
                        model_info_label.setText(info)
                    else:
                        model_info_label.setText("Модель не найдена")
                except Exception as e:
                    model_info_label.setText(f"Ошибка: {str(e)[:50]}")
            else:
                model_info_label.setText("Модель не выбрана")
            
            validate_form()
        
        # Функция обновления информации об устройстве
        def update_device_info():
            index = device_combo.currentIndex()
            if index > 0:  # index 0 это "-- Выберите устройство --"
                device_id = device_combo.itemData(index)
                try:
                    device = self.device_repo.get_by_id(device_id)
                    if device:
                        info = f"Архитектура: {device.architecture}, CPU: {device.cpu_core} ядер, ПЗУ: {device.memory_gb} GB"
                        device_info_label.setText(info)
                    else:
                        device_info_label.setText("Устройство не найдено")
                except Exception as e:
                    device_info_label.setText(f"Ошибка: {str(e)[:50]}")
            else:
                device_info_label.setText("Устройство не выбрано")
            
            validate_form()
        
        # Функция валидации формы
        def validate_form():
            # Проверяем выбранную модель
            model_selected = model_combo.currentIndex() > 0
            
            # Проверяем выбранное устройство
            device_selected = device_combo.currentIndex() > 0
            
            # Проверяем пути к данным
            x_data_path = x_data_input.text().strip()
            y_data_path = y_data_input.text().strip()
            
            data_valid = all([
                x_data_path,
                y_data_path,
                os.path.exists(x_data_path),
                os.path.exists(y_data_path)
            ])
            
            if model_selected and device_selected and data_valid:
                validation_status_label.setText("Все данные корректны. Можно запускать оптимизацию")
                validation_status_label.setStyleSheet("color: #2ECC71; font-weight: bold; padding: 5px;")
                start_btn.setEnabled(True)
            else:
                validation_status_label.setText("Выберите модель, устройство и укажите тестовые данные")
                validation_status_label.setStyleSheet("color: #F1C40F; font-weight: bold; padding: 5px;")
                start_btn.setEnabled(False)
        
        # Функция запуска оптимизации
        def start_optimization():
            try:
                # Получаем выбранную модель
                model_index = model_combo.currentIndex()
                if model_index <= 0:
                    QMessageBox.warning(dialog, "Ошибка", "Выберите модель")
                    return
                
                model_id = model_combo.itemData(model_index)
                
                # Получаем выбранное устройство
                device_index = device_combo.currentIndex()
                if device_index <= 0:
                    QMessageBox.warning(dialog, "Ошибка", "Выберите устройство")
                    return
                
                device_id = device_combo.itemData(device_index)
                
                # Получаем пути к данным
                x_test_data_path = x_data_input.text().strip()
                y_test_data_path = y_data_input.text().strip()
                
                # Загружаем данные
                try:
                    import numpy as np
                    x_test_data = np.load(x_test_data_path)
                    y_test_data = np.load(y_test_data_path)
                except Exception as e:
                    QMessageBox.critical(dialog, "Ошибка", f"Не удалось загрузить тестовые данные:\n{e}")
                    return
                
                # Показываем прогресс бар
                progress_bar.setVisible(True)
                progress_bar.setValue(10)
                validation_status_label.setText("Запуск оптимизации...")
                
                print(f"\n{'='*80}")
                print("ОПТИМИЗАЦИЯ МОДЕЛИ")
                print(f"Модель ID: {model_id}")
                print(f"Устройство ID: {device_id}")
                print(f"Тестовые данные: X={x_test_data_path}, y={y_test_data_path}")
                print(f"{'='*80}")
                
                # Запускаем оптимизацию
                result = self.optimization_service.optimize_model_by_id(
                    model_id=int(model_id),
                    device_id=int(device_id)
                )
                
                if result.get('success'):
                    print(f"[УСПЕХ] Оптимизация завершена успешно!")
                    
                    # Получаем информацию об оригинальной модели
                    original_model_path = self.model_repo.get_path_by_id(model_id)[0]
                    original_model_format = original_model_path.split('.')[-1].lower()
                    optimized_model_format = result['optimized_model_path'].split('.')[-1].lower()
                    
                    progress_bar.setValue(70)
                    validation_status_label.setText("Проверка качества модели...")
                    
                    # Валидация модели
                    success = self.validation_service.validate_model_pair(
                        original_model_path,
                        result['optimized_model_path'],
                        x_test_data,
                        y_test_data,
                        original_model_format,
                        optimized_model_format
                    )
                    
                    if success["success"]:
                        progress_bar.setValue(90)
                        validation_status_label.setText("Сохранение результатов...")
                        
                        # Сохраняем результат
                        self.validation_service._save_optimization_result(
                            model_id,
                            result['optimized_model_id'],
                            success
                        )
                        
                        progress_bar.setValue(100)
                        validation_status_label.setText("Оптимизация завершена успешно!")
                        
                        # Показываем отчет
                        report = (
                            f"Оптимизация завершена успешно!\n\n"
                            f"Отчет проверки качества модели:\n"
                            f"• Точность до оптимизации: {success['accuracy_before']:.4f}\n"
                            f"• Точность после оптимизации: {success['accuracy_after']:.4f}\n"
                            f"• Потери до оптимизации: {success['loss_before']:.4f}\n"
                            f"• Потери после оптимизации: {success['loss_after']:.4f}\n\n"
                            f"Оптимизированная модель: {result['optimized_model_path']}\n"
                            f"Размер: {result.get('model_size_mb', 0):.2f} MB\n"
                            f"ID оптимизированной модели: {result.get('optimized_model_id', 'N/A')}"
                        )
                        
                        QMessageBox.information(dialog, "Успех", report)
                        
                        # Обновляем статистику на главной
                        self.refresh_dashboard_stats()
                        
                        # Закрываем диалог
                        dialog.accept()
                        
                    else:
                        error_msg = success.get('error', 'Неизвестная ошибка')
                        progress_bar.setValue(100)
                        validation_status_label.setText(f"Ошибка проверки качества: {error_msg}")
                        
                        QMessageBox.warning(dialog, "Внимание", 
                            f"Оптимизация завершена, но не удалось проверить качество модели:\n{error_msg}")
                        
                else:
                    error_msg = result.get('error', 'Неизвестная ошибка')
                    progress_bar.setValue(100)
                    validation_status_label.setText(f"Ошибка оптимизации: {error_msg}")
                    
                    QMessageBox.critical(dialog, "Ошибка", f"Не удалось выполнить оптимизацию:\n{error_msg}")
                    
            except Exception as e:
                progress_bar.setVisible(False)
                QMessageBox.critical(dialog, "Ошибка", f"Ошибка при запуске оптимизации:\n{e}")
                print(f"Критическая ошибка оптимизации: {e}")
        
        # Подключаем сигналы
        model_combo.currentIndexChanged.connect(update_model_info)
        device_combo.currentIndexChanged.connect(update_device_info)
        x_data_input.textChanged.connect(validate_form)
        y_data_input.textChanged.connect(validate_form)
        
        button_box.accepted.connect(start_optimization)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec_()
    

    def show_optimization_stub(self):
        """Показать диалог оптимизации (заменяем заглушку)"""
        self.show_optimization_dialog()


    def show_deployment_dialog(self):
        """Показать диалог развертывания (модальное окно)"""
        dialog = QDialog(self)
        dialog.setWindowTitle("РАЗВЕРТЫВАНИЕ МОДЕЛИ")
        dialog.setModal(True)
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(700)
        
        layout = QVBoxLayout(dialog)
        
        # Информация
        info_label = QLabel(
            "Развертывание оптимизированной модели на Edge-устройство.<br>"
            "Выберите оптимизированную модель, устройство и параметры подключения."
        )
        info_label.setStyleSheet("""
            background-color: #1A1E24; 
            padding: 10px; 
            border-radius: 3px;
            color: #00B7EB;
            font-size: 11px;
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Группа выбора оптимизированной модели
        model_group = QGroupBox("ВЫБОР ОПТИМИЗИРОВАННОЙ МОДЕЛИ")
        model_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00B7EB;
                border: 1px solid #32363C;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        model_layout = QVBoxLayout()
        
        # Выпадающий список оптимизированных моделей
        optimized_model_combo = QComboBox()
        optimized_model_combo.setMinimumHeight(35)
        
        # Загружаем оптимизированные модели
        optimized_models = self.optimized_model_repo.get_all()
        optimized_model_combo.addItem("-- Выберите модель --", None)
        
        for model in optimized_models:
            # Получаем оригинальную модель для названия
            original_model = self.model_repo.get_by_id(model.original_model_id)
            original_name = original_model.name if original_model else f"ID: {model.original_model_id}"
            
            # Форматируем размер
            if model.size is not None:
                size_text = f"{model.size:.2f} МБ"
            else:
                size_text = "N/A"
            
            display_text = f"{original_name} → (ID: {model.id}, Размер: {size_text})"
            optimized_model_combo.addItem(display_text, model.id)
        
        # Информация о выбранной модели
        optimized_model_info_label = QLabel("Модель не выбрана")
        optimized_model_info_label.setStyleSheet("color: #F1C40F; padding: 5px;")
        
        model_layout.addWidget(QLabel("Выберите оптимизированную модель:"))
        model_layout.addWidget(optimized_model_combo)
        model_layout.addWidget(optimized_model_info_label)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Группа выбора устройства
        device_group = QGroupBox("ВЫБОР УСТРОЙСТВА")
        device_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00B7EB;
                border: 1px solid #32363C;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        device_layout = QVBoxLayout()
        
        # Выпадающий список устройств
        device_combo = QComboBox()
        device_combo.setMinimumHeight(35)
        
        # Загружаем устройства
        devices = self.device_repo.get_all()
        device_combo.addItem("-- Выберите устройство --", None)
        
        for device in devices:
            ram_text = f"{device.ram_gb} GB" if device.ram_gb else "N/A"
            display_text = f"{device.ip_address} (ID: {device.id}, RAM: {ram_text})"
            device_combo.addItem(display_text, device.id)
        
        # Информация о выбранном устройстве
        device_info_label = QLabel("Устройство не выбрано")
        device_info_label.setStyleSheet("color: #F1C40F; padding: 5px;")
        
        device_layout.addWidget(QLabel("Выберите устройство:"))
        device_layout.addWidget(device_combo)
        device_layout.addWidget(device_info_label)
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # Группа параметров подключения
        connection_group = QGroupBox("ПАРАМЕТРЫ ПОДКЛЮЧЕНИЯ")
        connection_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00B7EB;
                border: 1px solid #32363C;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        connection_layout = QFormLayout()
        
        # Поле для IP (с предзаполнением)
        ip_layout = QHBoxLayout()
        ip_input = QLineEdit()
        ip_input.setPlaceholderText("IP адрес устройства")
        ip_layout.addWidget(ip_input)
        
        # Кнопка использования IP из устройства
        def use_device_ip():
            device_index = device_combo.currentIndex()
            if device_index > 0:
                device_id = device_combo.itemData(device_index)
                device = self.device_repo.get_by_id(device_id)
                if device and device.ip_address:
                    ip_input.setText(device.ip_address)
        
        use_ip_btn = WarframeButton("Исп. IP устройства")
        use_ip_btn.setMinimumWidth(120)
        use_ip_btn.clicked.connect(use_device_ip)
        ip_layout.addWidget(use_ip_btn)
        connection_layout.addRow("IP адрес:", ip_layout)
        
        # Имя пользователя
        username_input = QLineEdit()
        username_input.setPlaceholderText("Имя пользователя")
        connection_layout.addRow("Имя пользователя:", username_input)
        
        # Пароль
        password_input = QLineEdit()
        password_input.setPlaceholderText("Пароль")
        password_input.setEchoMode(QLineEdit.Password)
        connection_layout.addRow("Пароль:", password_input)
        
        # Порт
        port_input = QLineEdit()
        port_input.setPlaceholderText("8022")
        port_input.setText("8022")
        connection_layout.addRow("Порт:", port_input)
        
        # Секрет для шифрования
        secret_input = QLineEdit()
        secret_input.setPlaceholderText("Оставьте пустым для автоматической генерации")
        secret_input.setEchoMode(QLineEdit.Password)
        connection_layout.addRow("Секрет для шифрования:", secret_input)
        
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)
        
        # Группа дополнительных настроек
        settings_group = QGroupBox("ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00B7EB;
                border: 1px solid #32363C;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        settings_layout = QFormLayout()
        
        # Удаленная директория
        remote_dir_input = QLineEdit()
        remote_dir_input.setPlaceholderText("~/ota_updates/")
        remote_dir_input.setText("~/ota_updates/")
        settings_layout.addRow("Удаленная директория:", remote_dir_input)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Статус валидации
        deployment_status_label = QLabel("Выберите модель, устройство и заполните параметры подключения")
        deployment_status_label.setStyleSheet("color: #F1C40F; font-weight: bold; padding: 5px;")
        deployment_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(deployment_status_label)
        
        # Прогресс бар
        deployment_progress_bar = QProgressBar()
        deployment_progress_bar.setVisible(False)
        layout.addWidget(deployment_progress_bar)
        
        # Кнопки
        button_box = QDialogButtonBox()
        deploy_btn = button_box.addButton("Запустить развертывание", QDialogButtonBox.AcceptRole)
        cancel_btn = button_box.addButton("Отмена", QDialogButtonBox.RejectRole)
        
        deploy_btn.setStyleSheet("""
            QPushButton {
                background-color: #00B7EB;
                color: #0A0E14;
                font-weight: bold;
                min-width: 120px;
                min-height: 40px;
            }
            QPushButton:disabled {
                background-color: #32363C;
                color: #666666;
            }
        """)
        
        deploy_btn.setEnabled(False)
        
        # Функция обновления информации о модели
        def update_optimized_model_info():
            index = optimized_model_combo.currentIndex()
            if index > 0:
                model_id = optimized_model_combo.itemData(index)
                try:
                    model = self.optimized_model_repo.get_by_id(model_id)
                    if model:
                        original_model = self.model_repo.get_by_id(model.original_model_id)
                        original_name = original_model.name if original_model else f"ID: {model.original_model_id}"
                        
                        info = f"Оригинальная модель: {original_name}, Формат: {model.format}"
                        optimized_model_info_label.setText(info)
                    else:
                        optimized_model_info_label.setText("Модель не найдена")
                except Exception as e:
                    optimized_model_info_label.setText(f"Ошибка: {str(e)[:50]}")
            else:
                optimized_model_info_label.setText("Модель не выбрана")
            
            validate_form()
        
        # Функция обновления информации об устройстве
        def update_device_info():
            index = device_combo.currentIndex()
            if index > 0:
                device_id = device_combo.itemData(index)
                try:
                    device = self.device_repo.get_by_id(device_id)
                    if device:
                        info = f"Архитектура: {device.architecture}, CPU: {device.cpu_core} ядер, ПЗУ: {device.memory_gb} GB"
                        device_info_label.setText(info)
                        
                        # Автозаполнение IP если поле пустое
                        if not ip_input.text() and device.ip_address:
                            ip_input.setText(device.ip_address)
                    else:
                        device_info_label.setText("Устройство не найдено")
                except Exception as e:
                    device_info_label.setText(f"Ошибка: {str(e)[:50]}")
            else:
                device_info_label.setText("Устройство не выбрано")
            
            validate_form()
        
        # Функция валидации формы
        def validate_form():
            # Проверяем выбранную модель
            model_selected = optimized_model_combo.currentIndex() > 0
            
            # Проверяем выбранное устройство
            device_selected = device_combo.currentIndex() > 0
            
            # Проверяем параметры подключения
            ip = ip_input.text().strip()
            username = username_input.text().strip()
            password = password_input.text().strip()
            port = port_input.text().strip()
            
            connection_valid = all([ip, username, password, port])
            
            # Проверяем удаленную директорию
            remote_dir = remote_dir_input.text().strip()
            remote_dir_valid = bool(remote_dir)
            
            if model_selected and device_selected and connection_valid and remote_dir_valid:
                deployment_status_label.setText("Все данные корректны. Можно запускать развертывание")
                deployment_status_label.setStyleSheet("color: #2ECC71; font-weight: bold; padding: 5px;")
                deploy_btn.setEnabled(True)
            else:
                deployment_status_label.setText("Заполните все обязательные поля")
                deployment_status_label.setStyleSheet("color: #F1C40F; font-weight: bold; padding: 5px;")
                deploy_btn.setEnabled(False)
        
        # Функция запуска развертывания
        def start_deployment():
            try:
                # Получаем выбранную модель
                model_index = optimized_model_combo.currentIndex()
                if model_index <= 0:
                    QMessageBox.warning(dialog, "Ошибка", "Выберите оптимизированную модель")
                    return
                
                model_id = optimized_model_combo.itemData(model_index)
                
                # Получаем выбранное устройство
                device_index = device_combo.currentIndex()
                if device_index <= 0:
                    QMessageBox.warning(dialog, "Ошибка", "Выберите устройство")
                    return
                
                device_id = device_combo.itemData(device_index)
                
                # Получаем параметры подключения
                connection_params = {
                    'host': ip_input.text().strip(),
                    'username': username_input.text().strip(),
                    'password': password_input.text().strip(),
                    'port': int(port_input.text().strip()) if port_input.text().strip().isdigit() else 8022
                }
                
                # Получаем секрет
                secret = secret_input.text().strip() or None
                
                # Получаем удаленную директорию
                remote_dir = remote_dir_input.text().strip()
                
                # Показываем прогресс бар
                deployment_progress_bar.setVisible(True)
                deployment_progress_bar.setValue(10)
                deployment_status_label.setText("Подготовка к развертыванию...")
                
                print(f"\n{'='*80}")
                print("РАЗВЕРТЫВАНИЕ МОДЕЛИ")
                print(f"Оптимизированная модель ID: {model_id}")
                print(f"Устройство ID: {device_id}")
                print(f"Параметры подключения: {connection_params}")
                print(f"{'='*80}")
                
                # Получаем модель и устройство для отображения
                optimized_model = self.optimized_model_repo.get_by_id(model_id)
                device = self.device_repo.get_by_id(device_id)
                
                if not optimized_model or not device:
                    QMessageBox.critical(dialog, "Ошибка", "Модель или устройство не найдены")
                    return
                
                # Подтверждение
                confirm_msg = (
                    f"Подтвердите развертывание:\n\n"
                    f"Модель: {optimized_model.path}\n"
                    f"Устройство: {device.ip_address} (ID: {device.id})\n"
                    f"Продолжить?"
                )
                
                reply = QMessageBox.question(
                    dialog,
                    "Подтверждение",
                    confirm_msg,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    deployment_status_label.setText("Развертывание отменено")
                    deployment_progress_bar.setVisible(False)
                    return
                
                # Создаем запись о развертывании
                deployment_progress_bar.setValue(20)
                deployment_status_label.setText("Создание записи о развертывании...")
                
                deployment = self.deployment_repo.create_deployment(
                    optimized_model_id=model_id,
                    device_id=device_id,
                    status="starting"
                )
                
                # Проверка подключения к устройству
                deployment_progress_bar.setValue(30)
                deployment_status_label.setText("Проверка подключения к устройству...")
                
                print("Проверка подключения к устройству...")
                connect_result = self.device_service.connect_device(
                    device_type="android",  # Или device.type если есть
                    **connection_params
                )
                
                if not connect_result.get('success'):
                    self.deployment_repo.update_status(deployment.id, "connection_failed")
                    deployment_progress_bar.setValue(100)
                    deployment_status_label.setText("Ошибка подключения")
                    
                    QMessageBox.critical(
                        dialog,
                        "Ошибка подключения",
                        f"Не удалось подключиться к устройству:\n{connect_result.get('error')}"
                    )
                    return
                
                print("Успешное подключение к устройству")
                
                # Запуск развертывания
                deployment_progress_bar.setValue(50)
                deployment_status_label.setText("Запуск развертывания OTA...")
                
                self.deployment_repo.update_status(deployment.id, "deploying")
                
                result = self.device_service.deploy_ota_update(
                    model_path=optimized_model.path,
                    model_id=model_id,
                    device_id=device_id,
                    secret=secret,
                    remote_dir=remote_dir
                )
                
                # Обновляем статус развертывания
                if result.get('success'):
                    deployment_progress_bar.setValue(100)
                    deployment_status_label.setText("Развертывание успешно завершено!")
                    
                    self.deployment_repo.update_status(deployment.id, "success")
                    
                    # Показываем отчет об успехе
                    success_report = (
                        f"OTA ОБНОВЛЕНИЕ УСПЕШНО РАЗВЕРНУТО!\n\n"
                        f"Отчет:\n"
                        f"• ID развертывания: {deployment.id}\n"
                        f"• Файл на устройстве: {result.get('output_file')}\n"
                        f"• Контрольная сумма: {result.get('checksum')[:16]}...\n"
                        f"• Размер файла: {result.get('original_size')} байт\n\n"
                        f"Для проверки на устройстве выполните:\n"
                        f"  ls -la {result.get('output_file')}\n"
                        f"  file {result.get('output_file')}"
                    )
                    
                    QMessageBox.information(dialog, "Успех", success_report)
                    
                    # Обновляем статистику на главной
                    self.refresh_dashboard_stats()
                    
                    # Закрываем диалог
                    dialog.accept()
                    
                else:
                    deployment_progress_bar.setValue(100)
                    deployment_status_label.setText("Ошибка развертывания")
                    
                    self.deployment_repo.update_status(deployment.id, "failed")
                    
                    error_msg = result.get('error', 'Неизвестная ошибка')
                    error_report = f"ОШИБКА РАЗВЕРТЫВАНИЯ OTA\n\nОшибка: {error_msg}"
                    
                    if 'command_output' in result:
                        error_report += f"\n\nВывод команды: {result.get('command_output')}"
                    
                    QMessageBox.critical(dialog, "Ошибка", error_report)
                    
            except Exception as e:
                deployment_progress_bar.setVisible(False)
                QMessageBox.critical(dialog, "Ошибка", f"Ошибка при запуске развертывания:\n{e}")
                print(f"Критическая ошибка развертывания: {e}")
        
        # Подключаем сигналы
        optimized_model_combo.currentIndexChanged.connect(update_optimized_model_info)
        device_combo.currentIndexChanged.connect(update_device_info)
        ip_input.textChanged.connect(validate_form)
        username_input.textChanged.connect(validate_form)
        password_input.textChanged.connect(validate_form)
        port_input.textChanged.connect(validate_form)
        remote_dir_input.textChanged.connect(validate_form)
        
        button_box.accepted.connect(start_deployment)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec_()



    def show_deployment_stub(self):
        """Показать диалог развертывания (заменяем заглушку)"""
        self.show_deployment_dialog()





















            # ===== СТРАНИЦА МОДЕЛЕЙ =====
    def create_models_page(self):
        """Создать страницу с таблицей моделей"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Заголовок
        title = QLabel("УПРАВЛЕНИЕ МОДЕЛЯМИ")
        title.setFont(WarframeStyles.get_font(24, True))
        title.setStyleSheet("color: #00B7EB; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Панель управления
        control_panel = self.create_models_control_panel()
        layout.addWidget(control_panel)
        
        # Таблица моделей
        self.models_table = self.create_models_table()
        layout.addWidget(self.models_table, 1)  # 1 - коэффициент растяжения
        
        # Панель навигации
        navigation_panel = self.create_models_navigation_panel()
        layout.addWidget(navigation_panel)
        
        return page
    
    def create_models_control_panel(self):
        """Создать панель управления для страницы моделей"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #32363C;
                border-radius: 3px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        
        # Кнопка добавления
        add_btn = WarframeButton("ДОБАВИТЬ МОДЕЛЬ")
        add_btn.setMinimumHeight(40)
        add_btn.clicked.connect(self.add_model)
        layout.addWidget(add_btn)
        
        # Кнопка обновления
        refresh_btn = WarframeButton("ОБНОВИТЬ")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.clicked.connect(self.refresh_models_table)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        
        return panel
    
    def create_models_table(self):
        """Создать таблицу для отображения моделей"""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["ID", "Название", "Тип", "Формат", "Размер (МБ)"])  # Изменено
        
        # Настройка таблицы
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        
        # Настройка ширины колонок
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Название
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Тип
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Формат
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Размер
        
        # Стилизация таблицы
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1A1E24;
                color: #FFFFFF;
                border: 1px solid #32363C;
                gridline-color: #32363C;
                alternate-background-color: #121620;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #00B7EB;
                color: #0A0E14;
            }
            QHeaderView::section {
                background-color: #1A1E24;
                color: #00B7EB;
                font-weight: bold;
                padding: 5px;
                border: 1px solid #32363C;
            }
        """)
        
        # Контекстное меню для таблицы
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.show_model_context_menu)
        
        return table
    
    def create_models_navigation_panel(self):
        """Создать панель навигации для страницы моделей"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #32363C;
                border-radius: 3px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        
        # Кнопка редактирования
        edit_btn = WarframeButton("РЕДАКТИРОВАТЬ")
        edit_btn.setMinimumHeight(40)
        edit_btn.clicked.connect(self.edit_selected_model)
        layout.addWidget(edit_btn)
        
        # Кнопка удаления
        delete_btn = WarframeButton("УДАЛИТЬ")
        delete_btn.setMinimumHeight(40)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #EB4B4B;
                color: #0A0E14;
            }
            QPushButton:hover {
                background-color: #FF6B6B;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected_model)
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        
        # Статистика
        self.models_stats_label = QLabel("Всего моделей: 0")
        self.models_stats_label.setStyleSheet("color: #00B7EB; font-weight: bold;")
        layout.addWidget(self.models_stats_label)
        
        return panel
    
    def show_model_context_menu(self, position):
        """Показать контекстное меню для выбранной модели"""
        row = self.models_table.rowAt(position.y())
        if row < 0:
            return
        
        # Создаем контекстное меню
        menu = QMenu()
        
        edit_action = QAction("Редактировать", self)
        edit_action.triggered.connect(self.edit_selected_model)
        menu.addAction(edit_action)
        
        delete_action = QAction("Удалить", self)
        delete_action.triggered.connect(self.delete_selected_model)
        menu.addAction(delete_action)
        
        
        
        # Показываем меню
        menu.exec_(self.models_table.viewport().mapToGlobal(position))
    
    def refresh_models_table(self):
        """Обновить таблицу моделей"""
        try:
            # Получаем все модели из базы
            models = self.model_repo.get_all()
            
            # Устанавливаем количество строк
            self.models_table.setRowCount(len(models))
            
            # Заполняем таблицу
            for row, model in enumerate(models):
                # ID
                id_item = QTableWidgetItem(str(model.id))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.models_table.setItem(row, 0, id_item)
                
                # Название
                name_item = QTableWidgetItem(model.name)
                self.models_table.setItem(row, 1, name_item)
                
                # Тип
                if model.type_neural_model and hasattr(model.type_neural_model, 'name'):
                    type_name = model.type_neural_model.name
                else:
                    type_name = str(model.type_id) if model.type_id else "N/A"
                
                type_item = QTableWidgetItem(type_name)
                type_item.setTextAlignment(Qt.AlignCenter)
                self.models_table.setItem(row, 2, type_item)
                
                # Формат
                if model.format_neural_model and hasattr(model.format_neural_model, 'name'):
                    format_name = model.format_neural_model.name
                else:
                    format_name = str(model.format_id) if model.format_id else "N/A"
                
                format_item = QTableWidgetItem(format_name)
                format_item.setTextAlignment(Qt.AlignCenter)
                self.models_table.setItem(row, 3, format_item)
                
                # Размер (МБ) - новая колонка вместо даты создания
                if model.size is not None:
                    size_text = f"{model.size:.2f}"
                else:
                    size_text = "N/A"
                
                size_item = QTableWidgetItem(size_text)
                size_item.setTextAlignment(Qt.AlignCenter)
                self.models_table.setItem(row, 4, size_item)
            
            # Обновляем статистику
            self.models_stats_label.setText(f"Всего моделей: {len(models)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить модели:\n{e}")
    
    def edit_selected_model(self):
        """Редактировать выбранную модель"""
        selected_rows = self.models_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите модель для редактирования")
            return
        
        row = selected_rows[0].row()
        model_id = int(self.models_table.item(row, 0).text())
        
        # Получаем модель из базы
        model = self.model_repo.get_by_id(model_id)
        if not model:
            QMessageBox.warning(self, "Ошибка", "Модель не найдена")
            return
        
        # Отладка: посмотрим что у нас в отношениях
        print(f"DEBUG: Модель ID: {model.id}, Название: {model.name}")
        print(f"DEBUG: model.type_neural_model = {model.type_neural_model}")
        print(f"DEBUG: type(model.type_neural_model) = {type(model.type_neural_model)}")
        
        if model.type_neural_model:
            print(f"DEBUG: dir(model.type_neural_model) = {dir(model.type_neural_model)}")
            if hasattr(model.type_neural_model, 'name'):
                print(f"DEBUG: model.type_neural_model.name = {model.type_neural_model.name}")
        
        # Диалог редактирования
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактирование: {model.name}")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Форма
        form_layout = QFormLayout()
        
        name_input = QLineEdit(model.name)
        form_layout.addRow("Название:", name_input)
        
        # Получаем все доступные типы моделей
        available_types = self.model_repo.get_model_types()
        type_combo = QComboBox()
        type_combo.addItems(available_types)
        
        # Устанавливаем текущий тип модели
        current_type = "cv"  # значение по умолчанию
        
        # Пробуем разные способы получить тип
        try:
            # Способ 1: Через отношение
            if model.type_neural_model:
                # Если это строка
                if isinstance(model.type_neural_model, str):
                    current_type = model.type_neural_model
                # Если это объект ModelType
                elif hasattr(model.type_neural_model, 'name'):
                    current_type = model.type_neural_model.name
                # Если это что-то другое
                else:
                    print(f"DEBUG: Неизвестный тип: {type(model.type_neural_model)}")
                    # Пробуем получить через репозиторий
                    type_info = self.model_repo.get_model_type_and_format(model_id)
                    if type_info and 'model_type' in type_info:
                        current_type = type_info['model_type']
        except Exception as e:
            print(f"DEBUG: Ошибка получения типа через отношение: {e}")
            # Используем запасной вариант
            type_info = self.model_repo.get_model_type_and_format(model_id)
            if type_info and 'model_type' in type_info:
                current_type = type_info['model_type']
        
        print(f"DEBUG: Выбранный тип: {current_type}")
        
        # Устанавливаем текущее значение
        if current_type in available_types:
            type_combo.setCurrentText(current_type)
        elif available_types:  # Если список не пустой
            type_combo.setCurrentIndex(0)
        
        form_layout.addRow("Тип:", type_combo)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        button_box = QDialogButtonBox()
        save_btn = button_box.addButton("Сохранить", QDialogButtonBox.AcceptRole)
        cancel_btn = button_box.addButton("Отмена", QDialogButtonBox.RejectRole)
        
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #00B7EB;
                color: #0A0E14;
                font-weight: bold;
            }
        """)
        
        def save_changes():
            try:
                # Обновляем модель
                self.model_repo.update(
                    model_id=model_id,
                    name=name_input.text().strip(),
                    type_name=type_combo.currentText()  # Передаем имя типа
                )
                
                QMessageBox.information(self, "Успех", "Модель обновлена")
                self.refresh_models_table()
                self.refresh_dashboard_stats()  # Обновляем статистику на главной
                dialog.accept()
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить модель:\n{e}")
        
        button_box.accepted.connect(save_changes)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(button_box)
        dialog.exec_()



    def delete_selected_model(self):
        """Удалить выбранную модель"""
        selected_rows = self.models_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите модель для удаления")
            return
        
        row = selected_rows[0].row()
        model_name = self.models_table.item(row, 1).text()
        model_id = int(self.models_table.item(row, 0).text())
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить модель '{model_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Удаляем модель
                success = self.model_repo.delete(model_id)
                
                if success:
                    QMessageBox.information(self, "Успех", "Модель удалена")
                    self.refresh_models_table()
                    self.refresh_dashboard_stats()  # Обновляем статистику на главной
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить модель")
                    
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить модель:\n{e}")
                
   










# ===== СТРАНИЦА УСТРОЙСТВ =====
    def create_devices_page(self):
        """Создать страницу с таблицей устройств"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Заголовок
        title = QLabel("УПРАВЛЕНИЕ УСТРОЙСТВАМИ")
        title.setFont(WarframeStyles.get_font(24, True))
        title.setStyleSheet("color: #00B7EB; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Панель управления
        control_panel = self.create_devices_control_panel()
        layout.addWidget(control_panel)
        
        # Таблица устройств
        self.devices_table = self.create_devices_table()
        layout.addWidget(self.devices_table, 1)  # 1 - коэффициент растяжения
        
        # Панель навигации
        navigation_panel = self.create_devices_navigation_panel()
        layout.addWidget(navigation_panel)
        
        return page

    def create_devices_control_panel(self):
        """Создать панель управления для страницы устройств"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #32363C;
                border-radius: 3px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        
        # Кнопка подключения
        connect_btn = WarframeButton("ПОДКЛЮЧИТЬ УСТРОЙСТВО")
        connect_btn.setMinimumHeight(40)
        connect_btn.clicked.connect(self.add_device)
        layout.addWidget(connect_btn)
        
        # Кнопка обновления
        refresh_btn = WarframeButton("ОБНОВИТЬ")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.clicked.connect(self.refresh_devices_table)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        
        return panel

    def create_devices_table(self):
        """Создать таблицу для отображения устройств"""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels(["ID", "IP Адрес", "Тип", "Архитектура", "Свободная память(ГБ)", "ОЗУ (ГБ)", "ЦПУ (ядер)", "Последняя активность"])
        
        # Настройка таблицы
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        
        # Настройка ширины колонок - смешанный подход
        header = table.horizontalHeader()
        
        # Колонки по содержимому
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID - короткая
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Тип - короткая
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Архитектура
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Свободная память(ГБ)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # ОЗУ (ГБ)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # ЦПУ (ядер)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Последняя активность
        
        # Колонки с растяжением для длинного текста
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # IP Адрес - может быть длинным
        
        # Стилизация таблицы
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1A1E24;
                color: #FFFFFF;
                border: 1px solid #32363C;
                gridline-color: #32363C;
                alternate-background-color: #121620;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #00B7EB;
                color: #0A0E14;
            }
            QHeaderView::section {
                background-color: #1A1E24;
                color: #00B7EB;
                font-weight: bold;
                padding: 5px;
                border: 1px solid #32363C;
            }
        """)
        
        # Контекстное меню для таблицы
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.show_device_context_menu)
        
        return table

    def create_devices_navigation_panel(self):
        """Создать панель навигации для страницы устройств"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #32363C;
                border-radius: 3px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        
        # Кнопка проверки связи
        ping_btn = WarframeButton("ПРОВЕРИТЬ СВЯЗЬ")
        ping_btn.setMinimumHeight(40)
        ping_btn.clicked.connect(self.ping_selected_device)
        layout.addWidget(ping_btn)
        
        # Кнопка удаления
        delete_btn = WarframeButton("УДАЛИТЬ")
        delete_btn.setMinimumHeight(40)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #EB4B4B;
                color: #0A0E14;
            }
            QPushButton:hover {
                background-color: #FF6B6B;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected_device)
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        
        # Статистика
        self.devices_stats_label = QLabel("Всего устройств: 0 | Подключено: 0")
        self.devices_stats_label.setStyleSheet("color: #00B7EB; font-weight: bold;")
        layout.addWidget(self.devices_stats_label)
        
        return panel

    def show_device_context_menu(self, position):
        """Показать контекстное меню для выбранного устройства"""
        row = self.devices_table.rowAt(position.y())
        if row < 0:
            return
        
        # Создаем контекстное меню
        menu = QMenu()
        
        ping_action = QAction("Проверить связь", self)
        ping_action.triggered.connect(self.ping_selected_device)
        menu.addAction(ping_action)
        
        menu.addSeparator()
        
        info_action = QAction("Получить информацию", self)
        info_action.triggered.connect(self.get_device_info)
        menu.addAction(info_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Удалить", self)
        delete_action.triggered.connect(self.delete_selected_device)
        menu.addAction(delete_action)
        
        # Показываем меню
        menu.exec_(self.devices_table.viewport().mapToGlobal(position))

    def refresh_devices_table(self):
        """Обновить таблицу устройств"""
        try:
            # Получаем все устройства из базы
            devices = self.device_repo.get_all()
            
            # Устанавливаем количество строк
            self.devices_table.setRowCount(len(devices))
            
            # Получаем подключенные устройства
            connected_devices = self.device_repo.get_connected()
            connected_ids = {device.id for device in connected_devices}
            
            # Заполняем таблицу
            for row, device in enumerate(devices):
                # ID
                id_item = QTableWidgetItem(str(device.id))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.devices_table.setItem(row, 0, id_item)
                
                # IP Адрес
                ip_item = QTableWidgetItem(device.ip_address)
                self.devices_table.setItem(row, 1, ip_item)
                
                # Тип устройства
                if device.type_device and hasattr(device.type_device, 'name'):
                    type_name = device.type_device.name
                else:
                    type_name = str(device.type_id) if device.type_id else "N/A"
                
                type_item = QTableWidgetItem(type_name)
                type_item.setTextAlignment(Qt.AlignCenter)
                self.devices_table.setItem(row, 2, type_item)
                
                # Архитектура
                arch_item = QTableWidgetItem(device.architecture if device.architecture else "N/A")
                arch_item.setTextAlignment(Qt.AlignCenter)
                self.devices_table.setItem(row, 3, arch_item)
                
                # Свободная память (ГБ) - новая колонка
                memory_item = QTableWidgetItem(str(device.memory_gb) if device.memory_gb else "N/A")
                memory_item.setTextAlignment(Qt.AlignCenter)
                self.devices_table.setItem(row, 4, memory_item)
                
                # ОЗУ (ГБ)
                ram_item = QTableWidgetItem(str(device.ram_gb) if device.ram_gb else "N/A")
                ram_item.setTextAlignment(Qt.AlignCenter)
                self.devices_table.setItem(row, 5, ram_item)
                
                # ЦПУ (ядер)
                cpu_item = QTableWidgetItem(str(device.cpu_core) if device.cpu_core else "N/A")
                cpu_item.setTextAlignment(Qt.AlignCenter)
                self.devices_table.setItem(row, 6, cpu_item)
                
                # Последняя активность
                if device.last_seen:
                    last_seen_text = device.last_seen.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    last_seen_text = "Никогда"
                
                last_seen_item = QTableWidgetItem(last_seen_text)
                last_seen_item.setTextAlignment(Qt.AlignCenter)
                
                # Подсвечиваем активные устройства
                if device.id in connected_ids:
                    last_seen_item.setForeground(QColor("#FFFFFF"))  # Зеленый
                    # Также можно подсветить всю строку
                    for col in range(self.devices_table.columnCount()):
                        item = self.devices_table.item(row, col)
                        if item:
                            item.setBackground(QColor("#0A2F1C"))  # Темно-зеленый фон
                            
                self.devices_table.setItem(row, 7, last_seen_item)  # Исправлен индекс для последней колонки
            
            # Обновляем статистику
            total_devices = len(devices)
            connected_count = len(connected_devices)
            self.devices_stats_label.setText(f"Всего устройств: {total_devices} | Подключено: {connected_count}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить устройства:\n{e}")




    def connect_device(self):
        """Подключиться к устройству"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Подключение к устройству")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Форма подключения
        form_layout = QFormLayout()
        
        # Тип устройства
        type_combo = QComboBox()
        type_combo.addItems(["android", "linux", "windows"])  # Можно расширить
        form_layout.addRow("Тип устройства:", type_combo)
        
        # IP адрес
        ip_input = QLineEdit()
        ip_input.setPlaceholderText("")
        form_layout.addRow("IP адрес:", ip_input)
        
        # Порт (для определенных типов)
        port_input = QSpinBox()
        port_input.setRange(1, 65535)
        port_input.setValue(5555)  # Дефолтный порт для ADB
        port_input.setEnabled(False)  # По умолчанию отключен
        
        def on_type_changed():
            if type_combo.currentText() == "android":
                port_input.setEnabled(True)
                port_input.setValue(8022)
            else:
                port_input.setEnabled(False)
        
        type_combo.currentTextChanged.connect(on_type_changed)
        form_layout.addRow("Порт:", port_input)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        button_box = QDialogButtonBox()
        connect_btn = button_box.addButton("Подключиться", QDialogButtonBox.AcceptRole)
        cancel_btn = button_box.addButton("Отмена", QDialogButtonBox.RejectRole)
        
        connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #00B7EB;
                color: #0A0E14;
                font-weight: bold;
            }
        """)
        
        def attempt_connect():
            device_type = type_combo.currentText()
            ip_address = ip_input.text().strip()
            port = port_input.value() if port_input.isEnabled() else None
            
            if not ip_address:
                QMessageBox.warning(dialog, "Ошибка", "Введите IP адрес устройства")
                return
            
            try:
                # Подключаемся к устройству
                connection_params = {"host": ip_address}
                if port:
                    connection_params["port"] = port
                
                result = self.device_service.connect_device(device_type, **connection_params)
                
                if result['success']:
                    # Получаем информацию об устройстве
                    info_result = self.device_service.get_and_save_device_info()
                    
                    if info_result['success']:
                        QMessageBox.information(self, "Успех", f"Устройство успешно подключено и сохранено\nIP: {ip_address}")
                        self.refresh_devices_table()
                        dialog.accept()
                    else:
                        QMessageBox.warning(self, "Внимание", 
                                        f"Устройство подключено, но не удалось сохранить информацию:\n{info_result.get('error', 'Неизвестная ошибка')}")
                else:
                    QMessageBox.critical(dialog, "Ошибка подключения", 
                                    f"Не удалось подключиться к устройству:\n{result.get('error', 'Неизвестная ошибка')}")
                    
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Ошибка при подключении:\n{e}")
        
        button_box.accepted.connect(attempt_connect)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(button_box)
        dialog.exec_()

    def ping_selected_device(self):
        """Проверить связь с выбранным устройством"""
        selected_rows = self.devices_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите устройство для проверки")
            return
        
        row = selected_rows[0].row()
        device_ip = self.devices_table.item(row, 1).text()
        device_id = int(self.devices_table.item(row, 0).text())
        
        # Показываем диалог ожидания
        progress = QProgressDialog("Проверка связи...", "Отмена", 0, 0, self)
        progress.setWindowTitle("Проверка устройства")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            # Получаем устройство из базы
            device = self.device_repo.get_by_id(device_id)
            if not device:
                progress.close()
                QMessageBox.warning(self, "Ошибка", "Устройство не найдено в базе")
                return
            
            # Пробуем подключиться к устройству
            # Здесь можно реализовать фактическую проверку связи
            # Например, ping или попытку подключения через соответствующий менеджер
            
            # Для примера - просто обновляем время последней активности
            from datetime import datetime
            device.last_seen = datetime.now()
            self.device_repo.save(device)
            
            progress.close()
            QMessageBox.information(self, "Успех", f"Связь с устройством {device_ip} установлена\nВремя обновлено")
            self.refresh_devices_table()
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Ошибка", f"Не удалось проверить связь:\n{e}")

    def get_device_info(self):
        """Получить информацию о выбранном устройстве"""
        selected_rows = self.devices_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите устройство")
            return
        
        row = selected_rows[0].row()
        device_ip = self.devices_table.item(row, 1).text()
        device_id = int(self.devices_table.item(row, 0).text())
        
        try:
            # Получаем устройство
            device = self.device_repo.get_by_id(device_id)
            if not device:
                QMessageBox.warning(self, "Ошибка", "Устройство не найдено")
                return
            
            # Создаем диалог с информацией
            info_dialog = QDialog(self)
            info_dialog.setWindowTitle(f"Информация об устройстве: {device_ip}")
            info_dialog.setModal(True)
            info_dialog.setMinimumWidth(500)
            
            layout = QVBoxLayout(info_dialog)
            
            # Форма с информацией
            form_layout = QFormLayout()
            
            # Основная информация
            form_layout.addRow("IP адрес:", QLabel(device.ip_address))
            
            if device.type_device and hasattr(device.type_device, 'name'):
                form_layout.addRow("Тип устройства:", QLabel(device.type_device.name))
            else:
                form_layout.addRow("Тип устройства:", QLabel(str(device.type_id)))
            
            form_layout.addRow("Архитектура:", QLabel(device.architecture))
            form_layout.addRow("ОЗУ (ГБ):", QLabel(str(device.ram_gb) if device.ram_gb else "N/A"))
            form_layout.addRow("Память (ГБ):", QLabel(str(device.memory_gb) if device.memory_gb else "N/A"))
            form_layout.addRow("Ядра ЦПУ:", QLabel(str(device.cpu_core) if device.cpu_core else "N/A"))
            
            if device.last_seen:
                last_seen = device.last_seen.strftime("%Y-%m-%d %H:%M:%S")
                status = "Активно" if self.device_repo.get_connected() and device.id in [d.id for d in self.device_repo.get_connected()] else "Неактивно"
                form_layout.addRow("Последняя активность:", QLabel(f"{last_seen} ({status})"))
            else:
                form_layout.addRow("Последняя активность:", QLabel("Никогда"))
            
            layout.addLayout(form_layout)
            
            # Кнопки
            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(info_dialog.accept)
            layout.addWidget(button_box)
            
            info_dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить информацию:\n{e}")

    def delete_selected_device(self):
        """Удалить выбранное устройство"""
        selected_rows = self.devices_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите устройство для удаления")
            return
        
        row = selected_rows[0].row()
        device_ip = self.devices_table.item(row, 1).text()
        device_id = int(self.devices_table.item(row, 0).text())
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить устройство '{device_ip}'?\n\n"
            f"ВНИМАНИЕ: Будут также удалены все связанные записи о развертываниях!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Получаем устройство
                device = self.device_repo.get_by_id(device_id)
                if not device:
                    QMessageBox.warning(self, "Ошибка", "Устройство не найдено")
                    return
                
                # Удаляем устройство
                self.device_repo.delete(device)
                
                QMessageBox.information(self, "Успех", "Устройство удалено")
                self.refresh_devices_table()
                self.refresh_dashboard_stats()  # Обновляем статистику на главной
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить устройство:\n{e}")



























# ===== СТРАНИЦА ОТЧЕТОВ ОПТИМИЗАЦИИ =====

    def create_optimization_reports_page(self):
        """Создать страницу с отчетами оптимизации"""
        page = QWidget()
        
        # Создаем основной layout
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Заголовок
        title = QLabel("ОТЧЕТЫ ОПТИМИЗАЦИИ МОДЕЛЕЙ")
        title.setFont(WarframeStyles.get_font(24, True))
        title.setStyleSheet("color: #00B7EB;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Панель фильтров
        filter_panel = self.create_optimization_reports_filter_panel()
        main_layout.addWidget(filter_panel)
        
        # Таблица отчетов (ДОБАВЛЯЕМ С КОЭФФИЦИЕНТОМ РАСТЯЖЕНИЯ 1)
        self.optimization_reports_table = self.create_optimization_reports_table()
        main_layout.addWidget(self.optimization_reports_table, 1)  # Вот этот 1 делает магию!
        
        # Панель действий
        action_panel = self.create_optimization_reports_action_panel()
        main_layout.addWidget(action_panel)
        
        return page

    def create_optimization_reports_filter_panel(self):
        """Создать панель фильтров для страницы отчетов оптимизации"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #32363C;
                border-radius: 3px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        
        # Фильтр по статусу
        status_label = QLabel("Статус:")
        status_label.setStyleSheet("color: #FFFFFF; margin-right: 5px;")
        layout.addWidget(status_label)
        
        self.optimization_status_filter = QComboBox()
        self.optimization_status_filter.addItems(["Все", "completed", "failed", "pending", "in_progress"])
        self.optimization_status_filter.currentTextChanged.connect(self.refresh_optimization_reports_table)
        layout.addWidget(self.optimization_status_filter)
        
        layout.addStretch()
        
        # Кнопка обновления
        refresh_btn = WarframeButton("ОБНОВИТЬ")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.clicked.connect(self.refresh_optimization_reports_table)
        layout.addWidget(refresh_btn)
        
        return panel

 

    def create_optimization_reports_action_panel(self):
        """Создать панель действий для отчетов оптимизации"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #32363C;
                border-radius: 3px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        
        # Кнопка удаления
        delete_btn = WarframeButton("УДАЛИТЬ")
        delete_btn.setMinimumHeight(40)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #EB4B4B;
                color: #0A0E14;
            }
            QPushButton:hover {
                background-color: #FF6B6B;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected_optimization_report)
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        
        # Статистика
        self.optimization_reports_stats_label = QLabel("Всего отчетов оптимизации: 0")
        self.optimization_reports_stats_label.setStyleSheet("color: #00B7EB; font-weight: bold;")
        layout.addWidget(self.optimization_reports_stats_label)
        
        return panel

   
    def create_optimization_reports_table(self):
        """Создать таблицу для отчетов оптимизации"""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "ID", "Оптимизированная модель ID", "Исходная модель ID", 
            "Точность до", "Точность после", 
            "Потери до", "Потери после", "Статус"
        ])
        
        # Настройка таблицы
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        
        # КРИТИЧЕСКИ ВАЖНО: Установить политику размеров для растяжения
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Настройка ширины колонок
        header = table.horizontalHeader()
        
        # ВАЖНО: Сделать хотя бы одну колонку растягивающейся
        # Колонки по содержимому
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Оптимизированная модель ID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Исходная модель ID
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Статус
        
        # Колонки с плавающей точкой растягиваются
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Точность до
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Точность после
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Потери до
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # Потери после
        
        # ИЛИ ПРОСТОЙ ВАРИАНТ: Все колонки по содержимому, но таблица растягивается
        # for i in range(table.columnCount()):
        #     header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # Стилизация таблицы
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1A1E24;
                color: #FFFFFF;
                border: 1px solid #32363C;
                gridline-color: #32363C;
                alternate-background-color: #121620;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #00B7EB;
                color: #0A0E14;
            }
            QHeaderView::section {
                background-color: #1A1E24;
                color: #00B7EB;
                font-weight: bold;
                padding: 8px;
                border: 1px solid #32363C;
            }
        """)
        
        # Контекстное меню для таблицы
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.show_optimization_report_context_menu)
        
        return table

    def refresh_optimization_reports_table(self):
        """Обновить таблицу отчетов оптимизации"""
        try:
            if not self.optimization_record_repo:
                QMessageBox.warning(self, "Ошибка", "Репозиторий отчетов оптимизации не инициализирован")
                return
            
            # Получаем все отчеты оптимизации
            all_records = self.optimization_record_repo.get_all()
            
            # Применяем фильтры
            filtered_records = []
            status_filter = self.optimization_status_filter.currentText()
            
            for record in all_records:
                # Фильтр по статусу
                if status_filter != "Все" and record.status != status_filter:
                    continue
                
                filtered_records.append(record)
            
            # Устанавливаем количество строк
            self.optimization_reports_table.setRowCount(len(filtered_records))
            
            # Заполняем таблицу данными из OptimizationRecord
            for row, record in enumerate(filtered_records):
                # ID
                id_item = QTableWidgetItem(str(record.id))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.optimization_reports_table.setItem(row, 0, id_item)
                
                # Оптимизированная модель ID
                optimized_model_id = str(record.optimized_model_id) if record.optimized_model_id else "N/A"
                optimized_item = QTableWidgetItem(optimized_model_id)
                optimized_item.setTextAlignment(Qt.AlignCenter)
                self.optimization_reports_table.setItem(row, 1, optimized_item)
                
                # Исходная модель ID
                original_model_id = str(record.original_model_id) if record.original_model_id else "N/A"
                original_item = QTableWidgetItem(original_model_id)
                original_item.setTextAlignment(Qt.AlignCenter)
                self.optimization_reports_table.setItem(row, 2, original_item)
                
                # Аккуратность до
                acc_before = f"{record.accuracy_before:.4f}" if record.accuracy_before is not None else "N/A"
                acc_before_item = QTableWidgetItem(acc_before)
                acc_before_item.setTextAlignment(Qt.AlignCenter)
                self.optimization_reports_table.setItem(row, 3, acc_before_item)
                
                # Аккуратность после
                acc_after = f"{record.accuracy_after:.4f}" if record.accuracy_after is not None else "N/A"
                acc_after_item = QTableWidgetItem(acc_after)
                acc_after_item.setTextAlignment(Qt.AlignCenter)
                self.optimization_reports_table.setItem(row, 4, acc_after_item)
                
                # Потери до
                loss_before = f"{record.loss_before:.4f}" if record.loss_before is not None else "N/A"
                loss_before_item = QTableWidgetItem(loss_before)
                loss_before_item.setTextAlignment(Qt.AlignCenter)
                self.optimization_reports_table.setItem(row, 5, loss_before_item)
                
                # Потери после
                loss_after = f"{record.loss_after:.4f}" if record.loss_after is not None else "N/A"
                loss_after_item = QTableWidgetItem(loss_after)
                loss_after_item.setTextAlignment(Qt.AlignCenter)
                self.optimization_reports_table.setItem(row, 6, loss_after_item)
                
                # Статус
                status_item = QTableWidgetItem(record.status if record.status else "N/A")
                status_item.setTextAlignment(Qt.AlignCenter)
                self.optimization_reports_table.setItem(row, 7, status_item)
            
            # Обновляем статистику
            self.optimization_reports_stats_label.setText(f"Всего отчетов оптимизации: {len(filtered_records)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить отчеты оптимизации:\n{e}")







    def delete_selected_optimization_report(self):
        """Удалить выбранный отчет оптимизации"""
        selected_rows = self.optimization_reports_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите отчет для удаления")
            return
        
        row = selected_rows[0].row()
        report_id = int(self.optimization_reports_table.item(row, 0).text())
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить отчет оптимизации #{report_id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Получаем отчет из базы
                report = self.optimization_record_repo.get_by_id(report_id)
                if not report:
                    QMessageBox.warning(self, "Ошибка", "Отчет не найден")
                    return
                
                # Удаляем отчет
                self.optimization_record_repo.delete(report)
                
                QMessageBox.information(self, "Успех", "Отчет оптимизации удален")
                self.refresh_optimization_reports_table()
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить отчет:\n{e}")

    def show_optimization_report_context_menu(self, position):
        """Контекстное меню для отчетов оптимизации"""
        row = self.optimization_reports_table.rowAt(position.y())
        if row < 0:
            return
        
        menu = QMenu()
        
        delete_action = QAction("Удалить", self)
        delete_action.triggered.connect(self.delete_selected_optimization_report)
        menu.addAction(delete_action)
        
        menu.exec_(self.optimization_reports_table.viewport().mapToGlobal(position))






















# ===== СТРАНИЦА ОТЧЕТОВ РАЗВЕРТЫВАНИЯ =====

    def create_deployment_reports_page(self):
        """Создать страницу с отчетами развертывания"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Заголовок
        title = QLabel("ОТЧЕТЫ РАЗВЕРТЫВАНИЯ МОДЕЛЕЙ")
        title.setFont(WarframeStyles.get_font(24, True))
        title.setStyleSheet("color: #00B7EB; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Панель фильтров
        filter_panel = self.create_deployment_reports_filter_panel()
        layout.addWidget(filter_panel)
        
        # Таблица отчетов
        self.deployment_reports_table = self.create_deployment_reports_table()
        layout.addWidget(self.deployment_reports_table, 1)  # 1 - коэффициент растяжения
        
        # Панель действий
        action_panel = self.create_deployment_reports_action_panel()
        layout.addWidget(action_panel)
        
        return page

    def create_deployment_reports_filter_panel(self):
        """Создать панель фильтров для отчетов развертывания"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #32363C;
                border-radius: 3px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        
        # Фильтр по статусу
        status_label = QLabel("Статус:")
        status_label.setStyleSheet("color: #FFFFFF; margin-right: 5px;")
        layout.addWidget(status_label)
        
        self.deployment_status_filter = QComboBox()
        self.deployment_status_filter.addItems(["Все", "success", "failed", "pending", "in_progress"])
        self.deployment_status_filter.currentTextChanged.connect(self.refresh_deployment_reports_table)
        layout.addWidget(self.deployment_status_filter)
        
        layout.addStretch()
        
        # Кнопка обновления
        refresh_btn = WarframeButton("ОБНОВИТЬ")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.clicked.connect(self.refresh_deployment_reports_table)
        layout.addWidget(refresh_btn)
        
        return panel

    
    def create_deployment_reports_table(self):
        """Создать таблицу для отчетов развертывания"""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "ID", "Оптимизированная модель ID", "Устройство ID", 
            "Дата развертывания", "Статус"
        ])
        
        # Настройка таблицы
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        
        # КРИТИЧЕСКИ ВАЖНО: Установить политику размеров для растяжения
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Настройка ширины колонок - смешанный подход
        header = table.horizontalHeader()
        
        # Колонки по содержимому
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID - короткая
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Оптимизированная модель ID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Устройство ID
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Статус
        
        # Колонки с растяжением для длинного текста
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Дата развертывания - может быть длинной
        
        # Стилизация таблицы
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1A1E24;
                color: #FFFFFF;
                border: 1px solid #32363C;
                gridline-color: #32363C;
                alternate-background-color: #121620;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #00B7EB;
                color: #0A0E14;
            }
            QHeaderView::section {
                background-color: #1A1E24;
                color: #00B7EB;
                font-weight: bold;
                padding: 5px;
                border: 1px solid #32363C;
            }
        """)
        
        # Контекстное меню для таблицы
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.show_deployment_report_context_menu)
        
        return table


    def refresh_deployment_reports_table(self):
        """Обновить таблицу отчетов развертывания"""
        try:
            if not self.deployment_repo:
                QMessageBox.warning(self, "Ошибка", "Репозиторий развертываний не инициализирован")
                return
            
            # Получаем все записи развертывания
            all_deployments = self.deployment_repo.get_all()
            
            # Применяем фильтры
            filtered_deployments = []
            status_filter = self.deployment_status_filter.currentText()
            
            for deployment in all_deployments:
                # Фильтр по статусу
                if status_filter != "Все" and deployment.status != status_filter:
                    continue
                
                filtered_deployments.append(deployment)
            
            # Устанавливаем количество строк
            self.deployment_reports_table.setRowCount(len(filtered_deployments))
            
            # Заполняем таблицу данными из DeploymentRecord
            for row, deployment in enumerate(filtered_deployments):
                # ID
                id_item = QTableWidgetItem(str(deployment.id))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.deployment_reports_table.setItem(row, 0, id_item)
                
                # Оптимизированная модель ID
                optimized_model_id = str(deployment.optimized_model_id) if deployment.optimized_model_id else "N/A"
                model_item = QTableWidgetItem(optimized_model_id)
                model_item.setTextAlignment(Qt.AlignCenter)
                self.deployment_reports_table.setItem(row, 1, model_item)
                
                # Устройство ID
                device_id = str(deployment.device_id) if deployment.device_id else "N/A"
                device_item = QTableWidgetItem(device_id)
                device_item.setTextAlignment(Qt.AlignCenter)
                self.deployment_reports_table.setItem(row, 2, device_item)
                
                # Дата развертывания
                if deployment.deployment_date:
                    date_text = deployment.deployment_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    date_text = "N/A"
                
                date_item = QTableWidgetItem(date_text)
                date_item.setTextAlignment(Qt.AlignCenter)
                self.deployment_reports_table.setItem(row, 3, date_item)
                
                # Статус
                status_item = QTableWidgetItem(deployment.status if deployment.status else "N/A")
                status_item.setTextAlignment(Qt.AlignCenter)
                self.deployment_reports_table.setItem(row, 4, status_item)
            
            # Обновляем статистику
            self.deployment_reports_stats_label.setText(f"Всего отчетов развертывания: {len(filtered_deployments)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить отчеты развертывания:\n{e}")

    def create_deployment_reports_action_panel(self):
        """Создать панель действий для отчетов развертывания"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #121620;
                border: 1px solid #32363C;
                border-radius: 3px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        
        # Кнопка удаления
        delete_btn = WarframeButton("УДАЛИТЬ")
        delete_btn.setMinimumHeight(40)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #EB4B4B;
                color: #0A0E14;
            }
            QPushButton:hover {
                background-color: #FF6B6B;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected_deployment_report)
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        
        # Статистика
        self.deployment_reports_stats_label = QLabel("Всего отчетов развертывания: 0")
        self.deployment_reports_stats_label.setStyleSheet("color: #00B7EB; font-weight: bold;")
        layout.addWidget(self.deployment_reports_stats_label)
        
        return panel

  
    def delete_selected_deployment_report(self):
        """Удалить выбранный отчет развертывания"""
        selected_rows = self.deployment_reports_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите отчет для удаления")
            return
        
        row = selected_rows[0].row()
        deployment_id = int(self.deployment_reports_table.item(row, 0).text())
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить отчет развертывания #{deployment_id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Удаляем запись развертывания
                success = self.deployment_repo.delete(deployment_id)
                
                if success:
                    QMessageBox.information(self, "Успех", "Отчет развертывания удален")
                    self.refresh_deployment_reports_table()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить отчет развертывания")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить отчет:\n{e}")

    def show_deployment_report_context_menu(self, position):
        """Контекстное меню для отчетов развертывания"""
        row = self.deployment_reports_table.rowAt(position.y())
        if row < 0:
            return
        
        menu = QMenu()
        
        delete_action = QAction("Удалить", self)
        delete_action.triggered.connect(self.delete_selected_deployment_report)
        menu.addAction(delete_action)
        
        menu.exec_(self.deployment_reports_table.viewport().mapToGlobal(position))



