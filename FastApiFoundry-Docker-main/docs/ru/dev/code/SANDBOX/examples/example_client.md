# Example Client

**Файл:** `SANDBOX/examples/example_client.py`  
**Тип:** `.py`

---

### `FastAPIFoundryClient` — Класс

```python
class FastAPIFoundryClient
```

Клиент для FastAPI Foundry API

### `main` — Функция

```python
async def main()
```

Демонстрация использования клиента

### `__init__` — Функция

```python
def __init__(self, base_url: str='http://localhost:9696', api_key: str=None)
```

### `__aenter__` — Функция

```python
async def __aenter__(self)
```

### `__aexit__` — Функция

```python
async def __aexit__(self, exc_type, exc_val, exc_tb)
```

### `health_check` — Функция

```python
async def health_check(self) -> Dict[str, Any]
```

Проверка здоровья сервиса

### `list_models` — Функция

```python
async def list_models(self) -> Dict[str, Any]
```

Получить список моделей

### `generate_text` — Функция

```python
async def generate_text(self, prompt: str, model: str=None, temperature: float=None, max_tokens: int=None, use_rag: bool=True, system_prompt: str=None) -> Dict[str, Any]
```

Генерация текста

### `batch_generate` — Функция

```python
async def batch_generate(self, prompts: List[str], model: str=None, temperature: float=None, max_tokens: int=None, use_rag: bool=True) -> Dict[str, Any]
```

Пакетная генерация

### `rag_search` — Функция

```python
async def rag_search(self, query: str, top_k: int=5) -> Dict[str, Any]
```

Поиск в RAG

### `get_config` — Функция

```python
async def get_config(self) -> Dict[str, Any]
```

Получить конфигурацию

### `rag_reload` — Функция

```python
async def rag_reload(self) -> Dict[str, Any]
```

Перезагрузить RAG индекс

### `get_connected_models` — Функция

```python
async def get_connected_models(self) -> Dict[str, Any]
```

Получить список подключенных моделей

### `connect_model` — Функция

```python
async def connect_model(self, model_id: str, provider: str='foundry', **kwargs) -> Dict[str, Any]
```

Подключить новую модель

### `get_model_providers` — Функция

```python
async def get_model_providers(self) -> Dict[str, Any]
```

Получить список провайдеров

### `check_models_health` — Функция

```python
async def check_models_health(self) -> Dict[str, Any]
```

Проверить здоровье всех моделей

### `start_tunnel` — Функция

```python
async def start_tunnel(self, tunnel_type: str, port: int=8000, subdomain: str=None) -> Dict[str, Any]
```

Запустить туннель

### `stop_tunnel` — Функция

```python
async def stop_tunnel(self) -> Dict[str, Any]
```

Остановить туннель

### `tunnel_status` — Функция

```python
async def tunnel_status(self) -> Dict[str, Any]
```

Статус туннеля

### `run_example` — Функция

```python
async def run_example(self, example_type: str) -> Dict[str, Any]
```

Запустить пример

### `list_examples` — Функция

```python
async def list_examples(self) -> Dict[str, Any]
```

Получить список примеров


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
