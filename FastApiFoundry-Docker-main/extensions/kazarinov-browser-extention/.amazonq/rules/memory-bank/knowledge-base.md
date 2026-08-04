# AI Assistant (ai_assist) — Knowledge Base

**Version:** 0.7.0
**Project:** AI Assistant (ai_assist)
**File:** `.amazonq/rules/memory-bank/knowledge-base.md`

---

## 1. Идентификация проекта

- **Внутреннее имя:** `ai_assist`
- **Публичное имя:** AI Assistant
- **Версия:** 0.7.0
- **Платформа:** Windows (primary), Linux (Docker)
- **Язык:** Python 3.11+
- **Порт по умолчанию:** 9696
- **GitHub:** https://github.com/hypo69/FastApiFoundry-Docker
- **Онлайн-документация:** https://hypo69.github.io/FastApiFoundry-Docker/

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
| без префикса | Foundry (legacy, с предупреждением) |

---

## 3. Точки входа

| Файл | Назначение |
|---|---|
| `start.ps1` | Основной лаунчер Windows (venv, Foundry, llama, MkDocs, run.py) |
| `run.py` | Python точка входа (Foundry уже запущен) |
| `install.ps1` | Установщик зависимостей |
| `docker-compose.yml` | Docker деплой |
| `stop.ps1` | Остановка всех сервисов |
| `autostart.ps1` | Автозапуск при входе в Windows |

---

## 4. Структура директорий

```
FastApiFoundry-Docker/
├── src/                    # Основной Python код
│   ├── api/                # FastAPI: app.py, endpoints/
│   ├── models/             # AI клиенты: foundry, hf, ollama, router.py
│   ├── rag/                # RAG: rag_system.py, indexer.py, text_extractor_4_rag/
│   ├── agents/             # Агенты: base.py, powershell_agent.py
│   ├── converter/          # GGUF → ONNX
│   ├── core/               # config.py (реэкспорт config_manager)
│   ├── logger/             # Логирование
│   └── utils/              # Утилиты: translator, foundry_utils, logging_config
├── static/                 # Веб-интерфейс SPA
│   ├── js/                 # Логика UI (chat.js, foundry.js, rag.js, i18n.js...)
│   ├── css/                # Стили
│   ├── locales/            # i18n: en.json, ru.json, he.json
│   └── partials/           # HTML-фрагменты вкладок
├── docs/                   # MkDocs документация
│   ├── ru/                 # Русская документация (основная)
│   └── en/                 # Английская документация
├── mcp/                    # MCP серверы (Python + PowerShell)
│   └── src/servers/        # local_models_mcp.py, ftp_mcp.py, McpSTDIOServer.ps1
├── mcp-powershell-servers/ # Дублирует mcp/ (legacy)
├── extensions/             # Браузерные расширения Chrome
│   ├── browser-extension-summarizer/
│   ├── browser-extension-locator-editor/
│   └── browser-extension-review-parser/
├── sdk/                    # Python SDK
│   ├── fastapi_foundry_sdk/
│   └── microsoft_foundry_sdk/
├── scripts/                # PowerShell операционные скрипты
├── install/                # Скрипты установки
├── check_engine/           # Диагностика и smoke-тесты
├── utils/                  # Standalone утилиты (ai_model_scanner, port_manager...)
├── bin/                    # llama.cpp бинарники Windows x64
├── rag_index/              # FAISS индекс (runtime)
├── logs/                   # Логи приложения
├── archive/                # Архив ротированных логов
├── config.json             # Публичная конфигурация
├── config_manager.py       # Config singleton
├── .env / .env.example     # Секреты
└── requirements.txt        # Зависимости
```

---

## 5. Конфигурационная система

### Приоритет источников
```
.env (секреты) → переопределяет → config.json → читается через → Config singleton
```

### Доступ к конфигурации
```python
from src.core.config import config

config.api_port                    # int, 9696
config.api_host                    # str, '0.0.0.0'
config.foundry_base_url            # str, runtime override
config.foundry_default_model       # str
config.foundry_auto_load_default   # bool
config.foundry_temperature         # float, 0.7
config.foundry_max_tokens          # int, 2048
config.rag_enabled                 # bool
config.rag_index_dir               # str
config.rag_model                   # str
config.rag_chunk_size              # int, 1000
config.rag_top_k                   # int, 5
config.llama_model_path            # str
config.dir_models                  # str, ~/.models
config.dir_hf_models               # str, ~/.cache/huggingface/hub
config.model_manager_max_loaded    # int, 1
config.model_manager_ttl_seconds   # int, 600
config.model_manager_max_ram_percent # float, 80.0
config.get_section("huggingface")  # dict
config.get_raw_config()            # весь config.json
config.update_config(new_dict)     # сохранить в файл
config.reload_config()             # перечитать файл
```

