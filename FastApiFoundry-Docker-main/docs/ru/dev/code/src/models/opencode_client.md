# Opencode Client

**Файл:** `src/models/opencode_client.py`  
**Тип:** `.py`

---

OpenCode 1.15.x HTTP/CLI integration client.

### `OpenCodeClient` — Класс

```python
class OpenCodeClient
```

Small client for `opencode serve` and the OpenCode HTTP API.

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `_settings` — Функция

```python
def _settings(self, include_secret: bool=False) -> Dict[str, Any]
```

### `settings` — Функция

```python
def settings(self) -> Dict[str, Any]
```

### `_to_openai_model_id` — Функция

```python
@staticmethod
```

### `build_opencode_config` — Функция

```python
def build_opencode_config(self) -> Dict[str, Any]
```

Build a valid project-local opencode.json from config.json.

### `write_opencode_config` — Функция

```python
def write_opencode_config(self) -> Dict[str, Any]
```

Write the generated OpenCode config into the project root.

### `_headers` — Функция

```python
def _headers(self) -> Dict[str, str]
```

### `health` — Функция

```python
async def health(self) -> Dict[str, Any]
```

### `request` — Функция

```python
async def request(self, method: str, path: str, json_body: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
```

### `start` — Функция

```python
async def start(self) -> Dict[str, Any]
```

### `stop` — Функция

```python
async def stop(self) -> Dict[str, Any]
```

### `send_message` — Функция

```python
async def send_message(self, prompt: str, session_id: str='', model: Optional[Dict[str, str]]=None, agent: str='', system: str='') -> Dict[str, Any]
```

### `pid` — Функция

```python
@property
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
