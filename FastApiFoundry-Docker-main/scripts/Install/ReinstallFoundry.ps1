# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Local - Reinstall (CI/QA Tool)
# =============================================================================
# Description:
#   Fully resets and reinstalls Microsoft Foundry Local.
#   Used in CI pipelines and QA validation runs.
#
#   Modes:
#     - clean uninstall via winget
#     - reinstall via winget (silent, non-interactive)
#     - readiness verification (polls /v1/models on auto-detected port)
#
# Examples:
#   .\scripts\Install\ReinstallFoundry.ps1
#   .\scripts\Install\ReinstallFoundry.ps1 -TimeoutSec 120
#   .\scripts\Install\ReinstallFoundry.ps1 -TimeoutSec 30 -Verbose
#
# Exit codes:
#   0 = success (API ready)
#   1 = install failed
#   2 = service not ready within timeout
#
# File: scripts\Install\ReinstallFoundry.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Restored missing code blocks (Uninstall-Foundry, Install-Foundry, Wait-Ready)
#   - Added full hypo69 header
#   - Aligned docstrings with project standard (Args/Returns/Exceptions/Examples)
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [int]$TimeoutSec = 60,
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'

# --- functions ----------------------------------------------------------------

function Write-Log {
    <#
    .SYNOPSIS
        Writes a cyan-coloured status message to the console.
    .DESCRIPTION
        Args:
            $Msg (string) — message text to display.
    .EXAMPLE
        Write-Log 'Stopping Foundry...'
        # Prints the message in cyan
    #>
    param([string]$Msg)
    Write-Host $Msg -ForegroundColor Cyan
}

function Stop-Foundry {
    <#
    .SYNOPSIS
        Forcefully stops all running Foundry inference processes.
    .DESCRIPTION
        Finds all processes whose name matches 'Inference.Service.Agent*'
        and kills them. Waits 2 seconds for ports to be released.
    .EXAMPLE
        Stop-Foundry
        # All Foundry processes are terminated
    #>
    Write-Log 'Stopping Foundry...'

    $procs = Get-Process | Where-Object { $_.ProcessName -like 'Inference.Service.Agent*' }
    if ($procs) {
        $procs | ForEach-Object {
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    }

    Start-Sleep 2
}

function Uninstall-Foundry {
    <#
    .SYNOPSIS
        Stops the Foundry service and uninstalls the package via winget.
    .DESCRIPTION
        Returns:
            void — exits with code 1 if winget uninstall fails fatally.
    .EXAMPLE
        Uninstall-Foundry
        # Foundry Local is removed from the system
    #>
    Write-Log 'Uninstalling Foundry Local...'

    $exists = Get-Command foundry -ErrorAction SilentlyContinue
    if ($exists) {
        & foundry service stop 2>$null
    }

    try {
        winget uninstall Microsoft.FoundryLocal --silent --accept-source-agreements
        Write-Log 'Foundry uninstalled.'
    } catch {
        Write-Host "Warning: winget uninstall returned an error: $_" -ForegroundColor Yellow
        # Non-fatal — package may already be absent; continue with reinstall
    }

    # Remove leftover CLI from PATH in the current session
    $env:PATH = ($env:PATH -split ';' | Where-Object { $_ -notlike '*FoundryLocal*' }) -join ';'

    Start-Sleep 2
}

function Install-Foundry {
    <#
    .SYNOPSIS
        Installs Microsoft Foundry Local via winget in silent non-interactive mode.
    .DESCRIPTION
        Refreshes PATH in the current session after installation so that
        the 'foundry' command is immediately available without reopening the shell.

        Exceptions:
            RuntimeException — exits with code 1 if winget install fails.
    .EXAMPLE
        Install-Foundry
        # Foundry Local is installed and PATH is refreshed
    #>
    Write-Log 'Installing Foundry Local...'

    winget install Microsoft.FoundryLocal `
        --silent `
        --accept-source-agreements `
        --accept-package-agreements `
        --disable-interactivity

    if ($LASTEXITCODE -ne 0) {
        Write-Host "winget install failed (exit code $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }

    # Refresh PATH so 'foundry' is usable in this session
    $env:PATH = [System.Environment]::GetEnvironmentVariable('PATH', 'Machine') + ';' +
                [System.Environment]::GetEnvironmentVariable('PATH', 'User')

    Write-Log 'Foundry Local installed.'
}

function Wait-Ready {
    <#
    .SYNOPSIS
        Polls the Foundry API until it responds 200 OK or the timeout expires.
    .DESCRIPTION
        Starts the Foundry service, then detects the listening port by scanning
        netstat output and calls GET /v1/models on each candidate port
        in the 50000-60000 range.

        Returns:
            int — 0 if API is ready, 2 if timeout was reached.
    .EXAMPLE
        $code = Wait-Ready
        exit $code
        # Exits 0 when Foundry is ready, 2 on timeout
    #>
    Write-Log 'Waiting for API readiness...'

    & foundry service start 2>$null

    $deadline = (Get-Date).AddSeconds($TimeoutSec)

    while ((Get-Date) -lt $deadline) {
        try {
            $lines = netstat -ano | Select-String 'LISTENING'

            foreach ($line in $lines) {
                if ($line -match ':(\d+)\s') {
                    $port = $matches[1]

                    # Only probe ports in the typical Foundry range
                    if ([int]$port -lt 50000 -or [int]$port -gt 60000) { continue }

                    $r = Invoke-WebRequest `
                        -Uri "http://127.0.0.1:$port/v1/models" `
                        -TimeoutSec 3 `
                        -UseBasicParsing `
                        -ErrorAction SilentlyContinue

                    if ($r -and $r.StatusCode -eq 200) {
                        Write-Log "Ready on port $port"
                        return 0
                    }
                }
            }
        } catch { }

        if ($Verbose) {
            Write-Host "  Waiting... ($([int]($deadline - (Get-Date)).TotalSeconds)s left)" -ForegroundColor Gray
        }

        Start-Sleep 2
    }

    Write-Host "Timeout: Foundry API did not become ready within ${TimeoutSec}s" -ForegroundColor Red
    return 2
}

# --- main ---------------------------------------------------------------------

Stop-Foundry
Uninstall-Foundry
Install-Foundry

$result = Wait-Ready
exit $result
