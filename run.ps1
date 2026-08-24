# Запуск и диагностика FastAPI-сервера проекта Mediteka.
# Скрипт активирует виртуальное окружение, загружает конфигурацию,
# проверяет зависимости и запускает локальный сервер вместе с
# сопутствующими сервисами, если они включены в настройках проекта.

$scriptDir = Split-Path $MyInvocation.MyCommand.Path
$venvActivate = Join-Path $scriptDir "venv\Scripts\Activate.ps1"
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8



Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         ЗАПУСК FastAPI СЕРВЕРА - ДИАГНОСТИКА                  ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# АКТИВАЦИЯ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ
# ============================================
Write-Host "[1/5] Проверка виртуального окружения..." -ForegroundColor Cyan

# Явный путь к python внутри venv — не зависит от $PATH и сломанных Store-заглушек
$venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    Write-Host "    [OK] Виртуальное окружение найдено" -ForegroundColor Green
    Write-Host "    Активация..." -ForegroundColor DarkGray
    if (Test-Path $venvActivate) { . $venvActivate }
    Write-Host "    [OK] Виртуальное окружение активировано" -ForegroundColor Green

    # Берём python напрямую из venv, минуя $PATH
    $pythonPath = $venvPython
    Write-Host "    Python: $pythonPath" -ForegroundColor Gray
} else {
    Write-Host "    [WARN] Виртуальное окружение не найдено: $venvPython" -ForegroundColor Yellow
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $pythonPath) {
        Write-Host "    [ERROR] Python не найден! Установите Python с python.org и пересоздайте venv." -ForegroundColor Red
        exit 1
    }
    Write-Host "    [WARN] Используется системный Python: $pythonPath" -ForegroundColor Yellow
}

# ============================================
# ПРОВЕРКА ЗАВИСИМОСТЕЙ
# ============================================
Write-Host ""
Write-Host "[2/5] Проверка зависимостей..." -ForegroundColor Cyan
try {
    $packages = & $pythonPath -c "import fastapi, uvicorn, dotenv, jwt; print('fastapi, uvicorn, python-dotenv, PyJWT - OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] Основные зависимости загружены" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] Некоторые зависимости не установлены. Запустите install.cmd" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    [ERROR] Ошибка при проверке зависимостей: $_" -ForegroundColor Red
    Write-Host "    Установка: install.cmd или pip install -r requirements.txt" -ForegroundColor Yellow
}

# ============================================
# ЗАГРУЗКА КОНФИГУРАЦИИ И ОКРУЖЕНИЯ (.env)
# ============================================
Write-Host ""
Write-Host "[3/7] Загрузка конфигурации..." -ForegroundColor Cyan
$configPath = Join-Path $scriptDir "config.json"
$envFile = Join-Path $scriptDir ".env"
$host_ = "0.0.0.0"
$port  = "3000"
$useSsl = $true
$useFoundry = $false
$preloadSilero = $false

if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath | ConvertFrom-Json
        $host_ = $cfg.server.host
        $port  = $cfg.server.port
        $useSsl = $cfg.server.use_ssl
        $useFoundry = $cfg.ai.use_foundry
        $preloadSilero = $cfg.ai.preload_silero
        Write-Host "    [OK] Конфигурация загружена" -ForegroundColor Green
        Write-Host "    Host: $host_" -ForegroundColor Gray
        Write-Host "    Port: $port" -ForegroundColor Gray
    } catch {
        Write-Host "    [ERROR] Ошибка чтения конфигурации: $_" -ForegroundColor Red
    }
} else {
    Write-Host "    [WARN] Файл конфигурации не найден: $configPath" -ForegroundColor Yellow
}

$proto = if ($useSsl) { "https" } else { "http" }
$url = "${proto}://${host_}:${port}"

# ============================================
# ЗАВЕРШЕНИЕ ПРОЦЕССОВ НА ПОРТЕ
# ============================================
Write-Host ""
Write-Host "[4/7] Проверка порта $port..." -ForegroundColor Cyan

# Проверяем, занят ли порт
$netstatOutput = netstat -aon 2>$null
$occupied = $netstatOutput | Select-String ":${port}\s" | ForEach-Object { ($_ -split '\s+')[-1] } | Where-Object { $_ -match '^\d+$' -and $_ -ne '0' } | Select-Object -Unique

