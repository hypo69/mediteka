# Ollama

**Файл:** `src/api/endpoints/ollama.py`  
**Тип:** `.py`

---

### `ollama_status` — Функция

```python
@router.get('/status')
```

Ollama server status — running, version, URL.

Returns:
    dict: success, running (bool), url, openai_url, version.

### `ollama_list_models` — Функция

```python
@router.get('/models')
```

List locally available Ollama models.

Returns:
    dict: success, models (list of {name, size_gb, modified_at, digest}), count.

### `ollama_pull_model` — Функция

```python
@router.post('/models/pull')
```

Pull (download) a model from Ollama Hub.

Args:
    request: JSON body с полями:
        model (str): Model name, e.g. 'qwen2.5:0.5b' (обязательно).

Returns:
    dict: success, model, status on success; success=False, error on failure.

Raises:
    HTTPException 400: model не передан.

### `ollama_delete_model` — Функция

```python
@router.post('/models/delete')
```

Delete a local Ollama model to free disk space.

Args:
    request: JSON body с полями:
        model (str): Model name, e.g. 'qwen2.5:0.5b' (обязательно).

Returns:
    dict: success, model on success; success=False, error on failure.

Raises:
    HTTPException 400: model не передан.

### `ollama_generate` — Функция

```python
@router.post('/generate')
```

Generate text via Ollama.

Args:
    request: JSON body с полями:
        model (str):       Model name (обязательно).
        prompt (str):      Input text (обязательно).
        max_tokens (int):  Max tokens to generate (default: 512).
        temperature (float): Sampling temperature (default: 0.7).

Returns:
    dict: success, content, model on success; success=False, error on failure.

Raises:
    HTTPException 400: model или prompt не переданы.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
