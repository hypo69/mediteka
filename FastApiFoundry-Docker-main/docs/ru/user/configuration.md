# Конфигурация

## Главное правило

> **Секреты → `.env`**  
> **Всё остальное → `config.json`**

Если значение содержит пароль, токен или ключ — оно в `.env`.  
Если это порт, путь, флаг или настройка поведения — оно в `config.json`.

---

## Два файла конфигурации

| Файл | Назначение | В git? |
|---|---|---|
| `config.json` | Публичные настройки приложения | ✅ да |
| `.env` | Секреты и машинно-специфичные переопределения | ❌ нет (в `.gitignore`) |
| `.env.example` | Шаблон `.env` с комментариями | ✅ да |

---

## config.json — полная структура

```json
{
  "fastapi_server": {
    "host": "0.0.0.0",        // Адрес прослушивания (0.0.0.0 = все интерфейсы)
    "port": 9696,              // Порт FastAPI
    "auto_find_free_port": false, // Автопоиск свободного порта если 9696 занят
    "mode": "dev",             // dev = hot-reload, prod = без reload
    "workers": 1               // Количество Uvicorn воркеров
  },

  "foundry_ai": {
    "base_url": "",            // URL Foundry (пусто = автоопределение)
    "default_model": "qwen3-0.6b-generic-cpu:4:4",
    "temperature": 0.7,
    "max_tokens": 2048,
    "auto_start": true,        // Запускать службу Foundry при старте start.ps1
    "auto_load_default": false,// Загружать default_model после старта FastAPI
    "startup_models": []       // Список Foundry моделей для прогрева при старте
  },

  "llama_cpp": {
    "port": 9780,              // Порт llama-server
    "host": "127.0.0.1",
    "model_path": "",          // Путь к .gguf файлу
    "auto_start": false,       // Запускать llama.cpp при старте start.ps1
    "bin_version": "llama-b8802-bin-win-cpu-x64"  // Версия бинарника в bin/
  },

  "huggingface": {
    "device": "auto",          // auto / cpu / cuda
    "default_max_new_tokens": 512,
    "default_temperature": 0.7
  },

  "lmstudio": {
    "base_url": "http://localhost:1234", // LM Studio REST API host
    "api_key": "",                       // Пусто = без Authorization
    "default_model": "",                 // Модель по умолчанию для lmstudio::
    "request_timeout_sec": 300
  },

  "rag_system": {
    "enabled": true,
    "index_dir": "~/.aiassistant/rag/default_index", // Активный FAISS индекс
    "chunk_size": 1000         // Размер чанка при индексации
  },

  "security": {
    "api_key": "",             // API ключ для защиты эндпоинтов (пусто = без защиты)
    "https_enabled": false
  },

  "logging": {
    "level": "INFO",           // DEBUG / INFO / WARNING / ERROR
    "file": ""                 // Путь к лог-файлу (пусто = только консоль)
  },

  "development": {
    "debug": false,
    "verbose": false
  },

  "docs_server": {
    "enabled": true,           // Запускать MkDocs при старте
    "port": 9697
  },

  "directories": {
    "models": "~/.models",     // GGUF модели для llama.cpp
    "rag": "~/.aiassistant/rag", // Корневая директория RAG индексов
    "hf_models": "~/.cache/huggingface/hub" // HuggingFace модели (стандартный кэш HF)
  },

  "app": {
    "language": "en"           // Язык интерфейса: en / ru / he
  },

  "dialogs": {
    "dir": "~/.ai_assist/dialogs", // Директория хранения диалогов (все клиенты)
    "retention_days": 30,         // Срок хранения в днях
    "max_size_mb": 100            // Максимальный размер директории в MB
  }
}
```

### Редактирование

В веб-интерфейсе доступны два способа:

- **Settings** — интуитивный интерфейс с полями и переключателями
- **Editor** — прямое редактирование сырых файлов `config.json` и `.env`

---

## .env — только секреты

```env
# HuggingFace токен для закрытых моделей (Gemma, Llama, Mistral)
# Получить: https://huggingface.co/settings/tokens
HF_TOKEN=hf_...

# Foundry URL — только если автоопределение не работает
# FOUNDRY_BASE_URL=http://localhost:50477/v1

# API ключ для защиты FastAPI эндпоинтов (опционально)
# API_KEY=your_secret_key

# Ключи внешних AI провайдеров
# Управляются через Settings → API Keys в веб-интерфейсе
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GEMINI_API_KEY=AIza...

# Явный путь к llama-server.exe (только если автоопределение из bin/ не работает)
# LLAMA_SERVER_PATH=.\bin\llama-b8802-bin-win-cpu-x64\llama-server.exe
```

