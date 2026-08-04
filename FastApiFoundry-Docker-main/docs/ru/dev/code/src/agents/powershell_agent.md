# Powershell Agent

**Файл:** `src/agents/powershell_agent.py`  
**Тип:** `.py`

---

### `_find_server_script` — Функция

```python
def _find_server_script(name: str) -> Optional[str]
```

### `_call_mcp_stdio` — Функция

```python
def _call_mcp_stdio(script_path: str, method: str, params: Dict) -> Dict
```

Отправить один JSON-RPC запрос в STDIO сервер

### `_extract_content` — Функция

```python
def _extract_content(response: Dict) -> str
```

### `PowerShellAgent` — Класс

```python
class PowerShellAgent(BaseAgent)
```

Агент для работы с локальной системой через MCP PowerShell серверы

### `tools` — Функция

```python
@property
```

### `_execute_tool` — Функция

```python
async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str
```

Execute a tool by name.

Args:
    name: Tool name ('run_powershell', 'run_wp_cli', 'http_get').
    arguments: Parsed JSON arguments from the model's tool_call.

Returns:
    str: Tool execution result as a string.

### `_run_powershell` — Функция

```python
async def _run_powershell(self, args: Dict) -> str
```

Execute PowerShell script via McpSTDIOServer.

Args:
    args: Dict with keys: script (str), working_directory (str, optional).

Returns:
    str: Script output or error message.

### `_run_wp_cli` — Функция

```python
async def _run_wp_cli(self, args: Dict) -> str
```

Execute WP-CLI command via McpWPCLIServer.

Args:
    args: Dict with keys: command (str), working_directory (str, optional).

Returns:
    str: WP-CLI output or error message.

### `_http_get` — Функция

```python
async def _http_get(self, args: Dict) -> str
```

Execute HTTP GET request.

Args:
    args: Dict with key: url (str).

Returns:
    str: HTTP status and response body (first 2000 chars) or error message.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
