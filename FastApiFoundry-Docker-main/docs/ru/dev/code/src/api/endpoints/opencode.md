# Opencode

**Файл:** `src/api/endpoints/opencode.py`  
**Тип:** `.py`

---

OpenCode 1.15.3 integration API.

### `OpenCodeMessageRequest` — Класс

```python
class OpenCodeMessageRequest(BaseModel)
```

### `OpenCodeConfigPatch` — Класс

```python
class OpenCodeConfigPatch(BaseModel)
```

### `opencode_status` — Функция

```python
@router.get('/status')
```

Return configured settings and OpenCode server health/version.

### `opencode_start` — Функция

```python
@router.post('/start')
```

Start `opencode serve` using saved settings.

### `opencode_stop` — Функция

```python
@router.post('/stop')
```

Stop an OpenCode server process started by this API.

### `opencode_config` — Функция

```python
@router.get('/config')
```

Proxy OpenCode `GET /config`.

### `opencode_generated_config` — Функция

```python
@router.get('/generated-config')
```

Return the project-local OpenCode config generated from config.json.

### `opencode_patch_config` — Функция

```python
@router.patch('/config')
```

Proxy OpenCode `PATCH /config`.

### `opencode_providers` — Функция

```python
@router.get('/providers')
```

Proxy OpenCode provider list.

### `opencode_sessions` — Функция

```python
@router.get('/sessions')
```

Proxy OpenCode session list.

### `opencode_create_session` — Функция

```python
@router.post('/sessions')
```

Create an OpenCode session.

### `opencode_messages` — Функция

```python
@router.get('/sessions/{session_id}/messages')
```

List messages for an OpenCode session.

### `opencode_message` — Функция

```python
@router.post('/message')
```

Send a prompt to OpenCode and wait for the response.

### `opencode_openapi_url` — Функция

```python
@router.get('/openapi-url')
```

Return the OpenCode OpenAPI documentation URL.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
