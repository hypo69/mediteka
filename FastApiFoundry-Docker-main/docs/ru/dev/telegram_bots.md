# Telegram Боты — Архитектура и разработка

## Структура модуля

```
telegram/
├── __init__.py        # start_all_bots() — asyncio.gather всех ботов
├── admin_bot.py       # class AdminBot
├── helpdesk_bot.py    # class HelpdeskBot + вспомогательные функции
└── listener_bot.py    # class ListenerBot — пассивный слушатель
```

Модуль живёт в корне проекта и импортирует `config_manager.config` напрямую (не через `src.core.config`), что позволяет запускать его автономно без FastAPI.

---

## AdminBot

**Файл:** `telegram/admin_bot.py`  
**Класс:** `AdminBot`  
**Токен:** `TELEGRAM_ADMIN_TOKEN` из `.env`  
**Доступ:** `TELEGRAM_ADMIN_IDS` (env) или `telegram.allowed_external_ids` (config.json)

### Метод `start()`

```python
async def start(self) -> None
```

Запускает `infinity_polling` и фоновую задачу `_monitor_foundry()`.  
Если `TELEGRAM_ADMIN_TOKEN` не задан — выходит без ошибки.

### Метод `broadcast(text)`

```python
async def broadcast(self, text: str) -> None
```

Отправляет Markdown-сообщение всем ID из `telegram_admin_ids`.  
Используется фоновым монитором для алертов.

### Фоновый монитор `_monitor_foundry()`

Запускается как `asyncio.create_task`. Каждые `telegram_status_check_interval` секунд:

1. Проверяет `psutil.disk_usage` — алерт при > 95%
2. Вызывает `CommandAgent.parse_foundry_status()` — алерт при смене статуса на критический

### Регистрация хендлеров `_register_handlers()`

Все хендлеры регистрируются в одном методе после создания `AsyncTeleBot`.  
Callback-хендлер обрабатывает `confirm_restart_*`, `confirm_clear_logs_*`, `rag_profile_*`.

---

## HelpdeskBot

**Файл:** `telegram/helpdesk_bot.py`  
**Класс:** `HelpdeskBot`  
**Токен:** `TELEGRAM_HELPDESK_TOKEN` из `.env`  
**Доступ:** открыт для всех

### Поток обработки сообщения

```
on_message(message)
    │
    ├─ _save(chat_id, username, "user", text)
    │
    ├─ _rag_search(question, profile)
    │     └─ POST /api/v1/rag/search  →  top-5 чанков, берётся первые 3
    │
    ├─ _generate(chat_id, question, context)
    │     ├─ строит messages[] с историей из _history[chat_id]
    │     └─ POST /api/v1/ai/generate  →  ответ модели
    │
    ├─ _save(chat_id, username, "assistant", answer)
    ├─ _update_history(chat_id, question, answer)
    └─ bot.reply_to(message, answer)  # разбивает на чанки по 4000 символов
```

### История диалогов `_history`

Глобальный словарь `dict[int, list[dict]]` в памяти процесса.  
Хранит последние `_MAX_HISTORY_TURNS = 6` ходов (12 сообщений).  
Сбрасывается командой `/new` или перезапуском процесса.

### Персистентность диалогов

Каждое сообщение дописывается в `logs/helpdesk_dialogs.jsonl`:

```json
{"chat_id": 123, "username": "user", "role": "user", "text": "...", "ts": "2025-..."}
{"chat_id": 123, "username": "user", "role": "assistant", "text": "...", "ts": "2025-..."}
```

Файл читается API эндпоинтом `GET /api/v1/helpdesk/dialogs` для веб-интерфейса.

---

## RAG Profile Manager

**Файл:** `src/rag/rag_profile_manager.py`  
**Класс:** `RAGProfileManager`  
**Синглтон:** `rag_profile_manager`

Управляет именованными RAG индексами в `~/.rag/<profile>/`.

### Методы

| Метод | Описание |
|---|---|
| `list_profiles()` | Список всех профилей с флагом `has_index` |
| `get_profile_path(name)` | Путь к профилю или `None` |
| `create_profile(name, description)` | Создать директорию профиля |
| `delete_profile(name)` | Переименовать в `<name>~` (soft delete) |

### Структура профиля

```
~/.rag/
├── support/
│   ├── faiss.index       # FAISS векторный индекс
│   ├── chunks.json       # Текстовые чанки с метаданными
│   ├── meta.json         # Статистика индекса
│   └── description.txt   # Описание профиля (опционально)
├── code/
│   └── ...
└── support~              # Удалённый профиль (soft delete)
```

---

## HelpDesk API Endpoints

**Файл:** `src/api/endpoints/helpdesk.py`  
**Prefix:** `/api/v1/helpdesk`

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/helpdesk/dialogs` | Диалоги сгруппированные по `chat_id` |
| `GET` | `/helpdesk/rag-profiles` | Список RAG профилей |
| `POST` | `/helpdesk/rag-profiles` | Создать профиль `{name, description}` |
| `DELETE` | `/helpdesk/rag-profiles/{name}` | Soft-delete профиля |
| `GET` | `/helpdesk/config` | Статус бота и активный RAG профиль |

---

## Config Manager — Telegram Properties

**Файл:** `config_manager.py`

| Property | Env / Config | Описание |
|---|---|---|
| `telegram_admin_token` | `TELEGRAM_ADMIN_TOKEN` | Токен Admin Bot |
| `telegram_admin_ids` | `TELEGRAM_ADMIN_IDS` | Список ID администраторов |
| `telegram_helpdesk_token` | `TELEGRAM_HELPDESK_TOKEN` | Токен HelpDesk Bot |
| `telegram_helpdesk_rag_profile` | `config.json → telegram_helpdesk.rag_profile` | RAG профиль |
| `telegram_listener_token` | `TELEGRAM_LISTENER_TOKEN` | Токен Listener Bot |
| `telegram_status_check_interval` | `config.json → telegram.status_check_interval` | Интервал мониторинга |

Legacy aliases (`telegram_token`, `telegram_allowed_ids`, `telegram_support_token`) сохранены для обратной совместимости.

---

## Добавление нового бота

1. Создать `telegram/my_bot.py` с классом `MyBot` и методом `async def start()`
2. Добавить токен в `.env` и property в `config_manager.py`
3. Добавить в `telegram/__init__.py`:

```python
from .my_bot import my_bot

async def start_all_bots() -> None:
    await asyncio.gather(
        admin_bot.start(),
        helpdesk_bot.start(),
        listener_bot.start(),
        my_bot.start(),
        return_exceptions=True,
    )
```

Подробнее о Listener Bot: [Telegram Слушатель](telegram_listener.md)
