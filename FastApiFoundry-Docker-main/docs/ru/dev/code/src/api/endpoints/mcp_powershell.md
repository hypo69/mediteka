# Mcp Powershell

**Файл:** `src/api/endpoints/mcp_powershell.py`  
**Тип:** `.py`

---

### `_load_settings` — Функция

```python
def _load_settings() -> Dict[str, Any]
```

### `_save_settings` — Функция

```python
def _save_settings(data: Dict[str, Any]) -> None
```

### `_load_pids` — Функция

```python
def _load_pids() -> Dict[str, int]
```

### `_save_pids` — Функция

```python
def _save_pids(pids: Dict[str, int]) -> None
```

### `_is_process_alive` — Функция

```python
def _is_process_alive(pid: int) -> bool
```

### `_get_server_status` — Функция

```python
def _get_server_status(name: str) -> str
```

### `list_mcp_servers` — Функция

```python
@router.get('/mcp-powershell/servers')
```

List all MCP servers from settings.json with their status

### `start_mcp_server` — Функция

```python
@router.post('/mcp-powershell/servers/{name}/start')
```

Start an MCP server by name

### `stop_mcp_server` — Функция

```python
@router.post('/mcp-powershell/servers/{name}/stop')
```

Stop an MCP server by name

### `get_mcp_server_status` — Функция

```python
@router.get('/mcp-powershell/servers/{name}/status')
```

Status of a specific MCP server

### `get_mcp_settings` — Функция

```python
@router.get('/mcp-powershell/settings')
```

Get the contents of mcp-powershell-servers/settings.json

### `McpSettingsRequest` — Класс

```python
class McpSettingsRequest(BaseModel)
```

### `save_mcp_settings` — Функция

```python
@router.post('/mcp-powershell/settings')
```

Save mcp-powershell-servers/settings.json


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
