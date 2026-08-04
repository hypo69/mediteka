# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI Foundry Smart Launcher (Умный запуск)
# =============================================================================
# Описание:
#   Основная точка входа для запуска сервера FastAPI Foundry.
#   При первом запуске — автоматическая установка зависимостей через install.ps1.
#   Загрузка переменных .env, обнаружение или запуск службы Foundry AI,
#   опциональный запуск серверов llama.cpp и MkDocs, финальный запуск FastAPI.
#
# Примеры:
#   powershell -ExecutionPolicy Bypass -File .\start.ps1
#   powershell -ExecutionPolicy Bypass -File .\start.ps1 -Config config.json
#
# File: start.ps1
# Project: Ai Assistant
# Package: FastApiFoundry
# Version: 0.7.1
# Author: hypo69
# Copyright: © 2025 - 2026 hypo69
# =============================================================================

# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Экстренная очистка временных файлов
# =============================================================================
# Описание:
#   Поиск и удаление папок __pycache__, temp/tmp директорий и временных файлов.
#   Используется автоматически при критическом уровне места на диске.
#
# File: scripts/Clear-TempFiles.ps1
# Project: Ai Assistant
# Version: 1.1.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

[CmdletBinding()]
param(
    [switch]$Force,
    [switch]$WhatIf,
    [int]$RetentionDays = 60
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogFile = Join-Path $ProjectRoot "logs\cleanup.log"

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$Timestamp] [AUTO-CLEANUP] $Message" | Add-Content -Path $LogFile -Encoding UTF8 -ErrorAction SilentlyContinue
}

Write-Host "🧹 Запуск экстренной очистки в $ProjectRoot..." -ForegroundColor Yellow

# 1. Удаление __pycache__
$pycache = Get-ChildItem -Path $ProjectRoot -Filter "__pycache__" -Recurse -Directory
foreach ($dir in $pycache) {
    if ($WhatIf) { Write-Host "  [WHATIF] Будет удален кэш: $($dir.FullName)" }
    else { 
        Remove-Item $dir.FullName -Recurse -Force
        Write-Log "Удален кэш Python: $($dir.FullName)"
    }
}

# 2. Удаление временных папок (temp, tmp) в корне и src
$tempDirs = Get-ChildItem -Path $ProjectRoot -Include "temp","tmp" -Recurse -Directory | Where-Object { $_.FullName -notmatch "venv" }
foreach ($dir in $tempDirs) {
    if ($WhatIf) { Write-Host "  [WHATIF] Будет удалена папка temp: $($dir.FullName)" }
    else { 
        Remove-Item $dir.FullName -Recurse -Force
        Write-Log "Удалена временная папка: $($dir.FullName)"
    }
}

# 3. Удаление временных файлов (*.tmp, *.bak, autostart_*.tmp)
$tempFiles = Get-ChildItem -Path $ProjectRoot -Include "*.tmp","*.bak","*.log.old" -Recurse -File | Where-Object { $_.FullName -notmatch "venv" }
foreach ($file in $tempFiles) {
    if ($WhatIf) { Write-Host "  [WHATIF] Будет удален файл: $($file.FullName)" }
    else { 
        Remove-Item $file.FullName -Force
        Write-Log "Удален временный файл: $($file.FullName)"
    }
}

# 4. Очистка папки релизов (temp_staging если осталась)
$staging = Join-Path $ProjectRoot "release\temp_staging"
if (Test-Path $staging) {
    if (-not $WhatIf) { 
        Remove-Item $staging -Recurse -Force 
        Write-Log "Очищена папка стейджинга релизов."
    }
}

# 5. Архивация и очистка старых RAG индексов
# По умолчанию индексы хранятся в ~/.ai-assist/rag/
$RagDir = [System.IO.Path]::Combine($env:USERPROFILE, ".ai-assist", "rag")
if (Test-Path $RagDir) {
    $LimitDate = (Get-Date).AddDays(-$RetentionDays)
    $OldIndices = Get-ChildItem -Path $RagDir -Directory | Where-Object { $_.LastWriteTime -lt $LimitDate }
    foreach ($idx in $OldIndices) {
        if ($WhatIf) { 
            Write-Host "  [WHATIF] Будет архивирован и удален старый RAG индекс: $($idx.FullName)" 
        } else {
            # Попытка архивации перед удалением
            $ArchiveScript = Join-Path $PSScriptRoot "Archive-RagIndices.ps1"
            if (Test-Path $ArchiveScript) {
                & $ArchiveScript -IndexPath $idx.FullName
                Write-Log "Индекс архивирован: $($idx.FullName)"
            }

            Remove-Item $idx.FullName -Recurse -Force
            Write-Log "Удален старый RAG индекс: $($idx.FullName) (не использовался > $RetentionDays дней)"
        }
    }
}

Write-Host "✨ Экстренная очистка завершена." -ForegroundColor Green
exit 0
    # Path to the JSON configuration file (relative to the project root)
    [string]$Config = 'config.json'
)

# Настройка режима обработки некритических ошибок
$ErrorActionPreference = 'Continue'
$Root = $PSScriptRoot

Write-Host '🚀 FastAPI Foundry Smart Launcher - Запуск' -ForegroundColor Cyan
Write-Host ('=' * 60) -ForegroundColor Cyan

