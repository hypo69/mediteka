# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Foundry Smart Launcher
# =============================================================================
# Description:
#   Thin orchestrator. Delegates each startup stage to scripts/Start-Engine/.
#   Stages: tray → update → venv → foundry → mkdocs → llama → opencode → fastapi
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\start.ps1
#   powershell -ExecutionPolicy Bypass -File .\start.ps1 -Config config.json
#
# File: start.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [string]$Config = 'config.json'
)

$ErrorActionPreference = 'Continue'
$Root        = $PSScriptRoot
$StartEngine = Join-Path $Root 'scripts\Start-Engine'

# Set console window icon
try {
    $icoPath = Join-Path $Root 'icon.ico'
    if (Test-Path $icoPath) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class WinApi {
    [DllImport("user32.dll")] public static extern bool SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    [DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
}
'@
        $icon   = [System.Drawing.Icon]::new($icoPath)
        $handle = [WinApi]::GetConsoleWindow()
        [WinApi]::SendMessage($handle, 0x0080, $icon.Handle, [IntPtr]::Zero) | Out-Null  # WM_SETICON small
        [WinApi]::SendMessage($handle, 0x0080, [IntPtr]1, $icon.Handle)       | Out-Null  # WM_SETICON big
    }
} catch {}

Write-Host '🚀 FastAPI Foundry Smart Launcher' -ForegroundColor Cyan
Write-Host ('=' * 60) -ForegroundColor Cyan

# -----------------------------------------------------------------------------
# Step 0: Tray icon — first, watches server state itself
# -----------------------------------------------------------------------------
$TrayScript = Join-Path $Root 'gui\Start-Tray.ps1'
if (Test-Path $TrayScript) {
    try {
        Start-Process powershell.exe -ArgumentList @(
            '-NonInteractive', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $TrayScript
        ) -WindowStyle Hidden
        Write-Host '🖥️ Tray icon launched' -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Could not start tray icon: $_" -ForegroundColor Yellow
    }
}

# -----------------------------------------------------------------------------
# Step 1: Check for updates
# -----------------------------------------------------------------------------
$UpdateScript = Join-Path $Root 'scripts\Update-Project.ps1'
if (Test-Path $UpdateScript) {
    try { & $UpdateScript } catch {
        Write-Host "⚠️ Update check failed: $_" -ForegroundColor Yellow
    }
}

# -----------------------------------------------------------------------------
# Step 2: venv — install if missing
# -----------------------------------------------------------------------------
if (-not (Test-Path "$Root\archive")) {
    New-Item -ItemType Directory -Path "$Root\archive" -Force | Out-Null
}

$venvPath = "$Root\venv\Scripts\python.exe"
if (-not (Test-Path $venvPath)) { $venvPath = "$Root\venv\Scripts\python311.exe" }

if (-not (Test-Path $venvPath)) {
    Write-Host '📦 First launch — installing dependencies...' -ForegroundColor Yellow
    & "$Root\install.ps1"
}

$ActivateScript = "$Root\venv\Scripts\Activate.ps1"
if (Test-Path $ActivateScript) { . $ActivateScript }

# Load .env
function Load-EnvFile {
    param([string]$EnvPath)
    if (-not (Test-Path $EnvPath -PathType Leaf)) { return }
    Get-Content $EnvPath | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match '^([^=]+)=(.*)$') {
            $k = $matches[1].Trim()
            $v = $matches[2].Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($k, $v)
        }
    }
}
Load-EnvFile "$Root\.env"

# -----------------------------------------------------------------------------
# Step 3: Foundry
# -----------------------------------------------------------------------------
& (Join-Path $StartEngine 'Start-Foundry.ps1') -Root $Root

# -----------------------------------------------------------------------------
# Step 4: MkDocs (optional)
# -----------------------------------------------------------------------------
& (Join-Path $StartEngine 'Start-MkDocs.ps1') -Root $Root -VenvPath $venvPath -Config $Config

# -----------------------------------------------------------------------------
# Step 5: llama.cpp (optional)
# -----------------------------------------------------------------------------
& (Join-Path $StartEngine 'Start-Llama.ps1') -Root $Root -Config $Config

# -----------------------------------------------------------------------------
# Step 6: OpenCode (optional)
# -----------------------------------------------------------------------------
& (Join-Path $StartEngine 'Start-OpenCode.ps1') -Root $Root -Config $Config

# -----------------------------------------------------------------------------
# Step 7: FastAPI (blocking)
# -----------------------------------------------------------------------------
& (Join-Path $StartEngine 'Start-FastApi.ps1') -Root $Root -VenvPath $venvPath -Config $Config