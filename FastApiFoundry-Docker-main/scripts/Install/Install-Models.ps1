# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Загрузка моделей по умолчанию
# =============================================================================
# Description:
#   Загружает модели по умолчанию для Foundry Local и HuggingFace.
#   Для llama.cpp: сканирует ~/.models на наличие .gguf-файлов
#   и позволяет выбрать модель по умолчанию для записи в config.json.
#   Запускается автоматически из install.ps1 при первой установке
#   или вручную в любое время.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Models.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Models.ps1 -SkipFoundry
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Models.ps1 -SkipHuggingFace
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Models.ps1 -SkipLlama
#
# File: scripts\Install\Install-Models.ps1
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
    [switch]$SkipFoundry,
    [switch]$SkipHuggingFace,
    [switch]$SkipLlama
)

$ErrorActionPreference = 'Stop'

$Root   = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $Root 'venv\Scripts\python.exe'

Write-Host 'FastAPI Foundry - Downloading models' -ForegroundColor Green
Write-Host ('=' * 50)

# ── Foundry ───────────────────────────────────────────────────────────────────

if (-not $SkipFoundry) {
    Write-Host "`nFoundry model..." -ForegroundColor Yellow

    if (-not (Get-Command foundry -ErrorAction SilentlyContinue)) {
        Write-Host '  Foundry is not installed, skipping' -ForegroundColor Gray
    } else {
        $foundryModel = 'qwen3-0.6b-generic-cpu:4'
        $answer = Read-Host "  Download '$foundryModel' (~300 MB)? (y/N)"
        if ($answer -match '^[Yy]$') {
            Write-Host '  Starting Foundry service...' -ForegroundColor Gray
            & foundry service start 2>&1 | Out-Null
            Write-Host "  Downloading $foundryModel ..." -ForegroundColor Yellow
            & foundry model download $foundryModel
            Write-Host '  Done' -ForegroundColor Green
        }
    }
}

# ── HuggingFace ───────────────────────────────────────────────────────────────

if (-not $SkipHuggingFace) {
    Write-Host "`nHuggingFace model (for RAG)..." -ForegroundColor Yellow

    if (-not (Test-Path $python)) {
        Write-Host '  venv not found, skipping' -ForegroundColor Gray
    } else {
        $hfModel = 'sentence-transformers/all-MiniLM-L6-v2'
        $answer = Read-Host "  Download '$hfModel' (~90 MB)? (y/N)"
        if ($answer -match '^[Yy]$') {
            Write-Host "  Downloading $hfModel ..." -ForegroundColor Yellow
            & $python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('$hfModel')"
            Write-Host '  Done' -ForegroundColor Green
        }
    }
}

# ── llama.cpp GGUF ───────────────────────────────────────────────────────────

if (-not $SkipLlama) {
    Write-Host "`nllama.cpp GGUF models..." -ForegroundColor Yellow

    # Read models dir from config.json
    $modelsDir = Join-Path $env:USERPROFILE '.models'
    try {
        $cfg = Get-Content (Join-Path $Root 'config.json') -Raw | ConvertFrom-Json
        if ($cfg.llama_cpp.models_dir) {
            $modelsDir = $cfg.llama_cpp.models_dir -replace '^~', $env:USERPROFILE
        } elseif ($cfg.directories.models) {
            $modelsDir = $cfg.directories.models -replace '^~', $env:USERPROFILE
        }
    } catch { }

    # Ensure directory exists
    if (-not (Test-Path $modelsDir)) {
        New-Item -ItemType Directory -Path $modelsDir -Force | Out-Null
        Write-Host "  ✅ Created models directory: $modelsDir" -ForegroundColor Green
    } else {
        Write-Host "  ℹ️  Models directory: $modelsDir" -ForegroundColor Gray
    }

    # Check if any .gguf already present
    $existing = Get-ChildItem -Path $modelsDir -Filter '*.gguf' -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "  ✅ Found $($existing.Count) GGUF model(s):" -ForegroundColor Green
        for ($i = 0; $i -lt $existing.Count; $i++) {
            $sizeGb = [math]::Round($existing[$i].Length / 1GB, 2)
            Write-Host "  [$($i+1)] $($existing[$i].Name)  ($sizeGb GB)" -ForegroundColor White
        }
        Write-Host ''

        # Read current value to show as default
        $currentModel = ''
        try {
            $cfgPath = Join-Path $Root 'config.json'
            $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
            $rawPath = $cfg.llama_cpp.model_path
            # Normalize: expand ~ and show only if file actually exists
            if ($rawPath) {
                $expanded = $rawPath -replace '^~', $env:USERPROFILE
                if (Test-Path $expanded) { $currentModel = $expanded }
            }
        } catch { }

        if ($currentModel) {
            Write-Host "  Current: $currentModel" -ForegroundColor Gray
            $choice = Read-Host "  Set as default model (1-$($existing.Count)), or Enter to keep current"
        } else {
            $choice = Read-Host "  Set as default model (1-$($existing.Count))"
        }

        if ($choice -match '^\d+$' -and [int]$choice -ge 1 -and [int]$choice -le $existing.Count) {
            $selected = $existing[[int]$choice - 1]
            try {
                $cfgPath = Join-Path $Root 'config.json'
                $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
                $cfg.llama_cpp.model_path    = $selected.FullName
                $cfg.llama_cpp.default_model = $selected.FullName
                $cfg | ConvertTo-Json -Depth 10 | Set-Content $cfgPath -Encoding UTF8
                Write-Host "  ✅ config.json updated: llama_cpp.model_path = $($selected.FullName)" -ForegroundColor Green
            } catch {
                Write-Host "  ⚠️  Could not update config.json: $_" -ForegroundColor Yellow
                Write-Host "  Set manually: config.json → llama_cpp.model_path = $($selected.FullName)" -ForegroundColor Cyan
            }
        } else {
            Write-Host '  Skipped — model_path unchanged.' -ForegroundColor Gray
        }
    } else {
        Write-Host ''
        Write-Host '  ⚠️  No GGUF models found in:' -ForegroundColor Yellow
        Write-Host "     $modelsDir" -ForegroundColor White
        Write-Host ''
        Write-Host '  You can add models later — llama.cpp will start automatically' -ForegroundColor Cyan
        Write-Host '  once a model is configured in config.json.' -ForegroundColor Cyan
        Write-Host ''
        Write-Host '  How to get GGUF models:' -ForegroundColor Cyan
        Write-Host '  1. Hugging Face (recommended):' -ForegroundColor White
        Write-Host '       pip install huggingface_hub' -ForegroundColor Gray
        Write-Host '       huggingface-cli download bartowski/gemma-2-2b-it-GGUF \' -ForegroundColor Gray
        Write-Host '         gemma-2-2b-it-Q6_K.gguf --local-dir ~/.models' -ForegroundColor Gray
        Write-Host '  2. Any .gguf file — place it into:' -ForegroundColor White
        Write-Host "       $modelsDir" -ForegroundColor Gray
        Write-Host '  3. After adding a model, run this script again or set in web UI:' -ForegroundColor White
        Write-Host '       llama.cpp tab → Browse → select model → Start' -ForegroundColor Gray
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────

Write-Host "`n$('=' * 50)" -ForegroundColor Green
Write-Host 'Done!' -ForegroundColor Green