# -----------------------------------------------------------------------------
# Этап -1: Мониторинг свободного места на диске
# -----------------------------------------------------------------------------
$MonitorDiskSpaceScript = "$Root\scripts\Monitor-DiskSpace.ps1"
if (Test-Path $MonitorDiskSpaceScript) {
    try {
        & $MonitorDiskSpaceScript
    } catch {
        Write-Host "⚠️ Проверка свободного места на диске завершилась с ошибкой: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host '💡 scripts/Monitor-DiskSpace.ps1 not found — disk space check skipped.' -ForegroundColor Gray
}
# -----------------------------------------------------------------------------
# Этап 0: Проверка обновлений (git tag-based)
# -----------------------------------------------------------------------------

$UpdateScript = "$Root\scripts\Update-Project.ps1"
if (Test-Path $UpdateScript) {
    try {
        # Execution of the update script
        & $UpdateScript
    } catch {
        Write-Host "⚠️ Проверка обновлений завершилась с ошибкой: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host '💡 scripts/Update-Project.ps1 not found — update check skipped.' -ForegroundColor Gray
}

# -----------------------------------------------------------------------------
# Этап 1: Проверка зависимостей и установка
# -----------------------------------------------------------------------------

# Создание директории архива при инсталляции
# Creation of the archive directory during installation
if (-not (Test-Path "$Root\archive")) {
    New-Item -ItemType Directory -Path "$Root\archive" -Force | Out-Null
}

<#
.SYNOPSIS
    Активация виртуального окружения Python.
    Настройка путей для работы с pip и python внутри venv.
#>

# Активация виртуального окружения

$ActivateScript = "$Root\venv\Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    . $ActivateScript
    Write-Host '✅ venv активирован' -ForegroundColor Green
} else {
    Write-Host '⚠️ venv/Scripts/Activate.ps1 не найден' -ForegroundColor Yellow
}

# Определение пути к интерпретатору
$venvPath = "$Root\venv\Scripts\python.exe"
if (-not (Test-Path $venvPath)) {
    $venvPath = "$Root\venv\Scripts\python311.exe"
}

if (-not (Test-Path $venvPath)) {
    Write-Host '📦 First launch - dependency installation...' -ForegroundColor Yellow
    Write-Host 'Это может занять несколько минут...' -ForegroundColor Yellow
    
    if (Test-Path "$Root\install.ps1") {
        try {
            & "$Root\install.ps1"
            Write-Host '✅ Установка завершена!' -ForegroundColor Green
        } catch {
            Write-Host "❌ Ошибка установки: $_" -ForegroundColor Red
            Write-Host 'Попробуйте запустить install.ps1 вручную' -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host '❌ install.ps1 не найден!' -ForegroundColor Red
        Write-Host 'Создайте venv вручную: python311 -m venv venv' -ForegroundColor Yellow
        exit 1
    }
}

# -----------------------------------------------------------------------------
# Этап 2: Загрузка переменных окружения
# -----------------------------------------------------------------------------

<#
.SYNOPSIS
    Загрузка переменных окружения из файла.
    Чтение .env файла и экспорт пар КЛЮЧ=ЗНАЧЕНИЕ.
.PARAMETER EnvPath
    Полный путь к файлу .env.
.NOTES
    - Пропуск пустых строк и комментариев (#).
    - Очистка кавычек вокруг значений.
    - Маскировка секретных данных (PASSWORD, SECRET, KEY, TOKEN, PAT) в выводе.
.OUTPUTS
    Переменные устанавливаются в [System.Environment].
#>
function Load-EnvFile {
    param([string]$EnvPath)
    
    $envVarsCount = 0
    $line = $null
    
    if (-not (Test-Path $EnvPath -PathType Leaf)) {
        if (Test-Path $EnvPath -PathType Container) { 
            Write-Host "⚠️ .env — это папка, а не файл: $EnvPath" -ForegroundColor Yellow
        } else {
            Write-Host "⚠️ Файл .env не найден: $EnvPath" -ForegroundColor Yellow
            Write-Host "💡 Создайте .env на основе .env.example" -ForegroundColor Cyan
        }
        return
    }
    
    Write-Host '⚙️ Loading .env variables...' -ForegroundColor Gray
    
    try {
        Get-Content $EnvPath | ForEach-Object {
            $line = $_.Trim()
            
            if ($line -and -not $line.StartsWith('#')) {
                if ($line -match '^([^=]+)=(.*)$') {
                    $key   = $matches[1].Trim()
                    $value = $matches[2].Trim()
                    
                    if ($value.StartsWith('"') -and $value.EndsWith('"')) {
                        $value = $value.Substring(1, $value.Length - 2)
                    }
                    if ($value.StartsWith("'") -and $value.EndsWith("'")) {
                        $value = $value.Substring(1, $value.Length - 2)
                    }
                    
                    [System.Environment]::SetEnvironmentVariable($key, $value)
                    $envVarsCount++
                    
                    if ($key -notmatch '(PASSWORD|SECRET|KEY|TOKEN|PAT)') {
                        Write-Host "  ✓ $key = $value" -ForegroundColor DarkGray
                    } else {
                        Write-Host "  ✓ $key = ***" -ForegroundColor DarkGray
                    }
                }
            }
        }
        Write-Host "✅ Environment variables loaded: $envVarsCount" -ForegroundColor Green
    } catch {
        Write-Host "❌ Ошибка загрузки .env: $_" -ForegroundColor Red
    }
}

Load-EnvFile "$Root\.env"

function Get-LauncherConfig {
    param([string]$ConfigPath)

    try {
        return Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Write-Host "⚠️ Не удалось прочитать конфигурацию запуска: $_" -ForegroundColor Yellow
        return $null
    }
}

$LauncherConfigPath = Join-Path $Root $Config
$LauncherConfig = Get-LauncherConfig $LauncherConfigPath

<#
.SYNOPSIS
    Проверка доступности Foundry CLI.
    Поиск утилиты 'foundry' в системном PATH.
.OUTPUTS
    bool — True если утилита найдена.
#>
function Test-FoundryCli {
    try {
        Get-Command foundry -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

<#
.SYNOPSIS
    Поиск TCP-порта службы инференса Foundry.
    Обнаружение активного порта Foundry AI.
.DESCRIPTION
    Поиск процесса 'Inference.Service.Agent', сканирование портов LISTENING
    и проверка через API запрос к /v1/models.
.OUTPUTS
    string — Номер порта или $null.
#>
function Get-FoundryPort {
    # First, try to find the Foundry process by name
    $foundryProcess = Get-Process | Where-Object { $_.ProcessName -like "Inference.Service.Agent*" }
    
    # Fallback: if no process found by name, try to find by module path
    if (-not $foundryProcess) {
        $foundryProcess = Get-Process | Where-Object { 
            $_.Path -like "*Inference.Service.Agent*" -or 
            $_.Path -like "*foundry*" -and $_.Path -like "*.exe"
        } -ErrorAction SilentlyContinue
    }
    
    if (-not $foundryProcess) { 
        Write-Host "⚠️ Foundry process not found" -ForegroundColor Yellow
        return $null 
    }
    
    Write-Host "🔍 Foundry process found: $($foundryProcess.ProcessName) (PID: $($foundryProcess.Id))" -ForegroundColor Cyan
    
    # Get all listening ports for this process
    $netstatOutput = netstat -ano | Select-String "$($foundryProcess.Id)" | Select-String "LISTENING"
    
    if (-not $netstatOutput) {
        Write-Host "⚠️ No listening ports found for Foundry process" -ForegroundColor Yellow
        return $null
    }
    
    Write-Host "🔍 Found $($netstatOutput.Count) listening port(s)" -ForegroundColor Cyan
    
    foreach ($line in $netstatOutput) {
        if ($line -match ':(\d+)\s') {
            $port = $matches[1]
            Write-Host "🔍 Checking port $port..." -ForegroundColor Cyan
            
            try {
                $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/v1/models" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-Host "✅ API Foundry найден на порту $port" -ForegroundColor Green
                    return $port
                } else {
                    Write-Host "⚠️ Port $port returned status $($response.StatusCode)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "⚠️ Port $port health check failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
    
    Write-Host "❌ No valid Foundry port found" -ForegroundColor Red
    return $null
}

# -----------------------------------------------------------------------------
# Этап 3: Обнаружение или запуск службы Foundry AI
# -----------------------------------------------------------------------------

Write-Host '🔍 Local Foundry check...' -ForegroundColor Cyan

$foundryCfg = if ($LauncherConfig) { $LauncherConfig.foundry_ai } else { $null }
$foundryAutoStart = $false
if ($foundryCfg -and $foundryCfg.PSObject.Properties['auto_start']) {
    $foundryAutoStart = [bool]$foundryCfg.auto_start
}

# Auto-enable Foundry if default_model points to a foundry:: model
if (-not $foundryAutoStart -and $foundryCfg) {
    $defModel = [string]($foundryCfg.default_model)
    if ($defModel -and (-not $defModel.StartsWith('hf::') -and -not $defModel.StartsWith('llama::') -and -not $defModel.StartsWith('ollama::') -and -not $defModel.StartsWith('lmstudio::'))) {
        Write-Host "💡 Foundry: default_model='$defModel' — auto_start автоматически включен (модель требует Foundry)." -ForegroundColor Cyan
        $foundryAutoStart = $true
    }
}

$foundryPort = Get-FoundryPort

if ($foundryPort) {
    Write-Host "✅ Foundry уже запущен на порту $foundryPort" -ForegroundColor Green
    $env:FOUNDRY_DYNAMIC_PORT = $foundryPort
} elseif (-not $foundryAutoStart) {
    Write-Host '💡 Foundry: auto_start=false в config.json — пропуск запуска службы.' -ForegroundColor Gray
} else {
    if (-not (Test-FoundryCli)) {
        Write-Host '⚠️ Foundry CLI not found. AI features might be limited.' -ForegroundColor Yellow
    } else {
        Write-Host '🚀 Starting Foundry service...' -ForegroundColor Yellow
        
        try {
            # Foundry execution in minimized window
            Start-Process -FilePath "foundry" -ArgumentList "service", "start" -WindowStyle Minimized -NoNewWindow:$false
            Write-Host "Выполнение команды запуска службы Foundry" -ForegroundColor Gray
            
            # Опрос готовности Foundry (таймаут 20 секунд)
            for ($i = 1; $i -le 10; $i++) {
                Start-Sleep 2
                $foundryPort = Get-FoundryPort
                if ($foundryPort) {
                    Write-Host "✅ Foundry запущен на порту $foundryPort" -ForegroundColor Green
                    $env:FOUNDRY_DYNAMIC_PORT = $foundryPort
                    break
                }
                Write-Host "⏳ Ожидание запуска Foundry... ($i/10)" -ForegroundColor Gray
            }
            
            if (-not $foundryPort) {
                Write-Host "❌ Ошибка запуска Foundry или порт не найден" -ForegroundColor Red
                Write-Host '⚠️ Продолжение работы без поддержки AI.' -ForegroundColor Yellow
            } else {
                # Apply config.json settings to Foundry after successful start
                try {
                    $foundryCacheDir = $null
                    if ($LauncherConfig -and $LauncherConfig.directories -and $LauncherConfig.directories.models) {
                        $foundryCacheDir = [string]$LauncherConfig.directories.models
                    }
                    if ($foundryCacheDir -and (Test-FoundryCli)) {
                        $resolvedCacheDir = $foundryCacheDir -replace '^~', $env:USERPROFILE
                        Write-Host "⚙️ Foundry config: cache-dir = $resolvedCacheDir" -ForegroundColor Gray
                        Start-Process -FilePath 'foundry' -ArgumentList 'config', 'set', 'cache-dir', $resolvedCacheDir -WindowStyle Hidden -Wait -ErrorAction SilentlyContinue
                    }
                } catch {
                    Write-Host "⚠️ Foundry config apply failed: $_" -ForegroundColor Yellow
                }
            }
        } catch {
            Write-Host "❌ Сбой при запуске Foundry: $_" -ForegroundColor Red
            Write-Host '⚠️ Продолжение работы без поддержки AI.' -ForegroundColor Yellow
        }
    }
}

# Экспорт базового URL для FastAPI
if ($foundryPort) {
    $env:FOUNDRY_BASE_URL = "http://localhost:$foundryPort/v1/"
    Write-Host "🔗 FOUNDRY_BASE_URL = $env:FOUNDRY_BASE_URL" -ForegroundColor Green

    $foundryStartupModels = @()
    if ($foundryCfg -and $foundryCfg.startup_models) {
        $foundryStartupModels = @($foundryCfg.startup_models | Where-Object { $_ -and -not ([string]$_).StartsWith('hf::') -and -not ([string]$_).StartsWith('llama::') -and -not ([string]$_).StartsWith('ollama::') })
    } elseif ($foundryCfg -and $foundryCfg.auto_load_default -and $foundryCfg.default_model) {
        $defaultFoundryModel = [string]$foundryCfg.default_model
        if ($defaultFoundryModel.StartsWith('foundry::')) {
            $defaultFoundryModel = $defaultFoundryModel.Substring('foundry::'.Length)
        }
        if ($defaultFoundryModel -and -not $defaultFoundryModel.StartsWith('hf::') -and -not $defaultFoundryModel.StartsWith('llama::') -and -not $defaultFoundryModel.StartsWith('ollama::')) {
            $foundryStartupModels = @($defaultFoundryModel)
        }
    }

    $foundryStartupMode = if ($foundryCfg -and $foundryCfg.startup_model_mode) { [string]$foundryCfg.startup_model_mode } else { "active" }
    if ($foundryStartupModels.Count -gt 0 -and $foundryStartupMode -in @("strict", "exact")) {
        try {
            $desiredFoundryModels = @($foundryStartupModels | ForEach-Object {
                $m = [string]$_
                if ($m.StartsWith('foundry::')) { $m.Substring('foundry::'.Length) } else { $m }
            })
            $loadedResponse = Invoke-RestMethod -Uri "http://127.0.0.1:$foundryPort/v1/models" -TimeoutSec 5 -ErrorAction Stop
            foreach ($loadedModel in @($loadedResponse.data)) {
                $loadedId = [string]$loadedModel.id
                if ($loadedId -and ($desiredFoundryModels -notcontains $loadedId)) {
                    Start-Process -FilePath "foundry" -ArgumentList "model", "unload", $loadedId -WindowStyle Minimized -NoNewWindow:$false | Out-Null
                    Write-Host "🧹 Foundry model unload requested: $loadedId" -ForegroundColor Yellow
                }
            }
        } catch {
            Write-Host "⚠️ Не удалось синхронизировать Foundry модели в strict режиме: $_" -ForegroundColor Yellow
        }
    }

    foreach ($modelIdRaw in $foundryStartupModels) {
        $modelId = [string]$modelIdRaw
        if ($modelId.StartsWith('foundry::')) {
            $modelId = $modelId.Substring('foundry::'.Length)
        }
        if (-not $modelId) { continue }
        try {
            Start-Process -FilePath "foundry" -ArgumentList "model", "load", $modelId -WindowStyle Minimized -NoNewWindow:$false | Out-Null
            Write-Host "🧠 Foundry model load requested: $modelId" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Не удалось запросить загрузку Foundry модели '$modelId': $_" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "⚠️ Foundry not available - AI features disabled" -ForegroundColor Yellow
}
# -----------------------------------------------------------------------------
# Этап 5: Опциональный сервер документации MkDocs
# Активация через параметр docs_server.enabled = true в config.json
# -----------------------------------------------------------------------------
Write-Host '🔍 Проверка конфигурации сервера документации...' -ForegroundColor Cyan

# Чтение секции docs_server из config.json
$docsServerConfig = $null
try {
    $configContent = Get-Content "$Root\$Config" | Out-String
    $parsedConfig = $configContent | ConvertFrom-Json
    
    if ($parsedConfig) {
        $docsServerConfig = $parsedConfig.docs_server
    }
} catch {
    Write-Host "❌ Ошибка чтения config.json для docs_server: $_" -ForegroundColor Red
    $docsServerConfig = $null
}

if ($docsServerConfig -and $docsServerConfig.enabled) {
    # Stop previous mkdocs serve instance if running on this port
    $docsPort = $docsServerConfig.port
    $oldMkdocs = Get-NetTCPConnection -LocalPort $docsPort -State Listen -ErrorAction SilentlyContinue
    if ($oldMkdocs) {
        $oldMkdocsPid = $oldMkdocs.OwningProcess
        try {
            Stop-Process -Id $oldMkdocsPid -Force -ErrorAction Stop
            Write-Host "✅ Предыдущий MkDocs (PID: $oldMkdocsPid) остановлен" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Не удалось остановить MkDocs (PID: $oldMkdocsPid): $_" -ForegroundColor Yellow
        }
    }

    $siteDir = Join-Path $Root 'site'
    if (Test-Path $siteDir) {
        Write-Host "📚 site/ найдена — запуск статического HTTP-сервера (без пересборки)" -ForegroundColor Cyan
        try {
            $mkdocsProc = Start-Process powershell.exe -ArgumentList @(
                '-NonInteractive', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                '-Command', "cd '$siteDir'; & '$venvPath' -m http.server $docsPort"
            ) -WindowStyle Minimized -PassThru
            $script:MkDocsPid = $mkdocsProc.Id
            Write-Host "✅ Сервер документации запущен на http://localhost:$docsPort (PID: $($mkdocsProc.Id))" -ForegroundColor Green
        } catch {
            Write-Host "❌ Сбой при запуске HTTP-сервера документации: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "📦 site/ не найдена — запуск mkdocs build..." -ForegroundColor Yellow
        try {
            Push-Location $Root
            & $venvPath -m mkdocs build --quiet
            Pop-Location
            Write-Host "✅ Документация собрана" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Сборка документации не удалась: $_" -ForegroundColor Yellow
        }

        Write-Host "🚀 Запуск сервера MkDocs на порту $docsPort..." -ForegroundColor Yellow
        try {
            $mkdocsProc = Start-Process powershell.exe -ArgumentList @(
                '-NonInteractive', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                '-Command', "cd '$Root'; & '$venvPath' -m mkdocs serve -a 0.0.0.0:$docsPort"
            ) -WindowStyle Minimized -PassThru
            $script:MkDocsPid = $mkdocsProc.Id
            Write-Host "✅ Сервер MkDocs запущен на http://localhost:$docsPort (PID: $($mkdocsProc.Id))" -ForegroundColor Green
        } catch {
            Write-Host "❌ Сбой при запуске сервера MkDocs: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "💡 Сервер документации отключен в config.json (пропуск)" -ForegroundColor Gray
}

# -----------------------------------------------------------------------------
# Step 6: llama.cpp local inference server
# Starts if llama_cpp.model_path is set in config.json.
# Set auto_start=false to disable automatic start.
# -----------------------------------------------------------------------------
<#
.SYNOPSIS
    Обеспечение актуальности бинарных файлов llama.cpp.
    Распаковка llama-server из zip архива в директории bin/.
.OUTPUTS
    string — Путь к llama-server.exe или $null.
#>
function Ensure-LlamaBin {
    $binDir     = Join-Path $Root 'bin'
    $configPath = Join-Path $Root 'config.json'
    $installedVersion = $null
    $cfg = $null
    
    # Find all llama zips, pick the latest by name (build number is in the name)
    $zips = Get-ChildItem -Path $binDir -Filter 'llama-*-bin-win-*.zip' -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending

    if (-not $zips) {
        Write-Host '⚠️  No llama.cpp zip found in bin/' -ForegroundColor Yellow
        return $null
    }

    $latestZip  = $zips[0]
    $latestStem = [System.IO.Path]::GetFileNameWithoutExtension($latestZip.Name)
    $extractDir = Join-Path $binDir $latestStem
    $serverExe  = Join-Path $extractDir 'llama-server.exe'

    # Read installed version from config.json
    try {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        $installedVersion = $cfg.llama_cpp.bin_version
    } catch { }

    $isUpToDate = ($installedVersion -eq $latestStem) -and (Test-Path $serverExe)

    if ($isUpToDate) {
        Write-Host "✅ llama.cpp binary up-to-date: $latestStem" -ForegroundColor Green
        return $serverExe
    }

    # Version update prompt
    if ($installedVersion -and $installedVersion -ne $latestStem) {
        Write-Host '' 
        Write-Host '📦 New llama.cpp version available!' -ForegroundColor Cyan
        Write-Host "   Installed : $installedVersion" -ForegroundColor Gray
        Write-Host "   Available : $latestStem" -ForegroundColor Green
        $answer = Read-Host '   Install now? [Y/n]'
        if ($answer -match '^[Nn]') {
            Write-Host '⏭️  Skipping update. Using existing binary.' -ForegroundColor Yellow
            # Return existing exe if it still works
            $oldExe = Join-Path $binDir $installedVersion 'llama-server.exe'
            if (Test-Path $oldExe) { return $oldExe }
            Write-Host '⚠️  Old binary not found, proceeding with extraction.' -ForegroundColor Yellow
        }
    } else {
        Write-Host "📦 Extracting $($latestZip.Name) → bin/$latestStem/ ..." -ForegroundColor Yellow
    }

    # Directory cleanup and extraction
    if (Test-Path $extractDir) {
        Remove-Item $extractDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    try {
        # Zip has no root folder — extract directly into the named subdirectory
        Expand-Archive -Path $latestZip.FullName -DestinationPath $extractDir -Force
        Write-Host "✅ Extracted: $extractDir" -ForegroundColor Green
    } catch {
        Write-Host "❌ Extraction failed: $_" -ForegroundColor Red
        return $null
    }

    # Configuration update
    try {
        if (-not $cfg) { $cfg = Get-Content $configPath -Raw | ConvertFrom-Json }
        $cfg.llama_cpp.bin_version = $latestStem
        $cfg | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
        Write-Host "✅ config.json updated: llama_cpp.bin_version = $latestStem" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Could not update config.json: $_" -ForegroundColor Yellow
    }

    if (Test-Path $serverExe) { return $serverExe }
    Write-Host "❌ llama-server.exe not found after extraction in $extractDir" -ForegroundColor Red
    return $null
}

<#
.SYNOPSIS
    Запуск сервера llama.cpp.
    Инициализация процесса инференса локальной модели.
.PARAMETER ServerExe
    Путь к бинарному файлу.
.PARAMETER ModelPath
    Путь к файлу модели GGUF.
.PARAMETER Port
    TCP порт для сервера.
#>
function Start-LlamaServer {
    param(
        [string]$ServerExe,
        [string]$ModelPath,
        [int]$Port,
        [string]$HostAddress = "127.0.0.1",
        [int]$CtxSize = 4096,
        [int]$Threads = 0,
        [int]$NGpuLayers = 0
    )

    for ($attempt = 1; $attempt -le 2; $attempt++) {
        if (-not (Test-Path $ServerExe)) {
            Write-Host "🔧 llama-server.exe missing, re-extracting (attempt $attempt)..." -ForegroundColor Yellow
            $ServerExe = Ensure-LlamaBin
            if (-not $ServerExe) {
                Write-Host '❌ Cannot find llama-server.exe after extraction.' -ForegroundColor Red
                return $false
            }
        }

        Write-Host "🦙 Starting llama.cpp (attempt $attempt): $([System.IO.Path]::GetFileName($ServerExe))" -ForegroundColor Cyan

        $arguments = @("--model", $ModelPath, "--port", $Port, "--host", $HostAddress, "--ctx-size", $CtxSize, "--n-gpu-layers", $NGpuLayers, "--log-disable")
        if ($Threads -gt 0) {
            $arguments += @("--threads", $Threads)
        }

        $proc = Start-Process -FilePath $ServerExe `
            -ArgumentList $arguments `
            -PassThru -WindowStyle Minimized -ErrorAction SilentlyContinue 

        if (-not $proc) {
            Write-Host "⚠️  Start-Process returned nothing on attempt $attempt." -ForegroundColor Yellow
            $ServerExe = ''  # force re-extract on next attempt
            continue
        }

        # Health endpoint polling
        for ($i = 1; $i -le 5; $i++) {
            Start-Sleep 2
            try {
                $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
                if ($r.StatusCode -eq 200) {
                    Write-Host "✅ llama.cpp running on port $Port (PID: $($proc.Id))" -ForegroundColor Green
                    return $true
                }
            } catch { }
            Write-Host "⏳ Waiting for llama.cpp... ($i/5)" -ForegroundColor Gray
        }

        # Crash handling
        if ($proc.HasExited) {
            Write-Host "⚠️  llama-server.exe exited immediately (code $($proc.ExitCode)). Re-extracting..." -ForegroundColor Yellow
            $ServerExe = Ensure-LlamaBin
            if (-not $ServerExe) { return $false }
        }
    }

    Write-Host '❌ llama.cpp failed to start after 2 attempts.' -ForegroundColor Red
    return $false
}

$llamaModelPath = $null
$llamaAutoStart = $true   # default: start if model_path is set
$llamaPort      = 9780
$llamaHost      = "127.0.0.1"
$llamaStartupModels = @()

# Read llama.cpp settings from config.json
try {
    $cfg        = if ($LauncherConfig) { $LauncherConfig } else { Get-Content (Join-Path $Root $Config) -Raw | ConvertFrom-Json }
    $llamaCfg   = $cfg.llama_cpp
    $llamaModelPath = $llamaCfg.model_path
    # auto_start=false is the only way to suppress start when model_path is set
    if ($llamaCfg.PSObject.Properties['auto_start']) {
        $llamaAutoStart = [bool]$llamaCfg.auto_start
    }

    # Auto-enable llama.cpp if default_model points to llama:: prefix
    if (-not $llamaAutoStart) {
        $defModel = [string]($foundryCfg.default_model)
        if ($defModel -and $defModel.StartsWith('llama::')) {
            Write-Host "💡 llama.cpp: default_model='$defModel' — auto_start автоматически включен (модель требует llama.cpp)." -ForegroundColor Cyan
            $llamaAutoStart = $true
        }
    }
    $llamaPort = if ($llamaCfg.port) { [int]$llamaCfg.port } else { 9780 }
    $llamaHost = if ($llamaCfg.host) { [string]$llamaCfg.host } else { "127.0.0.1" }

    if ($llamaCfg.PSObject.Properties['models'] -and $llamaCfg.models) {
        $i = 0
        foreach ($entry in @($llamaCfg.models)) {
            if (-not $entry) { continue }
            if ($entry -is [string]) {
                $llamaStartupModels += [pscustomobject]@{ model_path = $entry; port = ($llamaPort + $i); host = $llamaHost; auto_start = $true; ctx_size = 4096; threads = 0; n_gpu_layers = 0 }
            } else {
                $entryAutoStart = $true
                if ($entry.PSObject.Properties['auto_start']) { $entryAutoStart = [bool]$entry.auto_start }
                $llamaStartupModels += [pscustomobject]@{
                    model_path = [string]$entry.model_path
                    port       = if ($entry.port) { [int]$entry.port } else { ($llamaPort + $i) }
                    host       = if ($entry.host) { [string]$entry.host } else { $llamaHost }
                    auto_start = $entryAutoStart
                    ctx_size   = if ($entry.ctx_size) { [int]$entry.ctx_size } else { 4096 }
                    threads    = if ($entry.threads) { [int]$entry.threads } else { 0 }
                    n_gpu_layers = if ($entry.n_gpu_layers) { [int]$entry.n_gpu_layers } else { 0 }
                }
            }
            $i++
        }
    } elseif ($llamaModelPath) {
        $llamaStartupModels += [pscustomobject]@{ model_path = $llamaModelPath; port = $llamaPort; host = $llamaHost; auto_start = $llamaAutoStart; ctx_size = 4096; threads = 0; n_gpu_layers = 0 }
    }
} catch {
    Write-Host "⚠️  Could not read llama_cpp from config.json: $_" -ForegroundColor Yellow
}

# Override from .env
$llamaServerPathEnv = [System.Environment]::GetEnvironmentVariable('LLAMA_SERVER_PATH')

# Ensure binary is up-to-date only when at least one llama model may start
$llamaRunnableModels = @($llamaStartupModels | Where-Object { $_.model_path -and $_.auto_start })
$llamaServerExe = if ($llamaRunnableModels.Count -gt 0) { Ensure-LlamaBin } else { $null }

if ($llamaRunnableModels.Count -gt 0) {
    foreach ($llamaModel in $llamaRunnableModels) {
        $modelPath = [string]$llamaModel.model_path
        $modelPort = [int]$llamaModel.port
        $modelHost = [string]$llamaModel.host
        $modelCtx = [int]$llamaModel.ctx_size
        $modelThreads = [int]$llamaModel.threads
        $modelGpuLayers = [int]$llamaModel.n_gpu_layers

        Write-Host "🦙 Starting llama.cpp server..." -ForegroundColor Cyan
        Write-Host "   Model : $modelPath" -ForegroundColor Gray
        Write-Host "   Host  : $modelHost" -ForegroundColor Gray
        Write-Host "   Port  : $modelPort" -ForegroundColor Gray
        Write-Host "   Ctx   : $modelCtx" -ForegroundColor Gray

        # Остановка предыдущего инстанса на этом порту
        $oldLlama = Get-NetTCPConnection -LocalPort $modelPort -State Listen -ErrorAction SilentlyContinue
        if ($oldLlama) {
            try {
                Stop-Process -Id $oldLlama.OwningProcess -Force -ErrorAction Stop
                Write-Host "✅ Previous llama.cpp (PID: $($oldLlama.OwningProcess)) stopped" -ForegroundColor Green
                Start-Sleep 1
            } catch {
                Write-Host "⚠️  Could not stop previous llama.cpp: $_" -ForegroundColor Yellow
            }
        }

        if ($llamaServerExe) {
            $started = Start-LlamaServer -ServerExe $llamaServerExe -ModelPath $modelPath -Port $modelPort -HostAddress $modelHost -CtxSize $modelCtx -Threads $modelThreads -NGpuLayers $modelGpuLayers
            if ($started) {
                if (-not $env:LLAMA_BASE_URL) {
                    $env:LLAMA_BASE_URL = "http://$modelHost`:$modelPort/v1"
                    Write-Host "🔗 LLAMA_BASE_URL = $env:LLAMA_BASE_URL" -ForegroundColor Green
                }
                # Сохранение PID для очистки
                $llamaRunning = Get-NetTCPConnection -LocalPort $modelPort -State Listen -ErrorAction SilentlyContinue
                if ($llamaRunning) {
                    if (-not $script:LlamaPids) { $script:LlamaPids = @() }
                    $script:LlamaPids += $llamaRunning.OwningProcess
                }
            }
        } else {
            Write-Host '❌ llama-server.exe not available, skipping auto-start.' -ForegroundColor Red
        }
    }
} elseif ($llamaStartupModels.Count -gt 0) {
    Write-Host '💡 llama.cpp: all configured models have auto_start=false — skipping.' -ForegroundColor Gray
} else {
    Write-Host '💡 llama.cpp: no model_path in config.json — skipping.' -ForegroundColor Gray
    Write-Host '   Add a .gguf model and set llama_cpp.model_path, or use the web UI: llama.cpp tab → Browse' -ForegroundColor Gray
}

# -----------------------------------------------------------------------------
# Этап 5: Опциональный сервер документации MkDocs (Предпоследний этап)
# Активация через параметр docs_server.enabled = true в config.json
# -----------------------------------------------------------------------------
Write-Host '🔍 Проверка конфигурации сервера документации...' -ForegroundColor Cyan

# Чтение секции docs_server из config.json
$docsServerConfig = $null
try {
    $configContent = Get-Content "$Root\$Config" | Out-String
    $parsedConfig = $configContent | ConvertFrom-Json
    
    if ($parsedConfig) {
        $docsServerConfig = $parsedConfig.docs_server
    }
} catch {
    Write-Host "❌ Ошибка чтения config.json для docs_server: $_" -ForegroundColor Red
    $docsServerConfig = $null
}

if ($docsServerConfig -and $docsServerConfig.enabled) {
    # Stop previous mkdocs serve instance if running on this port
    $docsPort = $docsServerConfig.port
    $oldMkdocs = Get-NetTCPConnection -LocalPort $docsPort -State Listen -ErrorAction SilentlyContinue
    if ($oldMkdocs) {
        $oldMkdocsPid = $oldMkdocs.OwningProcess
        try {
            Stop-Process -Id $oldMkdocsPid -Force -ErrorAction Stop
            Write-Host "✅ Предыдущий MkDocs (PID: $oldMkdocsPid) остановлен" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Не удалось остановить MkDocs (PID: $oldMkdocsPid): $_" -ForegroundColor Yellow
        }
    }

    $siteDir = Join-Path $Root 'site'
    if (Test-Path $siteDir) {
        Write-Host "📚 site/ найдена — запуск статического HTTP-сервера (без пересборки)" -ForegroundColor Cyan
        try {
            $mkdocsProc = Start-Process powershell.exe -ArgumentList @(
                '-NonInteractive', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                '-Command', "cd '$siteDir'; & '$venvPath' -m http.server $docsPort"
            ) -WindowStyle Minimized -PassThru
            $script:MkDocsPid = $mkdocsProc.Id
            Write-Host "✅ Сервер документации запущен на http://localhost:$docsPort (PID: $($mkdocsProc.Id))" -ForegroundColor Green
        } catch {
            Write-Host "❌ Сбой при запуске HTTP-сервера документации: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "📦 site/ не найдена — запуск mkdocs build..." -ForegroundColor Yellow
        try {
            Push-Location $Root
            & $venvPath -m mkdocs build --quiet
            Pop-Location
            Write-Host "✅ Документация собрана" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Сборка документации не удалась: $_" -ForegroundColor Yellow
        }

        Write-Host "🚀 Запуск сервера MkDocs на порту $docsPort..." -ForegroundColor Yellow
        try {
            $mkdocsProc = Start-Process powershell.exe -ArgumentList @(
                '-NonInteractive', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                '-Command', "cd '$Root'; & '$venvPath' -m mkdocs serve -a 0.0.0.0:$docsPort"
            ) -WindowStyle Minimized -PassThru
            $script:MkDocsPid = $mkdocsProc.Id
            Write-Host "✅ Сервер MkDocs запущен на http://localhost:$docsPort (PID: $($mkdocsProc.Id))" -ForegroundColor Green
        } catch {
            Write-Host "❌ Сбой при запуске сервера MkDocs: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "💡 Сервер документации отключен в config.json (пропуск)" -ForegroundColor Gray
}

# -----------------------------------------------------------------------------
# Этап 6.5: Остановка installer-сервера (если запущен)
# -----------------------------------------------------------------------------
$InstallerPidFile = Join-Path $Root 'scripts\Install\.installer.pid'
if (Test-Path $InstallerPidFile) {
    $installerPid = Get-Content $InstallerPidFile -ErrorAction SilentlyContinue
    if ($installerPid) {
        try {
            $installerProc = Get-Process -Id $installerPid -ErrorAction Stop
            Write-Host "⚠️  Installer server still running (PID: $installerPid) — stopping..." -ForegroundColor Yellow
            $installerProc.Kill()
            $installerProc.WaitForExit(3000)
            Write-Host "✅ Installer server stopped" -ForegroundColor Green
        } catch {
            Write-Host "💡 Installer server (PID: $installerPid) already exited" -ForegroundColor Gray
        }
    }
    Remove-Item $InstallerPidFile -Force -ErrorAction SilentlyContinue
}

# -----------------------------------------------------------------------------
# Этап 6: Остановка предыдущего экземпляра и запуск FastAPI
# -----------------------------------------------------------------------------
$PidFile = Join-Path $env:TEMP 'fastapi-foundry.pid'

# Очистка предыдущих процессов FastAPI
if (Test-Path $PidFile) {
    $oldPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($oldPid) {
        try {
            $oldProcess = Get-Process -Id $oldPid -ErrorAction Stop
            Write-Host "⚠️ Найден предыдущий процесс FastAPI (PID: $oldPid) — останавливаем..." -ForegroundColor Yellow
            $oldProcess.Kill()
            $oldProcess.WaitForExit(5000)
            Write-Host "✅ Предыдущий процесс остановлен" -ForegroundColor Green
        } catch {
            Write-Host "💡 Предыдущий процесс (PID: $oldPid) уже завершён" -ForegroundColor Gray
        }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

Write-Host '🐍 FastAPI server launch...' -ForegroundColor Cyan

if (-not (Test-Path $venvPath)) {
    Write-Host '❌ ОШИБКА: venv Python не найден после этапа установки!' -ForegroundColor Red
    Write-Host "Ожидаемый путь: $venvPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "🔗 FOUNDRY_DYNAMIC_PORT = $env:FOUNDRY_DYNAMIC_PORT" -ForegroundColor Gray
Write-Host '🌐 FastAPI Foundry starting...' -ForegroundColor Green
Write-Host "📱 Веб-интерфейс:  http://localhost:9696" -ForegroundColor Cyan
if ($docsServerConfig -and $docsServerConfig.enabled) {
    Write-Host "📚 Документация:   http://localhost:$($docsServerConfig.port)" -ForegroundColor Cyan
}
Write-Host ('=' * 60) -ForegroundColor Cyan

try {
    # Основной цикл запуска сервера
    $proc = Start-Process -FilePath $venvPath -ArgumentList "run.py", "--config", $Config `
        -PassThru -NoNewWindow
    $proc.Id | Set-Content $PidFile -Encoding UTF8
    Write-Host "💾 PID $($proc.Id) сохранён в $PidFile" -ForegroundColor Gray

    # Open browser after server starts (wait up to 15s for port to become available)
    $appPort = 9696
    try {
        $cfg = Get-Content (Join-Path $Root 'config.json') -Raw | ConvertFrom-Json
        if ($cfg.fastapi_server.port) { $appPort = [int]$cfg.fastapi_server.port }
    } catch { }

    $browserOpened = $false
    for ($i = 1; $i -le 15; $i++) {
        Start-Sleep 1
        try {
            $tcp = [System.Net.Sockets.TcpClient]::new()
            $tcp.Connect('127.0.0.1', $appPort)
            $tcp.Close()
            Start-Process "http://localhost:$appPort"
            Write-Host "🌐 Браузер открыт: http://localhost:$appPort" -ForegroundColor Green
            $browserOpened = $true
            break
        } catch { }
    }
    if (-not $browserOpened) {
        Write-Host "💡 Откройте браузер вручную: http://localhost:$appPort" -ForegroundColor Yellow
    }

    $proc.WaitForExit()
} catch {
    Write-Host "❌ Ошибка запуска сервера FastAPI: $_" -ForegroundColor Red
    Write-Host "💡 Проверьте логи или запустите вручную: $venvPath run.py" -ForegroundColor Yellow
    exit 1
} finally {
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue

    # Остановка фоновых процессов при выходе
    if ($script:MkDocsPid) {
        try {
            Stop-Process -Id $script:MkDocsPid -Force -ErrorAction Stop
            Write-Host "✅ MkDocs остановлен (PID: $script:MkDocsPid)" -ForegroundColor Green
        } catch {
            Write-Host "💡 MkDocs (PID: $script:MkDocsPid) уже завершён" -ForegroundColor Gray
        }
    }
    if ($script:LlamaPids) {
        foreach ($llamaPid in @($script:LlamaPids | Select-Object -Unique)) {
            try {
                Stop-Process -Id $llamaPid -Force -ErrorAction Stop
                Write-Host "✅ llama.cpp остановлен (PID: $llamaPid)" -ForegroundColor Green
            } catch {
                Write-Host "💡 llama.cpp (PID: $llamaPid) уже завершён" -ForegroundColor Gray
            }
        }
    }
}
