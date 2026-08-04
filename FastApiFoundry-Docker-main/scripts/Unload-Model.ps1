# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Model Unload
# =============================================================================
# Description:
#   Unloads a model from the Foundry inference service memory to free RAM/VRAM.
#   The model remains in the local cache and can be reloaded later.
#
# Examples:
#   .\unload-model.ps1 -ModelId "qwen3-0.6b-generic-cpu:4"
#
# File: scripts/unload-model.ps1
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    # Foundry model identifier — must match a currently loaded model
    [Parameter(Mandatory=$true)]
    [string]$ModelId
)

Write-Host "Unloading model: $ModelId" -ForegroundColor Yellow

try {
    # Ask the Foundry service to release the model from memory
    foundry model unload $ModelId

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Model $ModelId unloaded successfully" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "❌ Failed to unload model $ModelId" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error unloading model: $_" -ForegroundColor Red
    exit 1
}
