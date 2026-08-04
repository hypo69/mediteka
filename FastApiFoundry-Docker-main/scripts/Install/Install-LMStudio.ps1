# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Установщик LM Studio
# =============================================================================
# Description:
#   Проверяет наличие LM Studio CLI (`lms`) и при согласии пользователя
#   устанавливает LM Studio официальной командой:
#     irm https://lmstudio.ai/install.ps1 | iex
#
#   Скрипт защищённо проверяет наличие Invoke-RestMethod / irm и
#   останавливается с объяснением, если PowerShell не поддерживает этот alias.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-LMStudio.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-LMStudio.ps1 -SkipIfExists
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-LMStudio.ps1 -DiagnosticsOnly
#
# File: scripts\Install\Install-LMStudio.ps1
# Project: AI Assistant (ai_assist)
# =============================================================================

param(
    [switch]$SkipIfExists,
    [switch]$DiagnosticsOnly,
    [switch]$AssumeYes
)

$ErrorActionPreference = 'Stop'

function Get-LMStudioCliPath {
    <#
    .SYNOPSIS
        Finds the LM Studio CLI executable if it is already installed.
    #>
    $cmd = Get-Command lms -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        (Join-Path $env:USERPROFILE '.lmstudio\bin\lms.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\LM Studio\resources\app\.webpack\lms.exe'),
        (Join-Path $env:LOCALAPPDATA 'LM Studio\lms.exe')
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) { return $candidate }
    }
    return $null
}

function Assert-InvokeRestMethodAvailable {
    <#
    .SYNOPSIS
        Ensures the official LM Studio install command can run.
    .DESCRIPTION
        `irm` is the standard PowerShell alias for Invoke-RestMethod.
        It downloads web content. LM Studio's official Windows command uses it
        to download the installer bootstrap script before passing it to `iex`.
    #>
    $irmCommand = Get-Command irm -ErrorAction SilentlyContinue
    $invokeRestMethod = Get-Command Invoke-RestMethod -ErrorAction SilentlyContinue

    if (-not $irmCommand -or -not $invokeRestMethod) {
        Write-Host '❌ PowerShell command irm / Invoke-RestMethod is unavailable.' -ForegroundColor Red
        Write-Host ''
        Write-Host 'Что это значит:' -ForegroundColor Cyan
        Write-Host '  irm — это стандартный alias PowerShell для Invoke-RestMethod.' -ForegroundColor Gray
        Write-Host '  Он скачивает HTTP/HTTPS содержимое; официальный установщик LM Studio использует его.' -ForegroundColor Gray
        Write-Host ''
        Write-Host 'Что делать:' -ForegroundColor Cyan
        Write-Host '  1. Запустите установку из PowerShell 7+ или Windows PowerShell 5.1+.' -ForegroundColor Gray
        Write-Host '  2. Если alias удалён политиками, восстановите его или используйте чистую PowerShell-сессию.' -ForegroundColor Gray
        Write-Host '  3. После этого повторите установку.' -ForegroundColor Gray
        throw 'irm / Invoke-RestMethod is required for LM Studio installation'
    }
}

function Invoke-LMStudioOfficialInstall {
    <#
    .SYNOPSIS
        Runs the official LM Studio Windows install command.
    #>
    Assert-InvokeRestMethodAvailable
    Write-Host '  Running official command: irm https://lmstudio.ai/install.ps1 | iex' -ForegroundColor Cyan

    try {
        irm https://lmstudio.ai/install.ps1 | iex
    } catch {
        Write-Host "❌ LM Studio official installer failed: $_" -ForegroundColor Red
        Write-Host 'Manual install: https://lmstudio.ai/' -ForegroundColor Cyan
        throw
    }
}

Write-Host 'LM Studio - Installer' -ForegroundColor Cyan
Write-Host ('=' * 50)

$lmsPath = Get-LMStudioCliPath
if ($lmsPath) {
    Write-Host "LM Studio CLI already installed: $lmsPath" -ForegroundColor Green
    try { & $lmsPath --version } catch { }
    if ($SkipIfExists) { exit 0 }
} else {
    Write-Host 'LM Studio CLI not found.' -ForegroundColor Yellow
    if ($DiagnosticsOnly) {
        Write-Host 'Diagnostics only: install skipped.' -ForegroundColor Cyan
        exit 0
    }

    $install = $AssumeYes
    if (-not $install) {
        $answer = Read-Host 'Install LM Studio now? (y/N)'
        $install = ($answer -eq 'y' -or $answer -eq 'Y')
    }

    if (-not $install) {
        Write-Host 'LM Studio install skipped by user.' -ForegroundColor Gray
        exit 0
    }

    Invoke-LMStudioOfficialInstall
    Start-Sleep -Seconds 2
}

$lmsPath = Get-LMStudioCliPath
if (-not $lmsPath) {
    Write-Host '⚠️ LM Studio installer finished, but lms CLI was not found in the current session.' -ForegroundColor Yellow
    Write-Host 'Open a new terminal or run LM Studio once, then repeat install if needed.' -ForegroundColor Cyan
    exit 0
}

try {
    if (-not (Get-Command lms -ErrorAction SilentlyContinue)) {
        Write-Host 'Bootstrapping lms into PATH...' -ForegroundColor Cyan
        & $lmsPath bootstrap
    }
} catch {
    Write-Host "⚠️ lms bootstrap warning: $_" -ForegroundColor Yellow
    Write-Host "Manual command: `"$lmsPath`" bootstrap" -ForegroundColor Cyan
}

try {
    $status = & $lmsPath server status 2>&1
    Write-Host "Server status: $status" -ForegroundColor Gray
} catch {
    Write-Host 'LM Studio installed. Start API server from LM Studio Developer tab or run: lms server start' -ForegroundColor Cyan
}

Write-Host ''
Write-Host 'LM Studio installer step complete.' -ForegroundColor Green
