# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CLI Commands Registry
# =============================================================================
# Description:
#   Single source of truth for all CLI commands.
#   Used by /list commands and Show-Help.
#
# File: cli/commands/registry.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

$CLI_COMMANDS = @(
    @{ Group = 'System';  Cmd = '/health';              Args = '';                  Desc = 'Service health status' }
    @{ Group = 'System';  Cmd = '/gui admin';           Args = '';                  Desc = 'Open web UI in browser' }
    @{ Group = 'System';  Cmd = '/restart <service>';   Args = 'foundry|llama|docs|rag'; Desc = 'Restart a background service' }
    @{ Group = 'System';  Cmd = '/logs [n]';            Args = '';                  Desc = 'Show last n log lines (default: 50)' }
    @{ Group = 'Models';  Cmd = '/models';              Args = '';                  Desc = 'List all available models' }
    @{ Group = 'Models';  Cmd = '/list models';          Args = '';                  Desc = 'List all available models (alias)' }
    @{ Group = 'Models';  Cmd = '/generate <prompt>';   Args = '';                  Desc = 'Generate text from prompt' }
    @{ Group = 'Chat';    Cmd = '/chat';                Args = '';                  Desc = 'Interactive chat session' }
    @{ Group = 'RAG';     Cmd = '/rag search <query>';  Args = '';                  Desc = 'Search RAG index' }
    @{ Group = 'RAG';     Cmd = '/rag build <dir>';     Args = '';                  Desc = 'Build RAG index from directory' }
    @{ Group = 'RAG';     Cmd = '/rag status';          Args = '';                  Desc = 'RAG system status' }
    @{ Group = 'RAG';     Cmd = '/rag profiles';        Args = '';                  Desc = 'List RAG profiles' }
    @{ Group = 'Foundry'; Cmd = '/foundry status';      Args = '';                  Desc = 'Foundry service status' }
    @{ Group = 'Foundry'; Cmd = '/foundry models';      Args = '';                  Desc = 'List Foundry models' }
    @{ Group = 'Foundry'; Cmd = '/foundry load <id>';   Args = '';                  Desc = 'Load a Foundry model' }
    @{ Group = 'Foundry'; Cmd = '/foundry unload <id>'; Args = '';                  Desc = 'Unload a Foundry model' }
    @{ Group = 'MCP';     Cmd = '/list mcp';            Args = '';                  Desc = 'List MCP servers with status' }
    @{ Group = 'MCP';     Cmd = '/start mcp <name>';    Args = '-all';              Desc = 'Start MCP server(s)' }
    @{ Group = 'MCP';     Cmd = '/stop mcp <name>';     Args = '-all';              Desc = 'Stop MCP server(s)' }
    @{ Group = 'Config';  Cmd = '/config get';          Args = '';                  Desc = 'Show current config' }
    @{ Group = 'Config';  Cmd = '/config set <k> <v>';  Args = '';                  Desc = 'Update config value (dot-notation)' }
    @{ Group = 'CLI';     Cmd = '/list commands';       Args = '';                  Desc = 'Show this command list' }
    @{ Group = 'CLI';     Cmd = '/help';                Args = '';                  Desc = 'Show help' }
    @{ Group = 'CLI';     Cmd = '/exit  /quit  Ctrl+C'; Args = '';                  Desc = 'Exit REPL' }
)
