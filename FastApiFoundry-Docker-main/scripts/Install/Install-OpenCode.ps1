# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: OpenCode Installer
# =============================================================================
# Description:
#   Installs OpenCode on Windows through Node.js/npm:
#     npm install -g opencode-ai
#
# File: scripts\Install\Install-OpenCode.ps1
# Project: AI Assistant (ai_assist)
# =============================================================================

param([switch]$DiagnosticsOnly)

$ErrorActionPreference = 'Stop'

Write-Host 'OpenCode - Installer' -ForegroundColor Cyan
Write-Host ('=' * 50)

$npm = Get-Command npm -ErrorAction SilentlyContinue
$opencode = Get-Command opencode -ErrorAction SilentlyContinue

if ($DiagnosticsOnly) {
    Write-Host ("npm available: " + [bool]$npm) -ForegroundColor Gray
    Write-Host ("opencode available: " + [bool]$opencode) -ForegroundColor Gray
    exit 0
}

if ($opencode) {
    Write-Host "OpenCode is already available: $($opencode.Source)" -ForegroundColor Green
    try {
        & opencode --version
        if ($LASTEXITCODE -ne 0) {
            Write-Host "OpenCode command exists, but version check failed with code $LASTEXITCODE" -ForegroundColor Red
            exit $LASTEXITCODE
        }
    } catch {
        Write-Host "OpenCode command exists, but cannot run: $_" -ForegroundColor Red
        exit 1
    }
    exit 0
}

$answer = Read-Host 'Install OpenCode now with npm install -g opencode-ai? (y/N)'
if ($answer -ne 'y' -and $answer -ne 'Y') {
    Write-Host 'OpenCode install skipped by user.' -ForegroundColor Gray
    exit 0
}

if (-not $npm) {
    Write-Host 'npm was not found. Install Node.js LTS, then run:' -ForegroundColor Yellow
    Write-Host '  npm install -g opencode-ai' -ForegroundColor Cyan
    exit 1
}

Write-Host 'Running: npm install -g opencode-ai' -ForegroundColor Cyan
try {
    & npm install -g opencode-ai
    if ($LASTEXITCODE -ne 0) {
        Write-Host "npm install exited with code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "OpenCode installer failed: $_" -ForegroundColor Red
    exit 1
}

$env:PATH = [System.Environment]::GetEnvironmentVariable('PATH', 'Machine') + ';' +
            [System.Environment]::GetEnvironmentVariable('PATH', 'User')

$opencode = Get-Command opencode -ErrorAction SilentlyContinue
if ($opencode) {
    Write-Host "OpenCode installed: $($opencode.Source)" -ForegroundColor Green
    try {
        & opencode --version
        if ($LASTEXITCODE -ne 0) {
            Write-Host "OpenCode installed, but version check failed with code $LASTEXITCODE" -ForegroundColor Red
            exit $LASTEXITCODE
        }
    } catch {
        Write-Host "OpenCode installed, but cannot run: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host 'OpenCode was installed, but opencode is not visible in this shell yet.' -ForegroundColor Yellow
    Write-Host 'Open a new PowerShell window and run: opencode' -ForegroundColor Cyan
}

Write-Host 'OpenCode installer step complete.' -ForegroundColor Green
exit 0
