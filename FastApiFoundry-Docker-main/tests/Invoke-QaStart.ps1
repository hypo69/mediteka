# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: QA - Stop All Services
# =============================================================================
# Description:
#   Stops all AI Assistant services to produce a clean state before QA testing.
#   Run this before qa-install.ps1 or before running the test suite.
#
#   Stops in order:
#     1. FastAPI server  — PID file or port 9696
#     2. llama.cpp       — port 9780
#     3. MkDocs          — port 9697
#     4. Foundry Local   — foundry service stop
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\tests\qa-start.ps1
#   powershell -ExecutionPolicy Bypass -File .\tests\qa-start.ps1 -KeepFoundry
#
# File: tests\qa-start.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    # Skip stopping Foundry Local (useful when Foundry is shared between test runs)
    [switch]$KeepFoundry
)

$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $PSScriptRoot

# =============================================================================
# FUNCTIONS
# =============================================================================

function Stop-ServiceByPort {
    <#
    .SYNOPSIS
        Kills the process listening on the given TCP port.
    .DESCRIPTION
        Args:
            $Port  (int)    — TCP port to check.
            $Label (string) — service name for log output.

        Returns:
            None.

    .EXAMPLE
        Stop-ServiceByPort -Port 9696 -Label 'FastAPI'
        # Kills the process on port 9696 if one exists
    #>
    param([int]$Port, [string]$Label)

    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conn) {
        Write-Host "  💡 $Label — port $Port is free" -ForegroundColor Gray
        return
    }
    try {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction Stop
        Write-Host "  ✅ $Label stopped (port $Port, PID $($conn.OwningProcess))" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Could not stop $Label on port ${Port}: $_" -ForegroundColor Yellow
    }
}

function Stop-ServiceByPidFile {
    <#
    .SYNOPSIS
        Kills a process identified by a PID stored in a file, then deletes the file.
    .DESCRIPTION
        Args:
            $PidFile (string) — full path to the file containing the process ID.
            $Label   (string) — service name for log output.

        Returns:
            None.

    .EXAMPLE
        Stop-ServiceByPidFile -PidFile "$env:TEMP\fastapi-foundry.pid" -Label 'FastAPI'
        # Reads PID from file, kills the process, removes the file
    #>
    param([string]$PidFile, [string]$Label)

    if (-not (Test-Path $PidFile)) { return }

    $storedPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($storedPid) {
        try {
            Stop-Process -Id $storedPid -Force -ErrorAction Stop
            Write-Host "  ✅ $Label stopped via PID file (PID $storedPid)" -ForegroundColor Green
        } catch {
            Write-Host "  💡 $Label (PID $storedPid) already gone" -ForegroundColor Gray
        }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

function Get-PortsFromConfig {
    <#
    .SYNOPSIS
        Reads service ports from config.json, returns defaults on failure.
    .DESCRIPTION
        Args:
            $ProjectRoot (string) — path to the project root containing config.json.

        Returns:
            hashtable — keys: ApiPort, LlamaPort, DocsPort.

    .EXAMPLE
        $ports = Get-PortsFromConfig -ProjectRoot 'D:\repos\FastApiFoundry-Docker'
        # Returns @{ ApiPort = 9696; LlamaPort = 9780; DocsPort = 9697 }
    #>
    param([string]$ProjectRoot)

    $ports = @{ ApiPort = 9696; LlamaPort = 9780; DocsPort = 9697 }
    $cfgPath = Join-Path $ProjectRoot 'config.json'

    if (-not (Test-Path $cfgPath)) { return $ports }

    try {
        $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
        if ($cfg.fastapi_server.port) { $ports.ApiPort   = [int]$cfg.fastapi_server.port }
        if ($cfg.llama_cpp.port)      { $ports.LlamaPort = [int]$cfg.llama_cpp.port }
        if ($cfg.docs_server.port)    { $ports.DocsPort  = [int]$cfg.docs_server.port }
    } catch {
        Write-Host '  ⚠️  config.json unreadable — using default ports' -ForegroundColor Yellow
    }

    return $ports
}

# =============================================================================
# MAIN
# =============================================================================

Write-Host '🛑 QA — stopping all services' -ForegroundColor Cyan
Write-Host ('─' * 50)

$ports = Get-PortsFromConfig -ProjectRoot $Root

Write-Host "`n[1] FastAPI (port $($ports.ApiPort))" -ForegroundColor Yellow
Stop-ServiceByPidFile -PidFile (Join-Path $env:TEMP 'fastapi-foundry.pid') -Label 'FastAPI'
Stop-ServiceByPort    -Port $ports.ApiPort -Label 'FastAPI'

Write-Host "`n[2] llama.cpp (port $($ports.LlamaPort))" -ForegroundColor Yellow
Stop-ServiceByPort -Port $ports.LlamaPort -Label 'llama.cpp'

Write-Host "`n[3] MkDocs (port $($ports.DocsPort))" -ForegroundColor Yellow
Stop-ServiceByPort -Port $ports.DocsPort -Label 'MkDocs'

if (-not $KeepFoundry) {
    Write-Host "`n[4] Foundry Local" -ForegroundColor Yellow
    if (Get-Command foundry -ErrorAction SilentlyContinue) {
        try {
            & foundry service stop 2>&1 | Out-Null
            Write-Host '  ✅ Foundry service stopped' -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️  Foundry stop error: $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host '  💡 Foundry not installed — skipping' -ForegroundColor Gray
    }
} else {
    Write-Host "`n[4] Foundry Local — skipped (-KeepFoundry)" -ForegroundColor Gray
}

Write-Host "`n$('─' * 50)"
Write-Host '✅ All services stopped. Ready for QA.' -ForegroundColor Green
