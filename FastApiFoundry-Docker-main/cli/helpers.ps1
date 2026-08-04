# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CLI Shared Helpers
# =============================================================================
# Description:
#   Shared utilities for all CLI command modules:
#   HTTP client, output helpers, server bootstrap.
#
# File: cli/helpers.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

# Called by cli.ps1 after setting $API — do not set $API here.

function Invoke-Api {
    <#
    .SYNOPSIS
        Sends an HTTP request to the API and returns parsed JSON.
    .DESCRIPTION
        Args:
            $Method (string) — HTTP verb: GET, POST, DELETE, PUT.
            $Path   (string) — API path, e.g. '/health'.
            $Body   (object) — Optional hashtable for POST/PUT body.

        Returns:
            object — Parsed JSON response, or $null on error.
    .EXAMPLE
        Invoke-Api GET /health
        Invoke-Api POST /generate @{ prompt = 'Hello' }
    #>
    param([string]$Method, [string]$Path, [object]$Body = $null)
    $url = "$API$Path"
    $p = @{ Method = $Method; Uri = $url; ContentType = 'application/json' }
    if ($Body) { $p.Body = ($Body | ConvertTo-Json -Depth 10 -Compress) }
    try {
        return Invoke-RestMethod @p
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        Write-Host "❌ HTTP $code — $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Write-Ok  { param([string]$M) Write-Host "✅ $M" -ForegroundColor Green }
function Write-Err { param([string]$M) Write-Host "❌ $M" -ForegroundColor Red }
function Write-Inf { param([string]$M) Write-Host "ℹ️  $M" -ForegroundColor Cyan }

function Show-Json {
    <#
    .SYNOPSIS
        Pretty-prints a JSON object.
    .DESCRIPTION
        Args:
            $Data (object) — Object to display.

        Returns:
            void
    .EXAMPLE
        Show-Json $response
    #>
    param([object]$Data)
    $Data | ConvertTo-Json -Depth 10 | Write-Host
}

function Ensure-Server {
    <#
    .SYNOPSIS
        Checks if the FastAPI server is reachable; starts it via start.ps1 if not.
    .DESCRIPTION
        Args:
            $MaxWait (int) — Seconds to wait for the server to come up. Default: 30.

        Returns:
            bool — $true if server is reachable, $false if timed out.
    .EXAMPLE
        Ensure-Server
        Ensure-Server -MaxWait 60
    #>
    param([int]$MaxWait = 30)

    try {
        $null = Invoke-RestMethod -Uri "$API/health" -Method GET -TimeoutSec 2 -ErrorAction Stop
        return $true
    } catch { }

    $startScript = Join-Path $PSScriptRoot '..\start.ps1'
    if (-not (Test-Path $startScript)) {
        Write-Host '⚠️  Server not reachable and start.ps1 not found.' -ForegroundColor Yellow
        return $false
    }

    Write-Host '🚀 Server is not running — starting via start.ps1 ...' -ForegroundColor Cyan
    Start-Process powershell.exe `
        -ArgumentList '-ExecutionPolicy', 'Bypass', '-File', (Resolve-Path $startScript) `
        -WindowStyle Minimized

    $deadline = (Get-Date).AddSeconds($MaxWait)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 2
        Write-Host -NoNewline '.'
        try {
            $null = Invoke-RestMethod -Uri "$API/health" -Method GET -TimeoutSec 2 -ErrorAction Stop
            Write-Host ''
            Write-Ok 'Server is up.'
            return $true
        } catch { }
    }

    Write-Host ''
    Write-Err "Server did not start within $MaxWait seconds."
    return $false
}
