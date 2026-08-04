# Logging Config

**Файл:** `src/utils/logging_config.py`  
**Тип:** `.py`

---

### `setup_logging` — Функция

```python
def setup_logging(log_level: str='INFO') -> None
```

Apply log level to the root logger and suppress noisy libraries.

Args:
    log_level (str): Logging level name (DEBUG, INFO, WARNING, ERROR).

Example:
    >>> setup_logging('DEBUG')


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
