# Архитектура проекта gemini-simplechat

## Точка входа

`main.py` — FastAPI-сервер + запуск Telegram-бота.

### Что делает main.py
- Читает конфиг FastAPI из `src/fastapi/config.json` через `j_loads_ns` → `_cfg`
- Читает API-ключ из `.env` → `os.getenv('GEMINI_API_KEY')`
- Читает системную инструкцию из `instructions/system_instruction.md`
- Создаёт глобальный экземпляр `GoogleGenerativeAI` → `model`
- Загружает плагины через `load_plugins(model)` → `plugins`
- Подключает роутеры: `init_chat_router(model, plugins)` и `init_qbt_router(_cfg.qbittorrent)`
- Маршруты: `GET /` → отдаёт `html/index.html`, `POST /api/chat` → чат, `GET|POST /api/torrents` → торренты
- При запуске как `__main__`: стартует Telegram-бот (если установлен) + uvicorn на `_cfg.port`

---

## Конфигурация

### `.env` (корень проекта)
```
GEMINI_API_KEY=...        # ключ Gemini API
TELEGRAM_BOT_TOKEN=...    # токен Telegram-бота
TMDB_API_KEY=...          # ключ TMDB (для media_organizer)
```

### `src/fastapi/config.json`
```json
{
  "host": "127.0.0.1",
  "port": 3000,
  "index_path": "html/index.html",
  "qbittorrent": {
    "host": "127.0.0.1",
    "port": 8080,
    "username": "admin",
    "password": "adminadmin"
  }
}
```
Читается в `main.py` как `_cfg`. Используется для host, port, пути к index.html и настроек qBittorrent.
⚠️ Старая папка `fastapi/` удалена — она перекрывала установленный пакет `fastapi`.

### `src/ai/gemini/config.json`
```json
{
  "model": "gemini-...",
  "model_choices": [...],
  "model_descriptions": {...},
  "response_mime_types": [...]
}
```
Читается в `src/ai/gemini/generative_ai.py` как `_gemini_config`.
Используется для дефолтной модели (`_DEFAULT_MODEL`) и списка моделей для переключения при ошибках (`_AVAILABLE_MODELS`).

---

## Модуль AI

### `src/ai/gemini/generative_ai.py` — класс `GoogleGenerativeAI`
Датакласс. Инициализируется через `api_key`, опционально `model_name`, `system_instruction`.

**Ключевые методы:**
- `ask(q, attempts=15)` — одиночный запрос без истории, с retry-логикой
- `chat(q, chat_data_folder, flag)` — чат с историей. Флаги: `save_chat`, `read_and_clear`, `clear`, `start_new`
- `describe_image(image, mime_type, prompt)` — описание изображения
- `upload_file(file, file_name)` — загрузка файла в Gemini API
- `_switch_model()` — переключение на следующую модель из `_AVAILABLE_MODELS` при 503/unavailable
- `_save_chat_history` / `_load_chat_history` — сохранение истории в JSON

**История чата** сохраняется в `chat_data/gemini_data/history/gemini_<timestamp>.json`

**Retry-логика в `ask()`:**
- `ResourceExhausted` (429) с `PerDay` / `per_day` / `quota_limit_value: '0'` → `_mark_key_exhausted()` + `_switch_api_key()`. Если ключи кончились → `_switch_model()` + перезагрузка ключей + `_switch_api_key()`
- `ResourceExhausted` (429) без признаков дневного/регионального лимита → ждёт время из ответа (экспоненциально)
- `GatewayTimeout` / `ServiceUnavailable` → `_switch_model()`
- `RequestException` → ждёт 20 мин (макс 5 попыток)
- `DefaultCredentialsError` / `RefreshError` → `_invalidate_api_key()` + `_switch_api_key()`
- `401` / `API_KEY_INVALID` / `PERMISSION_DENIED` → `_invalidate_api_key()` + `_switch_api_key()`
- `quota_limit_value: '0'` означает региональный лимит = 0, ждать бесполезно — ключ сразу помечается исчерпанным

**Цепочка fallback:** ключ → следующий ключ → ... → смена модели → ключи заново → ...

---

## Структура путей

