# AI Assistant (ai_assist) — Knowledge Base

**Version:** 0.8.0
**Project:** AI Assistant (ai_assist)
**File:** `.amazonq/rules/memory-bank/knowledge-base.md`

---

## 1. Идентификация проекта

- **Внутреннее имя:** `ai_assist`
- **Публичное имя:** AI Assistant
- **Версия:** 0.8.0
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

> **ПРАВИЛО:** Все запросы к AI и сервисам идут ТОЛЬКО через `http://localhost:9696/api/v1`.
> Никаких прямых вызовов к Gemini/OpenAI/OpenRouter/Foundry/Ollama/HuggingFace напрямую.
> Это касается браузерных расширений, MCP серверов, SDK, скриптов — всего.

### Генерация и чат

| Endpoint | Метод | Тело запроса (ключевые поля) | Ответ |
|---|---|---|---|
| `/generate` | POST | `prompt`, `model` (с префиксом), `temperature`, `max_tokens`, `use_rag`, `translate_model_dialog`, `user_language` | `{success, content, model, usage, user_language, translated}` |
| `/ai/generate` | POST | `prompt`, `model`, `temperature`, `max_tokens`, `use_rag`, `min_score` | `{success, content, model, usage}` |
| `/ai/generate/stream` | POST | `prompt`, `model`, `temperature`, `max_tokens` | SSE stream |
| `/ai/chat` | POST | `messages[]`, `model`, `use_rag`, `system_prompt`, `temperature`, `max_tokens` | OpenAI-совместимый ответ |
| `/ai/chat/stream` | POST | `messages[]`, `model`, `use_rag`, `system_prompt`, `session_id` | SSE stream |

### Сессионный чат

| Endpoint | Метод | Тело / Параметры | Ответ |
|---|---|---|---|
| `/chat/start` | POST | `model` | `{success, session_id, model}` |
| `/chat/message` | POST | `session_id`, `message`, `model`, `temperature`, `max_tokens`, `locale` | `{success, response, session_id}` |
| `/chat/stream` | POST | `session_id`, `message`, `model`, `temperature`, `max_tokens` | SSE stream |
| `/chat/history/{session_id}` | GET | — | `{success, history[]}` |
| `/chat/session/{session_id}` | DELETE | — | `{success}` |
| `/chat/history/save` | POST | `messages[]`, `session_id`, `model`, `title`, `aborted` | `{success, file, session_id}` |
| `/chat/history/list` | GET | `limit`, `offset` | `{success, dialogs[], total}` |
| `/chat/history/file/{filename}` | GET | — | полный диалог |
| `/chat/history/cleanup` | POST | `retention_days`, `max_size_mb` | `{success, deleted, freed_bytes}` |
| `/chat/models` | GET | — | `{success, models[]}` |

### Здоровье и статус

| Endpoint | Метод | Ответ |
|---|---|---|
| `/health` | GET | `{status, foundry_status, llama_status, hf_status, ollama_status, docs_status, rag_status, timestamp}` |
| `/restart/{service}` | POST | `{success, message}` — service: foundry\|llama\|docs\|rag |

### Модели (агрегация всех провайдеров)

| Endpoint | Метод | Ответ |
|---|---|---|
| `/models` | GET | `{success, models[], count, by_provider}` — все модели с префиксами |
| `/models/connected` | GET | `{success, models[], count}` — только загруженные |
| `/models/{model_id}/load` | POST | `{success, model_id, provider}` |
| `/models/{model_id}/unload` | POST | `{success, model_id, provider}` |

### Foundry

| Endpoint | Метод | Ответ |
|---|---|---|
| `/foundry/status` | GET | `{success, running, status, port, url}` |
| `/foundry/models/list` | GET | `{success, models[]}` |
| `/foundry/models` | GET | alias → `/foundry/models/available` |
| `/foundry/models/catalog` | GET | полный каталог Foundry (CLI) |
| `/foundry/models/available` | GET | загруженные модели (Foundry API) |
| `/foundry/models/cached` | GET | скачанные модели (сканирование диска) |
| `/foundry/models/loaded` | GET | модели в памяти |
| `/foundry/models/download` | POST | `{model_id}` → `{success, status, pid}` |
| `/foundry/models/download/status/{pid}` | GET | `{success, status, model_id}` |
| `/foundry/models/load` | POST | `{model_id}` → `{success, model_id}` |
| `/foundry/models/unload` | POST | `{model_id}` → `{success, model_id}` |
| `/foundry/models/status/{model_id}` | GET | `{success, loaded, cached, status}` |
| `/foundry/models/completions` | POST | `{prompt, model, temperature, max_tokens}` → OpenAI ответ |
| `/foundry/models/embeddings` | POST | `{input, model}` → `{success, data[]}` |
| `/foundry/models/auto-load-default` | POST | — → `{success, model_id}` |

