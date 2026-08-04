# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Service Status Check
# =============================================================================
# Description:
#   Queries the Foundry inference service for its current status using the CLI.
#   Outputs the raw status text returned by 'foundry service status'.
#   Used by the FastAPI backend and diagnostic scripts to verify the service is up.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\service-status.ps1
#
# File: scripts/service-status.ps1
# Project: AI Assistant
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2024 - 2026 hypo69
# Licence: MIT
# =============================================================================

Write-Host "Checking Foundry service status..." -ForegroundColor Yellow

try {
    # Capture both stdout and stderr so errors are visible in the output
    $result = foundry service status 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Service status retrieved successfully" -ForegroundColor Green
        # Write-Output sends the result back to the caller (e.g. FastAPI subprocess)
        Write-Output $result
        exit 0
    } else {
        Write-Host "❌ Failed to get service status" -ForegroundColor Red
        Write-Error $result
        exit 1
    }
} catch {
    Write-Host "❌ Error checking service status: $_" -ForegroundColor Red
    exit 1
}