```
gemini-simplechat/
├── main.py                          # точка входа
├── header.py                        # определяет __root__ (корень проекта)
├── .env                             # секреты
├── html/
│   └── index.html                   # веб-интерфейс: вкладки «Чат» и «Торренты» (Bootstrap)
├── instructions/
│   └── system_instruction.md        # системная инструкция для модели
├── src/
│   ├── __init__.py                  # пустой (закомментированный импорт gs)
│   ├── header.py                    # определяет __root__ для src-модулей
│   ├── ai/
│   │   ├── __init__.py              # экспортирует GoogleGenerativeAI
│   │   └── gemini/
│   │       ├── generative_ai.py     # основной класс GoogleGenerativeAI
│   │       ├── config.json          # модели Gemini
│   │       └── header.py            # __root__ + from src import gs (gs.path не используется активно)
│   ├── fastapi/
│   │   ├── __init__.py              # экспортирует init_chat_router, init_qbt_router
│   │   ├── config.json              # конфиг FastAPI (host, port, index_path, qbittorrent)
│   │   ├── router_chat.py           # POST /api/chat
│   │   └── router_qbittorrent.py    # GET /api/torrents, POST /api/torrents/recheck/{hash}, POST /api/torrents/relocate
│   ├── logger/
│   │   └── logger.py                # логгер проекта
│   └── utils/
│       ├── jjson.py                 # j_loads, j_loads_ns, j_dumps
│       ├── file.py                  # read_text_file, save_text_file
│       ├── image.py                 # get_image_bytes
│       ├── date_time.py             # TimeoutCheck
│       ├── get_free_port.py         # get_free_port(host, port_range)
│       └── convertors/
│           └── tts.py               # speech_recognizer, text2speech
├── plugins/
│   ├── __init__.py                  # load_plugins(model) → dict[name, plugin]
│   ├── plugin.py                    # BasePlugin(ABC): handle(), _handle(), name
│   ├── telegram_bot/
│   │   ├── __init__.py              # экспортирует plugin = TelegramBotPlugin
│   │   └── bot.py                   # TelegramBotPlugin: polling, voice↔text, TTS
│   ├── media_layer/
│   │   ├── __init__.py              # экспортирует plugin = MediaLayerPlugin
│   │   └── media_layer.py           # MediaLayerPlugin: поиск по media.db → промпт модели
│   ├── media_organizer/
│   │   ├── __init__.py
│   │   ├── media_organizer.py       # MediaOrganizerPlugin: сканирование, классификация, переименование
│   │   ├── database.py              # MediaDatabase (SQLite)
│   │   └── media.db                 # база данных медиатеки
│   └── qbittorrent/
│       ├── __init__.py              # экспортирует plugin = QBittorrentPlugin
│       └── qbittorrent.py           # QBittorrentClient, check_integrity, find_series, relocate_missing
└── logs/                            # логи (info.log, debug.log, errors.log, log.json)
```

---

## Плагины

### Базовый класс `BasePlugin` (`plugins/plugin.py`)
- `name` — строковый идентификатор плагина
- `handle(message)` — публичный метод, вызывается из `main.py`
- `_handle(message)` — абстрактный, реализуется в каждом плагине
- Возвращает `str` если плагин обработал запрос, иначе `None`

### `load_plugins(model)` (`plugins/__init__.py`)
Возвращает `dict[str, BasePlugin]`. В `main.py` итерируется: первый плагин вернувший не-None выигрывает.

### `TelegramBotPlugin` (`plugins/telegram_bot/bot.py`)
- Токен из `.env` → `TELEGRAM_BOT_TOKEN`
- `start()` / `stop()` — управление polling
- Голос: OGG → `speech_recognizer()` → `model.chat()` → `text2speech()` → отправить аудио
- Текст: `model.chat()` → ответить текстом

### `MediaLayerPlugin` (`plugins/media_layer/media_layer.py`)
- Читает данные из `media.db` через `MediaDatabase.export_all()`
- Формирует промпт с JSON-данными и передаёт в модель

### `QBittorrentPlugin` (`plugins/qbittorrent/qbittorrent.py`)
- `QBittorrentClient` — подключается к qBittorrent Web API, порт из `src/fastapi/config.json`
- Логин: поддерживает режим "Пропускать аутентификацию с localhost" (пустой ответ = OK)
- `check_integrity` — recheck всех торрентов
- `find_series` — парсит эпизоды по паттернам `S01E01 / 1x01 / EP01 / Серия 1`, показывает пропуски
- `relocate_missing` — ищет файлы утерянных торрентов в указанных директориях, вызывает `setLocation` + `recheck`
- Веб-роутер: `GET /api/torrents`, `POST /api/torrents/recheck/{hash}`, `POST /api/torrents/relocate`, `POST /api/torrents/set-location`, `GET|POST|DELETE /api/torrents/dirs`
- Пути поиска сохраняются в `src/fastapi/search_dirs.json`

