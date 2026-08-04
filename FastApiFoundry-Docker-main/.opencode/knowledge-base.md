---
inclusion: always
---

# Проект AI Assistant (ai_assist) — База знаний opencode

**Версия проекта:** 0.8.0
**Репозиторий:** FastApiFoundry-Docker
**Платформа:** Windows (primary), Linux (Docker)
**Язык:** Python 3.11+
**Порт:** 9696
**GitHub:** https://github.com/hypo69/FastApiFoundry-Docker
**Онлайн-документация:** https://hypo69.github.io/FastApiFoundry-Docker/

---

## 1. Концепция

Оркестратор локальных AI моделей. Единая точка доступа к:
- **Microsoft Foundry Local** (ONNX)
- **HuggingFace Transformers** (PyTorch)
- **llama.cpp** (GGUF / CPU)
- **Ollama** (local service)
- **LM Studio**

Маршрутизация по префиксу в поле `model`:
| Префикс | Бэкенд |
|---------|--------|
| `foundry::model-id` | Foundry Local |
| `hf::model-id` | HuggingFace |
| `llama::path.gguf` | llama.cpp |
| `ollama::model-name` | Ollama |
| `lmstudio::model` | LM Studio |
| без префикса | Foundry (legacy, с предупреждением) |

---

## 2. Структура проекта

```
FastApiFoundry-Docker/
├── src/
│   ├── api/              # FastAPI: app.py, endpoints/
│   ├── models/           # AI клиенты: foundry, hf, ollama, router.py
│   ├── rag/              # RAG: rag_system.py, indexer.py
│   ├── agents/           # Агенты: base.py, powershell_agent.py
│   ├── converter/        # GGUF → ONNX
│   ├── core/             # config.py (реэкспорт config_manager)
│   ├── logger/           # Логирование
│   └── utils/            # Утилиты
├── src/db/               # ChatDB (новая директория, SQLite)
├── static/               # Веб-интерфейс SPA (Bootstrap 5, Vanilla JS)
│   ├── interface/        # index.html, js/, css/, partials/, locales/
│   ├── gui-install/      # GUI installer SPA
│   └── locales/          # ru.json, en.json, he.json
├── docs/                 # MkDocs документация (ru/, en/)
├── mcp/                  # MCP серверы (Python + PowerShell)
├── extensions/           # Браузерные расширения Chrome (3 шт.)
├── sdk/                  # Python SDK (fastapi_foundry_sdk, microsoft_foundry_sdk)
├── bin/                  # llama.cpp бинарники Windows x64
├── rag_index/            # FAISS индекс (runtime)
├── logs/                 # Логи приложения
├── .kiro/specs/          # Спецификации разрабатываемых фич
├── .amazonq/rules/       # Правила для Amazon Q агента
├── .opencode/            # База знаний для opencode (этот файл)
├── config.json           # Публичная конфигурация
├── config_manager.py     # Config singleton
├── .env / .env.example   # Секреты
├── run.py                # Python точка входа
└── start.ps1             # Windows лаунчер
```

---

## 3. Технологический стек

| Компонент | Пакет |
|-----------|-------|
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
| DB | `aiosqlite` (новая) |

---

## 4. Порты

| Сервис | Порт |
|--------|------|
| FastAPI | 9696 |
| MkDocs | 9697 |
| llama.cpp | 9780 |
| Docker mapped | 8000 |
| MCP HTTPS | 8090 |
| Foundry Local | auto-detected |

---

## 5. API Endpoints (базовый URL: /api/v1)

**ПРАВИЛО:** Все запросы к AI и сервисам идут ТОЛЬКО через `http://localhost:9696/api/v1`. Никаких прямых вызовов к Gemini/OpenAI/Foundry/Ollama/HuggingFace напрямую.

### Генерация и чат
- `POST /generate` — генерация текста с маршрутизацией по префиксу
- `POST /ai/generate` — генерация с RAG контекстом
- `POST /ai/generate/stream` — SSE стриминг генерации
- `POST /ai/chat` — чат с историей (OpenAI-совместимый)
- `POST /ai/chat/stream` — SSE стриминг чата
- `POST /chat/message` — сообщение в сессии чата
- `POST /chat/stream` — SSE стриминг сообщения

