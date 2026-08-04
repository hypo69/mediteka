# Telegram Слушатель — архитектура и разработка

## Файл

```
telegram/listener_bot.py
```

## Класс `ListenerBot`

```python
class ListenerBot:
    bot: Optional[AsyncTeleBot]

    async def start(self) -> None
    def _register_handlers(self) -> None
```

**Токен:** `TELEGRAM_LISTENER_TOKEN` из `.env` → `config.telegram_listener_token`  
**Доступ:** открыт для всех — бот принимает сообщения от любого пользователя  
**Ответы:** никогда не отправляет

## Поток обработки

```
Telegram → on_any(message)
               │
               └─ _log(message)
                      │
                      └─ ~/.aiassistant/dialogs/listener_log.jsonl
```

Хендлер `on_any` подписан на все типы контента:

```python
content_types=[
    "text", "photo", "document", "voice", "video",
    "sticker", "location", "contact", "audio",
]
```

## Функция `_log(message)`

Записывает одну строку JSONL в лог-файл:

```python
entry = {
    "ts": datetime.now().isoformat(),
    "chat_id": message.chat.id,
    "chat_type": message.chat.type,   # private | group | supergroup | channel
    "user_id": message.from_user.id,
    "username": message.from_user.username or message.from_user.first_name,
    "content_type": message.content_type,
    "text": message.text or "",
}
```

Директория создаётся автоматически через `mkdir(parents=True, exist_ok=True)`.

## Config Manager

Добавлено свойство в `config_manager.py`:

```python
@property
def telegram_listener_token(self) -> str:
    """Token for listener_bot. Env: TELEGRAM_LISTENER_TOKEN."""
    return os.getenv('TELEGRAM_LISTENER_TOKEN', '')
```

## Синглтон

```python
listener_bot = ListenerBot()
```

Импортируется в `telegram/__init__.py` для запуска через `start_all_bots()`.

## Подключение к `telegram/__init__.py`

Добавьте в `telegram/__init__.py`:

```python
from .listener_bot import listener_bot

async def start_all_bots() -> None:
    await asyncio.gather(
        admin_bot.start(),
        helpdesk_bot.start(),
        listener_bot.start(),
        return_exceptions=True,
    )
```

## Структура модуля после добавления

```
telegram/
├── __init__.py        # start_all_bots() — asyncio.gather всех ботов
├── admin_bot.py       # AdminBot — управление системой
├── helpdesk_bot.py    # HelpdeskBot — RAG + AI ответы
└── listener_bot.py    # ListenerBot — пассивный слушатель
```

## Расширение функциональности

Чтобы добавить обработку конкретного типа контента (например, сохранять фото отдельно):

```python
@bot.message_handler(content_types=['photo'])
async def on_photo(message):
    _log(message)
    # дополнительная логика — скачать фото, сохранить в отдельную папку и т.д.
```

!!! warning "Не добавляйте ответы"
    Listener Bot по определению пассивен. Если нужен бот с ответами — используйте `HelpdeskBot` или создайте новый класс.

## Переменные окружения

| Переменная | Env | Описание |
|---|---|---|
| `telegram_listener_token` | `TELEGRAM_LISTENER_TOKEN` | Токен бота |

## Связанные файлы

| Файл | Роль |
|---|---|
| `telegram/listener_bot.py` | Реализация бота |
| `config_manager.py` | `telegram_listener_token` property |
| `.env.example` | Шаблон переменной `TELEGRAM_LISTENER_TOKEN` |
| `~/.aiassistant/dialogs/listener_log.jsonl` | Файл лога (runtime) |
