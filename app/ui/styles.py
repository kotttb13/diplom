from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette, QFont

class WarframeStyles:
    
    COLORS = {
        'background': QColor(10, 14, 20),
        'background_secondary': QColor(18, 22, 28),
        'background_tertiary': QColor(26, 30, 36),
        'accent_primary': QColor(0, 183, 235),     
        'accent_secondary': QColor(235, 75, 75),   
        'accent_success': QColor(46, 204, 113),  
        'text_primary': QColor(240, 240, 240),
        'text_secondary': QColor(180, 180, 180),
        'text_disabled': QColor(100, 100, 100),
        'border': QColor(50, 54, 60),
        'border_highlight': QColor(0, 183, 235, 100),
        'warning': QColor(241, 196, 15),
        'error': QColor(231, 76, 60),
    }
    
    @staticmethod
    def get_stylesheet():
        colors = WarframeStyles.COLORS
        
        return f"""
        /* Основные стили */
        QMainWindow {{
            background-color: {colors['background'].name()};
            color: {colors['text_primary'].name()};
        }}
        
        QWidget {{
            background-color: {colors['background'].name()};
            color: {colors['text_primary'].name()};
            font-family: 'Rajdhani', 'Segoe UI', sans-serif;
        }}
        
        /* Текст */
        QLabel {{
            color: {colors['text_primary'].name()};
            font-size: 12px;
        }}
        
        QLabel.title {{
            font-size: 24px;
            font-weight: bold;
            color: {colors['accent_primary'].name()};
        }}
        
        QLabel.subtitle {{
            font-size: 16px;
            color: {colors['text_secondary'].name()};
        }}
        
        /* Кнопки в стиле Warframe */
        QPushButton {{
            background-color: {colors['background_tertiary'].name()};
            border: 1px solid {colors['border'].name()};
            border-radius: 3px;
            padding: 8px 16px;
            color: {colors['text_primary'].name()};
            font-weight: bold;
            font-size: 12px;
            min-width: 100px;
            min-height: 32px;
        }}
        
        QPushButton:hover {{
            background-color: {colors['background_secondary'].name()};
            border: 1px solid {colors['accent_primary'].name()};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['accent_primary'].name()};
            color: {colors['background'].name()};
        }}
        
        QPushButton:disabled {{
            background-color: {colors['background_secondary'].name()};
            color: {colors['text_disabled'].name()};
            border: 1px solid {colors['border'].name()};
        }}
        
        QPushButton.primary {{
            background-color: {colors['accent_primary'].name()};
            color: {colors['background'].name()};
            border: none;
        }}
        
        QPushButton.danger {{
            background-color: {colors['accent_secondary'].name()};
            color: {colors['background'].name()};
            border: none;
        }}
        
        QPushButton.success {{
            background-color: {colors['accent_success'].name()};
            color: {colors['background'].name()};
            border: none;
        }}
        
        /* Поля ввода */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors['background_secondary'].name()};
            border: 1px solid {colors['border'].name()};
            border-radius: 3px;
            padding: 6px 8px;
            color: {colors['text_primary'].name()};
            selection-background-color: {colors['accent_primary'].name()};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {colors['accent_primary'].name()};
        }}
        
        /* Выпадающие списки */
        QComboBox {{
            background-color: {colors['background_secondary'].name()};
            border: 1px solid {colors['border'].name()};
            border-radius: 3px;
            padding: 6px 8px;
            color: {colors['text_primary'].name()};
            min-width: 120px;
        }}
        
        QComboBox::drop-down {{
            border: none;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors['background_secondary'].name()};
            color: {colors['text_primary'].name()};
            selection-background-color: {colors['accent_primary'].name()};
        }}
        
        /* Таблицы */
        QTableView {{
            background-color: {colors['background_secondary'].name()};
            border: 1px solid {colors['border'].name()};
            gridline-color: {colors['border'].name()};
            color: {colors['text_primary'].name()};
            font-size: 11px;
        }}
        
        QHeaderView::section {{
            background-color: {colors['background_tertiary'].name()};
            color: {colors['text_primary'].name()};
            padding: 6px;
            border: none;
            font-weight: bold;
        }}
        
        QTableView::item {{
            padding: 4px;
            border-bottom: 1px solid {colors['border'].name()};
        }}
        
        QTableView::item:selected {{
            background-color: {colors['accent_primary'].name()};
            color: {colors['background'].name()};
        }}
        
        /* Прогресс-бары */
        QProgressBar {{
            border: 1px solid {colors['border'].name()};
            border-radius: 3px;
            background-color: {colors['background_secondary'].name()};
            text-align: center;
            color: {colors['text_primary'].name()};
        }}
        
        QProgressBar::chunk {{
            background-color: {colors['accent_primary'].name()};
            border-radius: 2px;
        }}
        
        /* Вкладки */
        QTabWidget::pane {{
            border: 1px solid {colors['border'].name()};
            background-color: {colors['background_secondary'].name()};
        }}
        
        QTabBar::tab {{
            background-color: {colors['background_tertiary'].name()};
            color: {colors['text_secondary'].name()};
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid {colors['border'].name()};
            border-bottom: none;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['background_secondary'].name()};
            color: {colors['accent_primary'].name()};
            border-bottom: 2px solid {colors['accent_primary'].name()};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {colors['background_secondary'].name()};
            color: {colors['text_primary'].name()};
        }}
        
        /* Панели */
        QFrame.panel {{
            background-color: {colors['background_secondary'].name()};
            border: 1px solid {colors['border'].name()};
            border-radius: 4px;
            padding: 12px;
        }}
        
        /* Уведомления и ошибки */
        QFrame.notification {{
            background-color: {colors['warning'].name()}20;
            border: 1px solid {colors['warning'].name()};
            border-radius: 3px;
            padding: 12px;
        }}
        
        QFrame.error {{
            background-color: {colors['error'].name()}20;
            border: 1px solid {colors['error'].name()};
            border-radius: 3px;
            padding: 12px;
        }}
        
        QFrame.success {{
            background-color: {colors['accent_success'].name()}20;
            border: 1px solid {colors['accent_success'].name()};
            border-radius: 3px;
            padding: 12px;
        }}
        """
    
    @staticmethod
    def get_font(size=10, bold=False):
        """Получить шрифт Warframe"""
        font = QFont()
        font.setFamily("Rajdhani")
        font.setPointSize(size)
        font.setBold(bold)
        return font
