# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Foundry Stop
# =============================================================================
# Description:
#   Stops all FastAPI Foundry processes launched in silent mode
#   (via autostart.ps1 / Task Scheduler).
#
#   Stops in order:
#     1. FastAPI server  — via %TEMP%\fastapi-foundry.pid
#     2. llama.cpp       — via port from config.json (llama_cpp.port)
#     3. MkDocs          — via port from config.json (docs_server.port)
#
#   Foundry Local is intentionally NOT stopped — it is a system service.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\stop.ps1
#   powershell -ExecutionPolicy Bypass -File .\stop.ps1 -StopFoundry
#
# File: stop.ps1
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    # Also stop Foundry Local service (disabled by default)
    [switch]$StopFoundry
)

$ErrorActionPreference = 'Continue'
$Root = $PSScriptRoot

Write-Host '🛑 FastAPI Foundry — остановка всех сервисов' -ForegroundColor Cyan
Write-Host ('─' * 50) -ForegroundColor Cyan

# ── Helpers ───────────────────────────────────────────────────────────────────

function Stop-ByPidFile {
    <#
    .SYNOPSIS
        Stop a process using a PID file, then delete the file.
    .PARAMETER PidFile
        Path to the file containing the process ID.
    .PARAMETER Label
        Human-readable service name for log output.
    #>
    param([string]$PidFile, [string]$Label)

    if (-not (Test-Path $PidFile)) {
        Write-Host "  💡 $Label — PID-файл не найден: $PidFile" -ForegroundColor Gray
        return
    }

    $pid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if (-not $pid) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return
    }

    try {
        $proc = Get-Process -Id $pid -ErrorAction Stop
        $proc.Kill()
        $proc.WaitForExit(5000)
        Write-Host "  ✅ $Label остановлен (PID: $pid)" -ForegroundColor Green
    } catch {
        Write-Host "  💡 $Label (PID: $pid) уже завершён" -ForegroundColor Gray
    }

    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

function Stop-ByPort {
    <#
    .SYNOPSIS
        Stop the process listening on a given TCP port.
    .PARAMETER Port
        TCP port number.
    .PARAMETER Label
        Human-readable service name for log output.
    #>
    param([int]$Port, [string]$Label)

    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conn) {
        Write-Host "  💡 $Label — порт $Port не занят" -ForegroundColor Gray
        return
    }

    $ownerPid = $conn.OwningProcess
    try {
        Stop-Process -Id $ownerPid -Force -ErrorAction Stop
        Write-Host "  ✅ $Label остановлен (порт $Port, PID: $ownerPid)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Не удалось остановить $Label (PID: $ownerPid): $_" -ForegroundColor Yellow
    }
}

# ── Read config.json ──────────────────────────────────────────────────────────

$llamaPort = 9780
$docsPort  = 9697
$apiPort   = 9696

try {
    $cfg      = Get-Content (Join-Path $Root 'config.json') -Raw | ConvertFrom-Json
    $llamaPort = if ($cfg.llama_cpp.port)      { [int]$cfg.llama_cpp.port }      else { 9780 }
    $docsPort  = if ($cfg.docs_server.port)    { [int]$cfg.docs_server.port }    else { 9697 }
    $apiPort   = if ($cfg.fastapi_server.port) { [int]$cfg.fastapi_server.port } else { 9696 }
} catch {
    Write-Host "  ⚠️  Не удалось прочитать config.json, используются порты по умолчанию" -ForegroundColor Yellow
}

# ── 1. FastAPI server ─────────────────────────────────────────────────────────

Write-Host "`n[1] FastAPI сервер (порт $apiPort)" -ForegroundColor Yellow

$PidFile = Join-Path $env:TEMP 'fastapi-foundry.pid'
Stop-ByPidFile -PidFile $PidFile -Label 'FastAPI'

# Fallback: kill by port if PID file was missing
Stop-ByPort -Port $apiPort -Label 'FastAPI (по порту)'

# ── 2. llama.cpp ──────────────────────────────────────────────────────────────

Write-Host "`n[2] llama.cpp (порт $llamaPort)" -ForegroundColor Yellow
Stop-ByPort -Port $llamaPort -Label 'llama.cpp'

# ── 3. MkDocs ─────────────────────────────────────────────────────────────────

Write-Host "`n[3] MkDocs (порт $docsPort)" -ForegroundColor Yellow
Stop-ByPort -Port $docsPort -Label 'MkDocs'

# ── 4. Foundry (optional) ─────────────────────────────────────────────────────

if ($StopFoundry) {
    Write-Host "`n[4] Foundry Local" -ForegroundColor Yellow
    try {
        $result = & foundry service stop 2>&1
        Write-Host "  ✅ Foundry остановлен: $result" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Не удалось остановить Foundry: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[4] Foundry Local — пропущен (используйте -StopFoundry для остановки)" -ForegroundColor Gray
}

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host "`n$('─' * 50)" -ForegroundColor Cyan
Write-Host '✅ Готово.' -ForegroundColor Green
