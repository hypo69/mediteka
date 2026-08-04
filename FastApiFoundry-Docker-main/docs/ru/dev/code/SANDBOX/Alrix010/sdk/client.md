# Client

**Файл:** `SANDBOX/Alrix010/sdk/client.py`  
**Тип:** `.py`

---

Простой клиент для FastAPI Foundry API

### `FoundryClient` — Класс

```python
class FoundryClient
```

Простой клиент для работы с FastAPI Foundry API

### `__init__` — Функция

```python
def __init__(self, base_url='http://localhost:9696', timeout=30)
```

### `_request` — Функция

```python
def _request(self, method, endpoint, **kwargs)
```

Выполнить HTTP запрос

### `health` — Функция

```python
def health(self)
```

Проверить здоровье системы

### `generate` — Функция

```python
def generate(self, prompt, model=None, max_tokens=None, use_rag=True)
```

Генерировать текст

### `chat` — Функция

```python
def chat(self, message, conversation_id=None, use_rag=True)
```

Отправить сообщение в чат

### `list_models` — Функция

```python
def list_models(self)
```

Получить список моделей

### `rag_search` — Функция

```python
def rag_search(self, query, top_k=5)
```

Поиск в RAG индексе

### `close` — Функция

```python
def close(self)
```

Закрыть сессию

### `__enter__` — Функция

```python
def __enter__(self)
```

### `__exit__` — Функция

```python
def __exit__(self, exc_type, exc_val, exc_tb)
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
