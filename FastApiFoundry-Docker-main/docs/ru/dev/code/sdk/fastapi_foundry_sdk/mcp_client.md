# Mcp Client

**Файл:** `sdk/fastapi_foundry_sdk/mcp_client.py`  
**Тип:** `.py`

---

### `MCPPowerShellClient` — Класс

```python
class MCPPowerShellClient
```

Direct JSON-RPC 2.0 client for PowerShell MCP STDIO servers.

Launches the server as a subprocess and communicates via stdin/stdout.
Supports all standard MCP methods.

Example:
    >>> async with MCPPowerShellClient("mcp-powershell-servers/src/servers/McpSTDIOServer.ps1") as mcp:
    ...     tools = await mcp.list_tools()
    ...     result = await mcp.call_tool("run_powershell", {"command": "Get-Date"})
    ...     print(result)

### `__init__` — Функция

```python
def __init__(self, server_script: str) -> None
```

### `__aenter__` — Функция

```python
async def __aenter__(self) -> 'MCPPowerShellClient'
```

### `__aexit__` — Функция

```python
async def __aexit__(self, *args: Any) -> None
```

### `_start` — Функция

```python
async def _start(self) -> None
```

### `_send` — Функция

```python
async def _send(self, method: str, params: Optional[Dict]=None) -> Optional[Dict[str, Any]]
```

### `_initialize` — Функция

```python
async def _initialize(self) -> None
```

### `list_tools` — Функция

```python
async def list_tools(self) -> List[Dict[str, Any]]
```

List all tools available on the MCP server.

Returns:
    List of tool dicts with keys: name, description, inputSchema.

### `call_tool` — Функция

```python
async def call_tool(self, tool_name: str, arguments: Optional[Dict]=None) -> Dict[str, Any]
```

Call a tool on the MCP server.

Args:
    tool_name: Tool name as returned by list_tools().
    arguments: Tool input arguments dict.

Returns:
    dict: success, content (list of text/data items), raw response.

### `list_resources` — Функция

```python
async def list_resources(self) -> List[Dict[str, Any]]
```

List resources available on the MCP server.

Returns:
    List of resource dicts with keys: name, uri, mimeType.

### `read_resource` — Функция

```python
async def read_resource(self, uri: str) -> Dict[str, Any]
```

Read a resource by URI.

Args:
    uri: Resource URI as returned by list_resources().

Returns:
    dict: success, content.

### `stop` — Функция

```python
async def stop(self) -> None
```

Stop the MCP server subprocess.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
