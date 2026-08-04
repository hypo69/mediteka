# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Model Download
# =============================================================================
# Description:
#   Downloads a model into the local Foundry cache using the 'foundry' CLI.
#   The model ID must match a name from 'foundry model list'.
#
# Examples:
#   .\download-model.ps1 -ModelId "qwen3-0.6b-generic-cpu:4"
#   .\download-model.ps1 -ModelId "deepseek-r1-distill-qwen-7b-generic-cpu:3"
#
# File: scripts/download-model.ps1
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    # Foundry model identifier, e.g. "qwen3-0.6b-generic-cpu:4"
    [Parameter(Mandatory=$true)]
    [string]$ModelId
)

Write-Host "Downloading model to cache: $ModelId" -ForegroundColor Yellow

try {
    # Invoke the Foundry CLI to pull the model into the local cache
    foundry model download $ModelId

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Model $ModelId downloaded successfully" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "❌ Failed to download model $ModelId" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error downloading model: $_" -ForegroundColor Red
    exit 1
}
