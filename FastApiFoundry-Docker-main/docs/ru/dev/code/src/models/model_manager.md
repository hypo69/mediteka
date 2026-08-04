# Model Manager

**Файл:** `src/models/model_manager.py`  
**Тип:** `.py`

---

### `ModelManager` — Класс

```python
class ModelManager
```

Manager for connected AI models.

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `load_config` — Функция

```python
def load_config(self) -> None
```

Load model configuration from models_config.json.

### `save_config` — Функция

```python
def save_config(self) -> None
```

Persist model configuration to models_config.json.

### `add_default_foundry_model` — Функция

```python
def add_default_foundry_model(self) -> None
```

Add the default Foundry model entry.

### `connect_model` — Функция

```python
async def connect_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]
```

Connect a new model.

Args:
    model_data: Dict with keys: model_id, provider, model_name (opt),
                endpoint_url (opt), api_key (opt), parameters (opt),
                default_temperature (opt), default_max_tokens (opt), enabled (opt).

Returns:
    dict: success, model_id, status on success; success=False, error on failure.

### `disconnect_model` — Функция

```python
async def disconnect_model(self, model_id: str) -> Dict[str, Any]
```

Disconnect a model.

Args:
    model_id: ID of the model to disconnect.

Returns:
    dict: success, model_id on success; success=False, error on failure.

### `update_model` — Функция

```python
async def update_model(self, model_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]
```

Update model settings.

Args:
    model_id: ID of the model to update.
    update_data: Dict with any of: model_name, enabled, default_temperature,
                 default_max_tokens, api_key, parameters.

Returns:
    dict: success, model_id, status on success; success=False, error on failure.

### `test_model_connection` — Функция

```python
async def test_model_connection(self, model_cfg: Dict[str, Any], test_prompt: str='Hello') -> Dict[str, Any]
```

Test connectivity to a model endpoint.

Args:
    model_cfg: Model configuration dict (must contain model_id, provider, endpoint_url).
    test_prompt: Short prompt to send as a connectivity test.

Returns:
    dict: success, model_id, response_text, response_time on success;
          success=False, error, response_time on failure.

### `_test_foundry_model` — Функция

```python
async def _test_foundry_model(self, cfg: Dict[str, Any], prompt: str) -> Dict[str, Any]
```

### `_test_ollama_model` — Функция

```python
async def _test_ollama_model(self, cfg: Dict[str, Any], prompt: str) -> Dict[str, Any]
```

### `_test_openai_model` — Функция

```python
async def _test_openai_model(self, cfg: Dict[str, Any], prompt: str) -> Dict[str, Any]
```

### `_test_anthropic_model` — Функция

```python
async def _test_anthropic_model(self, cfg: Dict[str, Any], prompt: str) -> Dict[str, Any]
```

### `_test_lmstudio_model` — Функция

```python
async def _test_lmstudio_model(self, cfg: Dict[str, Any], prompt: str) -> Dict[str, Any]
```

### `_test_custom_model` — Функция

```python
async def _test_custom_model(self, cfg: Dict[str, Any], prompt: str) -> Dict[str, Any]
```

### `check_all_models_health` — Функция

```python
async def check_all_models_health(self) -> None
```

Check health of all enabled connected models.

### `get_connected_models` — Функция

```python
def get_connected_models(self) -> Dict[str, Any]
```

Return list of connected models with status.

Returns:
    dict: success, models (list), total_count, online_count,
          default_model, timestamp.

### `get_providers` — Функция

```python
def get_providers(self) -> Dict[str, Any]
```

Return list of available providers.

Returns:
    dict: success, providers (list of provider dicts), timestamp.

### `get_model_config` — Функция

```python
def get_model_config(self, model_id: str) -> Optional[Dict[str, Any]]
```

Return configuration for a specific model.

Args:
    model_id: Model identifier.

Returns:
    dict | None: Model config dict, or None if not found.

### `increment_usage` — Функция

```python
def increment_usage(self, model_id: str, response_time: Optional[float]=None) -> None
```

Increment usage counter and update average response time.

Args:
    model_id: Model identifier.
    response_time: Response time in seconds to include in rolling average.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
