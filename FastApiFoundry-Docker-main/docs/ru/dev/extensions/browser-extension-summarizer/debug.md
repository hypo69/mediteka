# Отладка сервера (Server Debug)

Страница `debug.html` — инструмент для тестирования endpoints FastAPI Foundry прямо из браузера.

## Компоновка страницы

```
┌─────────────────────────────────────────────────────┐
│ 🔧 Server Debug                          [✓ Connected] [EN▼] │
├─────────────────────────────────────────────────────┤
│ URL: [http://localhost:9696] [API key] [Check]       │
├─────────────────────────────────────────────────────┤
│                                                     │
│   RESPONSE (растягивается, занимает всё             │
│   свободное пространство, скроллится)               │
│   GET /api/v1/health  •  200 OK  •  12ms            │
│                                                     │
├─────────────────────────────────────────────────────┤
│ [Endpoints] [Custom] [Chat]                         │
│ ─────────────────────────────────────────────────── │
│ контролы активной вкладки                           │
└─────────────────────────────────────────────────────┘
```

Response panel всегда видна вверху — не нужно скроллить после каждого запроса.

## URL и API-ключ

- **URL** — базовый адрес сервера, по умолчанию `http://localhost:9696`
- **API key** — опционально, если задан `API_KEY` в `.env` сервера
- Кнопка **Check** — выполняет `GET /api/v1/health` и показывает статус подключения

URL и API-ключ сохраняются в `chrome.storage.sync` при изменении.

## Вкладка Endpoints

Список всех endpoints сервера, сгруппированных по категориям:

| Группа | Цвет | Endpoints |
|---|---|---|
| Core | серый | health, models, connected, config |
| Chat | синий | start session, send message, chat models |
| Generate | зелёный | generate text, generate + RAG |
| Foundry | фиолетовый | status, models list, loaded, cached |
| HuggingFace | оранжевый | status, downloaded, hub, generate, load, unload, download |
| llama.cpp | красный | status, scan GGUF, stop |
| RAG | голубой | status, profiles, dirs, search, clear |

**Поле фильтра** над списком — фильтрует по пути, названию или группе в реальном времени.

Клик по строке:
1. Выполняет запрос немедленно
2. Переключает на вкладку **Custom** с заполненными полями метода, пути и тела

## Вкладка Custom

Произвольный HTTP-запрос к серверу:

- **Метод** — GET / POST / PATCH / DELETE
- **Путь** — например `/api/v1/generate`
- **Body** — JSON тело запроса (для POST/PATCH/DELETE)

Кнопка **Send** выполняет запрос и показывает ответ в Response panel.

Если JSON в поле Body невалидный — показывается ошибка без отправки запроса.

## Вкладка Chat

Быстрый тест chat endpoint:

- **Model** — ID модели (пусто = auto)
- Кнопка **Load** — запрашивает `GET /api/v1/models` и подставляет первую доступную модель
- **Prompt** — текст запроса
- Кнопка **Send chat request** — отправляет `POST /api/v1/chat` с `messages: [{role:'user', content}]`

## Response panel

Показывает:
- Тело ответа (JSON форматируется с отступами)
- Строку метаданных: `METHOD /path  •  STATUS  •  Nms`
- Зелёный фон при успешном ответе (2xx)
- Красный фон при ошибке (4xx, 5xx, сетевая ошибка)

Кнопки:
- **Copy** — копирует тело ответа в буфер обмена
- **Clear** — очищает панель

## Все endpoints сервера

### Core

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/v1/health` | Статус сервиса, Foundry, количество моделей |
| GET | `/api/v1/models` | Все модели (Foundry + llama.cpp) |
| GET | `/api/v1/models/connected` | Подключённые модели с деталями |
| GET | `/api/v1/config` | Текущая конфигурация |

### Chat

| Метод | Путь | Body | Описание |
|---|---|---|---|
| POST | `/api/v1/chat/start` | `{model}` | Создать сессию, вернуть `session_id` |
| POST | `/api/v1/chat/message` | `{session_id, message, model?, max_tokens?}` | Отправить сообщение |
| POST | `/api/v1/chat/stream` | `{session_id, message}` | Стриминг ответа (SSE) |
| GET | `/api/v1/chat/history/{session_id}` | — | История сессии |
| DELETE | `/api/v1/chat/session/{session_id}` | — | Удалить сессию |
| GET | `/api/v1/chat/models` | — | Доступные модели для чата |
| POST | `/api/v1/chat/history/save` | `{messages, session_id?, model?, title?}` | Сохранить историю на диск |

### Generate

| Метод | Путь | Body | Описание |
|---|---|---|---|
| POST | `/api/v1/generate` | `{prompt, model?, temperature?, max_tokens?, use_rag?}` | Генерация текста |

Префиксы модели: `hf::model-id` для HuggingFace, `llama::path` для llama.cpp, без префикса — Foundry.

### Foundry

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/v1/foundry/status` | Статус сервиса Foundry |
| GET | `/api/v1/foundry/models/list` | Список всех доступных моделей |
| GET | `/foundry/models/loaded` | Загруженные в память модели |
| GET | `/foundry/models/cached` | Скачанные модели в кэше |

### HuggingFace

| Метод | Путь | Body | Описание |
|---|---|---|---|
| GET | `/api/v1/hf/status` | — | Статус библиотек и токена |
| GET | `/api/v1/hf/models` | — | Скачанные и загруженные модели |
| GET | `/api/v1/hf/hub/models` | — | Модели пользователя + популярные публичные |
| POST | `/api/v1/hf/models/download` | `{model_id, token?}` | Скачать модель с Hub |
| POST | `/api/v1/hf/models/load` | `{model_id, device?}` | Загрузить в память |
| POST | `/api/v1/hf/models/unload` | `{model_id}` | Выгрузить из памяти |
| POST | `/api/v1/hf/generate` | `{model_id, prompt, max_new_tokens?, temperature?}` | Генерация через HF |

### llama.cpp

| Метод | Путь | Body | Описание |
|---|---|---|---|
| GET | `/api/v1/llama/status` | — | Статус сервера, URL, PID |
| GET | `/api/v1/llama/models` | — | Сканирование GGUF файлов |
| POST | `/api/v1/llama/start` | `{model_path, port?, ctx_size?, threads?, n_gpu_layers?}` | Запустить сервер |
| POST | `/api/v1/llama/stop` | — | Остановить сервер |

### RAG

| Метод | Путь | Body | Описание |
|---|---|---|---|
| GET | `/api/v1/rag/status` | — | Статус RAG системы |
| GET | `/api/v1/rag/profiles` | — | Список RAG баз в `~/.rag` |
| GET | `/api/v1/rag/dirs` | — | Директории доступные для индексации |
| GET | `/api/v1/rag/browse` | `?path=` | Браузер файловой системы |
| POST | `/api/v1/rag/search` | `{query, top_k?}` | Поиск по индексу |
| POST | `/api/v1/rag/build` | `{docs_dir, model?, chunk_size?, overlap?}` | Построить индекс |
| POST | `/api/v1/rag/profiles/load` | `{name}` | Переключить активную RAG базу |
| POST | `/api/v1/rag/clear` | — | Очистить индекс |
| DELETE | `/api/v1/rag/profiles/{name}` | — | Удалить RAG базу |
