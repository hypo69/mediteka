# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Package Manager Installer
# =============================================================================
# Description:
#   Ensures winget is available. If winget is missing, downloads the official
#   App Installer MSIX bundle from Microsoft and installs it with Add-AppxPackage.
#
# File: scripts\Install\Install-Winget.ps1
# Project: AI Assistant (ai_assist)
# =============================================================================

param(
    [switch]$SkipIfExists
)

$ErrorActionPreference = 'Stop'

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

Write-Host 'winget - Installer' -ForegroundColor Cyan
Write-Host ('=' * 50)

if (Test-WingetAvailable) {
    Write-Host 'winget is already available.' -ForegroundColor Green
    if ($SkipIfExists) { exit 0 }
    exit 0
}

Write-Host 'winget was not found. Installing Microsoft App Installer...' -ForegroundColor Yellow

$downloadUrl = 'https://aka.ms/getwinget'
$tempDir = Join-Path $env:TEMP 'aiassistant-winget'
$bundlePath = Join-Path $tempDir 'Microsoft.DesktopAppInstaller.msixbundle'

try {
    if (-not (Test-Path $tempDir)) {
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    }

    Write-Host "Downloading: $downloadUrl" -ForegroundColor Gray
    Invoke-WebRequest -Uri $downloadUrl -OutFile $bundlePath -UseBasicParsing

    Write-Host 'Installing App Installer package...' -ForegroundColor Gray
    Add-AppxPackage -Path $bundlePath

    $env:PATH = [System.Environment]::GetEnvironmentVariable('PATH', 'Machine') + ';' +
                [System.Environment]::GetEnvironmentVariable('PATH', 'User')

    if (Test-WingetAvailable) {
        Write-Host 'winget installed successfully.' -ForegroundColor Green
        exit 0
    }

    Write-Host 'App Installer finished, but winget is not available in this session yet.' -ForegroundColor Yellow
    Write-Host 'Open a new terminal and run install.ps1 again if needed.' -ForegroundColor Cyan
    exit 1
} catch {
    Write-Host "Failed to install winget: $_" -ForegroundColor Red
    Write-Host 'Manual install: https://apps.microsoft.com/detail/9NBLGGH4NNS1' -ForegroundColor Cyan
    exit 1
}
