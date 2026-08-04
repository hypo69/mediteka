# Foundry Models

**Файл:** `src/api/endpoints/foundry_models.py`  
**Тип:** `.py`

---

### `_get_foundry_base_url` — Функция

```python
def _get_foundry_base_url() -> str
```

Return Foundry service base URL from environment or config.

### `auto_load_default_model` — Функция

```python
@router.post('/auto-load-default')
```

Warm up the default model from config.json.

For Foundry, "load" means a tiny inference request that makes the model
ready for normal requests. Foundry Local does not expose a reliable HTTP
load-into-RAM endpoint.

Returns:
    dict: success, model_id, message on success; success=False on failure.

### `list_models_root` — Функция

```python
@router.get('')
```

Alias for /available.

### `list_catalog_models` — Функция

```python
@router.get('/catalog')
```

List the full Foundry model catalog via CLI (foundry model list).

This is the catalog of ALL models available for download from Foundry,
not just the ones already cached or loaded.
Uses CLI because Foundry has no HTTP API for the catalog.

Returns:
    dict: success, models (list with id, alias, device, task, size, license, cached),
          count, source.

### `list_available_models` — Функция

```python
@router.get('/available')
```

List models reported by the running Foundry service.

Uses Foundry HTTP API (GET /v1/models).
Falls back to hardcoded AVAILABLE_MODELS when Foundry is unreachable.

NOTE: Foundry Local does not expose a reliable separate "loaded in RAM"
list here. Treat these as available/registered models.

Returns:
    dict: success, models, count, source ('foundry-api' or 'hardcoded').

### `list_cached_models` — Функция

```python
@router.get('/cached')
```

List models downloaded to the local Foundry cache on disk.

Foundry has no HTTP API for listing cached (not-yet-loaded) models,
so this endpoint scans the filesystem directly.

Cache structure: <cache_dir>/Microsoft/<model-dir>/v<version>/

Returns:
    dict: success, models (list of model_id strings), items (full model dicts),
          count, cache_dir.

### `list_loaded_models` — Функция

```python
@router.get('/loaded')
```

Compatibility alias for models reported by Foundry.

Foundry Local does not reliably separate available from loaded in this API.

Returns:
    dict: success, models (list of {id, name, status}), count.

### `download_model` — Функция

```python
@router.post('/download')
```

Download a model to the Foundry cache via CLI.

Foundry has no HTTP API for downloading models — CLI is the only option.
Launches download in background and returns PID immediately.

Args:
    request: {"model_id": "qwen3-0.6b-generic-cpu:4"}

Returns:
    dict: success, model_id, status ('downloading'/'already_cached'), pid.

### `get_download_status` — Функция

```python
@router.get('/download/status/{pid}')
```

Check status of a background download process.

Args:
    pid: PID returned by /download.

Returns:
    dict: success, pid, model_id, status ('downloading'/'done'/'error').

### `load_model` — Функция

```python
@router.post('/load')
```

Warm up a model in Foundry.

The client sends a short chat completion request. This is intentionally
simpler and more reliable than trying to track an internal loaded state.

Args:
    request: {"model_id": "qwen3-0.6b-generic-cpu:4"}

Returns:
    dict: success, model_id, message on success; success=False, error on failure.

### `unload_model` — Функция

```python
@router.post('/unload')
```

Best-effort unload of a Foundry model.

Args:
    request: {"model_id": "qwen3-0.6b-generic-cpu:4"}

Returns:
    dict: success, model_id, message on success; success=False, error on failure.

### `get_model_status` — Функция

```python
@router.get('/status/{model_id:path}')
```

Get model status: available in service and/or cached on disk.

Args:
    model_id: Model identifier (path parameter).

Returns:
    dict: success, model_id, available (bool), cached (bool), status.

### `foundry_completions` — Функция

```python
@router.post('/completions')
```

Text completion через Foundry /v1/completions.

Args:
    request: {"prompt": str, "model": str (optional),
              "temperature": float, "max_tokens": int, ...}

Returns:
    dict: OpenAI-совместимый ответ или success=False.

### `foundry_embeddings` — Функция

```python
@router.post('/embeddings')
```

Эмбеддинги через Foundry /v1/embeddings.

Args:
    request: {"input": str | list[str], "model": str (optional)}

Returns:
    dict: success, data (list of embedding vectors), usage.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
