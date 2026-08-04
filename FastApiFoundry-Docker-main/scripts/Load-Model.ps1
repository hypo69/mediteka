# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Model Load
# =============================================================================
# Description:
#   Loads a previously downloaded Foundry model into the inference service memory.
#   The model must already be present in the local cache (use download-model.ps1 first).
#
# Examples:
#   .\load-model.ps1 -ModelId "qwen3-0.6b-generic-cpu:4"
#
# File: scripts/load-model.ps1
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    # Foundry model identifier — must match a cached model name
    [Parameter(Mandatory=$true)]
    [string]$ModelId
)

Write-Host "Loading model: $ModelId" -ForegroundColor Green

try {
    # Ask the Foundry service to load the model into memory
    foundry model load $ModelId

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Model $ModelId loaded successfully" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "❌ Failed to load model $ModelId" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error loading model: $_" -ForegroundColor Red
    exit 1
}
