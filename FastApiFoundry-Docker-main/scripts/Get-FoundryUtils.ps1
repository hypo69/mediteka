# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Utility Functions
# =============================================================================
# Description:
#   Reusable Foundry helper functions extracted from start.ps1.
#   Dot-source this file to get utility functions WITHOUT launching the server.
#
#   Functions:
#     Test-FoundryCli   — check if 'foundry' CLI is in PATH
#     Get-FoundryPort   — detect active Foundry inference port
#     Get-FoundryUrl    — return full base URL (http://127.0.0.1:PORT/v1/)
#
# Examples:
#   . .\scripts\foundry-utils.ps1
#   Get-FoundryPort
#   Get-FoundryUrl
#
# File: scripts/Get-FoundryUtils.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Changes in 0.8.0:
#   - Extracted from start.ps1 to allow dot-sourcing without side effects
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

function Test-FoundryCli {
    <#
    .SYNOPSIS
        Checks whether the 'foundry' CLI is available in PATH.
    .DESCRIPTION
        Returns:
            bool — True if 'foundry' command is found, False otherwise.
    .EXAMPLE
        Test-FoundryCli
        # Returns $true on a machine with Foundry Local installed
    #>
    try {
        Get-Command foundry -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}


function Get-FoundryPort {
    <#
    .SYNOPSIS
        Detects the active Foundry inference service port.
    .DESCRIPTION
        Runs 'foundry service status', parses the port from the URL in output,
        then verifies the port is reachable via GET /v1/models.

        Returns:
            string — Port number (e.g. '50477'), or $null if not found/reachable.

        Exceptions:
            Writes a warning if 'foundry service status' fails.
    .EXAMPLE
        $port = Get-FoundryPort
        if ($port) { Write-Host "Foundry on port $port" }
    #>
    try {
        $output = foundry service status 2>&1 | Out-String
        $match  = [regex]::Match($output, 'http://127\.0\.0\.1:(\d+)')
        if ($match.Success) {
            $port = $match.Groups[1].Value
            try {
                $r = Invoke-WebRequest -Uri "http://127.0.0.1:$port/v1/models" `
                    -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
                if ($r.StatusCode -eq 200) {
                    Write-Host "✅ Foundry API found on port $port" -ForegroundColor Green
                    return $port
                }
            } catch { }
        }
    } catch {
        Write-Host "⚠️ Error detecting Foundry port: $_" -ForegroundColor Yellow
    }
    return $null
}


function Get-FoundryUrl {
    <#
    .SYNOPSIS
        Returns the full Foundry base URL for use in API calls.
    .DESCRIPTION
        Calls Get-FoundryPort and builds the URL.

        Returns:
            string — e.g. 'http://127.0.0.1:50477/v1/', or $null if Foundry not running.
    .EXAMPLE
        $url = Get-FoundryUrl
        # Returns 'http://127.0.0.1:50477/v1/'
    #>
    $port = Get-FoundryPort
    if ($port) {
        return "http://127.0.0.1:$port/v1/"
    }
    return $null
}
