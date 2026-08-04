# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Управление HuggingFace моделями
# =============================================================================
# Описание:
#   Просмотр скачанных и загруженных HF моделей, загрузка/выгрузка в память.
#
# Примеры:
#   .\hf-models.ps1                              # список всех моделей
#   .\hf-models.ps1 -Action load   -ModelId "google/gemma-2b"
#   .\hf-models.ps1 -Action unload -ModelId "google/gemma-2b"
#   .\hf-models.ps1 -Action status              # статус библиотек
#
# File: scripts/hf-models.ps1
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [ValidateSet("list", "load", "unload", "status")]
    [string]$Action = "list",

    [string]$ModelId = "",

    [ValidateSet("auto", "cpu", "cuda")]
    [string]$Device = "auto",

    [string]$ApiBase = "http://localhost:9696/api/v1"
)

$ErrorActionPreference = 'Continue'

Write-Host "🤗 HuggingFace Models Manager" -ForegroundColor Cyan

function Test-Server {
    try {
        Invoke-RestMethod -Uri "$ApiBase/health" -TimeoutSec 5 | Out-Null
        return $true
    } catch {
        Write-Host "❌ Server not available at $ApiBase" -ForegroundColor Red
        Write-Host "   Start: python run.py" -ForegroundColor Yellow
        return $false
    }
}

switch ($Action) {

    "status" {
        if (-not (Test-Server)) { exit 1 }
        $d = Invoke-RestMethod -Uri "$ApiBase/hf/status"
        Write-Host "`n📦 Library Status:" -ForegroundColor Yellow
        Write-Host "  transformers:    $($d.transformers.available) (v$($d.transformers.version))"
        Write-Host "  huggingface_hub: $($d.huggingface_hub.available) (v$($d.huggingface_hub.version))"
        Write-Host "  torch:           $($d.torch.available) (v$($d.torch.version))"
        Write-Host "  CUDA:            $($d.torch.cuda)"
        Write-Host "  HF Token set:    $($d.hf_token_set)"
        Write-Host "  Models dir:      $($d.models_dir)"
        if (-not $d.transformers.available) {
            Write-Host "`n💡 Install: $($d.install_cmd)" -ForegroundColor Cyan
        }
    }

    "list" {
        if (-not (Test-Server)) { exit 1 }
        $d = Invoke-RestMethod -Uri "$ApiBase/hf/models"

        Write-Host "`n💾 Downloaded models ($($d.downloaded.Count)):" -ForegroundColor Yellow
        if ($d.downloaded.Count -eq 0) {
            Write-Host "  (none)" -ForegroundColor Gray
        } else {
            $d.downloaded | ForEach-Object {
                $loadedMark = if ($_.loaded) { " [LOADED]" } else { "" }
                Write-Host "  $($_.id)  $($_.size_mb) MB$loadedMark" -ForegroundColor $(if ($_.loaded) { "Green" } else { "White" })
            }
        }

        Write-Host "`n🧠 Loaded in memory ($($d.loaded.Count)):" -ForegroundColor Yellow
        if ($d.loaded.Count -eq 0) {
            Write-Host "  (none)" -ForegroundColor Gray
        } else {
            $d.loaded | ForEach-Object { Write-Host "  $($_.id)" -ForegroundColor Green }
        }
    }

    "load" {
        if (-not $ModelId) { Write-Host "❌ -ModelId required" -ForegroundColor Red; exit 1 }
        if (-not (Test-Server)) { exit 1 }
        Write-Host "▶️ Loading $ModelId (device: $Device)..." -ForegroundColor Yellow
        $result = Invoke-RestMethod -Uri "$ApiBase/hf/models/load" `
            -Method POST -ContentType "application/json" `
            -Body (@{model_id=$ModelId; device=$Device} | ConvertTo-Json) `
            -TimeoutSec 600
        if ($result.success) {
            Write-Host "✅ Loaded: $ModelId on $($result.device)" -ForegroundColor Green
        } else {
            Write-Host "❌ $($result.error)" -ForegroundColor Red; exit 1
        }
    }

    "unload" {
        if (-not $ModelId) { Write-Host "❌ -ModelId required" -ForegroundColor Red; exit 1 }
        if (-not (Test-Server)) { exit 1 }
        $result = Invoke-RestMethod -Uri "$ApiBase/hf/models/unload" `
            -Method POST -ContentType "application/json" `
            -Body (@{model_id=$ModelId} | ConvertTo-Json)
        if ($result.success) {
            Write-Host "✅ Unloaded: $ModelId" -ForegroundColor Green
        } else {
            Write-Host "❌ $($result.error)" -ForegroundColor Red; exit 1
        }
    }
}
