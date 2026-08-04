# Ollama Client

**Файл:** `src/models/ollama_client.py`  
**Тип:** `.py`

---

### `_get_base_url` — Функция

```python
def _get_base_url() -> str
```

Get Ollama base URL from env or config.json.

Returns:
    str: Base URL, e.g. http://localhost:11434

### `OllamaClient` — Класс

```python
class OllamaClient
```

Async client for Ollama local model server.

Communicates with Ollama REST API (http://localhost:11434).
All methods return {"success": bool, ...} — never raise to callers.

Example:
    >>> from src.models.ollama_client import ollama_client
    >>> import asyncio
    >>> asyncio.run(ollama_client.list_models())
    {"success": True, "models": [...]}

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `_get_session` — Функция

```python
async def _get_session(self) -> aiohttp.ClientSession
```

Lazy-init aiohttp session.

### `close` — Функция

```python
async def close(self) -> None
```

Close the HTTP session.

### `get_status` — Функция

```python
async def get_status(self) -> dict
```

Check if Ollama server is reachable.

Returns:
    dict: {"success": bool, "running": bool, "url": str, "version": str}

### `list_models` — Функция

```python
async def list_models(self) -> dict
```

List locally available Ollama models.

Returns:
    dict: {"success": bool, "models": [{"name": str, "size_gb": float, ...}]}

### `pull_model` — Функция

```python
async def pull_model(self, model: str) -> dict
```

Pull (download) a model from Ollama Hub.

Args:
    model: Model name, e.g. "qwen2.5:0.5b" or "llama3.2:1b".

Returns:
    dict: {"success": bool, "model": str}

### `delete_model` — Функция

```python
async def delete_model(self, model: str) -> dict
```

Delete a local Ollama model.

Args:
    model: Model name, e.g. "qwen2.5:0.5b".

Returns:
    dict: {"success": bool, "model": str}

### `generate` — Функция

```python
async def generate(self, prompt: str, model: str, max_tokens: int=512, temperature: float=0.7) -> dict
```

Generate text via Ollama /api/generate.

Args:
    prompt:      Input text.
    model:       Model name, e.g. "qwen2.5:0.5b".
    max_tokens:  Maximum tokens to generate.
    temperature: Sampling temperature.

Returns:
    dict: {"success": bool, "content": str, "model": str}


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
