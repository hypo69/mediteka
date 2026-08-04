# Telegram Support Bot

**Файл:** `src/utils/telegram_support_bot.py`  
**Тип:** `.py`

---

### `_save_message` — Функция

```python
def _save_message(chat_id: int, username: str, role: str, text: str) -> None
```

Append a message to the dialogs log.

Args:
    chat_id (int): Telegram chat id.
    username (str): Telegram username or first name.
    role (str): 'user' or 'assistant'.
    text (str): Message text.

### `_ask_model` — Функция

```python
async def _ask_model(question: str, rag_profile: str) -> str
```

Search RAG profile and generate answer via active model.

Args:
    question (str): User question.
    rag_profile (str): RAG profile name to search.

Returns:
    str: Generated answer text.

### `TelegramSupportBot` — Класс

```python
class TelegramSupportBot
```

Customer-facing support bot powered by RAG + local AI model.

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `start` — Функция

```python
async def start(self) -> None
```

Start polling. Exits silently if support bot is disabled.

### `on_start` — Функция

```python
@self.bot.message_handler(commands=['start', 'help'])
```

### `on_message` — Функция

```python
@self.bot.message_handler(func=lambda m: True, content_types=['text'])
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
