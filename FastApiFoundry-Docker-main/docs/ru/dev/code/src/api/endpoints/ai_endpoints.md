# Ai Endpoints

**Файл:** `src/api/endpoints/ai_endpoints.py`  
**Тип:** `.py`

---

### `_save_session_history` — Функция

```python
def _save_session_history(history: list, session_id: str='default', chat_type: str='fastapi') -> None
```

Автоматическое сохранение истории чата в локальный файл.

Args:
    history (list): Список сообщений для сохранения.
    session_id (str): Идентификатор сессии. По умолчанию 'default'.
    chat_type (str): Тип источника чата. По умолчанию 'fastapi'.

### `generate_text` — Функция

```python
@router.post('/ai/generate')
```

Generate text via AI Assistant orchestrator (all backends).

Model prefix determines backend:
foundry:: / hf:: / llama:: / ollama::

### `generate_text_stream` — Функция

```python
@router.post('/ai/generate/stream')
```

Стриминговая генерация текста (Foundry only).

### `chat_completion` — Функция

```python
@router.post('/ai/chat')
```

Chat with message history via AI Assistant orchestrator (all backends).

### `chat_completion_stream` — Функция

```python
@router.post('/ai/chat/stream')
```

Стриминговый чат с автоматическим сохранением истории после завершения.

### `optimize_generation` — Функция

```python
@router.post('/ai/optimize')
```

Оптимизация параметров генерации — не реализовано.

### `generate` — Функция

```python
async def generate()
```

### `event_generator` — Функция

```python
async def event_generator()
```

### `DummyRAGSystem` — Класс

```python
class DummyRAGSystem
```

Заглушка для системы RAG при отсутствии зависимостей.

### `search` — Функция

```python
async def search(self, query, top_k=3)
```

### `reload_index` — Функция

```python
async def reload_index(self, index_dir: str) -> bool
```

### `_profile_index_dir` — Функция

```python
def _profile_index_dir(self, name: str)
```

### `format_context` — Функция

```python
def format_context(self, results: list) -> str
```

### `filter_by_score` — Функция

```python
def filter_by_score(self, results: list, min_score: float) -> list
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
