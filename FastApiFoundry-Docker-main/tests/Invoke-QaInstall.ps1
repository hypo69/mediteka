# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: QA - Clean Reinstall
# =============================================================================
# Description:
#   Full QA reinstall pipeline:
#     1. Stop all services          (calls tests\qa-start.ps1)
#     2. Remove venv/               (clean pip state)
#     3. Remove bin\llama-*\        (re-extracted from zip)
#     4. Run install.ps1 -Force     (clean install)
#     5. Optional: run smoke tests
#
#   Produces a deterministic environment identical to a first-time install.
#   Use in CI pipelines or before regression test runs.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1
#   powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1 -SkipRag
#   powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1 -SkipLMStudio
#   powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1 -SkipSmoke
#   powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1 -KeepFoundry
#
# File: tests\qa-install.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    # Pass -SkipRag to install.ps1 (skips sentence-transformers / faiss)
    [switch]$SkipRag,
    # Pass -SkipTesseract to install.ps1
    [switch]$SkipTesseract,
    # Pass -SkipLMStudio to install.ps1
    [switch]$SkipLMStudio,
    # Skip Foundry stop/reinstall (useful when Foundry is shared)
    [switch]$KeepFoundry,
    # Skip smoke tests after install
    [switch]$SkipSmoke
)

$ErrorActionPreference = 'Stop'
$Root      = Split-Path -Parent $PSScriptRoot
$TestsDir  = $PSScriptRoot

Write-Host '🔄 QA — clean reinstall' -ForegroundColor Cyan
Write-Host ('=' * 50)

# =============================================================================
# FUNCTIONS
# =============================================================================

function Remove-Directory {
    <#
    .SYNOPSIS
        Removes a directory if it exists, with a status message.
    .DESCRIPTION
        Args:
            $Path  (string) — full path to the directory.
            $Label (string) — name used in log output.

        Returns:
            None.

    .EXAMPLE
        Remove-Directory -Path 'D:\repos\project\venv' -Label 'venv'
        # Removes venv\ and prints status
    #>
    param([string]$Path, [string]$Label)

    if (Test-Path $Path) {
        Remove-Item $Path -Recurse -Force
        Write-Host "  ✅ $Label removed" -ForegroundColor Green
    } else {
        Write-Host "  💡 $Label not found — skipping" -ForegroundColor Gray
    }
}

function Invoke-SmokeTests {
    <#
    .SYNOPSIS
        Runs the smoke test suite against the freshly installed server.
    .DESCRIPTION
        Calls check_engine\smoke_all_endpoints.py via the venv Python.
        Exits with code 1 if tests fail.

        Args:
            $ProjectRoot (string) — project root directory.

        Returns:
            None.

        Exceptions:
            RuntimeException — if smoke tests exit with non-zero code.

    .EXAMPLE
        Invoke-SmokeTests -ProjectRoot 'D:\repos\FastApiFoundry-Docker'
        # Runs smoke_all_endpoints.py and prints results
    #>
    param([string]$ProjectRoot)

    $python    = Join-Path $ProjectRoot 'venv\Scripts\python.exe'
    $smokeScript = Join-Path $ProjectRoot 'check_engine\smoke_all_endpoints.py'

    if (-not (Test-Path $smokeScript)) {
        Write-Host '  ⚠️  smoke_all_endpoints.py not found — skipping' -ForegroundColor Yellow
        return
    }
    if (-not (Test-Path $python)) {
        Write-Host '  ⚠️  venv python not found — skipping smoke tests' -ForegroundColor Yellow
        return
    }

    Write-Host "`n🔍 Running smoke tests..." -ForegroundColor Cyan
    & $python $smokeScript

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Smoke tests failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host '✅ Smoke tests passed' -ForegroundColor Green
}

# =============================================================================
# MAIN
# =============================================================================

# --- [1] Stop all services ---
Write-Host "`n[1] Stopping all services" -ForegroundColor Yellow
$qaStartScript = Join-Path $TestsDir 'qa-start.ps1'

$keepFoundryArg = if ($KeepFoundry) { @('-KeepFoundry') } else { @() }
& $qaStartScript @keepFoundryArg

# --- [2] Remove venv ---
Write-Host "`n[2] Removing venv" -ForegroundColor Yellow
Remove-Directory -Path (Join-Path $Root 'venv') -Label 'venv'

# --- [3] Remove extracted llama.cpp binaries ---
Write-Host "`n[3] Removing extracted llama.cpp binaries" -ForegroundColor Yellow
$binDir = Join-Path $Root 'bin'
if (Test-Path $binDir) {
    Get-ChildItem -Path $binDir -Directory -Filter 'llama-*' -ErrorAction SilentlyContinue |
    ForEach-Object {
        Remove-Directory -Path $_.FullName -Label $_.Name
    }
}

# --- [4] Clean install ---
Write-Host "`n[4] Running install.ps1 -Force" -ForegroundColor Yellow
$installScript = Join-Path $Root 'install.ps1'

$installArgs = @('-Force')
if ($SkipRag)       { $installArgs += '-SkipRag' }
if ($SkipTesseract) { $installArgs += '-SkipTesseract' }
if ($SkipLMStudio)  { $installArgs += '-SkipLMStudio' }

& $installScript @installArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ install.ps1 failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}

# --- [5] Smoke tests ---
if (-not $SkipSmoke) {
    Invoke-SmokeTests -ProjectRoot $Root
} else {
    Write-Host "`n[5] Smoke tests skipped (-SkipSmoke)" -ForegroundColor Gray
}

# --- Done ---
Write-Host "`n$('=' * 50)" -ForegroundColor Green
Write-Host '✅ QA reinstall complete.' -ForegroundColor Green
