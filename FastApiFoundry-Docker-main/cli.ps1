# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Assistant CLI
# =============================================================================
# Description:
#   Entry point for the AI Assistant command-line interface.
#   Loads modules from cli/ and dispatches commands to them.
#
#   Interactive REPL (no arguments):
#     .\cli.ps1
#     > /health
#     > /gui admin
#     > /chat
#     > /list mcp
#     > /start mcp local-models
#     > /stop mcp -all
#     > /list commands
#     > /exit
#
#   Single command:
#     .\cli.ps1 health
#     .\cli.ps1 generate "Explain FAISS" --model ollama::llama3
#     .\cli.ps1 start mcp local-models
#
# File: cli.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Refactored into cli/ module structure
#   - Added /gui, /list mcp, /start mcp, /stop mcp, /list commands
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [Parameter(Position = 0)] [string]$Command = '',
    [Parameter(Position = 1)] [string]$Sub     = '',
    [Parameter(Position = 2)] [string]$Arg1    = '',
    [Parameter(Position = 3)] [string]$Arg2    = '',
    [string]$Model   = '',
    [string]$BaseUrl = 'http://localhost:9696',
    [int]   $TopK    = 5,
    [switch]$Raw
)

$ErrorActionPreference = 'Stop'
$API = "$BaseUrl/api/v1"

# ── load modules ──────────────────────────────────────────────────────────────

$_cli = Join-Path $PSScriptRoot 'cli'
. "$_cli\helpers.ps1"
. "$_cli\commands\registry.ps1"
. "$_cli\commands\system.ps1"
. "$_cli\commands\chat.ps1"
. "$_cli\commands\mcp.ps1"
. "$_cli\commands\ai.ps1"

# ── REPL dispatcher ───────────────────────────────────────────────────────────

function Invoke-ReplLine {
    <#
    .SYNOPSIS
        Parses and dispatches a single REPL input line.
    .DESCRIPTION
        Args:
            $Line (string) — Raw input from the REPL prompt.

        Returns:
            bool — $false when user wants to exit, $true otherwise.
    .EXAMPLE
        Invoke-ReplLine "/health"
        Invoke-ReplLine "/start mcp local-models"
    #>
    param([string]$Line)

    $line = $Line.Trim() -replace '^/', ''
    if (-not $line) { return $true }

    # tokenise: max 5 parts to handle "/start mcp server-name"
    $tokens  = $line -split '\s+', 5
    $cmd     = $tokens[0].ToLower()
    $sub     = if ($tokens.Count -gt 1) { $tokens[1].ToLower() } else { '' }
    $a1      = if ($tokens.Count -gt 2) { $tokens[2] } else { '' }
    $a2      = if ($tokens.Count -gt 3) { $tokens[3] } else { '' }
    $fullArg = ($tokens[1..($tokens.Count-1)] -join ' ').Trim()

    switch ($cmd) {
        { $_ -in 'exit','quit' } { return $false }

        # ── system ────────────────────────────────────────────────────────────
        'health'  { Invoke-Health  -RawOut:$Raw }
        'gui'     { Invoke-Gui     $sub }
        'restart' { Invoke-Restart $sub -RawOut:$Raw }
        'logs'    {
            $n = if ($sub -match '^\d+$') { [int]$sub } else { 50 }
            Invoke-Logs $n -RawOut:$Raw
        }

        # ── list ──────────────────────────────────────────────────────────────
        'list' {
            switch ($sub) {
                'mcp'      { Invoke-ListMcp -RawOut:$Raw }
                'models'   { Invoke-Models  -RawOut:$Raw }
                'commands' { Invoke-ListCommands }
                default    { Write-Err "Usage: /list mcp | /list models | /list commands" }
            }
        }

        # ── start / stop ──────────────────────────────────────────────────────
        'start' {
            switch ($sub) {
                'mcp' { Invoke-StartMcp $a1 -RawOut:$Raw }
                default { Write-Err "Usage: /start mcp <name>|-all" }
            }
        }
        'stop' {
            switch ($sub) {
                'mcp' { Invoke-StopMcp $a1 -RawOut:$Raw }
                default { Write-Err "Usage: /stop mcp <name>|-all" }
            }
        }

        # ── AI ────────────────────────────────────────────────────────────────
        'models'   { Invoke-Models  -RawOut:$Raw }
        'generate' { Invoke-Generate $fullArg -ModelId $Model -RawOut:$Raw }
        'chat'     { Invoke-Chat    -ModelId $Model }
        'rag'      { Invoke-Rag     $sub $a1 -K $TopK -RawOut:$Raw }
        'foundry'  { Invoke-Foundry $sub $a1 -RawOut:$Raw }
        'config'   { Invoke-Config  $sub $a1 $a2 -RawOut:$Raw }

        # ── help ──────────────────────────────────────────────────────────────
        'help'  { Show-Help -Repl }
        default { Write-Err "Unknown command: '$cmd'. Type /list commands for reference." }
    }
    return $true
}

