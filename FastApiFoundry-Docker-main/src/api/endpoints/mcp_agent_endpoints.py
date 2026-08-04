# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: MCP Agent Endpoints — API for McpAgent tool discovery
# =============================================================================
# Description:
#   Exposes McpAgent tool discovery and refresh via REST API.
#   Agent execution itself goes through the standard POST /api/v1/agent/run
#   endpoint with "agent": "mcp".
#
#   Endpoints:
#     GET  /api/v1/mcp-agent/tools          — list all discovered MCP tools
#     POST /api/v1/mcp-agent/refresh-tools  — re-discover tools from servers
#     GET  /api/v1/mcp-agent/servers        — list servers with tool counts
#
# File: src/api/endpoints/mcp_agent_endpoints.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Changes in 0.6.1:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_mcp_agent():
    """Lazy-import McpAgent from the agent registry to avoid circular imports."""
    from ..endpoints.agent import get_registry
    return get_registry().get("mcp")


@router.get("/mcp-agent/tools")
async def list_mcp_agent_tools() -> dict:
    """List all MCP tools discovered from local MCP servers.

    Returns a flat list of all tools available to the MCP agent,
    grouped by server name.

    Returns:
        dict: success, tools list, total count.

    Example response:
        {
          "success": true,
          "total": 5,
          "tools": [
            {
              "name": "mcp__powershell-stdio__run-script",
              "server": "powershell-stdio",
              "mcp_tool": "run-script",
              "description": "[MCP:powershell-stdio] Run a PowerShell script"
            }
          ]
        }
    """
    agent = _get_mcp_agent()
    if not agent:
        return {"success": False, "error": "McpAgent not registered"}

    tools = agent.tools
    result = []
    for t in tools:
        # Parse mcp__server__tool format
        parts = t.name.split("__", 2)
        server = parts[1] if len(parts) >= 2 else "unknown"
        mcp_tool = parts[2] if len(parts) >= 3 else t.name
        result.append({
            "name": t.name,
            "server": server,
            "mcp_tool": mcp_tool,
            "description": t.description,
        })

    return {"success": True, "total": len(result), "tools": result}


@router.post("/mcp-agent/refresh-tools")
async def refresh_mcp_agent_tools() -> dict:
    """Re-discover tools from all MCP servers in settings.json.

    Useful after starting new MCP servers or changing settings.json.
    Clears the cached tool list and re-queries each server via tools/list.

    Returns:
        dict: success, total discovered tools count.
    """
    agent = _get_mcp_agent()
    if not agent:
        return {"success": False, "error": "McpAgent not registered"}

    tools = agent.refresh_tools()
    logger.info(f"✅ MCP tools refreshed: {len(tools)} tool(s)")
    return {"success": True, "total": len(tools), "message": f"Discovered {len(tools)} tool(s)"}


@router.get("/mcp-agent/servers")
async def list_mcp_agent_servers() -> dict:
    """List MCP servers with their discovered tool counts.

    Returns:
        dict: success, servers list with tool counts per server.

    Example response:
        {
          "success": true,
          "servers": [
            {"name": "powershell-stdio", "tool_count": 3},
            {"name": "local-models", "tool_count": 2}
          ]
        }
    """
    agent = _get_mcp_agent()
    if not agent:
        return {"success": False, "error": "McpAgent not registered"}

    tools = agent.tools
    counts: dict = {}
    for t in tools:
        parts = t.name.split("__", 2)
        server = parts[1] if len(parts) >= 2 else "unknown"
        counts[server] = counts.get(server, 0) + 1

    return {
        "success": True,
        "servers": [{"name": k, "tool_count": v} for k, v in counts.items()],
    }
