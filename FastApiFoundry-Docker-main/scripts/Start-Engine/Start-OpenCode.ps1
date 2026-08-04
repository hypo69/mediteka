# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Start OpenCode Server
# =============================================================================
# Description:
#   Starts OpenCode server if enabled and auto_start=true in config.json.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Start-Engine\Start-OpenCode.ps1 `
#       -Root D:\repos\FastApiFoundry-Docker -Config config.json
#
# File: scripts/Start-Engine/Start-OpenCode.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [string]$Root,
    [string]$Config = 'config.json'
)

$PidFile = Join-Path $env:TEMP 'opencode-foundry.pid'

$enabled   = $false
$autoStart = $false
$host_     = '0.0.0.0'
$port      = 9699
$command   = 'opencode'

try {
    $cfg = Get-Content (Join-Path $Root $Config) -Raw | ConvertFrom-Json
    if ($cfg.opencode) {
        $enabled   = [bool]$cfg.opencode.enabled
        $autoStart = [bool]$cfg.opencode.auto_start
        if ($cfg.opencode.host)    { $host_   = $cfg.opencode.host }
        if ($cfg.opencode.port)    { $port    = [int]$cfg.opencode.port }
        if ($cfg.opencode.command) { $command = $cfg.opencode.command }
    }
} catch {}

if (-not $enabled -or -not $autoStart) {
    Write-Host '💡 OpenCode disabled or auto_start=false — skipping.' -ForegroundColor Gray
    return
}

$exe = Get-Command $command -ErrorAction SilentlyContinue
if (-not $exe) {
    Write-Host '💡 OpenCode not found — skipping. Install: npm install -g opencode-ai' -ForegroundColor Gray
    return
}

$conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($conn) { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue }

Write-Host "🧠 Starting OpenCode on http://localhost:$port ..." -ForegroundColor Cyan

$proc = Start-Process powershell.exe -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $exe.Source,
    'start', '--host', $host_, '--port', "$port"
) -WorkingDirectory $Root -PassThru -WindowStyle Minimized

if ($proc) {
    $proc.Id | Set-Content $PidFile -Encoding UTF8
    Write-Host "✅ OpenCode started (PID: $($proc.Id))" -ForegroundColor Green
} else {
    Write-Host '❌ OpenCode failed to start.' -ForegroundColor Red
}
