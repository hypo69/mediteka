# cli

> AI Assistant CLI

## Description

Entry point for the AI Assistant command-line interface.
Loads modules from cli/ and dispatches commands to them.
Interactive REPL (no arguments):
.\cli.ps1
> /health
> /gui admin
> /chat
> /list mcp
> /start mcp local-models
> /stop mcp -all
> /list commands
> /exit
Single command:
.\cli.ps1 health
.\cli.ps1 generate "Explain FAISS" --model ollama::llama3
.\cli.ps1 start mcp local-models
File: cli.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Refactored into cli/ module structure
- Added /gui, /list mcp, /start mcp, /stop mcp, /list commands
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

## Source

`cli.ps1`

