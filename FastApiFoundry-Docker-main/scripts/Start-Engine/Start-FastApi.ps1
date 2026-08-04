# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Start FastAPI Server
# =============================================================================
# Description:
#   Stops previous FastAPI instance (by PID file), then starts run.py.
#   Waits for port to become available and opens browser.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Start-Engine\Start-FastApi.ps1 `
#       -Root D:\repos\FastApiFoundry-Docker -VenvPath D:\repos\...\venv\Scripts\python.exe
#
# File: scripts/Start-Engine/Start-FastApi.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [string]$Root,
    [string]$VenvPath,
    [string]$Config = 'config.json'
)

$PidFile = Join-Path $env:TEMP 'fastapi-foundry.pid'

# Stop previous instance
if (Test-Path $PidFile) {
    $oldPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($oldPid) {
        try {
            $p = Get-Process -Id $oldPid -ErrorAction Stop
            $p.Kill(); $p.WaitForExit(5000)
            Write-Host "✅ Previous FastAPI (PID: $oldPid) stopped" -ForegroundColor Green
        } catch {
            Write-Host "💡 Previous FastAPI (PID: $oldPid) already exited" -ForegroundColor Gray
        }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $VenvPath)) {
    Write-Host '❌ venv Python not found!' -ForegroundColor Red
    exit 1
}

$appPort = 9696
try { $appPort = [int](Get-Content (Join-Path $Root $Config) -Raw | ConvertFrom-Json).fastapi_server.port } catch {}

Write-Host '🐍 Starting FastAPI...' -ForegroundColor Cyan
Write-Host "📱 Web UI: http://localhost:$appPort" -ForegroundColor Cyan

$proc = Start-Process -FilePath $VenvPath -ArgumentList 'run.py', '--config', $Config -PassThru -NoNewWindow -WorkingDirectory $Root
$proc.Id | Set-Content $PidFile -Encoding UTF8
Write-Host "💾 PID $($proc.Id) saved to $PidFile" -ForegroundColor Gray

# Wait for port and open browser
for ($i = 1; $i -le 15; $i++) {
    Start-Sleep 1
    try {
        $tcp = [System.Net.Sockets.TcpClient]::new()
        $tcp.Connect('127.0.0.1', $appPort); $tcp.Close()
        Start-Process "http://localhost:$appPort"
        Write-Host "🌐 Browser opened: http://localhost:$appPort" -ForegroundColor Green
        break
    } catch {}
}

$proc.WaitForExit()
