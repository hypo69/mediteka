# Telegram Боты

FastAPI Foundry включает два Telegram бота с разными ролями.

## Архитектура

```
telegram/
├── __init__.py        # start_all_bots() — asyncio.gather обоих ботов
├── admin_bot.py       # class AdminBot
└── helpdesk_bot.py    # class HelpdeskBot + вспомогательные функции
```

```
Клиент → HelpDesk Bot → RAG (профиль "support") → /api/v1/ai/generate → ответ
Админ  → Admin Bot   → Foundry / логи / система
```

Модуль живёт в корне проекта и импортирует `config_manager.config` напрямую (не через `src.core.config`), что позволяет запускать его автономно без FastAPI.

---

## Получение токена через @BotFather

!!! info "Что такое BotFather"
    **@BotFather** — официальный бот Telegram для создания и управления ботами.
    Все токены выдаются только через него.

!!! tip "Шаг 1 — Открыть BotFather"
    Откройте Telegram и найдите бота **[@BotFather](https://t.me/BotFather)**  
    или перейдите по ссылке: `https://t.me/BotFather`

    Нажмите **Start** (или отправьте `/start`).

!!! tip "Шаг 2 — Создать нового бота"
    Отправьте команду:

    ```
    /newbot
    ```

    BotFather спросит **имя бота** (отображаемое, например `My AI Assistant`) —
    это то, что видят пользователи в чате.

!!! tip "Шаг 3 — Задать username"
    Затем BotFather попросит **username** — уникальный идентификатор бота.

    Требования:

    - только латиница, цифры и `_`
    - должен заканчиваться на `bot` (например `my_ai_assistant_bot`)
    - должен быть уникальным во всём Telegram

!!! success "Шаг 4 — Получить токен"
    После успешного создания BotFather пришлёт сообщение вида:

    ```
    Done! Congratulations on your new bot.
    Use this token to access the HTTP API:

    1234567890:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ```

    Это и есть **токен**. Скопируйте его — он понадобится для `.env`.

!!! warning "Безопасность токена"
    - Никому не передавайте токен — он даёт полный контроль над ботом
    - Не коммитьте `.env` в git
    - Если токен скомпрометирован — отзовите его командой `/revoke` у @BotFather

!!! note "Полезные команды @BotFather"
    | Команда | Описание |
    |---|---|
    | `/mybots` | Список всех ваших ботов |
    | `/token` | Показать токен существующего бота |
    | `/revoke` | Отозвать и перевыпустить токен |
    | `/setdescription` | Описание бота (видно при старте) |
    | `/setuserpic` | Аватар бота |
    | `/deletebot` | Удалить бота |

!!! example "Шаг 5 — Узнать свой Telegram ID (для Admin Bot)"
    Admin Bot ограничен списком `TELEGRAM_ADMIN_IDS`. Чтобы узнать свой ID:

    1. Найдите бота **[@userinfobot](https://t.me/userinfobot)** или **[@getmyid_bot](https://t.me/getmyid_bot)**
    2. Отправьте `/start`
    3. Бот ответит вашим числовым ID, например `123456789`

    Этот ID вставьте в `.env`:

    ```env
    TELEGRAM_ADMIN_IDS=123456789
    ```

---

## Admin Bot

Бот для администратора системы. Мониторинг, управление Foundry, работа с логами и RAG.

**Доступ:** ограничен списком `TELEGRAM_ADMIN_IDS`.

### Настройка

В `.env`:

```env
TELEGRAM_ADMIN_TOKEN=токен_от_BotFather
TELEGRAM_ADMIN_IDS=123456789,987654321
```

### Команды

| Команда | Описание |
|---|---|
| `/status` | Статус Foundry: состояние, порт, PID |
| `/stats` | График CPU / RAM / Disk (PNG через matplotlib) |
| `/foundry_start` | Запустить Foundry сервис |
| `/foundry_stop` | Остановить Foundry сервис |
| `/logs` | Последние 5 ошибок из лога |
| `/get_logs` | Скачать полный файл лога |
| `/clear_logs` | Очистить лог (с подтверждением Да/Нет) |
| `/restart_server` | Перезапустить FastAPI сервер (с подтверждением) |
| `/rag_rebuild` | Инициировать переиндексацию RAG |
| `/rag_status` | Информация об активном RAG индексе (meta.json) |
| `/rag_profiles` | Список RAG профилей с inline-кнопками выбора |

### Фоновый мониторинг

Бот автоматически проверяет каждые `status_check_interval` секунд (по умолчанию 300):

- **Foundry статус** — при изменении на `failed` / `stopped` / `unknown` отправляет алерт
- **Диск** — при заполнении > 95% отправляет алерт (один раз до нормализации)

Мониторинг реализован через `CommandAgent.parse_foundry_status()`.

### Загрузка ZIP-архивов

Отправьте боту `.zip` файл — он распакует его в `data/uploads/<имя_архива>/`.  
После этого запустите `/rag_rebuild` для индексации.

---

## HelpDesk Bot

Бот для клиентов. Отвечает на вопросы о системе, используя RAG + активную AI модель.

**Доступ:** открыт для всех пользователей Telegram.

### Настройка

В `.env`:

```env
TELEGRAM_HELPDESK_TOKEN=токен_от_BotFather
```

В `config.json`:

```json
{
  "telegram_helpdesk": {
    "rag_profile": "support"
  }
}
```

### Команды

| Команда | Описание |
|---|---|
| `/start` | Приветствие и инструкция |
| `/help` | То же что `/start` |
| `/new` | Сбросить историю диалога |

### Логика ответа

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

## Подготовка RAG профиля для HelpDesk

Создайте профиль `support` и проиндексируйте документацию:

```bash
# Через API
POST /api/v1/helpdesk/rag-profiles
{"name": "support", "description": "Project documentation"}

POST /api/v1/rag/build
{"docs_dir": "./docs"}
```

Или через веб-интерфейс: таб **Support** → раздел **RAG Profiles** → **Create Profile**.

---

## Запуск

### Вместе с FastAPI сервером

Боты запускаются автоматически из `run.py` при наличии токенов:

```python
from telegram import start_all_bots
asyncio.create_task(start_all_bots())
```

### Автономно

```powershell
~venv\Scripts\python.exe -m telegram
```

---

## Диалоги в веб-интерфейсе

Таб **Support** в веб-интерфейсе показывает:

- Список пользователей, написавших в HelpDesk бот
- Историю переписки по каждому пользователю
- Статус бота (активен / отключён)
- Управление RAG профилями

---

## Переменные окружения

| Переменная | Описание |
|---|---|
| `TELEGRAM_ADMIN_TOKEN` | Токен Admin Bot (от @BotFather) |
| `TELEGRAM_ADMIN_IDS` | ID администраторов через запятую |
| `TELEGRAM_HELPDESK_TOKEN` | Токен HelpDesk Bot (от @BotFather) |

## Параметры config.json

| Параметр | По умолчанию | Описание |
|---|---|---|
| `telegram.status_check_interval` | `300` | Интервал мониторинга Foundry (сек) |
| `telegram_helpdesk.rag_profile` | `"support"` | RAG профиль для HelpDesk бота |
