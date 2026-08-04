# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: MCP PowerShell Client — Direct JSON-RPC 2.0 over STDIO
# =============================================================================
# Description:
#   Direct async client for our PowerShell MCP STDIO servers.
#   Sends JSON-RPC 2.0 requests via subprocess stdin/stdout.
#   Supports: initialize, tools/list, tools/call, resources/list.
#
# File: mcp_client.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPPowerShellClient:
    """Direct JSON-RPC 2.0 client for PowerShell MCP STDIO servers.

    Launches the server as a subprocess and communicates via stdin/stdout.
    Supports all standard MCP methods.

    Example:
        >>> async with MCPPowerShellClient("mcp-powershell-servers/src/servers/McpSTDIOServer.ps1") as mcp:
        ...     tools = await mcp.list_tools()
        ...     result = await mcp.call_tool("run_powershell", {"command": "Get-Date"})
        ...     print(result)
    """

    def __init__(self, server_script: str) -> None:
        self.server_script = Path(server_script).resolve()
        self._process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0

    async def __aenter__(self) -> "MCPPowerShellClient":
        await self._start()
        await self._initialize()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.stop()

    async def _start(self) -> None:
        if not self.server_script.exists():
            raise FileNotFoundError(f"MCP server not found: {self.server_script}")

        self._process = await asyncio.create_subprocess_exec(
            "pwsh", "-ExecutionPolicy", "Bypass", "-File", str(self.server_script),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        logger.info(f"✅ MCP server started: {self.server_script.name}")

    async def _send(self, method: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        if not self._process:
            return None

        self._request_id += 1
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or {},
        }) + "\n"

        try:
            self._process.stdin.write(request.encode())
            await self._process.stdin.drain()
            line = await asyncio.wait_for(self._process.stdout.readline(), timeout=10.0)
            if line:
                return json.loads(line.decode().strip())
        except asyncio.TimeoutError:
            logger.error(f"❌ MCP request timeout: {method}")
        except Exception as e:
            logger.error(f"❌ MCP request failed: {method} — {e}")
        return None

    async def _initialize(self) -> None:
        response = await self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
            "clientInfo": {"name": "FastAPIFoundrySDK", "version": "0.6.0"},
        })
        if response and "result" in response:
            server_name = response["result"].get("serverInfo", {}).get("name", "unknown")
            logger.info(f"✅ MCP initialized: server={server_name}")
        else:
            logger.warning("⚠️ MCP initialization response unexpected")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools available on the MCP server.

        Returns:
            List of tool dicts with keys: name, description, inputSchema.
        """
        response = await self._send("tools/list")
        if response and "result" in response:
            return response["result"].get("tools", [])
        return []

    async def call_tool(self, tool_name: str, arguments: Optional[Dict] = None) -> Dict[str, Any]:
        """Call a tool on the MCP server.

        Args:
            tool_name: Tool name as returned by list_tools().
            arguments: Tool input arguments dict.

        Returns:
            dict: success, content (list of text/data items), raw response.
        """
        response = await self._send("tools/call", {
            "name": tool_name,
            "arguments": arguments or {},
        })
        if not response:
            return {"success": False, "error": "No response from MCP server"}

        if "error" in response:
            return {"success": False, "error": response["error"]}

        result = response.get("result", {})
        content = result.get("content", [])
        text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
        return {
            "success": True,
            "content": "\n".join(text_parts),
            "raw": result,
        }

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List resources available on the MCP server.

        Returns:
            List of resource dicts with keys: name, uri, mimeType.
        """
        response = await self._send("resources/list")
        if response and "result" in response:
            return response["result"].get("resources", [])
        return []

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource by URI.

        Args:
            uri: Resource URI as returned by list_resources().

        Returns:
            dict: success, content.
        """
        response = await self._send("resources/read", {"uri": uri})
        if not response:
            return {"success": False, "error": "No response"}
        return {"success": True, "content": response.get("result", {})}

    async def stop(self) -> None:
        """Stop the MCP server subprocess."""
        if self._process:
            try:
                self._process.terminate()
                await self._process.wait()
            except Exception:
                pass
            logger.info("🛑 MCP server stopped")
