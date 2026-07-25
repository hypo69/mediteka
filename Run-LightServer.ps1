$scriptDir = Split-Path $MyInvocation.MyCommand.Path
$venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"
$venvActivate = Join-Path $scriptDir "venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         ЗАПУСК ЛОКАЛЬНОГО СЕРВЕРА (LIGHT)                     ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# СКАНАДИРОВАНИЕ ПОДКЛЮЧЕННЫХ ДИСКОВ
# ============================================
Write-Host ""
Write-Host "[1.5] Сканирование подключенных дисков..." -ForegroundColor Cyan
python -m plugins.media_organizer.core.drive_scanner
$env:CONNECTED_DRIVES = python -c "import os; print(os.environ.get('CONNECTED_DRIVES', ''))"
Write-Host "    Подключенные диски: $env:CONNECTED_DRIVES" -ForegroundColor Gray

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
# КОНФИГУРАЦИЯ СЕРВЕРА
# ============================================
$host_   = "127.0.0.1"
$port    = "3000"
$workers = 1
$useSsl  = $false

# Читаем .env для настроек режима отладки
$envFile = Join-Path $scriptDir ".env"
$mode = "dev"
$debug = "true"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -eq "MODE") { $mode = $val.ToLower() }
            if ($key -eq "DEBUG") { $debug = $val.ToLower() }
        }
    }
}

# ============================================
# ОСВОБОЖДЕНИЕ ПОРТА
# ============================================
Write-Host ""
Write-Host "[2/4] Освобождение порта $port на $host_..." -ForegroundColor Cyan
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
# ЗАПУСК UVICORN (1 воркер)
# ============================================
Write-Host ""
Write-Host "[3/4] Подготовка uvicorn (1 воркер)..." -ForegroundColor Cyan

$uvicornArgs = @(
    "-m", "uvicorn",
    "main:app",
    "--host", $host_,
    "--port", $port,
    "--workers", [string]$workers,
    "--loop", "asyncio"
)

$is_debug = ($mode -in ("dev","debug")) -or ($debug -in ("true","1","yes"))
if ($is_debug) {
    $uvicornArgs += "--log-level", "debug"
} else {
    $uvicornArgs += "--log-level", "info"
}

# SSL
if ($useSsl) {
    $certFile = "C:\Users\onela\.certs\localhost+2.pem"
    $keyFile  = "C:\Users\onela\.certs\localhost+2-key.pem"
    if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
        $uvicornArgs += "--ssl-certfile", $certFile, "--ssl-keyfile", $keyFile
        Write-Host "    SSL: включён ($certFile)" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] Сертификаты не найдены — запуск без SSL" -ForegroundColor Yellow
    }
}

Write-Host "    Команда: $venvPython $($uvicornArgs -join ' ')" -ForegroundColor Gray
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ЛОКАЛЬНЫЙ СЕРВЕР ЗАПУЩЕН НА http://127.0.0.1:3000           ║" -ForegroundColor Cyan
Write-Host "║  (без тоннелей, 1 воркер, Ctrl+C для остановки)               ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$logsDir = Join-Path $scriptDir "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
}
$logFilePath = Join-Path $logsDir "uvicorn_light.log"

Write-Host "[INFO] Запуск uvicorn в текущем окне..." -ForegroundColor Green
$cmdToRun = "`"$venvPython`" $argStr 2>&1"
$argStr = ($uvicornArgs | ForEach-Object { "`"$_`"" }) -join " "
$cmdToRun = "`"$venvPython`" $argStr 2>&1"
cmd /c $cmdToRun | Tee-Object -FilePath $logFilePath
