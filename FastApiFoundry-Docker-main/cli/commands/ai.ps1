# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CLI AI Commands
# =============================================================================
# Description:
#   models, generate, rag (search/build/status/profiles),
#   foundry (status/models/load/unload), config (get/set).
#
# File: cli/commands/ai.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

function Invoke-Models {
    <#
    .SYNOPSIS
        Lists all available models.
    .DESCRIPTION
        Returns:
            void — Prints model IDs and providers.
    .EXAMPLE
        Invoke-Models
    #>
    param([switch]$RawOut)
    $r = Invoke-Api GET /models
    if (-not $r) { return }
    if ($RawOut) { Show-Json $r; return }
    Write-Inf "Available models ($($r.count)):"
    foreach ($m in $r.models) {
        $p = if ($m.provider) { " [$($m.provider)]" } else { '' }
        Write-Host "  • $($m.id)$p"
    }
}

function Invoke-Generate {
    <#
    .SYNOPSIS
        Generates text from a prompt.
    .DESCRIPTION
        Args:
            $Prompt  (string) — Input text (required).
            $ModelId (string) — Model ID with prefix, e.g. 'ollama::llama3'.

        Returns:
            void — Prints generated content.
    .EXAMPLE
        Invoke-Generate "Explain FAISS" "ollama::llama3"
    #>
    param([string]$Prompt, [string]$ModelId = '', [switch]$RawOut)
    if (-not $Prompt) { Write-Err 'Prompt required.'; return }
    $body = @{ prompt = $Prompt }
    if ($ModelId) { $body.model = $ModelId }
    $r = Invoke-Api POST /generate $body
    if (-not $r) { return }
    if ($RawOut) { Show-Json $r; return }
    if (-not $r.success) { Write-Err $r.error; return }
    Write-Host $r.content
    Write-Host ''
    Write-Inf "Model: $($r.model)  |  Tokens: $($r.usage.total_tokens)"
}

function Invoke-Rag {
    <#
    .SYNOPSIS
        RAG subcommands: search, build, status, profiles.
    .DESCRIPTION
        Args:
            $SubCmd (string) — search | build | status | profiles.
            $A1     (string) — Query (search) or directory path (build).
            $K      (int)    — Top-K results for search.

        Returns:
            void
    .EXAMPLE
        Invoke-Rag search "what is FAISS" 5
        Invoke-Rag build ./docs
    #>
    param([string]$SubCmd, [string]$A1 = '', [int]$K = 5, [switch]$RawOut)
    switch ($SubCmd) {
        'search' {
            if (-not $A1) { Write-Err 'Usage: /rag search <query>'; return }
            $r = Invoke-Api POST /rag/search @{ query = $A1; top_k = $K }
            if (-not $r) { return }
            if ($RawOut) { Show-Json $r; return }
            if (-not $r.success) { Write-Err $r.error; return }
            Write-Inf "Results ($($r.total)):"
            $i = 1
            foreach ($res in $r.results) {
                $preview = $res.content.Substring(0, [math]::Min(180, $res.content.Length))
                Write-Host "[$i] score=$([math]::Round($res.score,3))" -ForegroundColor Cyan
                Write-Host "    $preview..."
                $i++
            }
        }
        'build' {
            if (-not $A1) { Write-Err 'Usage: /rag build <directory>'; return }
            Write-Inf "Building RAG index from: $A1"
            $r = Invoke-Api POST /rag/build @{ docs_dir = $A1 }
            if (-not $r) { return }
            if ($RawOut) { Show-Json $r; return }
            if (-not $r.success) { Write-Err $r.error; return }
            Write-Ok "$($r.message) — $($r.chunks) chunks"
        }
        'status' {
            $r = Invoke-Api GET /rag/status
            if (-not $r) { return }
            if ($RawOut) { Show-Json $r; return }
            Write-Host "Enabled   : $($r.enabled)"
            Write-Host "Index dir : $($r.index_dir)"
            Write-Host "Model     : $($r.model)"
            Write-Host "Chunks    : $($r.total_chunks)"
        }
        'profiles' {
            $r = Invoke-Api GET /rag/profiles
            if (-not $r) { return }
            if ($RawOut) { Show-Json $r; return }
            Write-Inf "RAG profiles ($($r.profiles.Count)):"
            foreach ($p in $r.profiles) {
                $idx = if ($p.has_index) { '✅' } else { '⬜' }
                Write-Host "  $idx $($p.name)"
            }
        }
        default { Write-Err "Unknown rag subcommand: '$SubCmd'. Use: search | build | status | profiles" }
    }
}

