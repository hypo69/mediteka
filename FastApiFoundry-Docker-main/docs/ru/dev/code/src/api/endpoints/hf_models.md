# Hf Models

**Файл:** `src/api/endpoints/hf_models.py`  
**Тип:** `.py`

---

### `list_hub_models` — Функция

```python
@router.get('/hub/models')
```

Список моделей пользователя с HuggingFace Hub.

Использует HF_TOKEN из .env.
Возвращает модели пользователя + популярные открытые text-generation модели.

Returns:
    dict: success, username, user_models (list), public_models (list);
          success=False, error, user_models=[], public_models if no token.

### `_get_popular_public_models` — Функция

```python
def _get_popular_public_models() -> list
```

Список популярных публичных text-generation моделей.

Разделён на две группы:
- Без лицензии: Phi, Qwen, TinyLlama, DeepSeek — скачиваются сразу
- С лицензией: Gemma, Llama, Mistral — нужно принять на huggingface.co

Returns:
    list: [{"id": str, "size": str, "note": str}]

### `list_hf_models` — Функция

```python
@router.get('/models')
```

Список скачанных и загруженных HF моделей.

Returns:
    dict: success, downloaded (list), loaded (list).

### `download_hf_model` — Функция

```python
@router.post('/models/download')
```

Download model from HuggingFace Hub (blocking, no progress).

Args:
    request: {model_id (str), token (str, optional)}

Returns:
    dict: success, model_id, path on success; success=False, error on failure.

Raises:
    HTTPException 400: model_id not provided.

### `download_hf_model_stream` — Функция

```python
@router.get('/models/download/stream')
```

Download HuggingFace model with SSE progress stream.

Streams file-by-file progress events as Server-Sent Events.
Each event is a JSON object with fields:
    type: 'file_start' | 'file_done' | 'done' | 'error'
    filename, file_index, total_files (for file events)
    path (for 'done'), error (for 'error')

Args:
    model_id: HuggingFace model ID, e.g. 'Qwen/Qwen2.5-0.5B-Instruct'.
    token:    Optional HF token (overrides HF_TOKEN env var).

Returns:
    StreamingResponse: text/event-stream

### `load_hf_model` — Функция

```python
@router.post('/models/load')
```

Загрузить скачанную модель в память для inference.

Args:
    request: JSON body с полями:
        model_id (str): HuggingFace model ID (обязательно).
        device (str):   'auto', 'cpu', 'cuda' (default: 'auto').

Returns:
    dict: success, model_id, device on success; success=False, error on failure.

Raises:
    HTTPException 400: model_id не передан.

### `unload_hf_model` — Функция

```python
@router.post('/models/unload')
```

Выгрузить модель из памяти (освободить RAM/VRAM).

Args:
    request: JSON body с полями:
        model_id (str): HuggingFace model ID (обязательно).

Returns:
    dict: success, model_id on success; success=False, error on failure.

Raises:
    HTTPException 400: model_id не передан.

### `hf_generate` — Функция

```python
@router.post('/generate')
```

Генерация текста через локальную HF модель.

Args:
    request: JSON body с полями:
        model_id (str):       ID модели (должна быть загружена или скачана).
        prompt (str):         Входной текст.
        max_new_tokens (int): Максимум новых токенов (default: 512).
        temperature (float):  Температура (default: 0.7).

Returns:
    dict: success, content, model on success; success=False, error on failure.

Raises:
    HTTPException 400: model_id или prompt не переданы.

### `hf_status` — Функция

```python
@router.get('/status')
```

Статус HuggingFace интеграции — доступность библиотек.

Returns:
    dict: success, transformers ({available, version}),
          huggingface_hub ({available, version}),
          torch ({available, version, cuda}),
          hf_token_set (bool), models_dir (str), install_cmd (str).

### `_run_download` — Функция

```python
def _run_download() -> None
```

### `_event_stream` — Функция

```python
async def _event_stream()
```

### `_cb` — Функция

```python
def _cb(event: dict) -> None
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
