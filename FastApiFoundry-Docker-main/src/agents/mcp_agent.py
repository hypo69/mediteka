# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: MCP Agent — Foundry agent backed by local MCP servers
# =============================================================================
# Description:
#   Bridges Microsoft Foundry Local (OpenAI-compatible function calling) with
#   local MCP servers defined in mcp-powershell-servers/settings.json.
#
#   How it works:
#     1. On construction, reads settings.json and discovers all mcpServers.
#     2. For each server it calls `tools/list` via STDIO to enumerate available
#        MCP tools and converts them to OpenAI ToolDefinition objects.
#     3. When the Foundry model emits a tool_call, _execute_tool() routes it to
#        the correct MCP server via `tools/call` over STDIO.
#
#   Supported MCP transports:
#     - STDIO  (pwsh / python command — default for all servers in settings.json)
#
#   Usage via API:
#     POST /api/v1/agent/run  { "agent": "mcp", "message": "...", "model": "..." }
#     GET  /api/v1/mcp-agent/tools          — list all discovered MCP tools
#     POST /api/v1/mcp-agent/refresh-tools  — re-discover tools from running servers
#
# File: src/agents/mcp_agent.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Changes in 0.6.1:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseAgent, ToolDefinition

logger = logging.getLogger(__name__)

MCP_SETTINGS_PATH = Path("mcp/settings.json")
_MCP_TOOL_PREFIX = "mcp__"  # prefix added to tool names to avoid collisions


def _load_mcp_settings() -> Dict[str, Any]:
    if not MCP_SETTINGS_PATH.exists():
        return {"mcpServers": {}}
    with open(MCP_SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _call_stdio(command: str, args: List[str], env: Dict[str, str], method: str, params: Dict) -> Dict:
    """Send a single JSON-RPC request to an MCP STDIO server.

    Args:
        command: Executable (e.g. 'pwsh', 'python').
        args: Command arguments list.
        env: Environment variables dict.
        method: JSON-RPC method name.
        params: JSON-RPC params dict.

    Returns:
        Dict: Parsed JSON-RPC response or {'error': '...'} on failure.
    """
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}) + "\n"
    try:
        proc = subprocess.run(
            [command] + args,
            input=payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=env,
            cwd=str(Path.cwd()),
        )
        stdout = proc.stdout or ""
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        return {"error": f"No JSON in stdout. stderr={proc.stderr[:200]!r}"}
    except subprocess.TimeoutExpired:
        return {"error": "MCP server timeout (30s)"}
    except FileNotFoundError:
        return {"error": f"Command not found: {command}"}
    except Exception as e:
        return {"error": str(e)}


def _build_env(cfg: Dict[str, Any]) -> Dict[str, str]:
    """Build environment dict for an MCP server config entry.

    Args:
        cfg: Server config dict from settings.json.

    Returns:
        Dict[str, str]: Merged environment variables.
    """
    env = os.environ.copy()
    env_file = cfg.get("envFile")
    if env_file and Path(env_file).exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
    for k, v in cfg.get("env", {}).items():
        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            v = os.environ.get(v[2:-1], "")
        env[k] = str(v)
    return env


def _discover_tools_for_server(name: str, cfg: Dict[str, Any]) -> List[ToolDefinition]:
    """Query an MCP server for its tool list via tools/list.

    Args:
        name: Server name (key in mcpServers).
        cfg: Server config dict.

    Returns:
        List[ToolDefinition]: Discovered tools, prefixed with 'mcp__<server>__'.
    """
    command = cfg.get("command", "")
    args = [str(a) for a in cfg.get("args", [])]
    env = _build_env(cfg)

    if not command:
        return []

    # Initialize session first (required by MCP protocol)
    _call_stdio(command, args, env, "initialize", {
        "protocolVersion": "2024-11-05",
        "clientInfo": {"name": "FastApiFoundry", "version": "0.6.1"},
        "capabilities": {}
    })

    resp = _call_stdio(command, args, env, "tools/list", {})
    if "error" in resp:
        logger.warning(f"⚠️ MCP server '{name}' tools/list failed: {resp['error']}")
        return []

    raw_tools = resp.get("result", {}).get("tools", [])
    result: List[ToolDefinition] = []
    for t in raw_tools:
        tool_name = f"{_MCP_TOOL_PREFIX}{name}__{t['name']}"
        result.append(ToolDefinition(
            name=tool_name,
            description=f"[MCP:{name}] {t.get('description', '')}",
            parameters=t.get("inputSchema", {"type": "object", "properties": {}}),
        ))
    logger.info(f"✅ MCP server '{name}': discovered {len(result)} tool(s)")
    return result


