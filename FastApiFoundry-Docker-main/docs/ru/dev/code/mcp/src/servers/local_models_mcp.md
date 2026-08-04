# Local Models Mcp

**Файл:** `mcp/src/servers/local_models_mcp.py`  
**Тип:** `.py`

---

### `list_tools` — Функция

```python
@server.list_tools()
```

Return all tools exposed by this MCP server.

### `call_tool` — Функция

```python
@server.call_tool()
```

Dispatch tool calls to FastAPI Foundry REST API.

Args:
    name (str): Tool name.
    arguments (dict[str, Any]): Tool arguments.

Returns:
    list[types.TextContent]: Response content.

### `_dispatch` — Функция

```python
async def _dispatch(client: httpx.AsyncClient, name: str, arguments: dict[str, Any]) -> str
```

Route tool name to the correct FastAPI endpoint.

Args:
    client (httpx.AsyncClient): Shared HTTP client.
    name (str): Tool name.
    arguments (dict[str, Any]): Tool arguments.

Returns:
    str: Response text.

### `main` — Функция

```python
async def main() -> None
```

Start MCP STDIO server.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