# ── REPL loop ─────────────────────────────────────────────────────────────────

function Start-Repl {
    <#
    .SYNOPSIS
        Starts the interactive REPL session.
    .DESCRIPTION
        Returns:
            void — Runs until user types /exit or presses Ctrl+C.
    .EXAMPLE
        Start-Repl
    #>
    Write-Host ''
    Write-Host '  AI Assistant CLI' -ForegroundColor Cyan
    Write-Host "  $BaseUrl"         -ForegroundColor DarkGray
    Write-Host '  /list commands — all commands   /exit — quit' -ForegroundColor DarkGray
    Write-Host ''

    $r = Invoke-Api GET /health
    if ($r) {
        $color = if ($r.status -eq 'healthy') { 'Green' } else { 'Yellow' }
        Write-Host "  Service: $($r.status)  |  Foundry: $($r.foundry_status)  |  llama: $($r.llama_status)" `
            -ForegroundColor $color
    } else {
        Write-Host '  ⚠️  Cannot reach API.' -ForegroundColor Yellow
    }
    Write-Host ''

    while ($true) {
        try   { $line = Read-Host '>' }
        catch { break }
        if (-not (Invoke-ReplLine $line)) { break }
    }

    Write-Host ''
    Write-Ok 'Bye!'
}

# ── main ──────────────────────────────────────────────────────────────────────

# 'help' never needs the server
if ($Command.ToLower() -notin 'help', '') {
    $null = Ensure-Server
}

if (-not $Command) {
    Start-Repl
    exit 0
}

# Single-command mode — map CLI args to the same dispatcher
switch ($Command.ToLower()) {
    'health'  { Invoke-Health  -RawOut:$Raw }
    'gui'     { Invoke-Gui     $Sub }
    'models'  { Invoke-Models  -RawOut:$Raw }
    'generate' {
        $prompt = "$Sub $Arg1 $Arg2".Trim()
        Invoke-Generate $prompt -ModelId $Model -RawOut:$Raw
    }
    'chat'    { Invoke-Chat    -ModelId $Model }
    'rag'     { Invoke-Rag     $Sub $Arg1 -K $TopK -RawOut:$Raw }
    'foundry' { Invoke-Foundry $Sub $Arg1 -RawOut:$Raw }
    'config'  { Invoke-Config  $Sub $Arg1 $Arg2 -RawOut:$Raw }
    'logs'    {
        $n = if ($Sub -match '^\d+$') { [int]$Sub } else { 50 }
        Invoke-Logs $n -RawOut:$Raw
    }
    'restart' { Invoke-Restart $Sub -RawOut:$Raw }
    'list' {
        switch ($Sub.ToLower()) {
            'mcp'      { Invoke-ListMcp -RawOut:$Raw }
            'models'   { Invoke-Models  -RawOut:$Raw }
            'commands' { Invoke-ListCommands }
            default    { Write-Err "Usage: .\cli.ps1 list mcp | list models | list commands" }
        }
    }
    'start' {
        switch ($Sub.ToLower()) {
            'mcp' { Invoke-StartMcp $Arg1 -RawOut:$Raw }
            default { Write-Err "Usage: .\cli.ps1 start mcp <name>|-all" }
        }
    }
    'stop' {
        switch ($Sub.ToLower()) {
            'mcp' { Invoke-StopMcp $Arg1 -RawOut:$Raw }
            default { Write-Err "Usage: .\cli.ps1 stop mcp <name>|-all" }
        }
    }
    'help'    { Show-Help }
    default   { Write-Err "Unknown command: '$Command'"; Show-Help; exit 1 }
}
