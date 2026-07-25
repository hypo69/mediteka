<#
.SYNOPSIS
    Перезапускает туннель ngrok.

.DESCRIPTION
    Завершает все процессы ngrok, ожидает полного завершения,
    запускает новый HTTP-туннель и выводит его публичный URL.

.EXAMPLE
    .\Run-Engrock.ps1

.EXAMPLE
    .\Run-Engrock.ps1 -Port 8000
#>

[CmdletBinding()]
param (
    [int]$Port = 3000,
    [string]$NgrokExe = 'ngrok.exe'
)

$ErrorActionPreference = 'Stop'

Write-Host ''
Write-Host '=== Restarting ngrok ===' -ForegroundColor Cyan

#
# Загрузка переменных окружения из .env
#
$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = Get-Location
}
$envFile = Join-Path $scriptDir ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim() -replace "^['`"]|['`"]$"
            [System.Environment]::SetEnvironmentVariable($key, $val)
        }
    }
}

#
# Остановка удаленных сессий туннелей через REST API (требует NGROK_API_KEY в .env)
#
$apiKey = [System.Environment]::GetEnvironmentVariable("NGROK_API_KEY")
if (-not $apiKey) {
    $apiKey = [System.Environment]::GetEnvironmentVariable("NGROCK_API_KEY")
}

if ($apiKey) {
    Write-Host "Ngrok API Key detected. Stopping all active remote tunnel sessions..." -ForegroundColor Yellow
    try {
        $headers = @{
            "Authorization" = "Bearer $apiKey"
            "ngrok-version" = "2"
        }
        $sessions = Invoke-RestMethod -Uri "https://api.ngrok.com/tunnel_sessions" -Headers $headers -Method Get -ErrorAction Stop
        
        if ($sessions -and $sessions.tunnel_sessions -and $sessions.tunnel_sessions.Count -gt 0) {
            Write-Host "Found $($sessions.tunnel_sessions.Count) active session(s). Disconnecting..." -ForegroundColor Yellow
            foreach ($session in $sessions.tunnel_sessions) {
                $sessionId = $session.id
                Write-Host "Stopping session $sessionId..." -ForegroundColor DarkYellow
                Invoke-RestMethod -Uri "https://api.ngrok.com/tunnel_sessions/$sessionId/stop" -Headers $headers -Method Post -ErrorAction Stop | Out-Null
            }
            Write-Host "All active remote sessions have been stopped." -ForegroundColor Green
            Start-Sleep -Seconds 3
        } else {
            Write-Host "No active remote sessions found." -ForegroundColor Gray
        }
    } catch {
        Write-Host "Warning: Failed to stop remote sessions via API: $_" -ForegroundColor Red
    }
} else {
    Write-Host "Note: NGROK_API_KEY is not set in your .env file." -ForegroundColor Gray
    Write-Host "To automatically close tunnels running on other devices, please generate an API Key at:" -ForegroundColor Gray
    Write-Host "https://dashboard.ngrok.com/api-keys" -ForegroundColor Cyan
    Write-Host "and add it to your .env file as: NGROK_API_KEY=your_api_key_here" -ForegroundColor Gray
    Write-Host ""
}

#
# Завершение всех процессов ngrok
#
Write-Host 'Stopping existing ngrok processes...' -ForegroundColor Yellow

Get-CimInstance Win32_Process |
    Where-Object Name -eq 'ngrok.exe' |
    ForEach-Object {
        try {
            Stop-Process -Id $_.ProcessId -Force
            Write-Host "Stopped PID $($_.ProcessId)"
        }
        catch {
        }
    }

#
# Ожидание завершения
#
$timeout = 15

for ($i = 0; $i -lt $timeout; $i++) {

    $running = Get-Process ngrok -ErrorAction SilentlyContinue

    if (-not $running) {
        break
    }

    Start-Sleep -Seconds 1
}

#
# Дать серверу ngrok время освободить соединение
#
Start-Sleep -Seconds 3

#
# Очистить старый Web UI (если был)
#
try {
    Invoke-RestMethod 'http://127.0.0.1:4040/api/tunnels' | Out-Null
}
catch {
}

#
# Запуск нового туннеля
#
$certFile = "C:\Users\onela\.certs\localhost+2.pem"
$keyFile = "C:\Users\onela\.certs\localhost+2-key.pem"
$protocol = "http"
$extraArgs = @()

if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
    $protocol = "https"
    $extraArgs += "--upstream-tls-verify=false"
    Write-Host "Detected HTTPS configuration. Tunnel will target: https://localhost:$Port" -ForegroundColor Cyan
} else {
    Write-Host "Tunnel will target: http://localhost:$Port" -ForegroundColor Cyan
}

$targetUrl = "${protocol}://localhost:$Port"

Write-Host "Starting ngrok process in background..." -ForegroundColor Green

# Запускаем в отдельном окне PowerShell, чтобы не блокировать текущий скрипт
$argList = @("http", $targetUrl) + $extraArgs
$ngrokProcess = Start-Process $NgrokExe -ArgumentList $argList -PassThru -WindowStyle Normal

if (-not $ngrokProcess) {
    Write-Host "[ERROR] Failed to start ngrok process." -ForegroundColor Red
    exit 1
}

#
# Ожидание запуска API
#
$api = $null
Write-Host "Waiting for ngrok API to respond..." -ForegroundColor Yellow

for ($i = 0; $i -lt 20; $i++) {

    try {

        $api = Invoke-RestMethod 'http://127.0.0.1:4040/api/tunnels'

        if ($api.tunnels.Count -gt 0) {
            break
        }
    }
    catch {
    }

    Start-Sleep -Seconds 1
}

if ($api -and $api.tunnels.Count -gt 0) {
    $publicUrl = $api.tunnels[0].public_url
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "  NGROK TUNNEL STARTED SUCCESSFULLY!                            " -ForegroundColor Green
    Write-Host "  Target URL: $targetUrl                                        " -ForegroundColor Gray
    Write-Host "  Public URL: $publicUrl                                        " -ForegroundColor Green
    Write-Host "  Web Admin:  http://127.0.0.1:4040                             " -ForegroundColor Gray
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[ERROR] Failed to retrieve public URL from ngrok API. Please check the ngrok terminal." -ForegroundColor Red
}
