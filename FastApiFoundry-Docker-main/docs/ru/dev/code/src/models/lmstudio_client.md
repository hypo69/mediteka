# Lmstudio Client

**Файл:** `src/models/lmstudio_client.py`  
**Тип:** `.py`

---

### `_get_config_section` — Функция

```python
def _get_config_section() -> dict
```

### `_get_base_url` — Функция

```python
def _get_base_url() -> str
```

### `_get_api_key` — Функция

```python
def _get_api_key() -> str
```

### `_get_default_model` — Функция

```python
def _get_default_model() -> str
```

### `_get_timeout_seconds` — Функция

```python
def _get_timeout_seconds() -> int
```

### `_extract_message_content` — Функция

```python
def _extract_message_content(data: dict) -> str
```

Extract assistant text from LM Studio /api/v1/chat response.

### `LMStudioClient` — Класс

```python
class LMStudioClient
```

Async LM Studio REST API v1 client.

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `_get_session` — Функция

```python
async def _get_session(self) -> aiohttp.ClientSession
```

### `close` — Функция

```python
async def close(self) -> None
```

### `_headers` — Функция

```python
def _headers(self) -> dict
```

### `_request` — Функция

```python
async def _request(self, method: str, path: str, **kwargs: Any) -> tuple[int, Any]
```

### `get_status` — Функция

```python
async def get_status(self) -> dict
```

Check LM Studio API reachability through GET /api/v1/models.

### `list_models` — Функция

```python
async def list_models(self) -> dict
```

List models known to LM Studio.

### `load_model` — Функция

```python
async def load_model(self, model: str, **load_options: Any) -> dict
```

Load a model into LM Studio memory.

### `unload_model` — Функция

```python
async def unload_model(self, instance_id: str) -> dict
```

Unload a loaded LM Studio model instance.

### `download_model` — Функция

```python
async def download_model(self, model: str, quantization: str='') -> dict
```

Start a model download job in LM Studio.

### `download_status` — Функция

```python
async def download_status(self, job_id: str) -> dict
```

Get LM Studio download job status.

### `generate` — Функция

```python
async def generate(self, prompt: str, model: str='', temperature: float=0.7, max_tokens: int=512, context_length: Optional[int]=None, reasoning: Optional[str]=None, previous_response_id: Optional[str]=None) -> dict
```

Generate text with LM Studio /api/v1/chat.

### `stream_generate` — Функция

```python
async def stream_generate(self, prompt: str, model: str='', temperature: float=0.7, max_tokens: int=512, context_length: Optional[int]=None, reasoning: Optional[str]=None, previous_response_id: Optional[str]=None) -> AsyncGenerator[dict, None]
```

Stream message.delta chunks from LM Studio /api/v1/chat SSE.

### `_handle_sse_event` — Функция

```python
async def _handle_sse_event(self, event_type: str, data_lines: list[str]) -> AsyncGenerator[dict, None]
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
