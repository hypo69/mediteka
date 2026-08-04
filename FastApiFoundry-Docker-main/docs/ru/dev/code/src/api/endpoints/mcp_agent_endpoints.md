# Mcp Agent Endpoints

**Файл:** `src/api/endpoints/mcp_agent_endpoints.py`  
**Тип:** `.py`

---

### `_get_mcp_agent` — Функция

```python
def _get_mcp_agent()
```

Lazy-import McpAgent from the agent registry to avoid circular imports.

### `list_mcp_agent_tools` — Функция

```python
@router.get('/mcp-agent/tools')
```

List all MCP tools discovered from local MCP servers.

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

### `refresh_mcp_agent_tools` — Функция

```python
@router.post('/mcp-agent/refresh-tools')
```

Re-discover tools from all MCP servers in settings.json.

Useful after starting new MCP servers or changing settings.json.
Clears the cached tool list and re-queries each server via tools/list.

Returns:
    dict: success, total discovered tools count.

### `list_mcp_agent_servers` — Функция

```python
@router.get('/mcp-agent/servers')
```

List MCP servers with their discovered tool counts.

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


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
