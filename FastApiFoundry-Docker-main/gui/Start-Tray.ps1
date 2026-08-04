# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Start Tray Icon for AI Assistant
# =============================================================================
# Description:
#   Launches gui/tray.py in background (hidden window).
#   Installs pystray + Pillow if missing.
#   Called from start.ps1 after FastAPI server starts.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\gui\Start-Tray.ps1
#
# File: gui/Start-Tray.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

$ErrorActionPreference = 'Continue'
$Root   = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $Root 'venv\Scripts\python.exe'
$Tray   = Join-Path $PSScriptRoot 'tray.py'
$PidFile = Join-Path $env:TEMP 'ai-assist-tray.pid'

if (-not (Test-Path $Python)) {
    Write-Host '❌ venv not found. Run install.ps1 first.' -ForegroundColor Red
    exit 1
}

# Kill previous tray instance
if (Test-Path $PidFile) {
    $oldPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($oldPid) {
        try { Stop-Process -Id $oldPid -Force -ErrorAction Stop } catch { }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

# Ensure dependencies
& $Python -m pip install pystray Pillow --quiet 2>&1 | Out-Null

Write-Host '🖥️ Starting tray icon...' -ForegroundColor Cyan

$proc = Start-Process -FilePath $Python `
    -ArgumentList $Tray `
    -WindowStyle Hidden `
    -PassThru `
    -WorkingDirectory $Root

if ($proc) {
    $proc.Id | Set-Content $PidFile -Encoding UTF8
    Write-Host "✅ Tray icon started (PID: $($proc.Id))" -ForegroundColor Green
} else {
    Write-Host '❌ Failed to start tray icon.' -ForegroundColor Red
}
