# Logging System

**Файл:** `src/utils/logging_system.py`  
**Тип:** `.py`

---

### `StructuredLogger` — Класс

```python
class StructuredLogger
```

Facade that adds structured JSON side-channel to a stdlib logger.

Args:
    name (str): Logger name.

Example:
    >>> log = StructuredLogger('my-module')
    >>> log.info("Request handled", status=200, duration=0.12)

### `get_logger` — Функция

```python
def get_logger(name: str) -> StructuredLogger
```

Return a StructuredLogger for the given name.

Args:
    name (str): Logger name.

Returns:
    StructuredLogger: Configured structured logger.

Example:
    >>> log = get_logger('rag-system')
    >>> log.info("Index loaded", chunks=512)

### `__init__` — Функция

```python
def __init__(self, name: str) -> None
```

### `_emit` — Функция

```python
def _emit(self, level: int, message: str, **kwargs) -> None
```

### `debug` — Функция

```python
def debug(self, message: str, **kwargs) -> None
```

### `info` — Функция

```python
def info(self, message: str, **kwargs) -> None
```

### `warning` — Функция

```python
def warning(self, message: str, **kwargs) -> None
```

### `error` — Функция

```python
def error(self, message: str, exc_info=None, **kwargs) -> None
```

### `critical` — Функция

```python
def critical(self, message: str, **kwargs) -> None
```

### `exception` — Функция

```python
def exception(self, message: str, **kwargs) -> None
```

### `timer` — Функция

```python
@contextmanager
```

Context manager that logs operation duration.

Args:
    operation (str): Human-readable operation name.

Example:
    >>> with log.timer('rag-search'):
    ...     results = rag.search(query)

### `log_api_request` — Функция

```python
def log_api_request(self, method: str, path: str, status_code: int, duration: float, **kwargs) -> None
```

Log an HTTP API request.

Args:
    method (str): HTTP method.
    path (str): Request path.
    status_code (int): Response status code.
    duration (float): Processing time in seconds.

### `log_model_operation` — Функция

```python
def log_model_operation(self, model_id: str, operation: str, status: str, duration: Optional[float]=None, **kwargs) -> None
```

Log a model lifecycle operation.

Args:
    model_id (str): Model identifier.
    operation (str): Operation name (load, unload, generate).
    status (str): 'success' or 'error'.
    duration (float, optional): Duration in seconds.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