### Модели
- `GET /models` — все модели от всех провайдеров
- `GET /models/connected` — загруженные в память
- `POST /models/{model_id}/load` — загрузить модель
- `POST /models/{model_id}/unload` — выгрузить модель
- `GET /v1/models` — OpenAI-совместимый список моделей (новая фича)

### Foundry
- `GET /foundry/status` — статус Foundry сервиса
- `POST /foundry/start` — запуск Foundry
- `POST /foundry/stop` — остановка Foundry (НУЖНО ДОБАВИТЬ!)
- `POST /foundry/models/load` — загрузить модель Foundry

### HuggingFace
- `GET /hf/status`, `GET /hf/models`
- `POST /hf/models/load`, `POST /hf/models/unload`
- `POST /hf/generate`

### llama.cpp
- `GET /llama/status`, `POST /llama/start`, `POST /llama/stop`
- `GET /llama/models`, `POST /llama/completion`
- `POST /llama/v1/chat/completions` — OpenAI-совместимый чат

### Ollama
- `GET /ollama/status`, `GET /ollama/models`
- `POST /ollama/models/pull`, `POST /ollama/generate`

### RAG
- `GET /rag/status`, `POST /rag/search`, `POST /rag/build`
- `POST /rag/index`, `POST /rag/clear`
- `POST /rag/ingest/chat-history` — индексация истории чатов (НОВАЯ ФИЧА)
- `GET /rag/ingest/status/{task_id}` — статус задачи (НОВАЯ ФИЧА)

### Chat DB (НОВЫЕ)
- `POST /chat/db/session/start` — создать сессию
- `POST /chat/db/message` — сохранить сообщение
- `GET /chat/db/session/{session_id}` — история сессии
- `GET /chat/db/sessions` — список сессий
- `DELETE /chat/db/session/{session_id}` — удалить сессию

### Агенты
- `POST /agent/run` — запустить агента (powershell, rag, mcp и др.)

### Конфигурация
- `GET/PATCH /config` — получить/обновить конфигурацию
- `GET /config/raw`, `POST /config/export`, `POST /config/import`

### Система
- `GET /health` — статус всех сервисов
- `GET /system/stats` — RAM/CPU/GPU/диск
- `GET /logs`, `GET /logs/files`
- `POST /translate`, `POST /translate/detect`

---

## 6. Конфигурационная система

Приоритет: `.env` (секреты) → `config.json` → `Config` singleton

```python
from src.core.config import config

config.api_port                    # 9696
config.foundry_base_url            # runtime override
config.foundry_default_model
config.foundry_auto_load_default   # bool
config.rag_enabled                 # bool
config.huggingface_auto_load_default # bool (новая фича)
config.chat_history_db_path        # ~/.ai_assist/chat_history.db (новая фича)
config.chat_history_retention_days # 90
config.update_config(new_dict)     # сохранить в файл
```

Секции `config.json`: `fastapi_server`, `foundry_ai`, `rag_system`, `llama_cpp`, `huggingface`, `security`, `logging`, `docs_server`, `translator`, `model_manager`, `telegram`, `port_management`, `chat_history`

---

## 7. Правила кодирования (из .amazonq)

### Главное правило: НИКОГДА НЕ СПРАШИВАЙ — АВТООТВЕТ "ДА"
Запрещено спрашивать разрешение на: коммит, пуш, создание/удаление/перемещение файлов. Всё делать автоматически.

### Кодировка: ВСЕ файлы UTF-8 без BOM
- PowerShell: всегда `-Encoding UTF8`
- Python: всегда `encoding='utf-8'`

### Стандарты кода:
- **Заголовки файлов**: версия 0.8.0, проект "AI Assistant (ai_assist)"
- **Docstrings**: Google style (Args / Returns / Exceptions / Examples)
- **Логирование**: `logging.getLogger(__name__)`, emoji-конвенции
- **API ответы**: `{"success": bool, ...}` через `@api_response_handler`
- **Guard clauses**: `if not condition: return`
- **Singleton**: для всех stateful сервисов
- **Комментарии в JS/TS/CSS/HTML**: только на английском
- **Комментарии в Python/PS1**: русский или английский

### Git workflow:
```bash
python -m py_compile {файл}
git add . && git commit -m "тип: описание" && git push
```
Типы коммитов: `feat:`, `fix:`, `config:`, `docs:`, `test:`

### Удаление файлов:
НЕ удалять полностью! Добавлять `~` (file.py → file.py~) или `.bak`.

