# Test Logging System

**Файл:** `tests/unit/test_logging_system.py`  
**Тип:** `.py`

---

### `_formatter` — Функция

```python
def _formatter() -> logging.Formatter
```

### `test_daily_line_handler_writes_warning_and_error_only` — Функция

```python
def test_daily_line_handler_writes_warning_and_error_only(tmp_path)
```

### `test_daily_line_handler_rotates_by_line_count` — Функция

```python
def test_daily_line_handler_rotates_by_line_count(tmp_path)
```

### `test_daily_line_handler_removes_expired_daily_files` — Функция

```python
def test_daily_line_handler_removes_expired_daily_files(tmp_path)
```

### `test_get_log_settings_reads_config_from_current_directory` — Функция

```python
def test_get_log_settings_reads_config_from_current_directory(tmp_path, monkeypatch)
```

### `test_logs_api_lists_and_reads_latest_file` — Функция

```python
@pytest.mark.asyncio
```

### `test_logs_api_lists_install_log_for_logs_tab` — Функция

```python
@pytest.mark.asyncio
```

### `test_logs_health_counts_warnings_and_errors` — Функция

```python
@pytest.mark.asyncio
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
