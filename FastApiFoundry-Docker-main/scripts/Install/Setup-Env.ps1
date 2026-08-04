# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Настройка переменных окружения
# =============================================================================
# Description:
#   Интерактивный мастер создания или перезаписи файла .env.
#   Копирует .env.example как шаблон, затем запрашивает GitHub-данные,
#   API-ключи, URL Foundry и название окружения.
#   Опционально генерирует криптографически стойкие ключи автоматически.
#   Запускает check_env.py в конце для валидации конфигурации.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Setup-Env.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Setup-Env.ps1 -Force
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Setup-Env.ps1 -GenerateKeys
#
# File: scripts\Install\Setup-Env.ps1
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
    # Overwrite an existing .env without asking for confirmation
    [switch]$Force,
    # Auto-generate API_KEY and SECRET_KEY instead of prompting
    [switch]$GenerateKeys
)

$ErrorActionPreference = 'Continue'
$Root    = $PSScriptRoot
$Project = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

Write-Host '🔐 FastAPI Foundry - Environment Setup' -ForegroundColor Cyan
Write-Host ('=' * 60) -ForegroundColor Cyan

# -----------------------------------------------------------------------------
# Step 1: Check whether .env already exists
# -----------------------------------------------------------------------------
$envPath        = "$Project\.env"
$envExamplePath = "$Project\.env.example"

if ((Test-Path $envPath) -and -not $Force) {
    Write-Host '⚠️ .env file already exists!' -ForegroundColor Yellow
    $response = Read-Host 'Overwrite? (y/N)'
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host '❌ Setup cancelled' -ForegroundColor Red
        exit 0
    }
}

# -----------------------------------------------------------------------------
# Step 2: Copy .env.example as the starting template
# -----------------------------------------------------------------------------
if (Test-Path $envExamplePath) {
    Copy-Item $envExamplePath $envPath -Force
    Write-Host '✅ Copied .env.example to .env' -ForegroundColor Green
} else {
    Write-Host '❌ .env.example not found!' -ForegroundColor Red
    exit 1
}

