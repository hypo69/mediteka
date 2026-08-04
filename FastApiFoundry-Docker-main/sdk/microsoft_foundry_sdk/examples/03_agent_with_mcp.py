# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Example 03 — Agent with MCP PowerShell Server
# =============================================================================
# Description:
#   Demonstrates: FoundryAgent + MCPConnector connecting to local
#   PowerShell MCP STDIO server. Agent auto-calls MCP tools.
#
# Examples:
#   pip install agent-framework --pre
#   python sdk/microsoft_foundry_sdk/examples/03_agent_with_mcp.py
#
# File: 03_agent_with_mcp.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from sdk.microsoft_foundry_sdk import FoundryManager, FoundryAgent, MCPConnector

# Path to our PowerShell MCP STDIO server
MCP_SERVER = Path(__file__).parents[3] / "mcp-powershell-servers" / "src" / "servers" / "McpSTDIOServer.ps1"

# Foundry Local endpoint (auto-discovered by run.py, or set manually)
FOUNDRY_URL = "http://localhost:50477/v1"
MODEL_ID = "phi-4"


async def main() -> None:
    # 1. Ensure model is loaded
    mgr = FoundryManager(app_name="agent_mcp_demo")
    if mgr.initialize():
        mgr.load_model(MODEL_ID)

    # 2. Build MCP tool config
    connector = MCPConnector()
    mcp_tool = connector.powershell_stdio_server(str(MCP_SERVER))
    print(f"MCP server config: {mcp_tool}")

    # 3. Run agent
    # Note: tools list format depends on agent-framework version.
    # Pass mcp_tool as a server config; agent-framework handles tool discovery.
    async with FoundryAgent(
        base_url=FOUNDRY_URL,
        model_id=MODEL_ID,
        instructions="You are a helpful assistant with access to PowerShell tools.",
        tools=[mcp_tool],
    ) as agent:

        print("\n=== Agent: single question ===")
        response = await agent.run("What PowerShell version is installed?")
        print(f"Agent: {response}")

        print("\n=== Agent: streaming ===")
        print("Agent: ", end="", flush=True)
        async for chunk in agent.stream("List files in the current directory."):
            print(chunk, end="", flush=True)
        print()

        print("\n=== Agent: new thread ===")
        agent.new_thread()
        response2 = await agent.run("Hello! Who are you?")
        print(f"Agent: {response2}")

    print("\n✅ Done")


if __name__ == "__main__":
    asyncio.run(main())
