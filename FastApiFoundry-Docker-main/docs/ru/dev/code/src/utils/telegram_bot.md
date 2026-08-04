# Telegram Bot

**Файл:** `src/utils/telegram_bot.py`  
**Тип:** `.py`

---

### `SystemBot` — Класс

```python
class SystemBot
```

Класс для реализации Telegram бота мониторинга системы.

### `__init__` — Функция

```python
def __init__(self) -> None
```

Инициализация бота с использованием токена из конфигурации.

### `_log_telegram_interaction` — Функция

```python
def _log_telegram_interaction(self, chat_id: int, role: str, content: str) -> None
```

Log telegram interaction to session history file if enabled.

### `_is_allowed` — Функция

```python
def _is_allowed(self, message) -> bool
```

Проверка прав доступа пользователя.

### `send_message` — Функция

```python
async def send_message(self, text: str) -> None
```

Отправка уведомления всем разрешенным администраторам.

Args:
    text (str): Текст уведомления (поддерживает Markdown).

### `_monitor_foundry_status` — Функция

```python
async def _monitor_foundry_status(self) -> None
```

Фоновая задача для периодической проверки состояния Foundry.

Обоснование:
  - Обеспечение автоматического оповещения при падении сервиса.
  - Минимизация времени простоя без ручного мониторинга.

### `start` — Функция

```python
async def start(self) -> None
```

Запуск процесса прослушивания сообщений (Polling).

### `handle_callbacks` — Функция

```python
@self.bot.callback_query_handler(func=lambda call: call.data.startswith(('confirm_restart_', 'rag_profile_', 'confirm_clear_logs_')))
```

Унифицированная обработка callback-запросов (перезагрузка, логи, RAG).

### `send_welcome` — Функция

```python
@self.bot.message_handler(commands=['start', 'help'])
```

### `get_status` — Функция

```python
@self.bot.message_handler(commands=['status'])
```

### `get_stats` — Функция

```python
@self.bot.message_handler(commands=['stats'])
```

### `start_foundry` — Функция

```python
@self.bot.message_handler(commands=['foundry_start'])
```

### `rag_rebuild` — Функция

```python
@self.bot.message_handler(commands=['rag_rebuild'])
```

### `get_rag_status` — Функция

```python
@self.bot.message_handler(commands=['rag_status'])
```

### `list_rag_profiles` — Функция

```python
@self.bot.message_handler(commands=['rag_profiles'])
```

### `handle_docs` — Функция

```python
@self.bot.message_handler(content_types=['document'])
```

Обработка загрузки ZIP-архивов для RAG.

### `clear_logs_request` — Функция

```python
@self.bot.message_handler(commands=['clear_logs'])
```

Запрос подтверждения очистки логов.

### `clear_chat_history` — Функция

```python
@self.bot.message_handler(commands=['clear_chat_history'])
```

### `clear_chat_history` — Функция

```python
@self.bot.message_handler(commands=['clear_chat_history'])
```

### `restart_server_request` — Функция

```python
@self.bot.message_handler(commands=['restart_server'])
```

### `get_logs` — Функция

```python
@self.bot.message_handler(commands=['logs'])
```

### `get_log_file` — Функция

```python
@self.bot.message_handler(commands=['get_logs'])
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