# -----------------------------------------------------------------------------
# Helper: Generate a URL-safe random key of the given byte length
# -----------------------------------------------------------------------------
function Generate-SecureKey {
    <#
    .SYNOPSIS
        Генерирует криптографически стойкую случайную строку.
    .DESCRIPTION
        Args:
            $Length (int) — длина в байтах (выходная строка длиннее из-за Base64). По умолчанию: 32.

        Returns:
            string — URL-безопасная Base64-строка без '+', '/' и '='.
    .EXAMPLE
        $key = Generate-SecureKey 32
        # $key — случайная строка для использования в .env
    #>
    param([int]$Length = 32)

    $bytes = New-Object byte[] $Length
    [System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
    # Strip non-URL-safe characters so the key can be used directly in .env
    return [Convert]::ToBase64String($bytes) -replace '[+/=]', ''
}

# -----------------------------------------------------------------------------
# Step 3: Auto-generate keys if -GenerateKeys flag is set
# -----------------------------------------------------------------------------
if ($GenerateKeys) {
    Write-Host '🔑 Generating secure keys...' -ForegroundColor Yellow

    $apiKey    = Generate-SecureKey 32
    $secretKey = Generate-SecureKey 64

    # Replace the placeholder values in the copied .env
    $content = Get-Content $envPath
    $content = $content -replace '^API_KEY=.*',    "API_KEY=$apiKey"
    $content = $content -replace '^SECRET_KEY=.*', "SECRET_KEY=$secretKey"
    $content | Set-Content $envPath

    Write-Host "✅ Generated API_KEY: $($apiKey.Substring(0,8))..." -ForegroundColor Green
    Write-Host "✅ Generated SECRET_KEY: $($secretKey.Substring(0,8))..." -ForegroundColor Green
}

# -----------------------------------------------------------------------------
# Step 4: Interactive prompts — press Enter to skip any field
# -----------------------------------------------------------------------------
Write-Host "`n🛠️ Interactive Setup" -ForegroundColor Cyan
Write-Host "Press Enter to skip any field`n" -ForegroundColor Gray

# GitHub credentials (used for private repo access and RAG indexing)
Write-Host '🐙 GitHub Configuration:' -ForegroundColor Yellow
$githubUser = Read-Host 'GitHub Username'
if ($githubUser) {
    $content = Get-Content $envPath
    $content = $content -replace '^GITHUB_USER=.*', "GITHUB_USER=$githubUser"
    $content | Set-Content $envPath
}

$githubPat = Read-Host 'GitHub Personal Access Token (PAT)'
if ($githubPat) {
    $content = Get-Content $envPath
    $content = $content -replace '^GITHUB_PAT=.*', "GITHUB_PAT=$githubPat"
    $content | Set-Content $envPath
}

# API security keys (skip if already generated above)
Write-Host "`n🔑 API Configuration:" -ForegroundColor Yellow
if (-not $GenerateKeys) {
    $apiKey = Read-Host 'API Key (leave empty to generate)'
    if (-not $apiKey) {
        $apiKey = Generate-SecureKey 32
        Write-Host "Generated API Key: $($apiKey.Substring(0,8))..." -ForegroundColor Green
    }

    $secretKey = Read-Host 'Secret Key (leave empty to generate)'
    if (-not $secretKey) {
        $secretKey = Generate-SecureKey 64
        Write-Host "Generated Secret Key: $($secretKey.Substring(0,8))..." -ForegroundColor Green
    }

    $content = Get-Content $envPath
    $content = $content -replace '^API_KEY=.*',    "API_KEY=$apiKey"
    $content = $content -replace '^SECRET_KEY=.*', "SECRET_KEY=$secretKey"
    $content | Set-Content $envPath
}

# Foundry base URL (leave blank to keep the default from .env.example)
Write-Host "`n🤖 Foundry Configuration:" -ForegroundColor Yellow
$foundryUrl = Read-Host 'Foundry Base URL (default: http://localhost:50477/v1)'
if ($foundryUrl) {
    $content = Get-Content $envPath
    $content = $content -replace '^FOUNDRY_BASE_URL=.*', "FOUNDRY_BASE_URL=$foundryUrl"
    $content | Set-Content $envPath
}

# Runtime environment tag (affects logging verbosity and debug features)
Write-Host "`n🌍 Environment Configuration:" -ForegroundColor Yellow
$environment = Read-Host 'Environment (development/production)'
if ($environment) {
    $content = Get-Content $envPath
    $content = $content -replace '^ENVIRONMENT=.*', "ENVIRONMENT=$environment"
    $content | Set-Content $envPath
}

# -----------------------------------------------------------------------------
# Step 5: Validate the resulting .env with the Python checker
# -----------------------------------------------------------------------------
Write-Host "`n✅ Setup completed!" -ForegroundColor Green
Write-Host "📁 Configuration saved to: $envPath" -ForegroundColor Gray

Write-Host "`n🔍 Checking configuration..." -ForegroundColor Cyan
if (Test-Path "$Project\check_env.py") {
    try {
        $pythonPath = "$Project\venv\Scripts\python.exe"
        if (Test-Path $pythonPath) {
            & $pythonPath "$Project\check_env.py"
        } else {
            python "$Project\check_env.py"
        }
    } catch {
        Write-Host "⚠️ Could not run environment check: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️ check_env.py not found, skipping validation" -ForegroundColor Yellow
}

Write-Host "`n🚀 Next steps:" -ForegroundColor Cyan
Write-Host "1. Review and edit .env file if needed" -ForegroundColor Gray
Write-Host "2. Run: python run.py" -ForegroundColor Gray
Write-Host "3. Open: http://localhost:9696" -ForegroundColor Gray

Write-Host "`n💡 Tips:" -ForegroundColor Yellow
Write-Host "- Never commit .env file to Git" -ForegroundColor Gray
Write-Host "- Use strong passwords and tokens" -ForegroundColor Gray
Write-Host "- Run 'python check_env.py' to validate" -ForegroundColor Gray
