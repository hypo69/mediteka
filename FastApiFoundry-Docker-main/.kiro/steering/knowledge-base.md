---
inclusion: always
---

# База знаний проекта AI Assistant (ai_assist)

**Версия проекта:** 0.7.1  
**Источник:** `.amazonq/rules/`

---

## 1. Идентификация проекта

- **Внутреннее имя:** `ai_assist`
- **Публичное имя:** AI Assistant (FastApiFoundry-Docker)
- **Версия:** 0.7.1
- **Платформа:** Windows (primary), Linux (Docker)
- **Язык:** Python 3.11+
- **Порт по умолчанию:** 9696
- **GitHub:** https://github.com/hypo69/FastApiFoundry-Docker
- **Документация:** https://hypo69.github.io/FastApiFoundry-Docker/

---

## 2. Концепция

Оркестратор локальных AI моделей. Единая точка доступа к:
- Microsoft Foundry Local (ONNX)
- HuggingFace Transformers (PyTorch)
- llama.cpp (GGUF / CPU)
- Ollama (local service)

Маршрутизация по префиксу в поле `model`:

| Префикс | Бэкенд |
|---|---|
| `foundry::model-id` | Foundry Local |
| `hf::model-id` | HuggingFace |
| `llama::path.gguf` | llama.cpp |
| `ollama::model-name` | Ollama |

---

## 3. Структура директорий

```
FastApiFoundry-Docker/
├── src/                    # Основной Python код
│   ├── api/                # FastAPI: app.py, endpoints/
│   ├── models/             # AI клиенты: foundry, hf, ollama, router.py
│   ├── rag/                # RAG: rag_system.py, indexer.py
│   ├── agents/             # Агенты: base.py, powershell_agent.py
│   ├── core/               # config.py (реэкспорт config_manager)
│   ├── logger/             # Логирование
│   └── utils/              # Утилиты
├── static/                 # Веб-интерфейс SPA (Bootstrap 5, Vanilla JS)
├── docs/                   # MkDocs документация (ru/ основная)
├── mcp/                    # MCP серверы (Python + PowerShell)
├── extensions/             # Браузерные расширения Chrome
├── sdk/                    # Python SDK
├── check_engine/           # Диагностика и smoke-тесты
├── config.json             # Публичная конфигурация
├── config_manager.py       # Config singleton
├── .env / .env.example     # Секреты
├── run.py                  # Python точка входа
└── start.ps1               # Windows лаунчер
```

---

## 4. Порты

| Сервис | Порт |
|---|---|
| FastAPI | 9696 |
| MkDocs | 9697 |
| llama.cpp | 9780 |
| Docker mapped | 8000 |
| MCP HTTPS | 8090 |
| Foundry Local | auto-detected |

---

## 5. Конфигурационная система

Приоритет: `.env` (секреты) → `config.json` → `Config` singleton

```python
from src.core.config import config

config.api_port           # int, 9696
config.foundry_base_url   # str, runtime override
config.rag_enabled        # bool
config.update_config(d)   # сохранить в файл
```

Секции `config.json`: `fastapi_server`, `foundry_ai`, `rag_system`, `llama_cpp`, `huggingface`, `security`, `logging`, `model_manager`, `telegram`, `port_management`, `docs_server`, `translator`

---

## 6. REST API Endpoints (базовый URL: http://localhost:9696/api/v1)

**ВАЖНО:** Весь взаимодействие с сервером происходит ТОЛЬКО через REST API. Веб-интерфейс и внешние системы используют только эти endpoints.

### Основные endpoints

| Endpoint | Метод | Назначение |
|---|---|---|
| `/health` | GET | Статус всех сервисов (Foundry, HuggingFace, llama.cpp, Ollama, RAG) |
| `/generate` | POST | Генерация текста (маршрутизация по префиксу) |
| `/ai/generate` | POST | Генерация с RAG контекстом |
| `/ai/chat` | POST | Чат с историей (OpenAI-совместимый) |
| `/ai/chat/stream` | POST | SSE стриминг чата |
| `/chat/message` | POST | Сообщение в сессии чата |
| `/chat/stream` | POST | SSE стриминг сообщения |
| `/models` | GET | Все локальные модели от всех провайдеров |
| `/models/connected` | GET | Модели, загруженные в память |
| `/models/{model_id}/load` | POST | Загрузить модель в память |
| `/models/{model_id}/unload` | POST | Выгрузить модель из памяти |
| `/rag/search` | POST | Поиск в RAG индексе |
| `/rag/build` | POST | Построить RAG индекс |
| `/agent/run` | POST | Запустить агента (Powershell, RAG, MCP и др.) |
| `/config` | GET/PATCH | Получить/обновить конфигурацию |
| `/config/env` | POST | Сохранить переменную окружения |
| `/config/export` | GET | Экспорт полной конфигурации |
| `/config/import` | POST | Импорт полной конфигурации |
| `/system/stats` | GET | RAM/CPU/GPU/диск |
| `/security/api-key/status` | GET | Статус API ключа |
| `/security/api-key/generate` | POST | Генерация API ключа |
| `/security/api-key` | DELETE | Удаление API ключа |

### Endpoints по провайдерам

