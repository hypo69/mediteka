# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Chromium for Testing Setup
# =============================================================================
# Description:
#   Downloads Chrome for Testing (stable) via @puppeteer/browsers into bin/chromium/.
#   After install, writes the chromium executable path to config.json under
#   browser.chromium_path so the web UI launcher can use it.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Chromium.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Chromium.ps1 -Channel canary
#
# File: scripts/Install/Install-Chromium.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [string]$Channel = 'stable'
)

$ErrorActionPreference = 'Stop'
$Root      = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$BinDir    = Join-Path $Root 'bin'
$ChromeDir = Join-Path $BinDir 'chromium'
$CfgPath   = Join-Path $Root 'config.json'

Write-Host ''
Write-Host '🌐 Chromium for Testing Setup' -ForegroundColor Cyan
Write-Host ('=' * 60) -ForegroundColor Cyan

# --- 1. Check node / npx ---

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    Write-Host '❌ npx not found. Install Node.js first: https://nodejs.org' -ForegroundColor Red
    exit 1
}

# --- 2. Create target directory ---

if (-not (Test-Path $ChromeDir)) {
    New-Item -ItemType Directory -Path $ChromeDir -Force | Out-Null
}

# --- 3. Download Chrome for Testing ---

Write-Host "📦 Installing chrome@$Channel into bin\chromium\ ..." -ForegroundColor Yellow

try {
    npx --yes @puppeteer/browsers install "chrome@$Channel" --path $ChromeDir
} catch {
    Write-Host "❌ Download failed: $_" -ForegroundColor Red
    exit 1
}

# --- 4. Locate the executable ---

$exe = Get-ChildItem -Path $ChromeDir -Filter 'chrome.exe' -Recurse -ErrorAction SilentlyContinue |
       Select-Object -First 1

if (-not $exe) {
    # Linux/macOS fallback name
    $exe = Get-ChildItem -Path $ChromeDir -Filter 'chrome' -Recurse -ErrorAction SilentlyContinue |
           Select-Object -First 1
}

if (-not $exe) {
    Write-Host '⚠️  chrome executable not found after install — check bin\chromium\ manually.' -ForegroundColor Yellow
} else {
    Write-Host "✅ Chromium executable: $($exe.FullName)" -ForegroundColor Green

    # --- 5. Write path to config.json ---

    if (Test-Path $CfgPath) {
        try {
            $cfg = Get-Content $CfgPath -Raw | ConvertFrom-Json

            if (-not $cfg.browser) {
                $cfg | Add-Member -NotePropertyName 'browser' -NotePropertyValue ([PSCustomObject]@{})
            }
            $cfg.browser | Add-Member -NotePropertyName 'chromium_path' -NotePropertyValue $exe.FullName -Force
            $cfg.browser | Add-Member -NotePropertyName 'channel'        -NotePropertyValue $Channel      -Force

            $cfg | ConvertTo-Json -Depth 10 | Set-Content $CfgPath -Encoding UTF8
            Write-Host "✅ config.json: browser.chromium_path = $($exe.FullName)" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Could not update config.json: $_" -ForegroundColor Yellow
        }
    }
}

Write-Host ''
Write-Host '✅ Chromium setup complete!' -ForegroundColor Green
