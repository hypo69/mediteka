# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Model List
# =============================================================================
# Description:
#   Retrieves the list of Foundry models.
#   In 'available' mode: calls 'foundry model list' to show all downloadable models.
#   In 'loaded' mode: calls 'foundry service list'; falls back to the HTTP API
#   at localhost:50477 if the CLI command fails.
#   Outputs only clean model ID lines, stripping headers and status messages.
#
# Examples:
#   .\list-models.ps1                    # list all available models
#   .\list-models.ps1 -Type loaded       # list models currently loaded in memory
#
# File: scripts/list-models.ps1
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    # 'available' — all downloadable models; 'loaded' — models active in the service
    [Parameter(Mandatory=$false)]
    [string]$Type = "available"
)

Write-Host "Getting models list: $Type" -ForegroundColor Yellow

try {
    if ($Type -eq "loaded") {
        Write-Host "Checking loaded models..." -ForegroundColor Cyan

        # Primary method: ask the Foundry service directly
        $result = foundry service list 2>&1

        if ($LASTEXITCODE -ne 0) {
            # Fallback: query the OpenAI-compatible HTTP API when CLI fails
            Write-Host "Trying alternative method..." -ForegroundColor Yellow
            try {
                $foundryUrl = "http://localhost:50477/v1/models"
                $response = Invoke-RestMethod -Uri $foundryUrl -TimeoutSec 5 -ErrorAction Stop
                if ($response -and $response.data) {
                    foreach ($model in $response.data) {
                        Write-Output $model.id
                    }
                    exit 0
                }
            } catch {
                Write-Host "No models loaded or Foundry not accessible" -ForegroundColor Yellow
                exit 0
            }
        }
    } else {
        # List all models available for download from the Foundry catalog
        Write-Host "Getting available models..." -ForegroundColor Cyan
        $result = foundry model list 2>&1
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Models list retrieved successfully" -ForegroundColor Green

        # Filter out header/status lines — output only actual model identifiers
        $result | ForEach-Object {
            $line = $_.ToString().Trim()
            if ($line -and
                -not $line.StartsWith('Available') -and
                -not $line.StartsWith('Service') -and
                -not $line.StartsWith('---') -and
                -not $line.StartsWith('✅') -and
                -not $line.StartsWith('Getting') -and
                -not $line.StartsWith('Checking') -and
                $line -notmatch '^\s*$') {
                Write-Output $line
            }
        }
        exit 0
    } else {
        Write-Host "❌ Failed to get models list" -ForegroundColor Red
        Write-Error $result
        exit 1
    }
} catch {
    Write-Host "❌ Error getting models list: $_" -ForegroundColor Red
    exit 1
}
