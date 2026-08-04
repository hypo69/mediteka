# Helpdesk Bot

**Файл:** `telegram/helpdesk_bot.py`  
**Тип:** `.py`

---

### `_save` — Функция

```python
def _save(chat_id: int, username: str, role: str, text: str) -> None
```

Append one message to the JSONL dialog log.

Args:
    chat_id (int): Telegram chat id.
    username (str): Display name of the user.
    role (str): 'user' or 'assistant'.
    text (str): Message content.

### `_rag_search` — Функция

```python
async def _rag_search(query: str, profile: str) -> str
```

Search the RAG profile and return concatenated top-3 chunks.

Args:
    query (str): User question.
    profile (str): RAG profile name (subdirectory under ~/.rag/).

Returns:
    str: Concatenated context text, or empty string on failure.

### `_generate` — Функция

```python
async def _generate(chat_id: int, question: str, context: str) -> str
```

Generate an answer using the active AI model.

Builds a system prompt with documentation context and sends the
conversation history for multi-turn support.

Args:
    chat_id (int): Used to retrieve per-user history.
    question (str): Current user question.
    context (str): RAG context text (may be empty).

Returns:
    str: Model answer or error message.

### `_update_history` — Функция

```python
def _update_history(chat_id: int, question: str, answer: str) -> None
```

Add the latest turn to in-memory history, capped at _MAX_HISTORY_TURNS.

Args:
    chat_id (int): Telegram chat id.
    question (str): User message.
    answer (str): Assistant reply.

### `HelpdeskBot` — Класс

```python
class HelpdeskBot
```

Customer-facing helpdesk bot powered by RAG + local AI model.

### `_split` — Функция

```python
def _split(text: str, limit: int) -> list[str]
```

Split text into chunks no longer than limit characters.

Args:
    text (str): Source text.
    limit (int): Maximum chunk length.

Returns:
    list[str]: List of chunks.

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `start` — Функция

```python
async def start(self) -> None
```

Start polling. Exits silently if TELEGRAM_HELPDESK_TOKEN is not set.

### `_register_handlers` — Функция

```python
def _register_handlers(self) -> None
```

### `on_start` — Функция

```python
@bot.message_handler(commands=['start', 'help'])
```

### `on_new` — Функция

```python
@bot.message_handler(commands=['new'])
```

### `on_message` — Функция

```python
@bot.message_handler(func=lambda m: True, content_types=['text'])
```

### `on_unsupported` — Функция

```python
@bot.message_handler(content_types=['photo', 'document', 'voice', 'video'])
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
