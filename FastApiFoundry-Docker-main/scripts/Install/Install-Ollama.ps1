# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Ollama Installer
# =============================================================================
# Description:
#   Installs Ollama with the official PowerShell installer:
#     irm https://ollama.com/install.ps1 | iex
#
# File: scripts\Install\Install-Ollama.ps1
# Project: AI Assistant (ai_assist)
# =============================================================================

param(
    [switch]$SkipIfExists,
    [switch]$DiagnosticsOnly
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

function Get-OllamaPath {
    $cmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'),
        (Join-Path $env:ProgramFiles 'Ollama\ollama.exe'),
        (Join-Path $env:USERPROFILE 'AppData\Local\Programs\Ollama\ollama.exe')
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) { return $candidate }
    }
    return $null
}

function Assert-InvokeRestMethodAvailable {
    $irmCommand = Get-Command irm -ErrorAction SilentlyContinue
    $invokeRestMethod = Get-Command Invoke-RestMethod -ErrorAction SilentlyContinue

    if (-not $irmCommand -or -not $invokeRestMethod) {
        Write-Host 'PowerShell command irm / Invoke-RestMethod is unavailable.' -ForegroundColor Red
        return $false
    }
    return $true
}

function Install-OllamaViaOfficialScript {
    if (-not (Assert-InvokeRestMethodAvailable)) {
        return $false
    }

    Write-Host 'Installing Ollama via official PowerShell script...' -ForegroundColor Yellow
    Write-Host 'Running: irm https://ollama.com/install.ps1 | iex' -ForegroundColor Cyan
    try {
        irm https://ollama.com/install.ps1 | iex
        return $true
    } catch {
        Write-Host "Official Ollama installer failed: $_" -ForegroundColor Red
        return $false
    }
}

Write-Host 'Ollama - Installer' -ForegroundColor Cyan
Write-Host ('=' * 50)

$ollamaPath = Get-OllamaPath
if ($ollamaPath) {
    Write-Host "Ollama is already installed: $ollamaPath" -ForegroundColor Green
    try { & $ollamaPath --version } catch { }
    if ($SkipIfExists -or $DiagnosticsOnly) { exit 0 }
    exit 0
}

if ($DiagnosticsOnly) {
    Write-Host 'Ollama not installed.' -ForegroundColor Yellow
    exit 0
}

$installed = Install-OllamaViaOfficialScript

if (-not $installed) {
    Write-Host 'Automatic Ollama installation failed.' -ForegroundColor Red
    Write-Host 'Manual install: https://ollama.com/download' -ForegroundColor Cyan
    exit 1
}

$env:PATH = [System.Environment]::GetEnvironmentVariable('PATH', 'Machine') + ';' +
            [System.Environment]::GetEnvironmentVariable('PATH', 'User')

$ollamaPath = Get-OllamaPath
if ($ollamaPath) {
    Write-Host "Ollama installed: $ollamaPath" -ForegroundColor Green
    Write-Host 'Start server manually if needed: ollama serve' -ForegroundColor Cyan
    exit 0
}

Write-Host 'Ollama installer finished, but ollama.exe was not found in this session.' -ForegroundColor Yellow
Write-Host 'Open a new terminal and run: ollama serve' -ForegroundColor Cyan
exit 0
