# Lmstudio

**Файл:** `src/api/endpoints/lmstudio.py`  
**Тип:** `.py`

---

### `lmstudio_status` — Функция

```python
@router.get('/status')
```

LM Studio server status.

### `lmstudio_list_models` — Функция

```python
@router.get('/models')
```

List LM Studio models.

### `lmstudio_load_model` — Функция

```python
@router.post('/models/load')
```

Load a model in LM Studio.

### `lmstudio_unload_model` — Функция

```python
@router.post('/models/unload')
```

Unload a loaded LM Studio model instance.

### `lmstudio_download_model` — Функция

```python
@router.post('/models/download')
```

Start an LM Studio model download job.

### `lmstudio_download_status` — Функция

```python
@router.get('/models/download/status/{job_id}')
```

Get LM Studio model download status.

### `lmstudio_generate` — Функция

```python
@router.post('/generate')
```

Generate text through LM Studio /api/v1/chat.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