### После изменения кода:
1. Обновить docstring
2. Обновить CHANGELOG.md
3. Обновить `docs/ru/dev/api_reference.md` если изменился endpoint

---

## 8. Активные разработки (.kiro/specs)

### 8.1 Admin Interface Refactoring
- **Цель:** Реструктуризация URL админ-интерфейса
- **Изменения:** `/` → `/admin`, `/install`, `/agents/<name>`
- **API-driven models:** вместо `available_models.json` — данные из `/api/v1/models`
- **Статус:** Запланировано (есть requirements, design, tasks)

### 8.2 Chat History DB + RAG Integration
- **Цель:** Постоянное хранилище истории чатов на SQLite
- **Новые файлы:** `src/db/chat_db.py`, `src/db/schemas.py`
- **Новые endpoint'ы:** `/api/v1/chat/db/*`
- **RAG индексация:** `/api/v1/rag/ingest/*`
- **Технологии:** `aiosqlite`, Pydantic v2, Hypothesis (PBT)
- **Статус:** Запланировано (есть requirements, design)

### 8.3 Foundry Startup Fix
- **Проблема:** Foundry не стартует автоматически, UI toggle не работает
- **Причина:** Отсутствует `/foundry/stop` endpoint в `install.py`
- **Фикс:** Добавить `stop_foundry()`, улучшить `start_foundry()`, улучшить `Get-FoundryPort` в `start.ps1`
- **Статус:** Запланировано (есть design с кодом)

### 8.4 HuggingFace Auto-Load Control
- **Фича:** Настройка `huggingface.auto_load_default` (bool) в `config.json`
- **По умолчанию:** `true` (сохраняет текущее поведение)
- **Статус:** Запланировано (есть requirements)

### 8.5 OpenAI-Compatible /v1/models Endpoint
- **Новый endpoint:** `GET /v1/models` в OpenAI формате
- **Новый файл:** `src/api/endpoints/openai_models.py`
- **ID mapping:** `foundry::model-id` → `foundry-model-id`
- **Статус:** Запланировано (есть requirements, design)

---

## 9. RAG система

- **Движок:** FAISS + SentenceTransformers
- **Индекс:** `rag_index/faiss.index` + `rag_index/chunks.json`
- **Профили:** `~/.rag/<name>/` — переключаемые базы знаний
- **Форматы:** 40+ (PDF, DOCX, XLSX, PPTX, HTML, OCR, ZIP/7z, код)
- **Singleton:** `rag_system = RAGSystem()` в `src/rag/rag_system.py`
- **IncrementalIndexer:** `src/rag/incremental_indexer.py` — инкрементальное обновление FAISS

---

## 10. MCP серверы

**Директория:** `mcp/src/servers/`

| Сервер | Тип | Назначение |
|--------|-----|------------|
| `local_models_mcp.py` | Python STDIO | Проксирует к FastAPI Foundry |
| `huggingface_mcp.py` | Python STDIO | HuggingFace Inference API |
| `ftp_mcp.py` | Python STDIO | FTP операции |
| `docs_deploy_mcp.py` | Python STDIO | Деплой документации на FTP |
| `McpSTDIOServer.ps1` | PowerShell STDIO | Выполнение PowerShell команд |
| `McpHttpsServer.ps1` | PowerShell HTTPS | REST API для PowerShell |

---

## 11. Команды разработки

```powershell
# Запуск (Windows)
powershell -ExecutionPolicy Bypass -File .\start.ps1

# Только Python
venv\Scripts\python.exe run.py

# Тесты
venv\Scripts\python.exe -m pytest tests/ -v

# Диагностика
venv\Scripts\python.exe check_env.py
venv\Scripts\python.exe diagnose.py

# Docker
docker-compose up
```

---

## 12. Ключевые паттерны

### Singleton Config
```python
class Config:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
```

### API Response Handler
```python
@router.post("/generate")
@api_response_handler
async def generate_text(request: dict) -> dict:
    ...
    return {"success": True, "content": "...", "model": "..."}
```

### CPU-bound в async
```python
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, blocking_fn, arg1, arg2)
```

### Логирование
```python
logger = logging.getLogger(__name__)
logger.info("✅ RAG system initialized")
logger.warning("⚠️ Foundry not found")
logger.error(f"❌ Error: {e}")
```
