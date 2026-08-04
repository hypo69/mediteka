# Security

**Файл:** `src/api/endpoints/security.py`  
**Тип:** `.py`

---

### `_read_env` — Функция

```python
def _read_env() -> dict[str, str]
```

Read .env file into a key-value dict, skipping comments and blanks.

Returns:
    dict[str, str]: Parsed environment variables.

### `_write_env` — Функция

```python
def _write_env(data: dict[str, str]) -> None
```

Write key-value dict back to .env file.

Args:
    data (dict[str, str]): Variables to persist.

### `_patch_config_api_key` — Функция

```python
def _patch_config_api_key(value: str) -> None
```

Update security.api_key in config.json.

Args:
    value (str): New API key value (empty string to clear).

### `generate_api_key` — Функция

```python
@router.post('/security/api-key/generate')
```

Generate a new cryptographically secure API key for this server.

Generates 32 random bytes encoded as a 64-character hex string.
Writes the key to .env (API_KEY) and config.json (security.api_key).
Sets the key in the current process environment immediately.

Returns:
    dict: ``{"success": True, "api_key": "<new key>"}``

Example:
    >>> POST /api/v1/security/api-key/generate
    {"success": true, "api_key": "a3f1..."}

### `get_api_key_status` — Функция

```python
@router.get('/security/api-key/status')
```

Return whether an API key is currently configured.

Never returns the key value itself — only its presence and a masked preview.

Returns:
    dict: ``{"success": True, "configured": bool, "preview": "abcd...ef12"}``

Example:
    >>> GET /api/v1/security/api-key/status
    {"success": true, "configured": true, "preview": "a3f1...cd89"}

### `delete_api_key` — Функция

```python
@router.delete('/security/api-key')
```

Remove the API key, disabling key-based protection.

Removes API_KEY from .env and clears security.api_key in config.json.
Unsets the key from the current process environment.

Returns:
    dict: ``{"success": True, "message": "API key removed"}``

Example:
    >>> DELETE /api/v1/security/api-key
    {"success": true, "message": "API key removed"}


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