### Создание .env

```powershell
Copy-Item .env.example .env
notepad .env
```

---

## Что куда — полная таблица

### ✅ config.json

| Параметр | Секция | Описание |
|---|---|---|
| Порт FastAPI | `fastapi_server.port` | 9696 по умолчанию |
| Хост FastAPI | `fastapi_server.host` | 0.0.0.0 = все интерфейсы |
| Режим сервера | `fastapi_server.mode` | dev / prod |
| URL Foundry | `foundry_ai.base_url` | Пусто = автоопределение |
| Модель по умолчанию | `foundry_ai.default_model` | ID модели Foundry |
| Температура | `foundry_ai.temperature` | 0.0 – 2.0 |
| Автостарт Foundry | `foundry_ai.auto_start` | Запускать службу через `start.ps1` |
| Автозагрузка модели | `foundry_ai.auto_load_default` | Загружать `default_model` после старта FastAPI |
| Модели Foundry при старте | `foundry_ai.startup_models` | Список ID моделей для загрузки в память |
| Порт llama.cpp | `llama_cpp.port` | 9780 по умолчанию |
| Путь к модели llama | `llama_cpp.model_path` | Путь к .gguf файлу |
| Автостарт llama.cpp | `llama_cpp.auto_start` | При запуске start.ps1 |
| Версия бинарника | `llama_cpp.bin_version` | Обновляется автоматически |
| URL LM Studio | `lmstudio.base_url` | `http://localhost:1234` по умолчанию |
| API ключ LM Studio | `lmstudio.api_key` | Пусто = без Authorization |
| Модель LM Studio по умолчанию | `lmstudio.default_model` | Используется если модель не передана клиенту |
| Таймаут LM Studio | `lmstudio.request_timeout_sec` | Таймаут запросов к локальному REST API |
| Устройство HF | `huggingface.device` | auto / cpu / cuda |
| RAG включён | `rag_system.enabled` | true / false |
| Активный индекс RAG | `rag_system.index_dir` | `~/.aiassistant/rag/default_index` |
| Размер чанка | `rag_system.chunk_size` | 1000 символов |
| Порог очистки (Compact) | `rag_system.compact_threshold_percent` | 20 (%) — доля неактивных данных |
| Интервал Compact | `rag_system.compact_check_interval_hours` | 24 (часа) — частота проверки |
| Уровень логов | `logging.level` | INFO по умолчанию |
| Файл логов | `logging.file` | Пусто = только консоль |
| MkDocs включён | `docs_server.enabled` | Документация на порту 9697 |
| Директория диалогов | `dialogs.dir` | `~/.ai_assist/dialogs` — единое место для всех клиентов |
| Срок хранения диалогов | `dialogs.retention_days` | 30 дней |
| Лимит директории диалогов | `dialogs.max_size_mb` | 100 MB |
| Язык интерфейса | `app.language` | en / ru / he |
| Директория моделей | `directories.models` | ~/.models — GGUF для llama.cpp |
| Директория HF моделей | `directories.hf_models` | `~/.cache/huggingface/hub` — стандартный кэш HuggingFace |
| Директория RAG | `directories.rag` | `~/.aiassistant/rag` — FAISS индексы |

### 🔐 .env

| Переменная | Описание |
|---|---|
| `HF_TOKEN` | Токен HuggingFace для закрытых моделей |
| `FOUNDRY_BASE_URL` | Переопределение URL Foundry (если автоопределение не работает) |
| `API_KEY` | Ключ для защиты FastAPI эндпоинтов |
| `OPENAI_API_KEY` | Ключ OpenAI |
| `ANTHROPIC_API_KEY` | Ключ Anthropic |
| `GEMINI_API_KEY` | Ключ Google Gemini |
| `OPENROUTER_API_KEY` | Ключ OpenRouter |
| `MISTRAL_API_KEY` | Ключ Mistral |
| `GROQ_API_KEY` | Ключ Groq |
| `DEEPSEEK_API_KEY` | Ключ DeepSeek |
| `GITHUB_PAT` | GitHub Personal Access Token |
| `LLAMA_SERVER_PATH` | Явный путь к llama-server.exe (если автоопределение не работает) |
| `LMSTUDIO_BASE_URL` | Переопределение URL LM Studio |
| `LMSTUDIO_API_KEY` | Токен LM Studio, если в LM Studio включена авторизация |
| `LMSTUDIO_DEFAULT_MODEL` | Модель LM Studio по умолчанию |

---

## Приоритет настроек

