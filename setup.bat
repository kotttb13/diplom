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

set MIRROR_URL=https://mirrors.aliyun.com/pypi/simple/
set TRUSTED_HOST=mirrors.aliyun.com

echo 3. Обновление менеджера пакетов pip через зеркало...
python -m pip install --upgrade pip --index-url %MIRROR_URL% --trusted-host %TRUSTED_HOST%
if errorlevel 1 (
    echo Предупреждение: Не удалось обновить pip через алиас-зеркало.
    echo Попытка через резервное зеркало...
    python -m pip install --upgrade pip --index-url https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn
    if errorlevel 1 (
        echo Ошибка: Не удалось обновить pip через доступные зеркала.
        pause
        exit /b 1
    )
)

echo 4. Установка зависимостей из requirements.txt через зеркало...
pip install -r requirements.txt --index-url %MIRROR_URL% --trusted-host %TRUSTED_HOST%
if errorlevel 1 (
    echo Предупреждение: Не удалось установить зависимости через алиас-зеркало.
    echo Попытка через резервное зеркало...
    pip install -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn
    if errorlevel 1 (
        echo Ошибка: Не удалось установить зависимости.
        echo Проверьте requirements.txt и доступность зеркал PyPI.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo   ОКРУЖЕНИЕ УСПЕШНО НАСТРОЕНО!
echo ========================================
echo.
echo Инструкция для запуска:
echo 1. Активируйте окружение: .venv\Scripts\activate.bat
echo 2. Запустите приложение: python main.py
echo.
Pause
