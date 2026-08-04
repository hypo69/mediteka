# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Установщик Microsoft Foundry Local
# =============================================================================
# Description:
#   Устанавливает Microsoft Foundry Local CLI через winget.
#   После установки запускает сервис и предлагает скачать модель.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Foundry.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Foundry.ps1 -Model "qwen3-0.6b-generic-cpu:4"
#
# File: scripts\Install\Install-Foundry.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Обновлён заголовок и проект
#   - Комментарии переведены на русский
# Author: hypo69
# Copyright: © 2024 - 2026 hypo69
# License: MIT
# =============================================================================

param(
    [string]$Model = "qwen3-0.6b-generic-cpu:4",
    [switch]$SkipIfExists,
    [switch]$DiagnosticsOnly,
    [switch]$SkipServiceStart,
    [switch]$SkipModelDownload
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

function Test-WingetAvailable {
    $cmd = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $cmd) { return $false }

    try {
        $null = & winget --version 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Ensure-Winget {
    if (Test-WingetAvailable) { return $true }

    $wingetScript = Join-Path $Root 'scripts\Install\Install-Winget.ps1'
    if (-not (Test-Path $wingetScript)) {
        Write-Host 'Install-Winget.ps1 not found.' -ForegroundColor Red
        return $false
    }

    & $wingetScript -SkipIfExists
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH", "User")
    return (Test-WingetAvailable)
}

Write-Host "Microsoft Foundry Local - Installer" -ForegroundColor Cyan
Write-Host ("=" * 50)

# --- Checking existing installation ---
if (Get-Command foundry -ErrorAction SilentlyContinue) {
    $ver = & foundry --version 2>&1
    Write-Host "Foundry is already installed: $ver" -ForegroundColor Green
    if ($DiagnosticsOnly -or $SkipIfExists) {
        try { & foundry service status 2>$null } catch { }
        exit 0
    }
} else {
    if ($DiagnosticsOnly) {
        Write-Host "Foundry not installed." -ForegroundColor Yellow
        exit 0
    }

    # --- Installation via winget ---
    if (-not (Ensure-Winget)) {
        Write-Host "winget not found and automatic installation failed." -ForegroundColor Red
        Write-Host "Install App Installer from the Microsoft Store:" -ForegroundColor Cyan
        Write-Host "  https://apps.microsoft.com/detail/9NBLGGH4NNS1" -ForegroundColor Gray
        exit 1
    }

    Write-Host "`nInstalling Microsoft Foundry Local..." -ForegroundColor Yellow
    try {
        winget install Microsoft.FoundryLocal --accept-source-agreements --accept-package-agreements
        Write-Host "Foundry Local installed" -ForegroundColor Green
    } catch {
        Write-Host "Error installing via winget: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Install manually:" -ForegroundColor Cyan
        Write-Host "  winget install Microsoft.FoundryLocal" -ForegroundColor Gray
        Write-Host "  or download from: https://aka.ms/foundry-local" -ForegroundColor Gray
        exit 1
    }

    # Update PATH in the current session
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH", "User")
}

# --- Service Startup ---
if ($SkipServiceStart) {
    Write-Host "`nService start skipped (-SkipServiceStart)" -ForegroundColor Gray
} else {
    Write-Host "`nStarting Foundry service..." -ForegroundColor Yellow
    try {
        & foundry service start
        Start-Sleep 3
        Write-Host "Service started" -ForegroundColor Green
    } catch {
        Write-Host "Failed to start service: $_" -ForegroundColor Yellow
        Write-Host "Start manually: foundry service start" -ForegroundColor Cyan
    }
}

# --- Downloading Model ---
if ($SkipModelDownload) {
    Write-Host "`nModel download skipped (-SkipModelDownload)" -ForegroundColor Gray
} else {
    Write-Host "`nDownloading model: $Model" -ForegroundColor Yellow
    Write-Host "This may take a few minutes..." -ForegroundColor Gray
    try {
        & foundry model download $Model
        Write-Host "Model downloaded: $Model" -ForegroundColor Green
    } catch {
        Write-Host "Failed to download model: $_" -ForegroundColor Yellow
        Write-Host "Download manually: foundry model download $Model" -ForegroundColor Cyan
    }
}

# --- Check ---
if (-not $SkipServiceStart) {
    Write-Host "`nChecking API..." -ForegroundColor Yellow
    Start-Sleep 2
    try {
        $response = Invoke-RestMethod "http://localhost:50477/v1/models" -TimeoutSec 5
        Write-Host "Foundry API available on port 50477" -ForegroundColor Green
        Write-Host "Models loaded: $($response.data.Count)" -ForegroundColor Gray
    } catch {
        Write-Host "API not yet available — Foundry may be using a different port." -ForegroundColor Yellow
        Write-Host "The server will find it automatically upon startup." -ForegroundColor Cyan
    }
}

Write-Host "`n$("=" * 50)" -ForegroundColor Green
Write-Host "Foundry Local is ready to use!" -ForegroundColor Green
Write-Host ""
Write-Host "Start the FastAPI server:"
Write-Host "  venv\Scripts\python.exe run.py"