Для некоторых параметров существует несколько источников. Приоритет (от высшего к низшему):

```
1. Переменная окружения (.env или системная)
2. config.json
3. Значение по умолчанию в коде
```

**Пример — директория HuggingFace моделей:**

```
directories.hf_models в config.json  ← приоритет 1
HF_MODELS_DIR в .env (legacy)        ← приоритет 2
~/.cache/huggingface/hub (по умолчанию) ← приоритет 3
```

**Пример — URL Foundry:**

```
FOUNDRY_BASE_URL в .env          ← приоритет 1 (переопределяет всё)
foundry_ai.base_url в config.json ← приоритет 2
Автоопределение через netstat     ← приоритет 3 (fallback)
```

**Пример — путь к llama-server.exe:**

```
LLAMA_SERVER_PATH в .env          ← приоритет 1
PATH системы (shutil.which)       ← приоритет 2
bin/<bin_version>/llama-server.exe ← приоритет 3 (из config.json)
Сканирование всех bin/ поддиректорий ← приоритет 4
Стандартные пути Windows          ← приоритет 5
```

**Пример — URL LM Studio:**

```
LMSTUDIO_BASE_URL в .env / окружении ← приоритет 1
lmstudio.base_url в config.json      ← приоритет 2
http://localhost:1234                ← приоритет 3
```

LM Studio подключается как provider с префиксом `lmstudio::`:

```json
{
  "model": "lmstudio::google/gemma-4-e4b"
}
```

---

## RAG индексы

RAG индексы хранятся в директории `~/.aiassistant/rag/<имя_индекса>`.

Каждый RAG индекс должен содержать файл `README.md`:

```markdown
# Название базы знаний

Короткое описание назначения этой RAG базы: какие документы в ней лежат,
для каких вопросов её подключать и кому она полезна.
```

API читает этот файл при запросе списка RAG:

```http
GET /api/v1/rag/profiles
```

Подключение и отключение выполняется без удаления индекса:

```http
POST /api/v1/rag/profiles/{name}/activate
POST /api/v1/rag/profiles/deactivate
```

Поле `rag_system.index_dir` показывает активный индекс, а `directories.rag`
задаёт корневую папку, где лежат все доступные RAG базы.

---

## Безопасность

### Что никогда не попадает в config.json

Бэкенд автоматически фильтрует при сохранении:

- `huggingface.token` — всегда только в `.env` как `HF_TOKEN`
- `huggingface.hf_token` — то же самое

Если токен случайно оказался в `config.json` — он удаляется автоматически при первом запросе `GET /api/v1/config`.

### .gitignore

`.env` исключён из git. Никогда не коммитьте реальный `.env` — только `.env.example`.

---

## Редактирование через веб-интерфейс

После запуска веб-интерфейс будет доступен по адресу http://localhost:9696

| Что редактировать | Где в UI |
|---|---|
| Все настройки приложения | **Settings** → поля формы → **Save All** |
| HF токен | **Settings** → HuggingFace → поле токена → **Save to .env** |
| Ключи AI провайдеров | **Settings** → **API Keys** |
| Сырой `config.json` | **Editor** → вкладка `config.json` |
| Сырой `.env` | **Editor** → вкладка `.env` |

!!! warning "HF токен сохраняется отдельно"
    Кнопка **Save All** в Settings НЕ сохраняет HF токен в `config.json`.
    Для сохранения токена используйте отдельную кнопку **Save to .env** рядом с полем токена.

---

## Резервное копирование

### Экспорт всех настроек

**Settings** → **Export** — скачивает полный JSON-бэкап, включающий:

| Источник | Что сохраняется |
|---|---|
| `config.json` | Все настройки приложения |
| `.env` | **Все переменные окружения, включая токены и ключи API** |
| `mcp-powershell-servers/settings.json` | Настройки MCP серверов |
| `mcp-servers/.../claude-desktop-config.json` | Конфиг Claude Desktop |
| `.foundry_url`, `.llama_url` | Сохранённые URL сервисов |

!!! danger "Файл бэкапа содержит секреты"
    Экспортированный файл содержит **полное содержимое `.env`**, включая все токены и ключи API.

    - Храните файл бэкапа в защищённом месте
    - Не передавайте его третьим лицам
    - Не загружайте в облачные хранилища без шифрования
    - Не коммитьте в git-репозиторий

### Ручной бэкап

```powershell
Copy-Item config.json config.json.bak
Copy-Item .env .env.bak
```

При каждом сохранении через UI автоматически создаётся `config.json.backup_YYYYMMDD_HHMMSS`.
