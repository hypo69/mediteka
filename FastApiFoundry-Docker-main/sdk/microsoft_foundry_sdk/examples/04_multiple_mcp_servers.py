# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Example 04 — Multiple MCP Servers (PowerShell + HuggingFace)
# =============================================================================
# Description:
#   Demonstrates connecting multiple MCP servers simultaneously:
#   - PowerShell STDIO server (system tools)
#   - HuggingFace Python MCP server (model search)
#   Agent picks the right tool automatically.
#
# Examples:
#   python sdk/microsoft_foundry_sdk/examples/04_multiple_mcp_servers.py
#
# File: 04_multiple_mcp_servers.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from sdk.microsoft_foundry_sdk import FoundryAgent, MCPConnector

FOUNDRY_URL = "http://localhost:50477/v1"
MODEL_ID = "phi-4"

SERVERS_DIR = Path(__file__).parents[3] / "mcp-powershell-servers" / "src" / "servers"


async def main() -> None:
    connector = MCPConnector()

    # PowerShell STDIO server
    ps_tool = connector.powershell_stdio_server(str(SERVERS_DIR / "McpSTDIOServer.ps1"))

    # HuggingFace Python MCP server
    hf_tool = connector.python_stdio_server(str(SERVERS_DIR / "huggingface_mcp.py"))

    print("MCP servers configured:")
    print(f"  PowerShell: {ps_tool['command']} {ps_tool['args']}")
    print(f"  HuggingFace: {hf_tool['command']} {hf_tool['args']}")

    async with FoundryAgent(
        base_url=FOUNDRY_URL,
        model_id=MODEL_ID,
        instructions=(
            "You are a helpful assistant. "
            "Use PowerShell tools for system tasks. "
            "Use HuggingFace tools to search AI models."
        ),
        tools=[ps_tool, hf_tool],
    ) as agent:

        questions = [
            "What is the current directory?",
            "Find a small text generation model on HuggingFace.",
        ]

        for q in questions:
            print(f"\nUser: {q}")
            response = await agent.run(q)
            print(f"Agent: {response}")

    print("\n✅ Done")


if __name__ == "__main__":
    asyncio.run(main())
