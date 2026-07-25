# Карта проекта

## Назначение

`gemini-simplechat` — FastAPI-приложение с веб-чатом на Gemini, локальным медиаплеером, медиатекой SQLite/RAG, плагинами и интеграцией qBittorrent. Основной запуск: `python main.py`.

## Запуск и конфигурация

- `main.py` загружает `.env` и `src/fastapi/config.json`, создаёт `FastAPI`, подключает CORS и отдаёт `webinterface/` как `/webinterface`.
- Сервер подключает маршруты чата, qBittorrent, медиатеки и OAuth-авторизации. Страницы: `/`, `/user`, `/tgmini`, `/admin`, `/rc`, `/tv`, `/user_tts`.
- В `main.py` системная инструкция чата загружается из `.ai_instructions/prompts/chat/system_instruction.md`.
- `GoogleGenerativeAI` получает имена ключей из `GEMINI_API_KEY_NAMES` (переменная окружения), а фактические ключи — через `src.secrets.api_key_state`.

## Поток чата

```text
webinterface/user/main.js
  -> POST /api/chat {message}
  -> src/fastapi/router_chat.py
  -> plugins.get('rag').handle() для медиа-запросов (определяется через _is_media_query)
  -> ИЛИ прямой вызов model.chat() / model.chat_stream() для обычных запросов
  -> GoogleGenerativeAI.chat(message) / chat_stream()
  -> {response} в UI через SSE (Server-Sent Events)
```

`BasePlugin.handle()` перехватывает исключения, пишет ошибку через `src.logger.logger` и возвращает пустую строку. RAG-плагин имеет приоритет для медиа-запросов.

## Загрузка плагинов

- `plugins/__init__.py` содержит функцию `load_plugins(ai_model)`, которая динамически обходит подкаталоги `plugins/`, импортирует `plugins.<name>` и вызывает экспортируемый `plugin(ai_model)`.
- Плагины регистрируются в словаре `{name: instance}` и передаются в `init_chat_router(model, plugins)`.
- Плагины можно отключить через переменную окружения `DISABLED_PLUGINS` (через запятую).
- `plugins/media_organizer/__init__.py` экспортирует функции БД и RAG через `media_organizer_core`.
- `plugins/media_organizer/core/media_organizer.py` содержит отдельный `MediaOrganizerPlugin` для сканирования, классификации и отчётов.
- Также присутствуют `telegram_bot`, `qbittorrent`, `rag` и `media_layer`.

## HTTP API (проверенные группы)

| Группа | Модуль | Назначение |
| --- | --- | --- |
| `/api/chat` | `src/fastapi/router_chat.py` | Сообщение чата и ответ модели/плагина. |
| `/api/media` | `src/fastapi/router_media.py` | Сканирование, аудит, пересборка БД/RAG, поиск, файлы и поток воспроизведения. |
| `/api/torrents` | `src/fastapi/router_qbittorrent.py` | Каталоги, список, проверка, перемещение и категории qBittorrent. |
| `/auth` | `src/fastapi/router_auth.py` | Проверка сессии и Google OAuth. |

Полезный уже реализованный контракт: `POST /api/media/by-title` принимает `title` и необязательный `type`, ищет `title`, `title_ru` и `title_orig`, фильтруя по `type` если указан, и возвращает запись с путём. Он предназначен для связки чатовой рекомендации с плеером.

## Веб-интерфейсы

- `webinterface/user/` — объединённый интерфейс пользователя: чат, встроенный `<video>`-плеер, авторизация и обработка торрент-ссылок.
- `webinterface/admin/` — оболочка административных вкладок.
- `webinterface/chat/`, `media/`, `torrents/`, `help/`, `admin_tab/` — содержимое соответствующих вкладок.
- В пользовательском UI плеер загружает `GET /api/media/files` и проигрывает `/api/media/stream?path=...`.

В `webinterface/admin/main.js` используются пути `/html/...`, тогда как `main.py` монтирует статику на `/webinterface`. Это нужно проверить в браузере перед развитием админки.
