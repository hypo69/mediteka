# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Example 05 — Remote MCP via SSE (Azure migration path)
# =============================================================================
# Description:
#   Demonstrates connecting to a remote MCP server via SSE transport.
#   Shows ngrok tunnel setup instructions for Azure AI Foundry migration.
#
# Examples:
#   python sdk/microsoft_foundry_sdk/examples/05_remote_mcp_sse.py
#
# File: 05_remote_mcp_sse.py
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

# Replace with your ngrok URL after running: ngrok http 8443
REMOTE_MCP_URL = "https://your-ngrok-id.ngrok.io/mcp"


async def main() -> None:
    connector = MCPConnector()

    # Print ngrok setup instructions
    print(connector.ngrok_tunnel_note())
    print()

    # Build SSE transport config for remote MCP server
    remote_tool = connector.build_sse_params(
        url=REMOTE_MCP_URL,
        headers={"Authorization": "Bearer your-token"},  # optional
    )
    print(f"Remote MCP config: {remote_tool}")

    # For demo: fall back to local STDIO if ngrok not configured
    if "your-ngrok-id" in REMOTE_MCP_URL:
        print("\n⚠️  Using local STDIO server as fallback (ngrok URL not configured)")
        servers_dir = Path(__file__).parents[3] / "mcp-powershell-servers" / "src" / "servers"
        tool = connector.powershell_stdio_server(str(servers_dir / "McpSTDIOServer.ps1"))
    else:
        tool = remote_tool

    async with FoundryAgent(
        base_url=FOUNDRY_URL,
        model_id=MODEL_ID,
        instructions="You are a helpful assistant with remote tool access.",
        tools=[tool],
    ) as agent:
        response = await agent.run("What tools do you have available?")
        print(f"\nAgent: {response}")

    print("\n✅ Done")


if __name__ == "__main__":
    asyncio.run(main())
