# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: MCP Connector — Local and Remote MCP Server Integration
# =============================================================================
# Description:
#   Connects MCP servers (STDIO or SSE/HTTP) to Foundry Agent.
#   Supports local PowerShell MCP servers via StdioClientTransport
#   and remote servers via SseClientTransport.
#   Includes ngrok tunnel helper for Azure migration path.
#
# File: mcp_connector.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MCP_AVAILABLE = False
try:
    from mcp import StdioServerParameters
    from mcp.client.stdio import StdioClientTransport
    MCP_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ mcp not installed. Run: pip install mcp")


class MCPConnector:
    """Connects MCP servers to Foundry Agent.

    Supports:
    - Local STDIO servers (PowerShell, Python)
    - Remote SSE/HTTP servers
    - Multiple servers simultaneously

    Example:
        >>> connector = MCPConnector()
        >>> tools = await connector.get_tools_from_stdio(
        ...     command="pwsh",
        ...     args=["-File", "mcp-powershell-servers/src/servers/McpSTDIOServer.ps1"]
        ... )
        >>> agent = FoundryAgent(..., tools=tools)
    """

    def __init__(self) -> None:
        self._connections: List[Dict[str, Any]] = []

    def build_stdio_params(
        self,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Build STDIO server parameters for a local MCP server.

        Args:
            command: Executable to run (e.g. 'pwsh', 'python', 'npx').
            args: Arguments list (e.g. ['-File', 'server.ps1']).
            env: Optional environment variables dict.

        Returns:
            dict with transport config for agent-framework.
        """
        return {
            "type": "stdio",
            "command": command,
            "args": args,
            "env": env or {},
        }

    def build_sse_params(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Build SSE/HTTP parameters for a remote MCP server.

        Args:
            url: Remote MCP server URL (e.g. 'https://my-server.ngrok.io/mcp').
            headers: Optional HTTP headers (e.g. Authorization).

        Returns:
            dict with transport config for agent-framework.
        """
        return {
            "type": "sse",
            "url": url,
            "headers": headers or {},
        }

    def powershell_stdio_server(self, server_script: str) -> Dict[str, Any]:
        """Shortcut: connect to a local PowerShell MCP STDIO server.

        Args:
            server_script: Path to .ps1 server script.

        Returns:
            STDIO transport config dict.
        """
        script_path = Path(server_script).resolve()
        if not script_path.exists():
            logger.warning(f"⚠️ MCP server script not found: {script_path}")
        return self.build_stdio_params(
            command="pwsh",
            args=["-ExecutionPolicy", "Bypass", "-File", str(script_path)],
        )

    def python_stdio_server(self, server_script: str) -> Dict[str, Any]:
        """Shortcut: connect to a local Python MCP STDIO server.

        Args:
            server_script: Path to Python server script.

        Returns:
            STDIO transport config dict.
        """
        import sys
        script_path = Path(server_script).resolve()
        return self.build_stdio_params(
            command=sys.executable,
            args=[str(script_path)],
        )

    def npx_server(self, package: str, *args: str) -> Dict[str, Any]:
        """Shortcut: connect to an npx-based MCP server.

        Args:
            package: npm package name (e.g. '@modelcontextprotocol/server-filesystem').
            *args: Additional arguments passed to the package.

        Returns:
            STDIO transport config dict.
        """
        return self.build_stdio_params(
            command="npx",
            args=["-y", package, *args],
        )

    @staticmethod
    def ngrok_tunnel_note() -> str:
        """Return instructions for exposing local MCP server via ngrok (Azure migration).

        Returns:
            str: Setup instructions.
        """
        return (
            "To expose a local MCP server for Azure AI Foundry:\n"
            "  1. Install ngrok: https://ngrok.com/download\n"
            "  2. Start your local MCP HTTPS server on port 8443\n"
            "  3. Run: ngrok http 8443\n"
            "  4. Use the ngrok URL in build_sse_params(url='https://xxxx.ngrok.io/mcp')\n"
            "  5. Pass the SSE config to your Azure-hosted agent"
        )
