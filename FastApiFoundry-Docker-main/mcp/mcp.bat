
@echo off
:: Этот файл запускает PowerShell (pwsh.exe) и передает
:: все аргументы в команду Start-GeminiChat из модуля Gemini-Cli.

pwsh.exe -ExecutionPolicy Bypass -NoProfile -Command "& { Import-Module MCP-Servers; Start-MCPServers.ps1 %* }"