# Mcp Agent

**Файл:** `src/agents/mcp_agent.py`  
**Тип:** `.py`

---

### `_load_mcp_settings` — Функция

```python
def _load_mcp_settings() -> Dict[str, Any]
```

### `_call_stdio` — Функция

```python
def _call_stdio(command: str, args: List[str], env: Dict[str, str], method: str, params: Dict) -> Dict
```

Send a single JSON-RPC request to an MCP STDIO server.

Args:
    command: Executable (e.g. 'pwsh', 'python').
    args: Command arguments list.
    env: Environment variables dict.
    method: JSON-RPC method name.
    params: JSON-RPC params dict.

Returns:
    Dict: Parsed JSON-RPC response or {'error': '...'} on failure.

### `_build_env` — Функция

```python
def _build_env(cfg: Dict[str, Any]) -> Dict[str, str]
```

Build environment dict for an MCP server config entry.

Args:
    cfg: Server config dict from settings.json.

Returns:
    Dict[str, str]: Merged environment variables.

### `_discover_tools_for_server` — Функция

```python
def _discover_tools_for_server(name: str, cfg: Dict[str, Any]) -> List[ToolDefinition]
```

Query an MCP server for its tool list via tools/list.

Args:
    name: Server name (key in mcpServers).
    cfg: Server config dict.

Returns:
    List[ToolDefinition]: Discovered tools, prefixed with 'mcp__<server>__'.

### `McpAgent` — Класс

```python
class McpAgent(BaseAgent)
```

Foundry agent that uses local MCP servers as tools.

Dynamically discovers tools from all servers listed in
mcp-powershell-servers/settings.json and exposes them to the Foundry
model via OpenAI function calling.

Tool naming convention:
    mcp__<server_name>__<tool_name>

Example:
    mcp__powershell-stdio__run-script
    mcp__local-models__generate_text

### `__init__` — Функция

```python
def __init__(self, foundry_client) -> None
```

### `tools` — Функция

```python
@property
```

### `refresh_tools` — Функция

```python
def refresh_tools(self) -> List[ToolDefinition]
```

Re-discover tools from all MCP servers.

Returns:
    List[ToolDefinition]: Updated tool list.

### `_discover_all_tools` — Функция

```python
def _discover_all_tools(self) -> List[ToolDefinition]
```

Discover tools from all servers in settings.json.

Returns:
    List[ToolDefinition]: All discovered tools across all servers.

### `_parse_tool_name` — Функция

```python
def _parse_tool_name(self, tool_name: str)
```

Parse 'mcp__server__tool' into (server_name, mcp_tool_name).

Args:
    tool_name: Full prefixed tool name.

Returns:
    Tuple[str, str] | None: (server_name, mcp_tool_name) or None if invalid.

### `_execute_tool` — Функция

```python
async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str
```

Route a tool call to the appropriate MCP server.

Args:
    name: Full tool name (mcp__<server>__<tool>).
    arguments: Tool arguments from the model.

Returns:
    str: Tool result text or error message.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