### Секции config.json
- `fastapi_server` — host, port, mode, workers, reload
- `foundry_ai` — base_url, default_model, auto_load_default, temperature, max_tokens
- `rag_system` — enabled, index_dir, model, chunk_size, top_k, source_dirs
- `llama_cpp` — model_path, models_dir, port, host
- `huggingface` — models_dir, device, default_max_new_tokens
- `security` — api_key, enable_https
- `logging` — retention_hours, history_retention_days, archive_max_size_gb
- `docs_server` — enabled, port (9697)
- `translator` — enabled, default_provider, mymemory_email
- `text_extractor` — 7 настроек
- `model_manager` — max_loaded_models, ttl_seconds, max_ram_percent
- `telegram` — admin bot settings
- `telegram_helpdesk` — helpdesk bot settings
- `port_management` — auto_find_free_port, port_range_start/end

---

## 6. API Endpoints (базовый URL: /api/v1)

| Endpoint | Метод | Файл | Назначение |
|---|---|---|---|
| `/health` | GET | health.py | Статус сервиса |
| `/generate` | POST | generate.py | Генерация текста (маршрутизация по префиксу) |
| `/ai/generate` | POST | ai_endpoints.py | Расширенная генерация |
| `/ai/chat` | POST | ai_endpoints.py | Чат (OpenAI-совместимый) |
| `/chat/start` | POST | chat_endpoints.py | Начать сессию |
| `/chat/message` | POST | chat_endpoints.py | Сообщение в сессию |
| `/chat/stream` | POST | chat_endpoints.py | SSE стриминг |
| `/models` | GET | models.py | Все модели |
| `/foundry/status` | GET | foundry.py | Статус Foundry |
| `/foundry/models` | GET | foundry_models.py | Модели Foundry |
| `/foundry/models/load` | POST | foundry_models.py | Загрузить модель |
| `/hf/*` | * | hf_models.py | HuggingFace операции |
| `/llama/*` | * | llama_cpp.py | llama.cpp операции |
| `/ollama/*` | * | ollama.py | Ollama операции |
| `/rag/search` | POST | rag.py | Поиск в RAG |
| `/rag/build` | POST | rag.py | Построить индекс |
| `/rag/extract/file` | POST | rag.py | Извлечь текст из файла |
| `/rag/extract/url` | POST | rag.py | Извлечь текст с URL |
| `/agent/run` | POST | agent.py | Запустить агента |
| `/mcp-powershell/*` | * | mcp_powershell.py | MCP серверы |
| `/config` | GET/PATCH/POST | config.py | Конфигурация |
| `/logs` | GET | logs.py | Логи |
| `/system/stats` | GET | system_stats.py | RAM/CPU |
| `/translate` | POST | translator.py | Перевод текста |
| `/helpdesk/*` | * | helpdesk.py | HelpDesk бот |

---

## 7. Ключевые паттерны кода

### Singleton
```python
class Config:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
config = Config()
```

### API Response Handler
```python
@router.post("/generate")
@api_response_handler  # из src/utils/api_utils.py
async def generate_text(request: dict) -> dict:
    ...
    return {"success": True, "content": "...", "model": "..."}
    # или
    return {"success": False, "error": "описание"}
```

### CPU-bound в async
```python
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, blocking_fn, arg1, arg2)
```

### Guard clause
```python
if not prompt:
    return {"success": False, "error": "Prompt is required"}
```

### Логирование
```python
logger = logging.getLogger(__name__)
logger.info("✅ RAG system initialized")
logger.warning("⚠️ Foundry not found")
logger.error(f"❌ Error: {e}")
```

---

## 8. RAG система

- **Движок:** FAISS + SentenceTransformers
- **Индекс:** `rag_index/faiss.index` + `rag_index/chunks.json`
- **Профили:** `~/.rag/<name>/` — переключаемые базы знаний
- **Форматы:** 40+ (PDF, DOCX, XLSX, PPTX, HTML, изображения OCR, ZIP/7z, исходный код)
- **Singleton:** `rag_system = RAGSystem()` в `src/rag/rag_system.py`
- **Инициализация:** при старте в `lifespan()` → `await rag_system.initialize()`
- **Кэш поиска:** `_search_cache: Dict[tuple, List]` — сбрасывается при reload_index

---

## 9. Веб-интерфейс (SPA)

**URL:** http://localhost:9696

Вкладки: Chat, Models, Foundry, HuggingFace, llama.cpp, Ollama, RAG, Agent, MCP, Logs, Settings, Editor, Docs

