# Models

**Файл:** `src/api/endpoints/models.py`  
**Тип:** `.py`

---

### `_safe_get` — Функция

```python
async def _safe_get(coro) -> dict
```

Execute a coroutine and return its result or empty dict on failure.

### `_collect_foundry` — Функция

```python
async def _collect_foundry() -> list[dict]
```

Get Foundry cached models with foundry:: prefix.

### `_collect_hf` — Функция

```python
async def _collect_hf() -> list[dict]
```

Get HuggingFace downloaded models with hf:: prefix.

### `_collect_llama` — Функция

```python
async def _collect_llama() -> list[dict]
```

Get llama.cpp GGUF models with llama:: prefix.

### `_collect_ollama` — Функция

```python
async def _collect_ollama() -> list[dict]
```

Get Ollama local models with ollama:: prefix.

### `load_model` — Функция

```python
@router.post('/models/{model_id:path}/load')
```

Prepare a model by prefixed model id.

Routes to the correct backend by prefix in the URL path.
For Foundry this performs a warm-up inference request, because Foundry
Local does not expose a reliable HTTP load-into-RAM endpoint.

Args:
    model_id: Provider-prefixed model id, e.g.:
        foundry::qwen3-0.6b-generic-cpu:4
        hf::Qwen/Qwen2.5-0.5B-Instruct
        llama::D:/models/gemma-4-E4B-it-Q4_K_M.gguf
        ollama::qwen2.5:0.5b

Returns:
    dict: success, model_id, provider, status on success; success=False, error on failure.

Examples:
    POST /api/v1/models/foundry::qwen3-0.6b-generic-cpu:4/load
    POST /api/v1/models/hf::Qwen%2FQwen2.5-0.5B-Instruct/load
    POST /api/v1/models/llama::D:%2Fmodels%2Fgemma.gguf/load
    POST /api/v1/models/ollama::qwen2.5:0.5b/load

### `unload_model` — Функция

```python
@router.post('/models/{model_id:path}/unload')
```

Unload a model from memory by prefixed model id.

Args:
    model_id: Provider-prefixed model id in the URL path.

Returns:
    dict: success, model_id, provider on success; success=False, error on failure.

Examples:
    POST /api/v1/models/hf::Qwen%2FQwen2.5-0.5B-Instruct/unload
    POST /api/v1/models/foundry::qwen3-0.6b-generic-cpu:4/unload

### `get_all_models` — Функция

```python
@router.get('/models')
```

Get all local models from all providers with provider prefixes.

Returns a flat list of all models grouped by provider.
Each model id includes the routing prefix (foundry::, hf::, llama::, ollama::).

Returns:
    dict: success, models (list), count, by_provider (dict with counts per provider).

### `get_connected_models` — Функция

```python
@router.get('/models/connected')
```

Get models currently ready/connected across providers.

For Foundry, this reports models available from the running service, not a
guaranteed loaded-in-RAM state.

Returns:
    dict: success, models (list), count.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
