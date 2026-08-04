# Example Mcp Client

**Файл:** `SANDBOX/examples/example_mcp_client.py`  
**Тип:** `.py`

---

### `MCPClient` — Класс

```python
class MCPClient
```

Простой MCP клиент для демонстрации

### `demo_mcp_client` — Функция

```python
async def demo_mcp_client()
```

Демонстрация MCP клиента

### `__init__` — Функция

```python
def __init__(self, server_path: str)
```

### `start_server` — Функция

```python
async def start_server(self)
```

Запуск MCP сервера

### `send_request` — Функция

```python
async def send_request(self, method: str, params: dict=None)
```

Отправка MCP запроса

### `stop_server` — Функция

```python
async def stop_server(self)
```

Остановка MCP сервера


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
