# Manager

**Файл:** `sdk/microsoft_foundry_sdk/manager.py`  
**Тип:** `.py`

---

### `FoundryManager` — Класс

```python
class FoundryManager
```

Manages Microsoft Foundry Local model lifecycle.

Wraps FoundryLocalManager singleton. Provides model catalog access,
load/unload, and status inspection.

Example:
    >>> mgr = FoundryManager(app_name="my_app")
    >>> mgr.initialize()
    >>> models = mgr.list_models()
    >>> mgr.load_model("phi-4")
    >>> mgr.unload_model("phi-4")

### `__init__` — Функция

```python
def __init__(self, app_name: str='fastapi_foundry') -> None
```

### `initialize` — Функция

```python
def initialize(self) -> bool
```

Initialize Foundry Local manager.

Returns:
    bool: True if initialized successfully.

### `list_models` — Функция

```python
def list_models(self) -> List[Dict[str, Any]]
```

List all models available in the local catalog.

Returns:
    List of model info dicts with keys: alias, id, size, quantization.

### `load_model` — Функция

```python
def load_model(self, model_alias: str) -> bool
```

Download (if needed) and load a model into memory.

Args:
    model_alias: Model alias, e.g. 'phi-4' or 'qwen2.5-0.5b'.

Returns:
    bool: True if loaded successfully.

### `unload_model` — Функция

```python
def unload_model(self, model_alias: str) -> bool
```

Unload a model from memory.

Args:
    model_alias: Model alias to unload.

Returns:
    bool: True if unloaded successfully.

### `get_model_status` — Функция

```python
def get_model_status(self, model_alias: str) -> Dict[str, Any]
```

Get current status of a model.

Args:
    model_alias: Model alias.

Returns:
    dict with keys: alias, loaded, endpoint_url.

### `get_chat_client` — Функция

```python
def get_chat_client(self, model_alias: str) -> Optional[Any]
```

Get OpenAI-compatible chat client for a loaded model.

Args:
    model_alias: Model alias (must be loaded first).

Returns:
    OpenAI-compatible client or None on failure.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
