# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Start Documentation Server and Open Browser
# =============================================================================
# Description:
#   Reads docs_server.port from config.json, generates PowerShell docs
#   via scripts\Create-Doc\Generate-PsDocs.ps1, rebuilds the MkDocs site,
#   starts the server and opens the documentation in the default browser.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\doc.ps1
#
# File: doc.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Changes in 0.8.0:
#   - Added Generate-FullReference.py step (telegram, js, mcp_servers)
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

$ErrorActionPreference = 'Stop'

# --- config ---

$SCRIPT_DIR  = $PSScriptRoot
$CONFIG_FILE = Join-Path $SCRIPT_DIR 'config.json'
$MKDOCS_FILE = Join-Path $SCRIPT_DIR 'mkdocs.yml'
$PYTHON      = Join-Path $SCRIPT_DIR 'venv\Scripts\python.exe'

# --- functions ---

function Get-DocsPort {
    <#
    .SYNOPSIS
        Reads docs_server.port from config.json.
    .DESCRIPTION
        Returns:
            int — port number (default 9697).
    .EXAMPLE
        Get-DocsPort
        # Returns 9697
    #>
    if (-not (Test-Path $CONFIG_FILE)) { return 9697 }
    try {
        $cfg = Get-Content $CONFIG_FILE -Raw -Encoding UTF8 | ConvertFrom-Json
        $port = [int]$cfg.docs_server.port
        return $(if ($port -gt 0) { $port } else { 9697 })
    } catch {
        return 9697
    }
}

function Test-PortInUse {
    <#
    .SYNOPSIS
        Checks whether a TCP port is already bound.
    .DESCRIPTION
        Args:
            $Port (int) — port number to check.

        Returns:
            bool — True if port is in use.
    .EXAMPLE
        Test-PortInUse -Port 9697
        # Returns $true if port is occupied
    #>
    param ([int]$Port)
    $result = netstat -ano | Select-String ":$Port\s"
    return [bool]$result
}

function Build-MkDocs {
    <#
    .SYNOPSIS
        Runs mkdocs build to generate static site/ directory.
    .DESCRIPTION
        Returns:
            bool — True if build succeeded.
    .EXAMPLE
        Build-MkDocs
        # Returns $true on success
    #>
    if (-not (Test-Path $PYTHON)) { return $false }
    if (-not (Test-Path $MKDOCS_FILE)) { return $false }

    Write-Host '📦 Building documentation to site/ ...'
    try {
        $result = & $PYTHON -m mkdocs build -f $MKDOCS_FILE 2>&1
        Write-Host $result
        return $true
    } catch {
        Write-Host "⚠️  mkdocs build failed: $_"
        return $false
    }
}

function Start-MkDocs {
    <#
    .SYNOPSIS
        Launches mkdocs serve in a new window.
    .DESCRIPTION
        Args:
            $Port (int) — TCP port to bind.
    .EXAMPLE
        Start-MkDocs -Port 9697
    #>
    param ([int]$Port)

    if (-not (Test-Path $PYTHON)) {
        Write-Host "❌ Python not found: $PYTHON"
        Write-Host '   Run install.ps1 first.'
        exit 1
    }
    if (-not (Test-Path $MKDOCS_FILE)) {
        Write-Host "❌ mkdocs.yml not found: $MKDOCS_FILE"
        exit 1
    }

    $mkdocsArgs = "-m mkdocs serve -f `"$MKDOCS_FILE`" --dev-addr 0.0.0.0:$Port"
    Start-Process -FilePath $PYTHON `
                  -ArgumentList $mkdocsArgs `
                  -WorkingDirectory $SCRIPT_DIR `
                  -WindowStyle Normal
}

