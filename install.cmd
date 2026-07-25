@echo off
setlocal

:: Путь к папке %LOCALAPPDATA%
echo Получение пути к папке LOCALAPPDATA
set "localAppData=%LOCALAPPDATA%"

:: Путь к целевой папке AI Assistant
echo Формирование пути к целевой папке AI Assistant
set "targetDir=%localAppData%\AI Assistant"

:: Путь к папке, из которой запущен скрипт
echo Получение пути к папке, из которой запущен скрипт
set "scriptDir=%~dp0"

:: Проверка существования целевой директории, и если она есть, то удаляем её
echo Проверка существования целевой директории
if exist "%targetDir%" (
    echo Удаление существующей директории: "%targetDir%"
    rmdir /s /q "%targetDir%"
)

:: Создание целевой директории
echo Создание директории: "%targetDir%"
mkdir "%targetDir%"

:: Копирование содержимого скриптовой директории в целевую, включая поддиректории и файлы, а так же venv
echo Копирование файлов из "%scriptDir%" в "%targetDir%"...
xcopy "%scriptDir%" "%targetDir%" /s /e /y /i

:: Получаем текущее значение переменной PATH
echo Получение текущего значения переменной PATH
for /f "tokens=2* delims= " %%a in ('reg query "HKCU\Environment" /v Path') do set "currentPath=%%b"

:: Проверяем, что путь к целевой директории отсутствует в PATH
echo Проверяем, что путь к целевой директории отсутствует в PATH
echo %currentPath% | findstr /i "%targetDir%" >nul
if errorlevel 1 (
    :: Добавляем путь к целевой директории в переменную PATH
    set "newPath=%currentPath%;%targetDir%"
    echo Добавление "%targetDir%" в PATH...
    setx Path "%newPath%" /m

    echo "Пожалуйста, перезапустите ваш терминал, чтобы изменения вступили в силу"
) else (
    echo "Путь "%targetDir%" уже присутствует в PATH"
)

echo Копирование завершено!
echo Установка завершена. Директория AI Assistant находится по адресу: %targetDir%
echo "Для использования команды 'ai', пожалуйста, перезапустите ваш терминал"

pause
endlocal