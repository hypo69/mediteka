# Listener Bot

**Файл:** `telegram/listener_bot.py`  
**Тип:** `.py`

---

### `_log` — Функция

```python
def _log(message) -> None
```

Append incoming message to JSONL log file.

Args:
    message: Telebot Message object.

### `ListenerBot` — Класс

```python
class ListenerBot
```

Passive Telegram bot — listens and logs, never replies.

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `start` — Функция

```python
async def start(self) -> None
```

Start polling. Exits silently if TELEGRAM_LISTENER_TOKEN is not set.

### `_register_handlers` — Функция

```python
def _register_handlers(self) -> None
```

### `on_any` — Функция

```python
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'document', 'voice', 'video', 'sticker', 'location', 'contact', 'audio'])
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
