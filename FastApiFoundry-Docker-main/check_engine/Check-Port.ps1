# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Port Discovery
# =============================================================================
# Description:
#   Finds the TCP port on which the Foundry inference service is listening
#   by scanning the Inference.Service.Agent process ports via netstat and
#   probing each with a GET /v1/models request.
#   Sets FOUNDRY_BASE_URL environment variable when a live port is found.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\check_port.ps1
#
# File: check_engine/check_port.ps1
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

function Get-FoundryPort {
    <#
    .SYNOPSIS
        Detects the active port of the Foundry inference service.
    .DESCRIPTION
        Finds the 'Inference.Service.Agent' process, reads its LISTENING ports
        from netstat output, then probes each port with GET /v1/models.
        Returns the first port that responds with HTTP 200.
    .OUTPUTS
        string | $null  — port number as string, or $null if Foundry is not running.
    #>
    try {
        # Locate the Foundry inference process by name pattern
        $foundryProcess = Get-Process | Where-Object { $_.ProcessName -like "Inference.Service.Agent*" }
        if (-not $foundryProcess) {
            Write-Host "No Foundry process found" -ForegroundColor Gray
            return $null
        }

        Write-Host "Found Foundry process: $($foundryProcess.ProcessName) (PID: $($foundryProcess.Id))" -ForegroundColor Green

        # Get all ports that the process is currently listening on
        $netstatOutput = netstat -ano | Select-String "$($foundryProcess.Id)" | Select-String "LISTENING"

        foreach ($line in $netstatOutput) {
            if ($line -match ':(\d+)\s') {
                $port = $matches[1]
                Write-Host "Testing port: $port" -ForegroundColor Cyan

                try {
                    # Confirm this port serves the Foundry OpenAI-compatible API
                    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/v1/models" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
                    if ($response.StatusCode -eq 200) {
                        Write-Host "SUCCESS: Foundry API confirmed on port $port" -ForegroundColor Green
                        return $port
                    }
                } catch {
                    Write-Host "Port $port not responding" -ForegroundColor Yellow
                }
            }
        }

        Write-Host "Foundry process found but no working API port detected" -ForegroundColor Yellow
    } catch {
        Write-Host "Error searching for Foundry: $_" -ForegroundColor Red
    }
    return $null
}

# --- main ---

$port = Get-FoundryPort
if ($port) {
    # Export the base URL so other scripts and FastAPI can use it
    $env:FOUNDRY_BASE_URL = "http://localhost:$port/v1/"
    Write-Host "FOUNDRY_BASE_URL = $env:FOUNDRY_BASE_URL" -ForegroundColor Green
} else {
    Write-Host "Foundry not found" -ForegroundColor Red
}
