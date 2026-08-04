# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Foundry SDK — MCP PowerShell Demo
# =============================================================================
# Description:
#   Demonstrates MCPPowerShellClient: connect to local PowerShell MCP STDIO
#   server, list tools, call tools, list resources.
#
# Examples:
#   python sdk/fastapi_foundry_sdk/examples/demo_mcp.py
#
# File: demo_mcp.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from sdk.fastapi_foundry_sdk import MCPPowerShellClient

MCP_SERVER = Path(__file__).parents[3] / "mcp-powershell-servers" / "src" / "servers" / "McpSTDIOServer.ps1"


async def main() -> None:
    if not MCP_SERVER.exists():
        print(f"❌ MCP server not found: {MCP_SERVER}")
        return

    async with MCPPowerShellClient(str(MCP_SERVER)) as mcp:

        # List tools
        print("=== Available Tools ===")
        tools = await mcp.list_tools()
        for tool in tools:
            print(f"  🔧 {tool['name']}: {tool.get('description', '')}")

        if not tools:
            print("  No tools found")
            return

        # Call first available tool
        first_tool = tools[0]
        print(f"\n=== Call: {first_tool['name']} ===")
        result = await mcp.call_tool(first_tool["name"], {})
        print(f"  success={result['success']}")
        if result.get("content"):
            print(f"  output: {result['content'][:200]}")

        # List resources
        print("\n=== Resources ===")
        resources = await mcp.list_resources()
        for res in resources[:3]:
            print(f"  📄 {res.get('name')} — {res.get('uri')}")

    print("\n✅ Done")


if __name__ == "__main__":
    asyncio.run(main())
