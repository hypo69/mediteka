# Logs

**Файл:** `src/api/endpoints/logs.py`  
**Тип:** `.py`

---

### `LogSettingsRequest` — Класс

```python
class LogSettingsRequest(BaseModel)
```

### `_log_dir` — Функция

```python
def _log_dir() -> Path
```

### `_resolve_file` — Функция

```python
def _resolve_file(filename: str) -> Path
```

Return validated path inside the configured log directory or raise 404.

### `_list_files` — Функция

```python
def _list_files() -> list[Path]
```

### `list_log_files` — Функция

```python
@router.get('/logs/files')
```

Return available log files with size info.

### `get_logs_settings` — Функция

```python
@router.get('/logs/settings')
```

Return log storage and retention settings.

### `get_logs_health` — Функция

```python
@router.get('/logs/health')
```

Return simple warning/error metrics for the settings page.

### `save_logs_settings` — Функция

```python
@router.post('/logs/settings')
```

Persist log viewer retention settings to config.json and apply them.

### `get_logs` — Функция

```python
@router.get('/logs')
```

Return filtered log lines from the requested file.

### `clear_log` — Функция

```python
@router.post('/logs/clear')
```

Truncate a log file.

### `download_log` — Функция

```python
@router.get('/logs/download')
```

Download a log file.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