### HuggingFace

| Endpoint | Метод | Тело / Параметры | Ответ |
|---|---|---|---|
| `/hf/status` | GET | — | `{success, transformers, torch, hf_token_set, models_dir}` |
| `/hf/models` | GET | — | `{success, downloaded[], loaded[]}` |
| `/hf/hub/models` | GET | — | `{success, username, user_models[], public_models[]}` |
| `/hf/models/download` | POST | `{model_id, token}` | `{success, model_id, path}` |
| `/hf/models/download/stream` | GET | `?model_id=&token=` | SSE прогресс |
| `/hf/models/load` | POST | `{model_id, device}` | `{success, model_id, device}` |
| `/hf/models/unload` | POST | `{model_id}` | `{success, model_id}` |
| `/hf/generate` | POST | `{model_id, prompt, max_new_tokens, temperature}` | `{success, content, model}` |

### llama.cpp

| Endpoint | Метод | Тело / Параметры | Ответ |
|---|---|---|---|
| `/llama/status` | GET | `?model=` | `{success, running, loading, pid, url, active_model}` |
| `/llama/start` | POST | `{model_path, port, ctx_size, threads, n_gpu_layers}` | `{success, pid, model, url}` |
| `/llama/stop` | POST | — | `{success, message}` |
| `/llama/models` | GET | `?extra_dir=` | `{success, models[], count}` |
| `/llama/models/copy` | POST | `{model_path}` | `{success, path, status}` |
| `/llama/props` | GET | — | `{success, props}` |
| `/llama/slots` | GET | — | `{success, slots[]}` |
| `/llama/metrics` | GET | — | Prometheus text/plain |
| `/llama/completion` | POST | `{prompt, temperature, top_k, n_predict, ...}` | `{success, content, ...}` |
| `/llama/tokenize` | POST | `{content}` | `{success, tokens[]}` |
| `/llama/detokenize` | POST | `{tokens[]}` | `{success, content}` |
| `/llama/v1/completions` | POST | OpenAI completions body | OpenAI ответ |
| `/llama/v1/embeddings` | POST | `{input, model}` | `{success, data[]}` |
| `/llama/v1/chat/completions` | POST | OpenAI chat body | OpenAI ответ |
| `/llama/v1/models` | GET | — | `{success, data[], model_name}` |

### Ollama

| Endpoint | Метод | Тело | Ответ |
|---|---|---|---|
| `/ollama/status` | GET | — | `{success, running, url, version}` |
| `/ollama/models` | GET | — | `{success, models[], count}` |
| `/ollama/models/pull` | POST | `{model}` | `{success, model, status}` |
| `/ollama/models/delete` | POST | `{model}` | `{success, model}` |
| `/ollama/generate` | POST | `{model, prompt, max_tokens, temperature}` | `{success, content, model}` |

### RAG

