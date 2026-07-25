$scriptDir = Split-Path $MyInvocation.MyCommand.Path
$venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"
$venvActivate = Join-Path $scriptDir "venv\Scripts\Activate.ps1"

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
$configPath = Join-Path $scriptDir "src\fastapi\config.json"
$envFile    = Join-Path $scriptDir ".env"
$host_   = "0.0.0.0"
$port    = "3000"
$workers = 4
$useSsl  = $false

if (Test-Path $configPath) {
    $cfg     = Get-Content $configPath | ConvertFrom-Json
    $host_   = $cfg.host
    $port    = [string]$cfg.port
    if ($cfg.PSObject.Properties['workers']) {
        $workers = [int]$cfg.workers
    }
    Write-Host "    Host:    $host_" -ForegroundColor Gray
    Write-Host "    Port:    $port"  -ForegroundColor Gray
    Write-Host "    Workers: $workers" -ForegroundColor Gray
}

# Читаем .env для USE_SSL
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -eq "USE_SSL") { $useSsl = $val -in ("true","1","yes") }
        }
    }
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
# ЗАПУСК UVICORN --workers
# ============================================
Write-Host ""
Write-Host "[4/4] Запуск uvicorn с $workers воркерами..." -ForegroundColor Cyan

# На Windows uvicorn --workers требует spawn-метода.
# Используем флаг --loop asyncio (стандартный для Windows).
$uvicornArgs = @(
    "-m", "uvicorn",
    "main:app",
    "--host", $host_,
    "--port", $port,
    "--workers", [string]$workers,
    "--loop", "asyncio"
)

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
Write-Host "║  ЗАПУЩЕНО $workers ВОРКЕРОВ — Ctrl+C для остановки              ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Запуск в отдельном окне PowerShell
$argStr = ($uvicornArgs | ForEach-Object { "`"$_`"" }) -join " "
$cmd = "Set-Location '$scriptDir'; & '$venvPython' $argStr"

$serverProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -PassThru -WindowStyle Normal

if (-not $serverProcess) {
    Write-Host "[ERROR] Не удалось запустить сервер." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Сервер запущен. PID: $($serverProcess.Id)" -ForegroundColor Green
