# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CLI Chat Command
# =============================================================================
# Description:
#   Full interactive chat session: start session, send messages,
#   display streamed responses, end session.
#
# File: cli/commands/chat.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

function Invoke-Chat {
    <#
    .SYNOPSIS
        Starts an interactive chat session in the terminal.
    .DESCRIPTION
        Creates a server-side session, then enters a read-respond loop.
        Session history is maintained server-side for the duration.

        Args:
            $ModelId (string) — Optional model ID with prefix, e.g. 'ollama::llama3'.

        Returns:
            void — Interactive loop. Type 'exit', 'quit', or press Ctrl+C to end.
    .EXAMPLE
        Invoke-Chat
        Invoke-Chat "foundry::qwen3-0.6b"
    #>
    param([string]$ModelId = '')

    # Start session
    $body = @{ model = if ($ModelId) { $ModelId } else { 'default' } }
    $session = Invoke-Api POST /chat/start $body
    if (-not $session) { return }

    $sid   = $session.session_id
    $model = $session.model

    Write-Host ''
    Write-Ok "Chat started"
    Write-Host "  Session : $($sid.Substring(0,8))..." -ForegroundColor DarkGray
    Write-Host "  Model   : $model"                    -ForegroundColor DarkGray
    Write-Host "  Type 'exit' or Ctrl+C to end"        -ForegroundColor DarkGray
    Write-Host ''

    while ($true) {
        # Prompt
        try {
            $input = Read-Host 'You'
        } catch {
            break   # Ctrl+C
        }

        if (-not $input) { continue }
        if ($input.ToLower() -in 'exit', 'quit', '/exit', '/quit') { break }

        # Send message
        $msgBody = @{ session_id = $sid; message = $input }
        if ($ModelId) { $msgBody.model = $ModelId }

        $r = Invoke-Api POST /chat/message $msgBody
        if (-not $r) { continue }
        if (-not $r.success) { Write-Err $r.error; continue }

        # Display response
        Write-Host ''
        Write-Host 'AI: ' -ForegroundColor DarkYellow -NoNewline
        Write-Host $r.response -ForegroundColor Yellow
        Write-Host ''
    }

    # Clean up session
    Invoke-Api DELETE "/chat/session/$sid" | Out-Null
    Write-Host ''
    Write-Ok 'Chat ended.'
}
