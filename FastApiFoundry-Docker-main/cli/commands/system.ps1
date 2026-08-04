# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CLI System Commands
# =============================================================================
# Description:
#   health, gui, restart, logs, list commands, help.
#
# File: cli/commands/system.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

function Invoke-Health {
    <#
    .SYNOPSIS
        Shows service health status.
    .DESCRIPTION
        Returns:
            void — Prints status of Foundry, llama.cpp, RAG, docs.
    .EXAMPLE
        Invoke-Health
    #>
    param([switch]$RawOut)
    $r = Invoke-Api GET /health
    if (-not $r) { return }
    if ($RawOut) { Show-Json $r; return }
    $color = if ($r.status -eq 'healthy') { 'Green' } else { 'Red' }
    Write-Host "Status    : $($r.status)"    -ForegroundColor $color
    Write-Host "Foundry   : $($r.foundry_status)"
    Write-Host "llama.cpp : $($r.llama_status)"
    Write-Host "RAG       : $($r.rag_status)"
    Write-Host "Docs      : $($r.docs_status)"
    Write-Host "Models    : $($r.models_count)"
}

function Invoke-Gui {
    <#
    .SYNOPSIS
        Opens the web UI in the default browser.
    .DESCRIPTION
        Args:
            $Sub (string) — Optional sub-target: 'admin' opens the main UI.

        Returns:
            void
    .EXAMPLE
        Invoke-Gui admin
    #>
    param([string]$Sub = 'admin')
    $url = $BaseUrl
    Write-Inf "Opening $url ..."
    Start-Process $url
}

function Invoke-Restart {
    <#
    .SYNOPSIS
        Restarts a background service.
    .DESCRIPTION
        Args:
            $Service (string) — foundry | llama | docs | rag.

        Returns:
            void
    .EXAMPLE
        Invoke-Restart foundry
    #>
    param([string]$Service, [switch]$RawOut)
    if (-not $Service) { Write-Err 'Usage: /restart <foundry|llama|docs|rag>'; return }
    $r = Invoke-Api POST "/restart/$Service"
    if (-not $r) { return }
    if ($RawOut) { Show-Json $r; return }
    if ($r.success) { Write-Ok $r.message } else { Write-Err $r.error }
}

function Invoke-Logs {
    <#
    .SYNOPSIS
        Fetches recent application logs.
    .DESCRIPTION
        Args:
            $Lines (int) — Number of lines to fetch (default: 50).

        Returns:
            void — Prints log lines.
    .EXAMPLE
        Invoke-Logs 100
    #>
    param([int]$Lines = 50, [switch]$RawOut)
    $r = Invoke-Api GET "/logs?lines=$Lines"
    if (-not $r) { return }
    if ($RawOut) { Show-Json $r; return }
    if ($r.logs)        { $r.logs    | ForEach-Object { Write-Host $_ } }
    elseif ($r.content) { Write-Host $r.content }
    else                { Show-Json $r }
}

function Invoke-ListCommands {
    <#
    .SYNOPSIS
        Prints all available CLI commands grouped by category.
    .DESCRIPTION
        Returns:
            void
    .EXAMPLE
        Invoke-ListCommands
    #>
    $currentGroup = ''
    foreach ($entry in $CLI_COMMANDS) {
        if ($entry.Group -ne $currentGroup) {
            $currentGroup = $entry.Group
            Write-Host ''
            Write-Host "  $currentGroup" -ForegroundColor DarkCyan
        }
        $cmd  = $entry.Cmd.PadRight(28)
        $args = if ($entry.Args) { "[$($entry.Args)]".PadRight(18) } else { ''.PadRight(18) }
        Write-Host "    $cmd $args $($entry.Desc)"
    }
    Write-Host ''
}

function Show-Help {
    <#
    .SYNOPSIS
        Prints CLI usage reference.
    .DESCRIPTION
        Args:
            $Repl (switch) — If set, shows REPL-style prefix '/'.

        Returns:
            void
    .EXAMPLE
        Show-Help
        Show-Help -Repl
    #>
    param([switch]$Repl)
    $prefix = if ($Repl) { '' } else { '.\cli.ps1 ' }
    Write-Host ''
    Write-Host "  AI Assistant CLI v0.7.1  |  $BaseUrl" -ForegroundColor Cyan
    Write-Host '  ─────────────────────────────────────────────────────────'
    Invoke-ListCommands
    if (-not $Repl) {
        Write-Host "  Options:"
        Write-Host "    --model <prefix::id>    Model for generate/chat"
        Write-Host "    --base-url <url>         API base URL (default: http://localhost:9696)"
        Write-Host "    --top-k <n>              RAG results count (default: 5)"
        Write-Host "    --raw                    Output raw JSON"
        Write-Host ''
    }
}
