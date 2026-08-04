# Helpdesk

**Файл:** `src/api/endpoints/helpdesk.py`  
**Тип:** `.py`

---

### `_dialogs_file` — Функция

```python
def _dialogs_file() -> Path
```

Return path to helpdesk JSONL log inside config.dir_dialogs.

### `_load_dialogs` — Функция

```python
def _load_dialogs() -> List[Dict]
```

Load all dialog entries from the JSONL log file.

### `get_dialogs` — Функция

```python
@router.get('/helpdesk/dialogs')
```

Return all helpdesk dialogs grouped by chat_id.

Returns:
    Dict: {success, dialogs: {chat_id: [{role, text, ts, username}]}}

### `get_rag_profiles` — Функция

```python
@router.get('/helpdesk/rag-profiles')
```

Return available RAG profiles.

Returns:
    Dict: {success, profiles: [...]}

### `create_rag_profile` — Функция

```python
@router.post('/helpdesk/rag-profiles')
```

Create a new RAG profile directory.

Args:
    body (Dict): {name, description}

Returns:
    Dict: {success, path}

### `delete_rag_profile` — Функция

```python
@router.delete('/helpdesk/rag-profiles/{name}')
```

Soft-delete a RAG profile (rename with ~ suffix).

Args:
    name (str): Profile name.

Returns:
    Dict: {success}

### `get_helpdesk_config` — Функция

```python
@router.get('/helpdesk/config')
```

Return current helpdesk bot configuration.

Returns:
    Dict: {success, enabled, rag_profile}


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