function Wait-ForServer {
    <#
    .SYNOPSIS
        Polls http://localhost:<Port> until it responds or timeout expires.
    .DESCRIPTION
        Args:
            $Port (int) — port to poll.
            $TimeoutSec (int) — maximum wait time in seconds. Default: 15.

        Returns:
            bool — True if server responded in time.
    .EXAMPLE
        Wait-ForServer -Port 9697 -TimeoutSec 20
        # Returns $true if server is up within 20 seconds
    #>
    param (
        [int]$Port,
        [int]$TimeoutSec = 15
    )

    $url      = "http://localhost:$Port"
    $deadline = (Get-Date).AddSeconds($TimeoutSec)

    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -lt 500) { return $true }
        } catch {
            # Server not ready yet — keep polling
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Stop-PortProcess {
    <#
    .SYNOPSIS
        Kills all processes listening on the given port.
    .DESCRIPTION
        Args:
            $Port (int) — TCP port to free.
    .EXAMPLE
        Stop-PortProcess -Port 9697
    #>
    param ([int]$Port)

    $lines = netstat -ano | Select-String ":$Port\s"
    if (-not $lines) { return }

    foreach ($line in $lines) {
        $parts  = ($line -replace '\s+', ' ').Trim().Split(' ')
        $procId = $parts[-1]
        if ($procId -match '^\d+$' -and [int]$procId -gt 0) {
            try {
                Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue
                Write-Host "🛑 Killed PID $procId (port $Port)"
            } catch { }
        }
    }
}

# --- main ---

$port    = Get-DocsPort
$url     = "http://localhost:$port"
$siteDir = Join-Path $SCRIPT_DIR 'site'

if (Test-PortInUse -Port $port) {
    Write-Host "🛑 Stopping existing MkDocs on port $port..."
    Stop-PortProcess -Port $port
    Start-Sleep -Milliseconds 800
}

# Generate PowerShell docs before building
$generatePsDocs = Join-Path $SCRIPT_DIR 'scripts\Create-Doc\Generate-PsDocs.ps1'
if (Test-Path $generatePsDocs) {
    Write-Host '📝 Generating PowerShell docs...'
    & powershell -ExecutionPolicy Bypass -File $generatePsDocs
}

# Generate Python Code Reference before building
$generateCodeRef = Join-Path $SCRIPT_DIR 'scripts\Create-Doc\Generate-CodeReference.py'
if (Test-Path $generateCodeRef) {
    Write-Host '📝 Generating Python Code Reference...'
    & $PYTHON $generateCodeRef
}

# Generate Full API Reference before building
$generateApiRef = Join-Path $SCRIPT_DIR 'scripts\Create-Doc\Generate-ApiReference.py'
if (Test-Path $generateApiRef) {
    Write-Host '📝 Generating Full API Reference...'
    & $PYTHON $generateApiRef
}

# Generate universal reference docs (all project dirs from root)
$generateFullRef = Join-Path $SCRIPT_DIR 'scripts\Create-Doc\Generate-FullReference.py'
if (Test-Path $generateFullRef) {
    Write-Host '📝 Generating Full Reference (all dirs)...'
    & $PYTHON $generateFullRef
}

# Generate mkdocs.yml from template + scanned nav
$generateNav = Join-Path $SCRIPT_DIR 'scripts\Create-Doc\Generate-Nav.py'
if (Test-Path $generateNav) {
    Write-Host '📝 Generating mkdocs.yml from template...'
    & $PYTHON $generateNav
}

# Always remove site/ and rebuild from scratch
if (Test-Path $siteDir) {
    Write-Host '🗑️  Removing site/ ...'
    Remove-Item $siteDir -Recurse -Force
}
Build-MkDocs | Out-Null

Write-Host "🚀 Starting MkDocs on port $port..."
Start-MkDocs -Port $port

Write-Host '⏳ Waiting for server...'
$ready = Wait-ForServer -Port $port -TimeoutSec 20

if (-not $ready) {
    Write-Host "⚠️  Server did not respond in time — opening browser anyway"
}

Write-Host "🌐 Opening $url"
Start-Process $url
