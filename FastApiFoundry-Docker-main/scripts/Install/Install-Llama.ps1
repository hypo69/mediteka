# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Настройка llama.cpp
# =============================================================================
# Description:
#   Распаковывает Windows-бинарник llama.cpp из bin\llama-*.zip
#   (если ещё не распакован), затем записывает путь к директории моделей
#   в config.json (секции directories.models и llama_cpp.model_path).
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Llama.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Llama.ps1 -ModelsDir "D:\models"
#
# File: scripts\Install\Install-Llama.ps1
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
    [string]$ModelsDir = "",
    [string]$EnvFile = ""
)

$ErrorActionPreference = 'Continue'
$Root    = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$BinDir  = Join-Path $Root 'bin'
$CfgPath = Join-Path $Root 'config.json'
if (-not $EnvFile) { $EnvFile = Join-Path $Root '.env' }

Write-Host ''
Write-Host '🦙 llama.cpp Setup' -ForegroundColor Cyan
Write-Host ('=' * 60) -ForegroundColor Cyan

# --- 1. Read config.json defaults ---

$cfg = $null
$defaultModelsDir = '~/.models'

if (Test-Path $CfgPath) {
    try {
        $cfg = Get-Content $CfgPath -Raw | ConvertFrom-Json
        $fromCfg = $null
        if ($cfg.PSObject.Properties['directories'] -and $cfg.directories.PSObject.Properties['models']) {
            $fromCfg = $cfg.directories.models
        }
        if ($fromCfg) { $defaultModelsDir = $fromCfg }
    } catch {
        Write-Host "⚠️  Could not read config.json: $_" -ForegroundColor Yellow
    }
}

if (-not $ModelsDir) { $ModelsDir = $defaultModelsDir }

Write-Host "   Models directory : $ModelsDir" -ForegroundColor Gray

# --- 2. Extract llama.cpp zip ---

$zips = Get-ChildItem -Path $BinDir -Filter 'llama-*-bin-win-*.zip' -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending

if (-not $zips) {
    Write-Host '⚠️  No llama.cpp zip found in bin/ — skipping extraction.' -ForegroundColor Yellow
} else {
    $zip      = $zips[0]
    $stem     = [System.IO.Path]::GetFileNameWithoutExtension($zip.Name)
    $destDir  = Join-Path $BinDir $stem
    $serverExe = Join-Path $destDir 'llama-server.exe'

    if (Test-Path $serverExe) {
        Write-Host "✅ Already extracted: $stem" -ForegroundColor Green
    } else {
        Write-Host "📦 Extracting $($zip.Name) → bin\$stem\ ..." -ForegroundColor Yellow
        try {
            if (Test-Path $destDir) { Remove-Item $destDir -Recurse -Force }
            Expand-Archive -Path $zip.FullName -DestinationPath $destDir -Force
            Write-Host "✅ Extracted: $destDir" -ForegroundColor Green
        } catch {
            Write-Host "❌ Extraction failed: $_" -ForegroundColor Red
            exit 1
        }
    }

    # Update bin_version in config.json
    if ($cfg) {
        try {
            if (-not $cfg.llama_cpp) { $cfg | Add-Member -NotePropertyName 'llama_cpp' -NotePropertyValue ([PSCustomObject]@{}) }
            $cfg.llama_cpp | Add-Member -NotePropertyName 'bin_version' -NotePropertyValue $stem -Force
            $cfg.llama_cpp | Add-Member -NotePropertyName 'server_path' -NotePropertyValue $serverExe -Force
            $cfg | ConvertTo-Json -Depth 10 | Set-Content $CfgPath -Encoding UTF8
            Write-Host "✅ config.json: llama_cpp.bin_version = $stem" -ForegroundColor Green
            Write-Host "✅ config.json: llama_cpp.server_path = $serverExe" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Could not update bin_version: $_" -ForegroundColor Yellow
        }
    }

    try {
        $relPath = ".\bin\$stem\llama-server.exe"
        $envContent = if (Test-Path $EnvFile) { Get-Content $EnvFile -Raw } else { '' }
        if ($envContent -notmatch 'LLAMA_SERVER_PATH') {
            Add-Content -Path $EnvFile -Value "`nLLAMA_SERVER_PATH=$relPath"
            Write-Host "✅ .env: LLAMA_SERVER_PATH=$relPath" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Could not update .env LLAMA_SERVER_PATH: $_" -ForegroundColor Yellow
    }
}

# --- 3. Write models directory to config.json ---

if ($cfg) {
    try {
        # Expand ~ to real home path for storage
        $resolvedDir = $ModelsDir -replace '^~', $env:USERPROFILE

        if (-not $cfg.directories) {
            $cfg | Add-Member -NotePropertyName 'directories' -NotePropertyValue ([PSCustomObject]@{}) }
        $cfg.directories | Add-Member -NotePropertyName 'models' -NotePropertyValue $ModelsDir -Force

        if (-not $cfg.llama_cpp) {
            $cfg | Add-Member -NotePropertyName 'llama_cpp' -NotePropertyValue ([PSCustomObject]@{}) }
        $cfg.llama_cpp | Add-Member -NotePropertyName 'model_path' -NotePropertyValue $resolvedDir -Force

        $cfg | ConvertTo-Json -Depth 10 | Set-Content $CfgPath -Encoding UTF8
        Write-Host "✅ config.json: directories.models = $ModelsDir" -ForegroundColor Green
        Write-Host "✅ config.json: llama_cpp.model_path = $resolvedDir" -ForegroundColor Green
    } catch {
        Write-Host "❌ Could not update config.json: $_" -ForegroundColor Red
    }
}

# --- 4. Create models directory ---

$resolvedDir = $ModelsDir -replace '^~', $env:USERPROFILE
if (-not (Test-Path $resolvedDir)) {
    try {
        New-Item -ItemType Directory -Path $resolvedDir -Force | Out-Null
        Write-Host "✅ Created models directory: $resolvedDir" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Could not create directory: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ Models directory exists: $resolvedDir" -ForegroundColor Green
}

Write-Host ''
Write-Host '✅ llama.cpp setup complete!' -ForegroundColor Green
