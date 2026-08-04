# Models

**Файл:** `src/api/models.py`  
**Тип:** `.py`

---

### `create_generate_response` — Функция

```python
def create_generate_response(success: bool, content: str=None, model: str=None, error: str=None) -> dict
```

Create a text generation response.

Args:
    success: Whether generation succeeded.
    content: Generated text content.
    model:   Model ID used for generation.
    error:   Error message if success is False.

Returns:
    dict: success, content, model, error.

### `create_health_response` — Функция

```python
def create_health_response(status: str, foundry_status: str, rag_available: bool) -> dict
```

Create a health check response.

Args:
    status:         Overall API status string.
    foundry_status: Foundry service status string.
    rag_available:  Whether the RAG system is available.

Returns:
    dict: status, foundry_status, rag_available, timestamp (ISO 8601).

### `create_error_response` — Функция

```python
def create_error_response(error: str, detail: str=None) -> dict
```

Create an error response.

Args:
    error:  Short error description.
    detail: Optional extended detail message.

Returns:
    dict: error, detail.

### `create_models_response` — Функция

```python
def create_models_response(success: bool, models: list=None, error: str=None) -> dict
```

Create a models list response.

Args:
    success: Whether the request succeeded.
    models:  List of model dicts.
    error:   Error message if success is False.

Returns:
    dict: success, models (list, empty if None), error.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
