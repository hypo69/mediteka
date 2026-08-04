# Mcp Connector

**Файл:** `sdk/microsoft_foundry_sdk/mcp_connector.py`  
**Тип:** `.py`

---

### `MCPConnector` — Класс

```python
class MCPConnector
```

Connects MCP servers to Foundry Agent.

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

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `build_stdio_params` — Функция

```python
def build_stdio_params(self, command: str, args: List[str], env: Optional[Dict[str, str]]=None) -> Dict[str, Any]
```

Build STDIO server parameters for a local MCP server.

Args:
    command: Executable to run (e.g. 'pwsh', 'python', 'npx').
    args: Arguments list (e.g. ['-File', 'server.ps1']).
    env: Optional environment variables dict.

Returns:
    dict with transport config for agent-framework.

### `build_sse_params` — Функция

```python
def build_sse_params(self, url: str, headers: Optional[Dict[str, str]]=None) -> Dict[str, Any]
```

Build SSE/HTTP parameters for a remote MCP server.

Args:
    url: Remote MCP server URL (e.g. 'https://my-server.ngrok.io/mcp').
    headers: Optional HTTP headers (e.g. Authorization).

Returns:
    dict with transport config for agent-framework.

### `powershell_stdio_server` — Функция

```python
def powershell_stdio_server(self, server_script: str) -> Dict[str, Any]
```

Shortcut: connect to a local PowerShell MCP STDIO server.

Args:
    server_script: Path to .ps1 server script.

Returns:
    STDIO transport config dict.

### `python_stdio_server` — Функция

```python
def python_stdio_server(self, server_script: str) -> Dict[str, Any]
```

Shortcut: connect to a local Python MCP STDIO server.

Args:
    server_script: Path to Python server script.

Returns:
    STDIO transport config dict.

### `npx_server` — Функция

```python
def npx_server(self, package: str, *args: str) -> Dict[str, Any]
```

Shortcut: connect to an npx-based MCP server.

Args:
    package: npm package name (e.g. '@modelcontextprotocol/server-filesystem').
    *args: Additional arguments passed to the package.

Returns:
    STDIO transport config dict.

### `ngrok_tunnel_note` — Функция

```python
@staticmethod
```

Return instructions for exposing local MCP server via ngrok (Azure migration).

Returns:
    str: Setup instructions.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