function Invoke-Foundry {
    <#
    .SYNOPSIS
        Foundry subcommands: status, models, load, unload.
    .DESCRIPTION
        Args:
            $SubCmd  (string) — status | models | load | unload.
            $ModelId (string) — Model ID for load/unload.

        Returns:
            void
    .EXAMPLE
        Invoke-Foundry status
        Invoke-Foundry load qwen3-0.6b-generic-cpu:4
    #>
    param([string]$SubCmd, [string]$ModelId = '', [switch]$RawOut)
    switch ($SubCmd) {
        'status' {
            $r = Invoke-Api GET /foundry/status
            if (-not $r) { return }
            if ($RawOut) { Show-Json $r; return }
            $color = if ($r.running) { 'Green' } else { 'Red' }
            Write-Host "Running : $($r.running)" -ForegroundColor $color
            Write-Host "Status  : $($r.status)"
            if ($r.port) { Write-Host "Port    : $($r.port)" }
            if ($r.url)  { Write-Host "URL     : $($r.url)" }
            if ($r.error){ Write-Err $r.error }
        }
        'models' {
            $r = Invoke-Api GET /foundry/models/list
            if (-not $r) { return }
            if ($RawOut) { Show-Json $r; return }
            Write-Inf "Foundry models ($($r.models.Count)):"
            foreach ($m in $r.models) { Write-Host "  • $($m.id)" }
        }
        'load' {
            if (-not $ModelId) { Write-Err 'Usage: /foundry load <model-id>'; return }
            $r = Invoke-Api POST /foundry/models/load @{ model_id = $ModelId }
            if (-not $r) { return }
            if ($RawOut) { Show-Json $r; return }
            if ($r.success) { Write-Ok "Loaded: $ModelId" } else { Write-Err $r.error }
        }
        'unload' {
            if (-not $ModelId) { Write-Err 'Usage: /foundry unload <model-id>'; return }
            $r = Invoke-Api POST /foundry/models/unload @{ model_id = $ModelId }
            if (-not $r) { return }
            if ($RawOut) { Show-Json $r; return }
            if ($r.success) { Write-Ok "Unloaded: $ModelId" } else { Write-Err $r.error }
        }
        default { Write-Err "Unknown foundry subcommand: '$SubCmd'. Use: status | models | load | unload" }
    }
}

function Invoke-Config {
    <#
    .SYNOPSIS
        Config subcommands: get, set.
    .DESCRIPTION
        Args:
            $SubCmd (string) — get | set.
            $Key    (string) — Dot-notation key, e.g. 'rag_system.enabled'.
            $Value  (string) — New value for set.

        Returns:
            void
    .EXAMPLE
        Invoke-Config get
        Invoke-Config set rag_system.enabled true
    #>
    param([string]$SubCmd, [string]$Key = '', [string]$Value = '', [switch]$RawOut)
    switch ($SubCmd) {
        'get' {
            $r = Invoke-Api GET /config
            if (-not $r) { return }
            Show-Json $r
        }
        'set' {
            if (-not $Key -or -not $Value) { Write-Err 'Usage: /config set <key.path> <value>'; return }
            $keys = $Key -split '\.'
            $val  = switch ($Value.ToLower()) {
                'true'  { $true }
                'false' { $false }
                default { if ($Value -match '^\d+$') { [int]$Value } else { $Value } }
            }
            $update = @{}; $cur = $update
            for ($i = 0; $i -lt $keys.Count - 1; $i++) { $cur[$keys[$i]] = @{}; $cur = $cur[$keys[$i]] }
            $cur[$keys[-1]] = $val
            $r = Invoke-Api POST /config $update
            if (-not $r) { return }
            if ($RawOut) { Show-Json $r; return }
            if ($r.success) { Write-Ok "Set $Key = $Value" } else { Write-Err ($r.error ?? 'Failed') }
        }
        default { Write-Err "Unknown config subcommand: '$SubCmd'. Use: get | set" }
    }
}
