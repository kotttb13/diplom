@echo off
chcp 65001 >nul
echo ========================================
echo   НАСТРОЙКА ОКРУЖЕНИЯ NEURO-OPTIMIZER
echo ========================================
echo.

echo 1. Создание виртуального окружения Python...
python -m venv .venv
if errorlevel 1 (
    echo Ошибка: Не удалось создать виртуальное окружение.
    echo Убедитесь, что Python 3.9+ установлен и добавлен в PATH.
    pause
    exit /b 1
)

echo 2. Активация виртуального окружения...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Ошибка: Не удалось активировать виртуальное окружение.
    pause
    exit /b 1
)

echo 3. Обновление менеджера пакетов pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Предупреждение: Не удалось обновить pip. Продолжение установки...
)

echo 4. Установка зависимостей из requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo Ошибка: Не удалось установить зависимости.
    echo Проверьте наличие файла requirements.txt в текущей директории.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ОКРУЖЕНИЕ УСПЕШНО НАСТРОЕНО!
echo ========================================
echo.
echo Инструкция для запуска:
echo 1. Активируйте окружение: .venv\Scripts\activate.bat
echo 2. Настройте подключение к БД (при необходимости)
echo 3. Запустите приложение: python main.py
echo.
Pause
