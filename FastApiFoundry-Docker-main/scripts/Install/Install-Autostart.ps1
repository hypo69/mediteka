# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Регистрация автозапуска в Планировщике заданий Windows
# =============================================================================
# Description:
#   Создаёт задание в Windows Task Scheduler, которое запускает autostart.ps1
#   при входе пользователя (скрытое окно, вывод в лог).
#   Требует запуска от имени администратора.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Autostart.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Autostart.ps1 -Uninstall
#
# File: scripts\Install\Install-Autostart.ps1
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
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'

$TaskName   = 'FastApiFoundry-Autostart'
$Root       = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Script     = Join-Path $Root 'autostart.ps1'
$LogDir     = Join-Path $Root 'logs'
$LogFile    = Join-Path $LogDir 'autostart.log'

# Administrator rights check
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
        ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host '❌ Administrator rights required. Run as Admin.' -ForegroundColor Red
    exit 1
}

# Task removal
if ($Uninstall) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ Task '$TaskName' deleted." -ForegroundColor Green
    } else {
        Write-Host "⚠️ Task '$TaskName' not found." -ForegroundColor Yellow
    }
    exit 0
}

# Checking autostart.ps1
if (-not (Test-Path $Script)) {
    Write-Host "❌ autostart.ps1 not found: $Script" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Arguments for powershell.exe (hidden launch, output to log)
$PsArgs = "-NonInteractive -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Script`""

$Action  = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $PsArgs -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

# Remove old task if it exists
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action   $Action `
    -Trigger  $Trigger `
    -Settings $Settings `
    -RunLevel Highest `
    -Description 'FastAPI Foundry autostart upon login' | Out-Null

Write-Host "✅ Task '$TaskName' registered." -ForegroundColor Green
Write-Host "📋 Launch log: $LogFile" -ForegroundColor Cyan
Write-Host "To remove: .\scripts\Install\Install-Autostart.ps1 -Uninstall" -ForegroundColor Gray
