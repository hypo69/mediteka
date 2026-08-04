# Health

**Файл:** `src/api/endpoints/health.py`  
**Тип:** `.py`

---

### `_check_rag_status` — Функция

```python
def _check_rag_status() -> str
```

Check RAG index availability.

### `_check_foundry_status` — Функция

```python
async def _check_foundry_status() -> dict
```

Check Foundry service: status + active_model.

Returns:
    dict: status ('running'|'stopped'|'not_checked'), active_model.

### `_check_llama_status_health` — Функция

```python
async def _check_llama_status_health() -> dict
```

Check llama.cpp server: status + active_model.

Returns:
    dict: status ('running'|'loading'|'stopped'), active_model.

### `_check_hf_status` — Функция

```python
def _check_hf_status() -> dict
```

Check HuggingFace: libraries, token, downloaded/loaded models + active_model.

Returns:
    dict: status, active_model, transformers, torch, token_set,
          models_downloaded, models_loaded, models_dir.

### `_check_ollama_status` — Функция

```python
async def _check_ollama_status() -> dict
```

Check Ollama service: status + active_model.

Returns:
    dict: status ('running'|'stopped'), active_model.

### `_check_docs_status` — Функция

```python
async def _check_docs_status() -> str
```

Check MkDocs documentation server availability.

### `restart_service` — Функция

```python
@router.post('/restart/{service}')
```

Restart a background service.

Args:
    service: One of 'foundry', 'llama', 'docs', 'rag'.

Returns:
    dict: success, message.

### `health_check` — Функция

```python
@router.get('/health')
```

Проверка здоровья сервиса.

All provider blocks share the shape: {status, active_model, ...}

Returns:
    dict: status, foundry_status, llama_status, hf_status, ollama_status,
          docs_status, rag_status, timestamp.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
