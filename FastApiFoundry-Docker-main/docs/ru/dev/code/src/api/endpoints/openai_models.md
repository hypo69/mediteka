# Openai Models

**Файл:** `src/api/endpoints/openai_models.py`  
**Тип:** `.py`

---

### `_safe_get` — Функция

```python
async def _safe_get(coro) -> dict
```

Execute a coroutine and return its result or empty dict on failure.

### `map_to_openai_id` — Функция

```python
def map_to_openai_id(provider_prefixed_id: str) -> str
```

Convert provider-prefixed ID to OpenAI-compatible format.

Replaces '::' with '-' for provider prefixes.
Non-prefixed IDs pass through unchanged.

Args:
    provider_prefixed_id: Model ID with provider prefix (e.g., 'foundry::model-id')

Returns:
    OpenAI-compatible model ID (e.g., 'foundry-model-id')

### `map_from_openai_id` — Функция

```python
def map_from_openai_id(openai_id: str) -> str
```

Convert an OpenAI-facing model ID back to the internal provider prefix.

### `_safe_collect` — Функция

```python
async def _safe_collect(coro) -> list
```

Execute collection coroutine and return empty list on failure.

### `_collect_foundry` — Функция

```python
async def _collect_foundry() -> list
```

Get Foundry cached models with foundry:: prefix.

### `_collect_hf` — Функция

```python
async def _collect_hf() -> list
```

Get HuggingFace downloaded models with hf:: prefix.

### `_collect_llama` — Функция

```python
async def _collect_llama() -> list
```

Get llama.cpp GGUF models with llama:: prefix.

### `_collect_ollama` — Функция

```python
async def _collect_ollama() -> list
```

Get Ollama local models with ollama:: prefix.

### `collect_all_models` — Функция

```python
async def collect_all_models() -> List[Dict[str, Any]]
```

Collect models from all providers.

Uses asyncio.gather to collect from all providers concurrently.
Continues processing if individual providers fail.

Returns:
    List of all models from all providers

### `build_openai_response` — Функция

```python
def build_openai_response(models: List[Dict[str, Any]]) -> Dict[str, Any]
```

Build OpenAI-compatible response from internal models.

Args:
    models: List of provider model objects

Returns:
    OpenAI-compatible response with data array, total count, and by_provider breakdown

### `get_openai_models` — Функция

```python
@router.get('/v1/models')
```

Get models in OpenAI-compatible format.

Returns a list of all available models from all providers in the OpenAI API format.
The response includes:
- data: Array of model objects with id, object, created, and owned_by fields
- total: Total number of models
- by_provider: Object with model counts per provider

Returns:
    OpenAI-compatible response dictionary

### `create_chat_completion` — Функция

```python
@router.post('/v1/chat/completions')
```

OpenAI-compatible chat completions endpoint for external tools.

This is intentionally small and routes through the existing backend router,
so OpenCode and other OpenAI-compatible clients can use FastAPI Foundry as
their single local provider.

### `stream_response` — Функция

```python
async def stream_response()
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
