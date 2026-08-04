# Enhanced Foundry Client

**Файл:** `src/models/enhanced_foundry_client.py`  
**Тип:** `.py`

---

### `EnhancedFoundryClient` — Класс

```python
class EnhancedFoundryClient
```

Расширенный клиент для работы с Foundry API

### `__init__` — Функция

```python
def __init__(self, base_url: str | None=None) -> None
```

### `_find_foundry_url` — Функция

```python
def _find_foundry_url(self) -> str
```

Найти URL Foundry сервиса.

Returns:
    str: Base URL like 'http://127.0.0.1:<port>/v1', or fallback URL.

### `_get_session` — Функция

```python
async def _get_session(self)
```

Получить HTTP сессию.

Returns:
    aiohttp.ClientSession: Active HTTP session.

### `close` — Функция

```python
async def close(self) -> None
```

Закрыть HTTP сессию.

Returns:
    None

### `health_check` — Функция

```python
async def health_check(self) -> Dict
```

Проверка здоровья Foundry.

Returns:
    dict: status (healthy/unhealthy/disconnected), models_count,
          response_time_ms, url, timestamp.

### `list_models` — Функция

```python
async def list_models(self) -> Dict
```

Получить список доступных моделей с детальной информацией.

Returns:
    dict: success, models (list with type/size/capabilities/recommended_settings),
          count, timestamp on success; success=False, error, models=[] on failure.

### `generate_text` — Функция

```python
async def generate_text(self, prompt: str, **kwargs: object) -> Dict
```

Генерация текста с расширенными параметрами.

Args:
    prompt: User input text.
    **kwargs: model (str), temperature (float), max_tokens (int),
              top_p (float), top_k (int), stop (list),
              presence_penalty (float), frequency_penalty (float).

Returns:
    dict: success, content, model, usage, performance, timestamp on success;
          success=False, error on failure.

### `generate_stream` — Функция

```python
async def generate_stream(self, prompt: str, **kwargs: object) -> AsyncGenerator[Dict, None]
```

Стриминговая генерация текста.

Args:
    prompt: User input text.
    **kwargs: model (str), temperature (float), max_tokens (int).

Yields:
    dict: success, content, model, finished on each token chunk;
          success=False, error on failure.

### `load_model` — Функция

```python
async def load_model(self, model_id: str) -> Dict
```

Загрузить модель в память.

Args:
    model_id: Foundry model identifier.

Returns:
    dict: success, message on success; success=False, error on failure.

### `unload_model` — Функция

```python
async def unload_model(self, model_id: str) -> Dict
```

Выгрузить модель из памяти.

Args:
    model_id: Foundry model identifier.

Returns:
    dict: success, message on success; success=False, error on failure.

### `_detect_model_type` — Функция

```python
def _detect_model_type(self, model_id: str) -> str
```

Определить тип модели по ID.

Args:
    model_id: Model identifier string.

Returns:
    str: One of 'reasoning', 'coding', 'general'.

### `_estimate_model_size` — Функция

```python
def _estimate_model_size(self, model_id: str) -> str
```

Оценить размер модели.

Args:
    model_id: Model identifier string.

Returns:
    str: Size label like '7B', '14B', '70B', or 'unknown'.

### `_get_model_capabilities` — Функция

```python
def _get_model_capabilities(self, model_id: str) -> List[str]
```

Получить возможности модели.

Args:
    model_id: Model identifier string.

Returns:
    List[str]: Capability tags, e.g. ['text_generation', 'reasoning', 'multilingual'].

### `_get_recommended_settings` — Функция

```python
def _get_recommended_settings(self, model_id: str) -> Dict
```

Получить рекомендуемые настройки для модели.

Args:
    model_id: Model identifier string.

Returns:
    dict: temperature, top_p, max_tokens tuned for the model type.

### `_select_optimal_model` — Функция

```python
def _select_optimal_model(self) -> str
```

Выбрать оптимальную модель.

Priority: DeepSeek 14B → any Qwen → first available → fallback 'deepseek-r1:14b'.

Returns:
    str: Model ID of the best available model.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
