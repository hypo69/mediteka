# PowerShell скрипт для запуска консоли Code Helper

# Проверяем наличие виртуального окружения
$venvPath = Join-Path $PSScriptRoot "venv"
if (-not (Test-Path $venvPath)) {
    Write-Error "Виртуальное окружение venv не найдено. Пожалуйста, запустите установку."
    exit 1
}

# Активируем окружение и запускаем чат
& "$venvPath\Scripts\python.exe" "plugins/code_helper/rag/chat_interface.py"
