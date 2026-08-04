# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Конфигурация и инициализация данных
# =============================================================================
# Описание:
#   Создание файлов конфигурации (.env, config.json), настройка папок логов,
#   установка RAG-зависимостей, Tesseract OCR и инициализация баз данных SQLite.
#   Использует скрипт install_rag_deps.py для умного выбора FAISS (CPU/GPU).
#
# File: scripts/Install/Step-ConfigAndData.ps1
# Project: Наш интеллектуальный помощник
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$Python,
    [switch]$SkipRag,
    [switch]$SkipTesseract
)

if (-not $SkipTesseract) {
    $tesseractScript = Get-InstallScriptPath 'Install-Tesseract.ps1'
    if (Test-Path $tesseractScript) {
        try {
            & $tesseractScript -SkipIfExists
        } catch {
            Write-Host "  Tesseract error: $_" -ForegroundColor Yellow
            Write-Host '  Install manually: https://github.com/UB-Mannheim/tesseract/wiki' -ForegroundColor Cyan
        }
    }
} else {
    Write-Host "`nTesseract skipped (-SkipTesseract)" -ForegroundColor Gray
}

Write-Host "`n.env configuration..." -ForegroundColor Yellow
$envFile = Join-Path $Root '.env'
$envExample = Join-Path $Root '.env.example'

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host '  .env created from .env.example' -ForegroundColor Green
    } else {
        "# FastAPI Foundry`nFOUNDRY_BASE_URL=http://localhost:50477/v1" | Out-File $envFile -Encoding UTF8
        Write-Host '  .env created with defaults' -ForegroundColor Green
    }
} else {
    Write-Host '  .env already exists' -ForegroundColor Gray
}

Write-Host "`nconfig.json..." -ForegroundColor Yellow
$configFile = Join-Path $Root 'config.json'
$configExample = Join-Path $Root 'config.json.example'

if (-not (Test-Path $configFile)) {
    if (Test-Path $configExample) {
        Copy-Item $configExample $configFile
        Write-Host '  config.json created from config.json.example' -ForegroundColor Green
    } else {
        Write-Host '  config.json.example not found - creating minimal config.json' -ForegroundColor Yellow
        $minCfg = [ordered]@{
            fastapi_server = [ordered]@{ host='0.0.0.0'; port=9696; mode='dev'; workers=1; auto_find_free_port=$false }
            foundry_ai     = [ordered]@{ base_url=''; default_model='llama::llama-server'; temperature=0.7; max_tokens=2048; auto_load_default=$false }
            llama_cpp      = [ordered]@{ port=9780; host='127.0.0.1'; server_path=''; model_path=''; auto_start=$false }
            ollama         = [ordered]@{ base_url='http://localhost:11434'; temperature=0.7; top_p=0.9; top_k=50; max_tokens=2048 }
            opencode       = [ordered]@{ enabled=$true; auto_start=$true; host='0.0.0.0'; port=9699; command='opencode' }
            lmstudio       = [ordered]@{ base_url='http://localhost:1234'; api_key=''; default_model=''; request_timeout_sec=300 }
            directories    = [ordered]@{ models='~/.models'; rag='~/.rag'; hf_models='~/.cache/huggingface/hub' }
            rag_system     = [ordered]@{ enabled=$false; index_dir='~/.rag'; chunk_size=1000 }
            security       = [ordered]@{ api_key=''; https_enabled=$false }
            logging        = [ordered]@{ level='INFO'; retention_hours=24; console=$true; file_handler=$true }
            docs_server    = [ordered]@{ enabled=$false; port=9697 }
            ftp            = [ordered]@{ host=''; user=''; port=21; docs_dir='' }
            custom         = [ordered]@{ base_url=''; api_key='' }
            browser        = [ordered]@{ chromium_path=''; channel='stable' }
        }
        $minCfg | ConvertTo-Json -Depth 5 | Set-Content $configFile -Encoding UTF8
        Write-Host '  config.json created with defaults' -ForegroundColor Green
    }
} else {
    Write-Host '  config.json already exists' -ForegroundColor Gray
}

Ensure-LMStudioConfig -ConfigPath $configFile
Ensure-OllamaConfig -ConfigPath $configFile
Ensure-OpenCodeConfig -ConfigPath $configFile

Write-Host "`nLogs folder..." -ForegroundColor Yellow
$logsDir = Join-Path $Root 'logs'
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
    Write-Host '  logs/ created' -ForegroundColor Green
} else {
    Write-Host '  logs/ already exists' -ForegroundColor Gray
}

Write-Host "`nInitialising databases..." -ForegroundColor Yellow
try {
    & $Python (Get-InstallScriptPath 'Init-Databases.py')
    if ($LASTEXITCODE -ne 0) { Write-Host '  DB init returned non-zero exit code' -ForegroundColor Yellow }
} catch {
    Write-Host "  DB init error: $_" -ForegroundColor Yellow
}
