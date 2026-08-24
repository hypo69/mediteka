<#
.SYNOPSIS
    Запускает FastAPI-сервер через uvicorn (Unicorn) для проекта Mediteka.

.DESCRIPTION
    Активирует виртуальное окружение, загружает параметры из config.json,
    освобождает порт, применяет SSL при необходимости и запускает
    FastAPI-сервер в текущем окне PowerShell.

.EXAMPLE
    .\Run-Unicorn.ps1
#>

$scriptDir = Split-Path $MyInvocation.MyCommand.Path
$venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"
$venvActivate = Join-Path $scriptDir "venv\Scripts\Activate.ps1"
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8



Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         ЗАПУСК FastAPI СЕРВЕРА - MULTI-WORKER                  ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# АКТИВАЦИЯ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ
# ============================================
Write-Host "[1/4] Проверка виртуального окружения..." -ForegroundColor Cyan
if (Test-Path $venvActivate) {
    . $venvActivate
    Write-Host "    [OK] venv активирован: $venvPython" -ForegroundColor Green
} else {
    $venvPython = (Get-Command python -ErrorAction Stop).Source
    Write-Host "    [WARN] venv не найден, используется: $venvPython" -ForegroundColor Yellow
}

# ============================================
# ЗАГРУЗКА КОНФИГУРАЦИИ
# ============================================
Write-Host ""
Write-Host "[2/4] Загрузка конфигурации..." -ForegroundColor Cyan
$configPath = Join-Path $scriptDir "config.json"
$envFile    = Join-Path $scriptDir ".env"
$host_   = "0.0.0.0"
$port    = "3000"
$workers = 1
$useSsl  = $false
$reload  = $true

if (Test-Path $configPath) {
    $cfg     = Get-Content $configPath | ConvertFrom-Json
    $host_   = $cfg.server.host
    $port    = [string]$cfg.server.port
    $useSsl  = $cfg.server.use_ssl
    $mode    = $cfg.server.mode.ToLower()
    $debug   = if ($cfg.server.debug) { "true" } else { "false" }
    
    if ($cfg.server.PSObject.Properties['reload']) {
        $reload = [bool]$cfg.server.reload
    } else {
        $reload = $true
    }

    if ($cfg.server.PSObject.Properties['workers']) {
        $workers = [int]$cfg.server.workers
    }
    
    Write-Host "    Host:       $host_" -ForegroundColor Gray
    Write-Host "    Port:       $port"  -ForegroundColor Gray
    Write-Host "    Autoreload: $(if ($reload) { 'ВКЛЮЧЁН (config.json)' } else { 'ВЫКЛЮЧЕН (config.json)' })" -ForegroundColor $(if ($reload) { 'Green' } else { 'Yellow' })
    if (-not $reload) {
        Write-Host "    Workers:    $workers" -ForegroundColor Gray
    }
} else {
    $mode = "dev"
    $debug = "true"
    $reload = $true
    Write-Host "    Autoreload: ВКЛЮЧЁН (По умолчанию)" -ForegroundColor Green
}

# ============================================
# ОСВОБОЖДЕНИЕ ПОРТА
# ============================================
Write-Host ""
Write-Host "[3/4] Освобождение порта $port..." -ForegroundColor Cyan
try {
    $conns = Get-NetTCPConnection -LocalPort ([int]$port) -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns.OwningProcess | Select-Object -Unique
        Write-Host "    [WARN] Порт занят. Завершение PID: $pids" -ForegroundColor Yellow
        $pids | Where-Object { $_ -gt 0 } | ForEach-Object {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    } else {
        Write-Host "    [OK] Порт свободен" -ForegroundColor Green
    }
} catch {
    Write-Host "    [WARN] Не удалось проверить порт: $_" -ForegroundColor Yellow
}

# ============================================
# ЗАПУСК UVICORN
# ============================================
Write-Host ""
if ($reload) {
    Write-Host "[4/4] Запуск uvicorn в режиме AUTORELOAD..." -ForegroundColor Cyan
} else {
    Write-Host "[4/4] Запуск uvicorn с $workers воркерами..." -ForegroundColor Cyan
}

$uvicornArgs = @(
    "-m", "uvicorn",
    "main:app",
    "--host", $host_,
    "--port", $port,
    "--loop", "asyncio"
)

if ($reload) {
    $uvicornArgs += "--reload"
    $uvicornArgs += "--reload-dir", $scriptDir
    Write-Host "    [MODE] Autoreload активен (отслеживание изменений файлов в $scriptDir)" -ForegroundColor Green
} else {
    if ($workers -gt 1) {
        $uvicornArgs += "--workers", [string]$workers
    }
}

$is_debug = ($mode -in ("dev","debug")) -or ($debug -in ("true","1","yes"))
if ($is_debug) {
    $uvicornArgs += "--log-level", "debug"
} else {
    $uvicornArgs += "--log-level", "info"
}

# SSL
if ($useSsl) {
    $certsDir = Join-Path $env:USERPROFILE ".certs"
    $certFile = Join-Path $certsDir "localhost+2.pem"
    $keyFile  = Join-Path $certsDir "localhost+2-key.pem"
    if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
        $uvicornArgs += "--ssl-certfile", $certFile, "--ssl-keyfile", $keyFile
        Write-Host "    SSL: включён ($certFile)" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] Сертификаты не найдены — запуск без SSL" -ForegroundColor Yellow
    }
}

Write-Host "    Команда: $venvPython $($uvicornArgs -join ' ')" -ForegroundColor Gray
Write-Host ""
if ($reload) {
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  AUTORELOAD: ВКЛЮЧЁН (авто-перезапуск при изменении кода)      ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
} else {
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  ЗАПУЩЕНО $workers ВОРКЕРОВ — Ctrl+C для остановки              ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
}
Write-Host ""

# Запуск в текущем окне PowerShell
$argStr = ($uvicornArgs | ForEach-Object { "`"$_`"" }) -join " "
$logsDir = Join-Path $scriptDir "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
}
$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$logFilePath = Join-Path $logsDir "uvicorn_$timestamp.log"

Write-Host "[INFO] Запуск uvicorn в текущем окне..." -ForegroundColor Green
$cmdToRun = "set CONNECTED_DRIVES=$env:CONNECTED_DRIVES && `"$venvPython`" $argStr 2>&1"
cmd /c $cmdToRun | Tee-Object -FilePath $logFilePath

