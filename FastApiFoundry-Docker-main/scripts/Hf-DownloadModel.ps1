# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Скачивание HuggingFace модели
# =============================================================================
# Описание:
#   Скачивает модель с HuggingFace Hub через FastAPI Foundry API.
#   Для закрытых моделей (Gemma, Llama) нужен HF токен.
#
# Примеры:
#   .\hf-download-model.ps1 -ModelId "google/gemma-2b"
#   .\hf-download-model.ps1 -ModelId "google/gemma-2b" -Token "hf_..."
#   .\hf-download-model.ps1 -ModelId "microsoft/phi-2"
#
# File: scripts/hf-download-model.ps1
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$ModelId,

    [string]$Token = "",

    [string]$ApiBase = "http://localhost:9696/api/v1"
)

$ErrorActionPreference = 'Continue'

Write-Host "🤗 HuggingFace Model Download" -ForegroundColor Cyan
Write-Host "Model: $ModelId" -ForegroundColor Yellow

# Загрузка токена из .env если не передан
if (-not $Token) {
    $envPath = Join-Path $PSScriptRoot ".." ".env"
    if (Test-Path $envPath) {
        $envContent = Get-Content $envPath | Where-Object { $_ -match '^HF_TOKEN=' }
        if ($envContent) {
            $Token = ($envContent -split '=', 2)[1].Trim()
            Write-Host "✅ HF_TOKEN loaded from .env" -ForegroundColor Green
        }
    }
}

if (-not $Token) {
    Write-Host "⚠️ No HF token. Closed models (Gemma, Llama) will fail." -ForegroundColor Yellow
    Write-Host "   Get token: https://huggingface.co/settings/tokens" -ForegroundColor Gray
}

# Проверка доступности сервера
try {
    $health = Invoke-RestMethod -Uri "$ApiBase/health" -TimeoutSec 5
    Write-Host "✅ Server is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Server not available at $ApiBase" -ForegroundColor Red
    Write-Host "   Start the server first: python run.py" -ForegroundColor Yellow
    exit 1
}

# Запрос на скачивание
$body = @{ model_id = $ModelId }
if ($Token) { $body.token = $Token }

Write-Host "⬇️ Starting download (this may take several minutes)..." -ForegroundColor Yellow

try {
    $result = Invoke-RestMethod -Uri "$ApiBase/hf/models/download" `
        -Method POST `
        -ContentType "application/json" `
        -Body ($body | ConvertTo-Json) `
        -TimeoutSec 3600

    if ($result.success) {
        Write-Host "✅ Downloaded: $ModelId" -ForegroundColor Green
        Write-Host "   Path: $($result.path)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Download failed: $($result.error)" -ForegroundColor Red
        if ($result.error -match "401|403|license") {
            Write-Host "💡 Accept the license at: https://huggingface.co/$ModelId" -ForegroundColor Cyan
        }
        exit 1
    }
} catch {
    Write-Host "❌ Request error: $_" -ForegroundColor Red
    exit 1
}