| Endpoint | Метод | Тело / Параметры | Ответ |
|---|---|---|---|
| `/rag/status` | GET | — | `{success, enabled, index_dir, model, total_chunks}` |
| `/rag/search` | POST | `{query, top_k, min_score}` | `{success, results[], total}` |
| `/rag/build` | POST | `{docs_dir, model, chunk_size, overlap, force}` | `{success, chunks, rebuilt, index_dir}` |
| `/rag/index` | POST | `file` (upload) или `?url=` | `{success, source, method, length}` |
| `/rag/rebuild` | POST | — | `{success, message}` |
| `/rag/clear` | POST | — | `{success, deleted_count}` |
| `/rag/dirs` | GET | — | `{success, dirs[]}` |
| `/rag/cwd` | GET | — | `{success, cwd}` |
| `/rag/browse` | GET | `?path=` | `{success, current, parent, dirs[]}` |
| `/rag/extract/file` | POST | `file` (upload) | `{success, filename, text, method, total_chars}` |
| `/rag/extract/url` | POST | `{url, enable_javascript, process_images}` | `{success, url, text, method, total_chars}` |
| `/rag/extract/formats` | GET | — | `{success, formats[]}` |
| `/rag/config` | PUT | RAGConfig body | `{success}` |
| `/rag/profiles` | GET | — | `{success, profiles[]}` |
| `/rag/profiles/load` | POST | `{name}` | `{success, index_dir}` |
| `/rag/profiles/{name}/activate` | POST | — | `{success}` |
| `/rag/profiles/deactivate` | POST | — | `{success}` |
| `/rag/profiles/{name}` | DELETE | — | `{success}` |
| `/rag/documents` | GET | — | `{success, documents[], total}` |
| `/rag/documents` | POST | `{title, content, source_path}` | `{success, doc_id, chunks_added}` |
| `/rag/documents/{doc_id}` | GET | — | `{success, document}` |
| `/rag/documents/{doc_id}` | PUT | `{title, content}` | `{success, chunks_added, changed}` |
| `/rag/documents/{doc_id}` | DELETE | — | `{success}` |
| `/rag/documents/{doc_id}/reindex` | POST | — | `{success, chunks_added}` |
| `/rag/documents/stats` | GET | — | `{success, documents, active_chunks, faiss_vectors}` |
| `/rag/compact` | POST | — | `{success, vectors_before, vectors_after}` |

### Агенты

| Endpoint | Метод | Тело | Ответ |
|---|---|---|---|
| `/agent/list` | GET | — | `{success, agents[{name, description}]}` |
| `/agent/{name}/tools` | GET | — | `{success, tools[], descriptions}` |
| `/agent/run` | POST | `{message, agent, model, temperature, max_tokens, max_iterations}` | `{success, answer, tool_calls[], iterations}` |

Доступные агенты: `powershell`, `rag`, `keystroke`, `mcp`, `windows_os`, `computer_admin`, `recommender`, `google`

### Конфигурация

| Endpoint | Метод | Тело | Ответ |
|---|---|---|---|
| `/config` | GET | — | `{success, config, foundry_ai, api}` |
| `/config` | POST | `{config: {...}}` | `{success}` |
| `/config` | PATCH | `{"section.key": value}` (dot-notation) | `{success}` |
| `/config/raw` | GET | — | `{success, content}` |
| `/config/raw` | POST | `{content}` | `{success}` |
| `/config/env-raw` | GET | — | `{success, content}` |
| `/config/env-raw` | POST | `{content}` | `{success}` |
| `/config/env` | POST | `{key, value}` | `{success, key}` |
| `/config/provider-keys` | GET | — | `{success, keys}` |
| `/config/provider-keys` | POST | `{keys: {provider: key}}` | `{success, saved[]}` |
| `/config/export` | GET | — | JSON backup (attachment) |
| `/config/import` | POST | `{config, merge}` | `{success, restored}` |
| `/config/extension-export` | GET | — | extension sync format |
| `/config/extension-import` | POST | extension sync body | `{success, imported[]}` |
| `/config/provider-models/{provider}` | GET | — | `{success, data}` |

### Логи

| Endpoint | Метод | Параметры | Ответ |
|---|---|---|---|
| `/logs` | GET | `?file=&lines=&level=&search=&offset=` | `{success, lines[], returned, total_lines}` |
| `/logs/files` | GET | — | `{success, files[], log_dir}` |
| `/logs/settings` | GET | — | `{success, settings}` |
| `/logs/settings` | POST | `{max_lines_per_file, retention_days, level}` | `{success}` |
| `/logs/health` | GET | — | `{success, status, metrics}` |
| `/logs/clear` | POST | `?file=` | `{success}` |
| `/logs/download` | GET | `?file=` | file download |

### Система и утилиты

| Endpoint | Метод | Ответ |
|---|---|---|
| `/system/stats` | GET | `{success, ram_used_mb, ram_pct, cpu_pct, disk_used_gb, gpus[]}` |
| `/translate` | POST | `{text, source_lang, target_lang, provider}` → `{success, translated}` |
| `/translate/detect` | POST | `{text}` → `{success, language}` |
| `/translate/config` | GET | `{enabled, default_provider, available_providers[]}` |

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
- Все файлы заголовков: версия 0.8.0, проект "AI Assistant (ai_assist)"

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
