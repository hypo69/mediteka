# Проверка, запущен ли скрипт от имени администратора
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "Этот скрипт необходимо запускать от имени администратора."
    return
}

# Путь к папке %LOCALAPPDATA%
$localAppData = [Environment]::GetFolderPath("LocalApplicationData")

# Путь к целевой папке AI Assistant
$targetDir = Join-Path $localAppData "AI Assistant"

# Путь к папке, из которой запущен скрипт
$scriptDir = Split-Path $MyInvocation.MyCommand.Path

# Путь к файлу run.ps1 в целевой директории
$targetRunScriptPath = Join-Path $targetDir "run.ps1"

# Проверка существования целевой директории, и если она есть, то удаляем её
if (Test-Path $targetDir) {
    Write-Host "Удаление существующей директории: $($targetDir)" -ForegroundColor Yellow
    Remove-Item $targetDir -Recurse -Force
}

# Создание целевой директории
Write-Host "Создание директории: $($targetDir)" -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $targetDir

# Копирование содержимого скриптовой директории в целевую, включая поддиректории и файлы, а так же venv
Write-Host "Копирование файлов из $($scriptDir) в $($targetDir)..." -ForegroundColor Green
Copy-Item -Path "$scriptDir\*" -Destination $targetDir -Recurse -Force

# Получаем текущее значение переменной PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Проверяем, что путь к целевой директории отсутствует в PATH
if ($currentPath -notcontains $targetDir) {
     # Добавляем путь к целевой директории в переменную PATH
    $newPath = "$currentPath;$targetDir"
    Write-Host "Добавление $($targetDir) в PATH..." -ForegroundColor Green
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")

    Write-Host "Обновление переменной окружения PATH" -ForegroundColor Green
    Write-Host "Пожалуйста, перезапустите ваш терминал, чтобы изменения вступили в силу" -ForegroundColor Yellow
    # Обновляем переменную окружения PATH
    # $env:Path = $newPath

} else {
    Write-Host "Путь $($targetDir) уже присутствует в PATH" -ForegroundColor Yellow
}

# Создание ключа реестра для автозапуска
$appName = "AI Assistant"
$appPath =  "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$targetRunScriptPath`""
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"

Write-Host "Установка автозапуска $($appName)..." -ForegroundColor Green
New-ItemProperty -Path $regPath -Name $appName -Value $appPath -PropertyType String -Force

# Создание алиаса для команды 'ai'
$aliasName = "ai"
$aliasValue = "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$targetRunScriptPath`""
$aliasFunction = "function $aliasName { & $aliasValue }"
Write-Host "Создание алиаса для команды 'ai'..." -ForegroundColor Green

if (Get-Alias -Name $aliasName -ErrorAction SilentlyContinue) {
    Write-Host "Алиас '$aliasName' уже существует. Переопределение." -ForegroundColor Yellow
    Set-Alias -Name $aliasName -Value $aliasValue -Force
} else {
   New-Alias -Name $aliasName -Value $aliasValue
   
   # Сохраняем алиас в профиль
    Write-Host "Сохранение алиаса в профиль PowerShell" -ForegroundColor Green
    $profile =  Split-Path -Parent $PROFILE
    if (!(Test-Path $profile)){
      New-Item -ItemType Directory -Force -Path $profile
    }
     Add-Content $PROFILE $aliasFunction
}


Write-Host "Копирование завершено!" -ForegroundColor Green
Write-Host "Установка завершена. Директория AI Assistant находится по адресу $($targetDir)" -ForegroundColor Green
Write-Host "Для использования команды 'ai', пожалуйста, перезапустите ваш терминал и профиль PowerShell" -ForegroundColor Yellow