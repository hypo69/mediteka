# Chat Endpoints

**Файл:** `src/api/endpoints/chat_endpoints.py`  
**Тип:** `.py`

---

### `_translate_enabled` — Функция

```python
def _translate_enabled() -> bool
```

### `_chat_should_translate` — Функция

```python
async def _chat_should_translate(request: dict) -> bool
```

Per-request translate_model_dialog overrides global config.

### `_dialogs_dir` — Функция

```python
def _dialogs_dir() -> Path
```

Return resolved dialogs directory path, creating it if needed.

### `_ensure_session_loaded` — Функция

```python
async def _ensure_session_loaded(session_id: str) -> bool
```

Load a persisted chat session into memory if it exists.

### `_persist_chat_message` — Функция

```python
async def _persist_chat_message(session_id: str, role: str, content: str) -> None
```

Best-effort persistence for shared chat context.

### `start_chat_session` — Функция

```python
@router.post('/chat/start')
```

Start a new chat session.

Args:
    request: JSON body with fields:
        model (str): Model ID (default: 'default').

Returns:
    dict: success, session_id (UUID), model, message.

### `send_chat_message` — Функция

```python
@router.post('/chat/message')
```

Send a message to an existing chat session.

Args:
    request: JSON body with fields:
        session_id (str):    Session ID (required).
        message (str):       Message text (required).
        model (str):         Model ID (optional).
        temperature (float): Sampling temperature (default: 0.7).
        max_tokens (int):    Max tokens (default: 2048).
        source_lang (str):   Input language (default: 'auto').
        locale (str):        Reply language override ('ru', 'he', etc.).

Returns:
    dict: success, response, session_id.

Raises:
    HTTPException 400: Invalid session_id or empty message.
    HTTPException 500: Generation error.

### `send_chat_message_stream` — Функция

```python
@router.post('/chat/stream')
```

Send a message with SSE streaming response.

Args:
    request: JSON body with fields:
        session_id (str):    Session ID (required).
        message (str):       Message text (required).
        model (str):         Model ID (optional).
        temperature (float): Sampling temperature (default: 0.7).
        max_tokens (int):    Max tokens (default: 2048).

Returns:
    StreamingResponse: SSE stream with {chunk} events and final {done: True}.

Raises:
    HTTPException 400: Invalid session_id or empty message.

### `get_chat_history` — Функция

```python
@router.get('/chat/history/{session_id}')
```

Get in-memory session history.

Args:
    session_id: Chat session UUID.

Returns:
    dict: success, session_id, history (list of {role, content}).

Raises:
    HTTPException 404: Session not found.

### `delete_chat_session` — Функция

```python
@router.delete('/chat/session/{session_id}')
```

Delete an in-memory chat session.

Args:
    session_id: Chat session UUID.

Returns:
    dict: success, message.

Raises:
    HTTPException 404: Session not found.

### `save_chat_history` — Функция

```python
@router.post('/chat/history/save')
```

Persist chat history to disk.

Saves to config.dir_dialogs (~/.ai-assist/dialogs/ by default).

Args:
    request: JSON body with fields:
        messages (list):  List of {role, content} (required).
        session_id (str): Session UUID (generated if empty).
        model (str):      Model ID (optional).
        title (str):      Dialog title (optional).
        aborted (bool):   Whether chat was aborted (default: False).

Returns:
    dict: success, file (absolute path), session_id.

Raises:
    HTTPException 400: messages missing or empty.

### `list_saved_dialogs` — Функция

```python
@router.get('/chat/history/list')
```

List saved dialog files from disk, newest first.

Args:
    limit (int):  Max number of entries to return (default: 50).
    offset (int): Pagination offset (default: 0).

Returns:
    dict: success, dialogs (list of metadata), total, dir.

### `load_saved_dialog` — Функция

```python
@router.get('/chat/history/file/{filename}')
```

Load a single saved dialog from disk.

Args:
    filename: JSON filename (e.g. 'uuid_1234567890.json').

Returns:
    dict: success + full dialog payload.

Raises:
    HTTPException 400: Unsafe filename.
    HTTPException 404: File not found.

### `cleanup_dialogs` — Функция

```python
@router.post('/chat/history/cleanup')
```

Delete old and oversized dialog files.

Applies retention_days and max_size_mb from config.dialogs.
Can be overridden per-request.

Args:
    request: Optional JSON body with fields:
        retention_days (int): Override retention period.
        max_size_mb (int):    Override size limit.

Returns:
    dict: success, deleted (count), freed_bytes, remaining.

### `get_available_models` — Функция

```python
@router.get('/chat/models')
```

List chat models without probing Foundry.

Returns:
    dict: success, models (list of {id, name, type, size}), count.

### `generate_stream` — Функция

```python
async def generate_stream()
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
