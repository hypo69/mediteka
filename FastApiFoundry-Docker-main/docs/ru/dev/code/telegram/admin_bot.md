# Admin Bot

**Файл:** `telegram/admin_bot.py`  
**Тип:** `.py`

---

### `AdminBot` — Класс

```python
class AdminBot
```

Admin bot: system monitoring and Foundry management.

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `_is_allowed` — Функция

```python
def _is_allowed(self, message) -> bool
```

### `broadcast` — Функция

```python
async def broadcast(self, text: str) -> None
```

Send a notification to all allowed admin IDs.

Args:
    text (str): Markdown-formatted message text.

### `_monitor_foundry` — Функция

```python
async def _monitor_foundry(self) -> None
```

Periodically check Foundry status and disk usage; alert on issues.

### `start` — Функция

```python
async def start(self) -> None
```

Start admin bot polling. Exits silently if token is not set.

### `_register_handlers` — Функция

```python
def _register_handlers(self) -> None
```

### `on_callback` — Функция

```python
@bot.callback_query_handler(func=lambda c: c.data.startswith(('confirm_restart_', 'confirm_clear_logs_', 'rag_profile_')))
```

### `on_help` — Функция

```python
@bot.message_handler(commands=['start', 'help'])
```

### `on_status` — Функция

```python
@bot.message_handler(commands=['status'])
```

### `on_stats` — Функция

```python
@bot.message_handler(commands=['stats'])
```

### `on_foundry_start` — Функция

```python
@bot.message_handler(commands=['foundry_start'])
```

### `on_foundry_stop` — Функция

```python
@bot.message_handler(commands=['foundry_stop'])
```

### `on_logs` — Функция

```python
@bot.message_handler(commands=['logs'])
```

### `on_get_logs` — Функция

```python
@bot.message_handler(commands=['get_logs'])
```

### `on_clear_logs` — Функция

```python
@bot.message_handler(commands=['clear_logs'])
```

### `on_restart` — Функция

```python
@bot.message_handler(commands=['restart_server'])
```

### `on_rag_rebuild` — Функция

```python
@bot.message_handler(commands=['rag_rebuild'])
```

### `on_rag_status` — Функция

```python
@bot.message_handler(commands=['rag_status'])
```

### `on_rag_profiles` — Функция

```python
@bot.message_handler(commands=['rag_profiles'])
```

### `on_document` — Функция

```python
@bot.message_handler(content_types=['document'])
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