### `MediaOrganizerPlugin` (`plugins/media_organizer/media_organizer.py`)
Триггеры: `фильм`, `сериал`, `скан`, `отчет`, `медиатек`, `ревизи`, `audit` и др.
Команда `диск N` запускает полный цикл:
1. Сканирование путей из `media_paths.txt`
2. Классификация через TMDB + Gemini (4 поэтапных промпта)
3. Сохранение в `media.db` + JSON-отчёт в `media_reports/`
4. Переименование файлов/папок по схеме `NN. Название Год`
5. Аудит (сверка БД с диском)
6. Поиск дубликатов

Команда `ревизи` / `audit` — только аудит без сканирования.

---

## База данных медиатеки (`plugins/media_organizer/database.py`)

### Класс `MediaDatabase`
Файл: `plugins/media_organizer/media.db`

**Таблица `media`** — уникальный ключ `(disk_name, title, type)`:
`id, disk_name, path, number, review, title, type, year, main_category, country, genres, directors, cast, num_of_seasons, num_of_seasons, status, rating, awards, plot, atmosphere, why_watch, mood, final_verdict, seasons, can_stop_at, quote, facts, similar`

JSON-поля (сериализуются): `genres, directors, cast, num_of_seasons, rating, awards, seasons, facts, similar, review`

**Таблица `duplicates`** — ключ `(title, type, disk_name)`:
Заполняется триггером `trg_check_duplicates` при INSERT в `media`.

**Методы:**
- `get_media(disk_name, title, type)` → Dict | None
- `find_any_disk(title, type)` → Dict | None (поиск по всей БД)
- `save_media(disk_name, type, data)` → INSERT OR REPLACE
- `export_all()` → List[Dict]
- `find_duplicates()` → Dict[str, List[Dict]]

**Миграция:** если в таблице есть колонка `raw_name` — таблица дропается и пересоздаётся.

---

## Запуск

### `run_media_organizer.py`
- Без аргументов или с пустым вводом имени диска (двойной Enter) → запускает `main.py` через `sys.executable` и открывает браузер
- С аргументами (`--disk`, `--title`, `--audit` и др.) → CLI-режим
- Логика пустого ввода: первый Enter → предупреждение, второй Enter → веб-интерфейс

## API Key Management

### Файлы
- `src/secrets/gemini_keys.json` — хранилище ключей (в `.gitignore`)
- `.env` — только имена: `GEMINI_API_KEY_NAMES=benavrahamdavidka,davidka,...`
- `src/secrets/api_key_state.py` — менеджер состояния

### Структура `gemini_keys.json`
```json
{
  "name": {
    "api_key": "<API_KEY>",
    "status": "active",
    "last_run": "2024-06-01T12:00:00Z",
    "exhausted_at": "2024-06-01T12:00:00Z"  // появляется при бане
  }
}
```
- `status`: `"active"` | `"regional restriction"` | любой другой статус блокирует ключ
- `last_run`: ISO timestamp последнего успешного запроса
- `exhausted_at`: выставляется автоматически при дневном бане, снимается через 24ч

### Логика выбора ключа (`load_api_keys`)
1. Фильтр: только `status == "active"`
2. Фильтр: не забаненые (нет `exhausted_at` или прошло 24ч)
3. Сортировка по `last_run` асц — первым идёт самый давно не использовавшийся

### Функции `api_key_state.py`
- `load_api_keys(names)` → `(api_keys, key_names, key_names)` — загрузить доступные ключи
- `mark_exhausted(key_name)` — записать `exhausted_at` в `gemini_keys.json`
- `update_last_run(key_name)` — обновить `last_run` после успешного запроса
- `get_status(names)` — вывести статус всех ключей в консоль

### Управление ключами
- Добавить/удалить: редактировать `gemini_keys.json` вручную + обновить `GEMINI_API_KEY_NAMES` в `.env`
- Снять бан: удалить `exhausted_at` из записи в `gemini_keys.json`
- Выбрать конкретный ключ: `py run_media_organizer.py --key kazarinov` или интерактивно без `--key`

---

| Файл | Зависит от |
|------|-----------|
| `main.py` | `header.py`, `src/fastapi/config.json`, `.env`, `src/ai`, `src/utils`, `plugins/`, `src/fastapi/` |
| `generative_ai.py` | `src/ai/gemini/config.json`, `header.py` (`__root__`), `src/utils/` |
| `media_organizer.py` | `database.py`, `src/logger`, `.env` (TMDB_API_KEY) |
| `bot.py` | `.env` (TELEGRAM_BOT_TOKEN), `src/utils/convertors/tts.py` |
| `media_layer.py` | `database.py` (`media.db`) |
| `router_qbittorrent.py` | `plugins/qbittorrent/qbittorrent.py` |
| `run_media_organizer.py` | `main.py` (subprocess), `src/fastapi/config.json` |