**Технологии:** Bootstrap 5, Vanilla JS (fetch API), без фреймворков

**i18n:** `data-i18n` атрибуты в HTML, `i18n()` функция в JS, файлы `static/locales/`

**Структура JS:**
- `ui.js` — переключение вкладок, модалки, уведомления
- `chat.js` — логика чата
- `foundry.js` — управление Foundry
- `rag.js` — RAG поиск и индексация
- `config.js` — настройки
- `i18n.js` — интернационализация
- `model-badge.js` — бейдж активной модели

---

## 10. MCP серверы

**Директория:** `mcp/src/servers/`

| Сервер | Тип | Назначение |
|---|---|---|
| `local_models_mcp.py` | Python STDIO | Проксирует к FastAPI Foundry |
| `huggingface_mcp.py` | Python STDIO | HuggingFace Inference API |
| `ftp_mcp.py` | Python STDIO | FTP операции |
| `docs_deploy_mcp.py` | Python STDIO | Деплой документации на FTP |
| `McpSTDIOServer.ps1` | PowerShell STDIO | Выполнение PowerShell команд |
| `McpHttpsServer.ps1` | PowerShell HTTPS | REST API для PowerShell |

**Управление через API:** `GET/POST /api/v1/mcp-powershell/servers/{name}/start|stop|status`

---

## 11. Startup workflow (start.ps1 → run.py)

```
start.ps1:
  [1] venv проверка → install.ps1 если нет
  [2] Load .env
  [3] Get-FoundryPort() → foundry service start если не найден
  [4] docs_server.enabled? → mkdocs serve (фон)
  [5] llama_cpp.model_path? → llama-start.ps1 (фон)
  [6] Убить предыдущий FastAPI процесс
  [7] python run.py (блокирующий)

run.py:
  - UTF-8 setup (Windows)
  - load_env_variables()
  - Config() singleton
  - cleanup_log_temp_files()
  - cleanup_session_history()
  - cleanup_archive_size()
  - resolve_foundry_base_url() → config.foundry_base_url = url
  - get_server_port()
  - uvicorn.run("src.api.main:app", ...)

lifespan(app):
  - await rag_system.initialize()
  - if auto_load_default: subprocess foundry model load <model>
  yield
  - await foundry_client.close()
```

---

## 12. Браузерные расширения

| Расширение | Назначение |
|---|---|
| `browser-extension-summarizer` | Суммаризация страниц через AI |
| `browser-extension-locator-editor` | Редактор локаторов (TypeScript/React) |
| `browser-extension-review-parser` | Парсер отзывов |

---

## 13. SDK

| Пакет | Файл | Назначение |
|---|---|---|
| `fastapi_foundry_sdk` | `sdk/fastapi_foundry_sdk/client.py` | HTTP клиент к FastAPI Foundry |
| `microsoft_foundry_sdk` | `sdk/microsoft_foundry_sdk/` | Прямая работа с Foundry Local |

---

## 14. Диагностика

```powershell
venv\Scripts\python.exe check_env.py          # Проверка окружения
venv\Scripts\python.exe diagnose.py           # Диагностика
venv\Scripts\python.exe check_engine\smoke_all_endpoints.py  # Smoke тесты
```

---

## 15. Ключевые переменные окружения (.env)

| Переменная | Назначение |
|---|---|
| `FOUNDRY_BASE_URL` | URL Foundry (если не автоопределяется) |
| `HF_TOKEN` | HuggingFace токен (для закрытых моделей) |
| `HF_MODELS_DIR` | Директория HF моделей |
| `LLAMA_MODEL_PATH` | Путь к GGUF файлу |
| `LLAMA_AUTO_START` | Автозапуск llama.cpp |
| `API_KEY` | Ключ API для безопасности |
| `TELEGRAM_ADMIN_TOKEN` | Токен Telegram admin бота |
| `TELEGRAM_HELPDESK_TOKEN` | Токен HelpDesk бота |
| `FTP_HOST/USER/PASSWORD` | FTP для MCP сервера |

---

## 16. Правила документации

- Документация на русском: `docs/ru/`
- При изменении кода → обновить docstring → обновить CHANGELOG.md → обновить `docs/ru/dev/api_reference.md` если изменился endpoint
- Формат CHANGELOG: `## [version] - date / ### Added|Changed|Fixed / - описание`
- Все файлы заголовков: версия 0.7.0, проект "AI Assistant (ai_assist)"

---

## 17. Порты

| Сервис | Порт |
|---|---|
| FastAPI | 9696 |
| MkDocs | 9697 |
| llama.cpp | 9780 |
| Foundry Local | auto-detected |
| Docker mapped | 8000 |
| MCP HTTPS | 8090 |