| Endpoint | Метод | Назначение |
|---|---|---|
| `/foundry/status` | GET | Статус Foundry сервиса |
| `/foundry/models/list` | GET | Список доступных моделей Foundry |
| `/foundry/models/load` | POST | Загрузить модель Foundry |
| `/foundry/models/unload` | POST | Выгрузить модель Foundry |
| `/hf/models` | GET | Список скачанных HF моделей |
| `/hf/models/download/stream` | GET | SSE поток загрузки HF модели |
| `/hf/models/load` | POST | Загрузить HF модель в память |
| `/hf/models/unload` | POST | Выгрузить HF модель |
| `/hf/generate` | POST | Генерация через HF модель |
| `/hf/status` | GET | Статус HF интеграции |
| `/llama/status` | GET | Статус llama.cpp сервера |
| `/llama/start` | POST | Запустить llama.cpp сервер |
| `/llama/stop` | POST | Остановить llama.cpp сервер |
| `/llama/models` | GET | Сканирование .gguf файлов на диске |
| `/llama/completion` | POST | Нативная генерация llama-server |
| `/llama/v1/chat/completions` | POST | OpenAI-совместимый чат |
| `/ollama/status` | GET | Статус Ollama сервера |
| `/ollama/models` | GET | Список локальных Ollama моделей |
| `/ollama/models/pull` | POST | Скачать Ollama модель |
| `/ollama/generate` | POST | Генерация через Ollama |
| `/lmstudio/status` | GET | Статус LM Studio сервера |
| `/lmstudio/models` | GET | Список LM Studio моделей |
| `/lmstudio/models/load` | POST | Загрузить LM Studio модель |
| `/lmstudio/generate` | POST | Генерация через LM Studio |

### Дополнительные endpoints

| Endpoint | Метод | Назначение |
|---|---|---|
| `/translate` | POST | Перевод текста |
| `/translate/detect` | POST | Определение языка |
| `/logs` | GET | Просмотр логов |
| `/logs/files` | GET | Список файлов логов |
| `/support/dialogs` | GET | История диалогов Telegram support бота |
| `/helpdesk/dialogs` | GET | История диалогов Telegram helpdesk бота |
| `/training/pairs` | GET/POST/PATCH/DELETE | Управление QA парами для обучения |
| `/training/run` | POST | Запуск fine-tuning |
| `/recommender/track` | POST | Отслеживание просмотров для рекомендаций |
| `/recommender/recommendations` | POST | Получение рекомендаций |
| `/mcp-powershell/servers` | GET/POST | Управление MCP PowerShell серверами |
| `/mcp-agent/tools` | GET | Список MCP инструментов |
| `/content/blocks` | GET | Список content blocks |
| `/install/status` | GET | Статус установки (для GUI installer) |

### OpenAI-совместимые endpoints

| Endpoint | Метод | Назначение |
|---|---|---|
| `/v1/models` | GET | Список моделей в OpenAI формате |
| `/api/v1/llama/v1/chat/completions` | POST | OpenAI чат через llama.cpp |
| `/api/v1/llama/v1/completions` | POST | OpenAI completions через llama.cpp |
| `/api/v1/llama/v1/embeddings` | POST | OpenAI embeddings через llama.cpp |

### Структура запросов

**Генерация текста:**
```json
{
  "prompt": "Текст запроса",
  "model": "hf::Qwen/Qwen2.5-0.5B-Instruct",
  "temperature": 0.7,
  "max_tokens": 1024,
  "use_rag": false
}
```

**Чат:**
```json
{
  "messages": [
    {"role": "user", "content": "Привет"},
    {"role": "assistant", "content": "Привет! Чем могу помочь?"}
  ],
  "model": "hf::Qwen/Qwen2.5-0.5B-Instruct",
  "temperature": 0.7,
  "max_tokens": 1024
}
```

**Загрузка модели:**
```
POST /api/v1/models/hf::Qwen/Qwen2.5-0.5B-Instruct/load
```

**Обновление конфигурации:**
```json
{
  "foundry_ai.default_model": "hf::Qwen/Qwen2.5-0.5B-Instruct",
  "huggingface.auto_load_default": false
}
```

---

## 7. Технологический стек

| Компонент | Пакет |
|---|---|
| Web framework | `fastapi` 0.136.0 |
| ASGI server | `uvicorn` 0.44.0 |
| Data validation | `pydantic` 2.13.2 |
| HTTP client (async) | `aiohttp` 3.13.5 |
| Vector search | `faiss-cpu` 1.13.2 |
| Embeddings | `sentence-transformers` 5.4.1 |
| AI models | `transformers`, `torch`, `onnxruntime` |
| MCP protocol | `mcp` 1.27.0 |
| Docs | `mkdocs-material` 9.7.6 |
| Tests | `pytest` 9.0.3 |

---

## 8. Команды разработки

```powershell
# Запуск (Windows)
powershell -ExecutionPolicy Bypass -File .\start.ps1

# Только Python (Foundry уже запущен)
venv\Scripts\python.exe run.py

# Тесты
venv\Scripts\python.exe -m pytest tests/ -v

# Диагностика
venv\Scripts\python.exe check_env.py
venv\Scripts\python.exe diagnose.py
venv\Scripts\python.exe check_engine\smoke_all_endpoints.py

# Docker
docker-compose up
```

---

## 9. REST API Usage Pattern

**ВСЕ взаимодействия с сервером происходят ТОЛЬКО через REST API:**

1. **Веб-интерфейс** делает HTTP запросы к `http://localhost:9696/api/v1/*`
2. **Внешние системы** (WordPress, Telegram боты) используют только REST API
3. **Модули Python** внутри проекта могут использовать напрямую клиенты (foundry_client, hf_client и т.д.), но внешние запросы всегда идут через API endpoints
4. **API ключ** защищает все `/api/v1/*` endpoints (если настроен в `.env` как `API_KEY`)

**Маршрутизация моделей:**
- `foundry::model-id` → Microsoft Foundry Local
- `hf::model-id` → HuggingFace Transformers
- `llama::path.gguf` → llama.cpp
- `ollama::model-name` → Ollama
- `lmstudio::model` → LM Studio
- Без префикса → Foundry Local (legacy)

**Статус endpoints всегда возвращают:**
```json
{
  "success": true,
  "data": {...},
  "error": null
}
```