if ($occupied) {
    Write-Host "    [WARN] Порт $port занят!" -ForegroundColor Yellow
    foreach ($pid_ in $occupied) {
        try {
            $proc = Get-Process -Id $pid_ -ErrorAction Stop
            Write-Host "        PID $pid_ | $($proc.ProcessName) | $($proc.Path)" -ForegroundColor Yellow
            Write-Host "        Завершение процесса..." -ForegroundColor DarkGray
            Stop-Process -Id $pid_ -Force -ErrorAction Stop
            Write-Host "        [OK] Завершен" -ForegroundColor Green
        } catch {
            Write-Host "        [ERROR] Не удалось завершить PID ${pid_}: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "    [OK] Порт свободен" -ForegroundColor Green
}


# ============================================
# ЗАПУСК CLOUDFLARE TUNNEL
# ============================================
Write-Host ""
Write-Host "[6/7] Запуск Cloudflare Tunnel..." -ForegroundColor Cyan
$cloudflaredScript = Join-Path $scriptDir "Run-Cloudflared.ps1"
if (Test-Path $cloudflaredScript) {
    Write-Host "    Вызов Run-Cloudflared.ps1..." -ForegroundColor DarkGray
    & $cloudflaredScript
    
    # Ожидание доступности туннеля в фоне
    Write-Host "[INFO] Ожидание доступности туннеля $targetUrl в фоне..." -ForegroundColor Cyan
    Start-Job -ScriptBlock {
        param($targetUrl)
        $maxRetries = 20
        $retryDelay = 5
        $isUp = $false
        for ($i = 1; $i -le $maxRetries; $i++) {
            try {
                $response = Invoke-WebRequest -Uri $targetUrl -Method Head -UseBasicParsing -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    $isUp = $true
                    break
                }
            } catch {
            }
            Start-Sleep -Seconds $retryDelay
        }
        if ($isUp) {
            Start-Process $targetUrl
        }
    } -ArgumentList $targetUrl | Out-Null
}

# ============================================
# ЗАПУСК LOCAL FOUNDRY SERVICE
# ============================================
if ($useFoundry) {
    Write-Host ""
    Write-Host "[6.1] Запуск локальной службы Foundry..." -ForegroundColor Cyan
    $foundryScript = Join-Path $scriptDir "Run-Foundry.ps1"
    if (Test-Path $foundryScript) {
        Write-Host "    Вызов Run-Foundry.ps1..." -ForegroundColor DarkGray
        & $foundryScript -Action start
    } else {
        Write-Host "    [WARN] Run-Foundry.ps1 не найден: $foundryScript" -ForegroundColor Yellow
    }
}

# ============================================
# СКАНАДИРОВАНИЕ ПОДКЛЮЧЕННЫХ ДИСКОВ
# ============================================
Write-Host ""
Write-Host "[7/7] Сканирование подключенных дисков..." -ForegroundColor Cyan
& $pythonPath -m plugins.media_organizer.core.drive_scanner
$env:CONNECTED_DRIVES = & $pythonPath -c "import os; print(os.environ.get('CONNECTED_DRIVES', ''))"
Write-Host "    Подключенные диски: $env:CONNECTED_DRIVES" -ForegroundColor Gray
Write-Host ""
Write-Host ""
Write-Host "[SUCCESS] Настройка завершена. Запуск сервера..." -ForegroundColor Green
# ЗАПУСК СЕРВЕРА В ТЕКУЩЕМ ОКНЕ (Unicorn)
# ============================================
$env:PRELOAD_SILERO = $preloadSilero
$unicornScript = Join-Path $scriptDir "Run-Unicorn.ps1"
if (Test-Path $unicornScript) {
    Write-Host "    Запуск Run-Unicorn.ps1..." -ForegroundColor DarkGray
    
    Start-Job -ScriptBlock {
        Start-Sleep -Seconds 5
        Start-Process "https://kino.davidka.net/"
    } | Out-Null

    & $unicornScript
} else {
    Write-Host "    [ERROR] Run-Unicorn.ps1 не найден: $unicornScript" -ForegroundColor Red
    exit 1
}
