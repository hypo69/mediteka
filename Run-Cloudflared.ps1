<#
.SYNOPSIS
    Перезапускает туннель Cloudflare Tunnel (cloudflared).

.DESCRIPTION
    Завершает все процессы cloudflared, автоматически скачивает cloudflared.exe (при отсутствии),
    и запускает туннель с использованием токена из .env.

.EXAMPLE
    .\Run-Cloudflared.ps1
#>

[CmdletBinding()]
param (
    [string]$CloudflaredExe = 'cloudflared.exe'
)

$ErrorActionPreference = 'Stop'

Write-Host ''
Write-Host '=== Restarting Cloudflare Tunnel ===' -ForegroundColor Cyan

#
# Загрузка переменных окружения из .env
#
$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = Get-Location
}
$envFile = Join-Path $scriptDir ".env"
$token = $null
$mode = "dev"
$debug = "true"

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim() -replace "^['`"]|['`"]$"
            if ($key -eq "CLOUDFLARE_TUNNEL_TOKEN") {
                $token = $val
            }
            if ($key -eq "MODE") { $mode = $val.ToLower() }
            if ($key -eq "DEBUG") { $debug = $val.ToLower() }
        }
    }
}

if (-not $token) {
    Write-Host "[ERROR] CLOUDFLARE_TUNNEL_TOKEN не найден в вашем файле .env!" -ForegroundColor Red
    Write-Host "Пожалуйста, добавьте строку в .env:" -ForegroundColor Yellow
    Write-Host "CLOUDFLARE_TUNNEL_TOKEN=ваш_токен_из_cloudflare" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

#
# Проверка и скачивание cloudflared.exe
#
$localExePath = Join-Path $scriptDir $CloudflaredExe
if (-not (Test-Path $localExePath)) {
    Write-Host "cloudflared.exe не найден в папке проекта. Скачиваю последнюю версию..." -ForegroundColor Yellow
    $downloadUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $downloadUrl -OutFile $localExePath -UseBasicParsing
        Write-Host "[OK] Скачивание завершено успешно." -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Не удалось скачать cloudflared.exe: $_" -ForegroundColor Red
        exit 1
    }
}

#
# Завершение всех запущенных процессов cloudflared
#
Write-Host 'Остановка существующих процессов cloudflared...' -ForegroundColor Yellow
Get-CimInstance Win32_Process |
    Where-Object Name -eq 'cloudflared.exe' |
    ForEach-Object {
        try {
            Stop-Process -Id $_.ProcessId -Force
            Write-Host "Остановлен процесс PID $($_.ProcessId)"
        }
        catch {
        }
    }

# Ожидание завершения
Start-Sleep -Seconds 2

#
# Запуск туннеля
#
# Запуск туннеля
#
Write-Host "Запуск Cloudflare Tunnel..." -ForegroundColor Green
$logsDir = Join-Path $scriptDir "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
}
$logFilePath = Join-Path $logsDir "cloudflared.log"

$is_debug = ($mode -in ("dev","debug")) -or ($debug -in ("true","1","yes"))
$logLevelArg = if ($is_debug) { "debug" } else { "info" }

$argList = @("tunnel", "--no-autoupdate", "run", "--token", $token, "--loglevel", $logLevelArg, "--logfile", $logFilePath)

$cfProcess = Start-Process $localExePath -ArgumentList $argList -PassThru -WindowStyle Minimized

if (-not $cfProcess) {
    Write-Host "[ERROR] Не удалось запустить cloudflared." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  CLOUDFLARE TUNNEL ЗАПУЩЕН!                                    " -ForegroundColor Green
Write-Host "  Адрес: https://kino.davidka.net                                " -ForegroundColor Green
Write-Host "  PID процесса: $($cfProcess.Id)                                " -ForegroundColor Gray
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