class McpAgent(BaseAgent):
    """Foundry agent that uses local MCP servers as tools.

    Dynamically discovers tools from all servers listed in
    mcp-powershell-servers/settings.json and exposes them to the Foundry
    model via OpenAI function calling.

    Tool naming convention:
        mcp__<server_name>__<tool_name>

    Example:
        mcp__powershell-stdio__run-script
        mcp__local-models__generate_text
    """

    name = "mcp"
    description = "Агент с доступом ко всем локальным MCP серверам как инструментам"

    def __init__(self, foundry_client) -> None:
        super().__init__(foundry_client)
        self._tools: Optional[List[ToolDefinition]] = None

    @property
    def tools(self) -> List[ToolDefinition]:
        if self._tools is None:
            self._tools = self._discover_all_tools()
        return self._tools

    def refresh_tools(self) -> List[ToolDefinition]:
        """Re-discover tools from all MCP servers.

        Returns:
            List[ToolDefinition]: Updated tool list.
        """
        self._tools = self._discover_all_tools()
        return self._tools

    def _discover_all_tools(self) -> List[ToolDefinition]:
        """Discover tools from all servers in settings.json.

        Returns:
            List[ToolDefinition]: All discovered tools across all servers.
        """
        settings = _load_mcp_settings()
        servers = settings.get("mcpServers", {})
        all_tools: List[ToolDefinition] = []
        for server_name, cfg in servers.items():
            try:
                tools = _discover_tools_for_server(server_name, cfg)
                all_tools.extend(tools)
            except Exception as e:
                logger.warning(f"⚠️ Could not discover tools for '{server_name}': {e}")
        logger.info(f"✅ McpAgent: total {len(all_tools)} tool(s) from {len(servers)} server(s)")
        return all_tools

    def _parse_tool_name(self, tool_name: str):
        """Parse 'mcp__server__tool' into (server_name, mcp_tool_name).

        Args:
            tool_name: Full prefixed tool name.

        Returns:
            Tuple[str, str] | None: (server_name, mcp_tool_name) or None if invalid.
        """
        if not tool_name.startswith(_MCP_TOOL_PREFIX):
            return None
        rest = tool_name[len(_MCP_TOOL_PREFIX):]
        parts = rest.split("__", 1)
        if len(parts) != 2:
            return None
        return parts[0], parts[1]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Route a tool call to the appropriate MCP server.

        Args:
            name: Full tool name (mcp__<server>__<tool>).
            arguments: Tool arguments from the model.

        Returns:
            str: Tool result text or error message.
        """
        parsed = self._parse_tool_name(name)
        if not parsed:
            return f"❌ Unknown tool format: {name}"

        server_name, mcp_tool = parsed
        settings = _load_mcp_settings()
        cfg = settings.get("mcpServers", {}).get(server_name)
        if not cfg:
            return f"❌ MCP server '{server_name}' not found in settings.json"

        command = cfg.get("command", "")
        args = [str(a) for a in cfg.get("args", [])]
        env = _build_env(cfg)

        # Initialize session
        _call_stdio(command, args, env, "initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "FastApiFoundry", "version": "0.6.1"},
            "capabilities": {}
        })

        resp = _call_stdio(command, args, env, "tools/call", {
            "name": mcp_tool,
            "arguments": arguments,
        })

        if "error" in resp and "result" not in resp:
            return f"❌ MCP error: {resp['error']}"

        result = resp.get("result", {})
        content = result.get("content", [])
        if content:
            return "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
        return json.dumps(result) if result else "Tool executed (no output)"
