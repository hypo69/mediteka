# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Настройка интерфейса установки
# =============================================================================
# Описание:
#   Установка Chromium for Testing и запуск временного сервера FastAPI 
#   для предоставления пользователю графического веб-интерфейса настройки.
#
# File: scripts/Install/Step-UserInterface.ps1
# Project: Наш интеллектуальный помощник
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$Python,
    [switch]$NoGui
)

Write-Host "`nChromium for Testing..." -ForegroundColor Yellow
$chromiumExe = $null
try {
    $cfg = Get-Content (Join-Path $Root 'config.json') -Raw | ConvertFrom-Json
    $chromiumExe = $cfg.browser.chromium_path
} catch { }

if ($chromiumExe -and (Test-Path $chromiumExe)) {
    Write-Host "  Already installed: $chromiumExe" -ForegroundColor Gray
} else {
    $answerChrome = Read-Host '  Install Chromium for Testing (opens UI in local browser)? (y/N)'
    if ($answerChrome -eq 'y' -or $answerChrome -eq 'Y') {
        $chromiumScript = Get-InstallScriptPath 'Install-Chromium.ps1'
        if (Test-Path $chromiumScript) {
            try { & $chromiumScript } catch { Write-Host "  Chromium install error: $_" -ForegroundColor Yellow }
        } else {
            Write-Host '  scripts\Install\Install-Chromium.ps1 not found - skipping' -ForegroundColor Yellow
        }
    } else {
        Write-Host '  Skipped' -ForegroundColor Gray
    }
}

if ($NoGui) { return }

$answerGui = Read-Host "`nLaunching GUI installer? (y/N)"
if ($answerGui -ne 'y' -and $answerGui -ne 'Y') {
    Write-Host '  Skipped' -ForegroundColor Gray
    return
}

Write-Host '  Launching GUI installer...' -ForegroundColor Cyan
$appPort = 9696
try {
    $cfg = Get-Content (Join-Path $Root 'config.json') -Raw | ConvertFrom-Json
    if ($cfg.fastapi_server.port) { $appPort = [int]$cfg.fastapi_server.port }
} catch { }

$fastApiProc = Start-Process -FilePath $Python `
                             -ArgumentList 'run.py' `
                             -WorkingDirectory $Root `
                             -PassThru `
                             -WindowStyle Minimized

$installerPidDir = Join-Path $Root 'scripts\Install'
if (-not (Test-Path $installerPidDir)) { New-Item -ItemType Directory -Path $installerPidDir -Force | Out-Null }
$fastApiProc.Id | Out-File (Join-Path $installerPidDir '.installer.pid') -Encoding UTF8
$fastApiProc.Id | Out-File (Join-Path $env:TEMP 'fastapi-foundry-installer.pid') -Encoding UTF8

$chromiumExe = $null
try {
    $cfg = Get-Content (Join-Path $Root 'config.json') -Raw | ConvertFrom-Json
    $chromiumExe = $cfg.browser.chromium_path
} catch { }

Write-Host "  Waiting for FastAPI on port $appPort..." -ForegroundColor Gray
$deadline = (Get-Date).AddSeconds(30)
$ready = $false
while ((Get-Date) -lt $deadline) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$appPort/api/v1/health" `
                               -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -lt 500) { $ready = $true; break }
    } catch { }
    Start-Sleep -Milliseconds 600
}

if ($ready) {
    $url = "http://localhost:$appPort/install"
    Write-Host "  Opening $url" -ForegroundColor Green
    if ($chromiumExe -and (Test-Path $chromiumExe)) {
        Start-Process -FilePath $chromiumExe -ArgumentList "--app=$url"
    } else {
        Start-Process $url
    }
    Write-Host '  Complete the remaining steps in the browser.' -ForegroundColor Cyan
    Write-Host '  The server will keep running after this script exits.' -ForegroundColor Gray
} else {
    Write-Host '  FastAPI did not start in time - falling back to CLI install.' -ForegroundColor Yellow
    $fastApiProc | Stop-Process -Force -ErrorAction SilentlyContinue
}
