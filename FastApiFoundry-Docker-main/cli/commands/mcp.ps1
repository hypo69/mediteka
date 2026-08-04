# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CLI MCP Commands
# =============================================================================
# Description:
#   /list mcp        — list all MCP servers with running/stopped status
#   /start mcp <name>|-all  — start one or all MCP servers
#   /stop  mcp <name>|-all  — stop  one or all MCP servers
#
# File: cli/commands/mcp.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

function Invoke-ListMcp {
    <#
    .SYNOPSIS
        Lists all MCP servers with their running/stopped status.
    .DESCRIPTION
        Returns:
            void — Prints a table of server name, status, and description.
    .EXAMPLE
        Invoke-ListMcp
    #>
    param([switch]$RawOut)
    $r = Invoke-Api GET /mcp-powershell/servers
    if (-not $r) { return }
    if ($RawOut) { Show-Json $r; return }
    if (-not $r.success) { Write-Err $r.error; return }

    Write-Host ''
    Write-Inf "MCP Servers ($($r.servers.Count)):"
    Write-Host ''

    $nameW = 24; $statusW = 10
    Write-Host ("  " + "Name".PadRight($nameW) + "Status".PadRight($statusW) + "Description") `
        -ForegroundColor DarkGray
    Write-Host ("  " + ('-' * $nameW) + ('-' * $statusW) + ('-' * 36)) -ForegroundColor DarkGray

    foreach ($s in $r.servers) {
        $statusColor = if ($s.status -eq 'running') { 'Green' } else { 'DarkGray' }
        $icon        = if ($s.status -eq 'running') { '▶' } else { '■' }
        $name        = $s.name.PadRight($nameW)
        $status      = "$icon $($s.status)".PadRight($statusW)
        Write-Host "  $name" -NoNewline
        Write-Host $status   -NoNewline -ForegroundColor $statusColor
        Write-Host $s.description
    }
    Write-Host ''
}

function Invoke-StartMcp {
    <#
    .SYNOPSIS
        Starts one or all MCP servers.
    .DESCRIPTION
        Args:
            $Name (string) — Server name, or '-all' to start all servers.

        Returns:
            void
    .EXAMPLE
        Invoke-StartMcp local-models
        Invoke-StartMcp -all
    #>
    param([string]$Name, [switch]$RawOut)

    if (-not $Name) { Write-Err 'Usage: /start mcp <name> | -all'; return }

    if ($Name -eq '-all') {
        $r = Invoke-Api GET /mcp-powershell/servers
        if (-not $r -or -not $r.success) { Write-Err 'Cannot fetch server list'; return }
        foreach ($s in $r.servers) {
            _Start-McpOne $s.name $RawOut
        }
    } else {
        _Start-McpOne $Name $RawOut
    }
}

function Invoke-StopMcp {
    <#
    .SYNOPSIS
        Stops one or all MCP servers.
    .DESCRIPTION
        Args:
            $Name (string) — Server name, or '-all' to stop all servers.

        Returns:
            void
    .EXAMPLE
        Invoke-StopMcp local-models
        Invoke-StopMcp -all
    #>
    param([string]$Name, [switch]$RawOut)

    if (-not $Name) { Write-Err 'Usage: /stop mcp <name> | -all'; return }

    if ($Name -eq '-all') {
        $r = Invoke-Api GET /mcp-powershell/servers
        if (-not $r -or -not $r.success) { Write-Err 'Cannot fetch server list'; return }
        foreach ($s in $r.servers) {
            _Stop-McpOne $s.name $RawOut
        }
    } else {
        _Stop-McpOne $Name $RawOut
    }
}

# ── private helpers ───────────────────────────────────────────────────────────

function _Start-McpOne {
    param([string]$Name, [switch]$RawOut)
    $r = Invoke-Api POST "/mcp-powershell/servers/$Name/start"
    if (-not $r) { return }
    if ($RawOut) { Show-Json $r; return }
    if ($r.success) { Write-Ok "$Name — $($r.message)" } else { Write-Err "$Name — $($r.error)" }
}

function _Stop-McpOne {
    param([string]$Name, [switch]$RawOut)
    $r = Invoke-Api POST "/mcp-powershell/servers/$Name/stop"
    if (-not $r) { return }
    if ($RawOut) { Show-Json $r; return }
    if ($r.success) { Write-Ok "$Name — $($r.message)" } else { Write-Err "$Name — $($r.error)" }
}
