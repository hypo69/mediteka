# Быстрый старт

## Первый запуск — установка + старт

```powershell
# Первая установка
powershell -ExecutionPolicy Bypass -File .\install.ps1

# Запуск сервера
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

После запуска веб-интерфейс доступен по адресу **http://localhost:9696**

!!! tip "Первая установка через install.bat"
    Двойной клик по `install.bat` — автоматически найдёт или установит PowerShell 7,
    затем запустит `install.ps1`.

    Подробнее: [Установка](installation.md)

---

## Создание первой базы знаний (RAG)

Чтобы ассистент начал отвечать на вопросы, основываясь на ваших документах, необходимо создать поисковый индекс:

1. **Откройте веб-интерфейс**: После запуска перейдите по адресу [http://localhost:9696](http://localhost:9696).
2. **Перейдите на вкладку RAG**: Выберите этот пункт в верхнем меню.
3. **Укажите путь к документам**:
    - В блоке **Создать новую RAG базу** введите полный путь к папке с вашими файлами (например, `C:\Documents\MyProject`).
    - Вы также можете нажать иконку домика 🏠 для быстрого выбора пути.
4. **Запустите индексацию**: Нажмите кнопку **Создать индекс**.
    - Процесс может занять от нескольких секунд до минут в зависимости от объема данных. Статус и количество обработанных фрагментов отобразятся в логах ниже.
5. **Использование в чате**:
    - Перейдите на вкладку **Chat**.
    - В настройках справа включите галочку **Использовать RAG контекст**.
    - Теперь ассистент будет сначала искать информацию в ваших документах и использовать её для ответа.

!!! tip "Обновление данных"
    Если вы добавили новые файлы в папку или изменили существующие, просто вернитесь во вкладку **RAG** и снова нажмите **Создать индекс**. Ассистент обновит свою память.

!!! info "Где хранятся индексы?"
    Все базы знаний по умолчанию сохраняются в директории `~/.aiassistant/rag/` вашего профиля пользователя.

---

## Что происходит при запуске

`start.ps1` — единая точка входа. Он последовательно проходит 7 этапов,
затем передаёт управление `run.py`, который запускает FastAPI через Uvicorn.

=== "Для пользователя"

    1. **Проверка окружения** — если `venv\` нет, автоматически запускается установка
    2. **Загрузка настроек** — переменные из `.env` попадают в окружение процесса
    3. **Foundry AI** — ищет запущенный Foundry, при необходимости запускает его
    4. **MkDocs** — опционально запускает сервер документации (`docs_server.enabled=true`)
    5. **llama.cpp** — опционально запускает локальный сервер инференса (`llama_cpp.auto_start=true`)
    6. **OpenCode** — опционально запускает OpenCode сервер (`opencode.enabled=true` и `opencode.auto_start=true`)
    7. **Очистка** — останавливает предыдущий экземпляр FastAPI (если был)
    8. **Запуск** — стартует FastAPI сервер, открывается http://localhost:9696

=== "Для разработчика"

    ```
    start.ps1
      │
      ├─[1] Test-Path venv\Scripts\python.exe
      │      ├─ найден → . venv\Scripts\Activate.ps1
      │      └─ не найден → .\install.ps1 → создать venv
      │
      ├─[2] Load-EnvFile ".env"
      │      └─ SetEnvironmentVariable KEY=VALUE (секреты маскируются ***)
      │
      ├─[3] объявление функций Test-FoundryCli, Get-FoundryPort
      │
      ├─[4] Get-FoundryPort()
      │      ├─ Get-Process "Inference.Service.Agent*" → найден?
      │      │   ├─ да  → netstat -ano | grep PID | grep LISTENING
      │      │   │         → GET /v1/models → HTTP 200
      │      │   │         → FOUNDRY_DYNAMIC_PORT=<port>
      │      │   │         → FOUNDRY_BASE_URL=http://localhost:<port>/v1/
      │      │   └─ нет → Test-FoundryCli?
      │      │             ├─ да  → foundry service start (свёрнутое окно)
      │      │             │         → опрос 10×2 сек → FOUNDRY_DYNAMIC_PORT=<port>
      │      │             └─ нет → предупреждение, продолжить без Foundry
      │
      ├─[4] config.json → docs_server.enabled?
      │      └─ true →
      │          ├─ [site/ существует] → python -m http.server <port> (из site/, без пересборки)
      │          └─ [site/ нет] →
      │               ├─ python -m mkdocs build --quiet
      │               └─ mkdocs serve -a 0.0.0.0:<port>  (фоновое окно, hot-reload)
      │
      ├─[5] config.json → llama_cpp.auto_start=true AND model_path задан?
      │      └─ true → Start-Llama.ps1 → llama-server.exe --model ... --port ...
      │                 → LLAMA_BASE_URL=http://127.0.0.1:<port>/v1
      │                 (если auto_start=false — пропускается, даже если модель указана)
      │
      ├─[6] config.json → opencode.enabled=true AND opencode.auto_start=true?
      │      └─ true → Start-OpenCode.ps1 → opencode start --port ...
      │
      ├─[7] %TEMP%\fastapi-foundry.pid → Kill предыдущий процесс FastAPI
      │
      └─[8] Start-Process $venvPath run.py  ← блокирует до завершения
             └─ PID сохраняется в %TEMP%\fastapi-foundry.pid
    ```

---

## Этапы подробно

??? note "Этап 1 — Проверка venv"

    `start.ps1` ищет `venv\Scripts\python.exe` (или `python311.exe`).

    - **Найден** → активирует `venv\Scripts\Activate.ps1` и продолжает
    - **Не найден** → запускает `install.ps1` автоматически

    `install.ps1` создаёт venv, устанавливает `requirements.txt`, опционально
    устанавливает RAG-зависимости и Foundry CLI.

??? note "Этап 2 — Загрузка .env"

    Функция `Load-EnvFile` читает `.env` построчно и экспортирует каждую пару
    `КЛЮЧ=ЗНАЧЕНИЕ` через `[System.Environment]::SetEnvironmentVariable`.

    Секретные переменные (`PASSWORD`, `SECRET`, `KEY`, `TOKEN`, `PAT`) маскируются
    в выводе как `***`.

    Если `.env` не найден — выводится подсказка создать его из `.env.example`:

    ```powershell
    Copy-Item .env.example .env
    notepad .env
    ```

??? note "Этап 3 — Foundry AI"

    Алгоритм поиска запущенного Foundry:

    ```
    Get-Process | Where ProcessName -like "Inference.Service.Agent*"
      └─ найден → netstat -ano | grep PID | grep LISTENING
          └─ для каждого порта → GET http://127.0.0.1:<port>/v1/models
              └─ HTTP 200 → вернуть порт
    ```

    Если Foundry не запущен, но `foundry` есть в PATH:

    ```powershell
    Start-Process foundry -ArgumentList "service", "start" -WindowStyle Minimized
    # Опрос каждые 2 сек, максимум 10 попыток (20 сек)
    ```

    !!! warning "Foundry недоступен"
        Если Foundry не найден и не установлен — сервер всё равно запустится.
        HuggingFace и llama.cpp продолжат работать. Foundry-модели будут недоступны.

??? note "Этап 4 — MkDocs (опционально)"

    Управляется через `config.json`:

    ```json
    {
      "docs_server": {
        "enabled": true,
        "port": 9697
      }
    }
    ```

    Запускается только если `enabled: true`.

??? note "Этап 5 — llama.cpp (опционально)"

    ### Автозапуск

    Управляется через `config.json`:

    ```json
    {
      "llama_cpp": {
        "model_path": "~/.models/qwen2.5-0.5b-q4_k_m.gguf",
        "auto_start": true,
        "port": 9780
      }
    }
    ```

    Запускается только если `auto_start: true` **и** задан `model_path` (или `default_model` в `models_dir`).
    Если `auto_start: false` — llama.cpp не запускается, даже если модель указана.

??? note "Этап 6 — OpenCode (опционально)"

    Управляется через `config.json`:

    ```json
    {
      "opencode": {
        "enabled": true,
        "auto_start": true,
        "port": 9699
      }
    }
    ```

    Запускается только если `enabled: true` **и** `auto_start: true`.
    Требует установленного `opencode-ai`: `npm install -g opencode-ai`.

??? note "Детали MkDocs"

    **Управляется через `config.json`:**

    ```json
    {
      "docs_server": {
        "enabled": true,
        "port": 9697
      }
    }
    ```

    Последовательность действий:

    1. `Get-NetTCPConnection -LocalPort 9697` — если порт занят, убивает процесс (`Stop-Process`)
    2. **Если `site/` существует** — запускает `python -m http.server` прямо из папки `site/` (быстро, без пересборки)
    3. **Если `site/` нет** — сначала `mkdocs build`, затем `mkdocs serve` с hot-reload

    !!! info "Почему так"
        При наличии готовой статики пересборка не нужна — документация отдаётся мгновенно.
        `mkdocs serve` с hot-reload запускается только при первом запуске, когда `site/` ещё не собран.
        Чтобы принудительно пересобрать документацию, удалите папку `site/` перед запуском.

??? note "Детали llama.cpp"

    ### Проверка и установка бинарника

    При каждом запуске `start.ps1` вызывает `Ensure-LlamaBin`:

    1. Ищет файлы `llama-*-bin-win-*.zip` в директории `bin/`
    2. Берёт последний по имени (номер сборки растёт лексикографически)
    3. Читает установленную версию из `config.json` → `llama_cpp.bin_version`
    4. Если версия совпадает и `llama-server.exe` существует — пропускает
    5. Если найдена **новая версия** — спрашивает:

    ```
    📦 New llama.cpp version available!
       Installed : llama-b8000-bin-win-cpu-x64
       Available : llama-b8802-bin-win-cpu-x64
       Install now? [Y/n]
    ```

    При согласии (`Y` или Enter):
    - Удаляет старую директорию
    - Распаковывает zip в `bin/<version>/` (файлы из zip без корневой папки)
    - Обновляет `config.json` → `llama_cpp.bin_version`

    При отказе (`n`) — продолжает с уже установленным бинарником.

    ### Поиск llama-server.exe

    `_find_llama_server()` в Python ищет в следующем порядке:

    1. `LLAMA_SERVER_PATH` из `.env` (явный путь)
    2. `PATH` системы (`shutil.which`)
    3. `bin/<bin_version>/llama-server.exe` — **основной путь**, версия из `config.json`
    4. Любая поддиректория `bin/` (fallback, по убыванию имени)
    5. Стандартные места Windows (`C:/llama.cpp/`, `%LOCALAPPDATA%/llama.cpp/`)

    ### Автозапуск сервера

    Управляется через `config.json`:

    ```json
    {
      "llama_cpp": {
        "model_path": "~/.models/qwen2.5-0.5b-q4_k_m.gguf",
        "auto_start": true,
        "port": 9780
      }
    }
    ```

    При `auto_start: true`:

    1. Останавливает предыдущий процесс на порту
    2. Запускает `llama-server.exe` напрямую из `bin/<bin_version>/`
    3. Ждёт до 10 сек пока `/health` ответит 200
    4. При немедленном падении процесса — переизвлекает бинарник и повторяет (max 2 попытки)
    5. Экспортирует `LLAMA_BASE_URL=http://127.0.0.1:<port>/v1`

    !!! info "Версия бинарника в config.json"
        ```json
        {
          "llama_cpp": {
            "port": 9780,
            "host": "127.0.0.1",
            "bin_version": "llama-b8802-bin-win-cpu-x64"
          }
        }
        ```
        Поле `bin_version` обновляется автоматически при установке новой версии.
        Чтобы добавить новую версию — положите zip в `bin/` и перезапустите `start.ps1`.

??? note "Этап 7 — Остановка предыдущего экземпляра FastAPI"

    PID запущенного FastAPI сохраняется в `%TEMP%\fastapi-foundry.pid`.
    При следующем запуске `start.ps1` читает этот файл и завершает старый процесс
    перед стартом нового — порт не будет занят.

??? note "Этап 8 — run.py и FastAPI lifespan"

    `start.ps1` запускает `venv\Scripts\python.exe run.py` и ждёт завершения.

    `run.py` выполняет:

    1. Форсирует UTF-8 для stdout/stderr (важно на Windows)
    2. Загружает `.env` через `src/utils/env_processor`
    3. Импортирует `Config` singleton — читает `config.json` один раз
    4. Определяет порт FastAPI (фиксированный или автопоиск в диапазоне 9696–9796)
    5. Повторно ищет Foundry (на случай прямого запуска без `start.ps1`)
    6. Запускает Uvicorn

    После старта Uvicorn выполняется `lifespan` в `app.py`:

    ```python
    async with lifespan(app):
        await rag_system.initialize()          # загружает FAISS индекс
        if auto_load_default and default_model:
            subprocess foundry model load ...  # автозагрузка модели
        yield
        await foundry_client.close()           # закрытие aiohttp сессии
    ```

    ### Reloader (WatchFiles)

    В режиме `mode: dev` Uvicorn запускает **два процесса**:

    ```
    reloader process [33548] using WatchFiles   ← следит за изменениями *.py
    Started server process [33612]              ← фактический FastAPI сервер
    ```

    Это нормальное поведение. При сохранении любого `.py` файла worker перезапускается автоматически.

    Чтобы стартовые сообщения не печатались дважды, `run.py` использует флаг `_UVICORN_CHILD`.

    Для отключения reloader установите `mode: prod` в `config.json`.

---

## Остановка системы

### Остановить FastAPI сервер

```powershell
# Через stop.py (рекомендуется)
venv\Scripts\python.exe stop.py

# Или через stop_precise.py — точечная остановка по PID
venv\Scripts\python.exe stop_precise.py
```

### Остановить все сервисы

| Сервис | Команда |
|---|---|
| **FastAPI** | `venv\Scripts\python.exe stop.py` |
| **llama.cpp** | `python utils/port_manager.py --kill-port 9780` |
| **OpenCode** | `python utils/port_manager.py --kill-port 9699` |
| **MkDocs** | `python utils/port_manager.py --kill-port 9697` |
| **Foundry** | `foundry service stop` |

!!! warning "Foundry останавливается отдельно"
    `stop.py` не трогает Foundry — это внешний системный сервис Microsoft.
    Для его остановки используйте `foundry service stop` в терминале.

---

## Повторный запуск (restart)

Команда та же самая:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

`start.ps1` сам разберётся что остановить, что оставить и что запустить заново:

| Сервис | Уже запущен? | Действие |
|---|---|---|
| **FastAPI** (порт 9696) | да | убивает по `%TEMP%/fastapi-foundry.pid` → запускает новый |
| **MkDocs** (порт 9697) | да | убивает по порту → [site/ есть] http.server / [site/ нет] mkdocs build + serve |
| **llama.cpp** (порт 9780) | да | убивает по порту → запускает новый (только если `auto_start=true`) |
| **OpenCode** (порт 9699) | да | убивает по порту → запускает новый (только если `enabled=true` и `auto_start=true`) |
| **Foundry** | да | не трогает — только читает порт |
| **Foundry** | нет | запускает `foundry service start`, ждёт 20 сек |

!!! info "Foundry не перезапускается намеренно"
    Foundry — внешний системный сервис Microsoft. Его перезапуск выгрузил бы загруженную модель из памяти.
    `start.ps1` никогда не останавливает Foundry самостоятельно.

---

## Прямой запуск без start.ps1

!!! tip "Если Foundry уже запущен"
    ```powershell
    venv\Scripts\python.exe run.py
    ```
    `run.py` сам найдёт Foundry через `tasklist` + `netstat`.

---

## Параметры start.ps1

| Параметр | По умолчанию | Описание |
|---|---|---|
| `-Config` | `config.json` | Путь к файлу конфигурации |

```powershell
.\start.ps1 -Config config.prod.json
```

---

## Ключевые переменные окружения

!!! info "Актуальность"
    Таблица отражает текущее состояние. Правило проекта: **`.env` хранит только секреты**.
    Все пути, порты, флаги и настройки поведения — в `config.json`.
    Состав может меняться по мере развития проекта. Актуальный эталон — в [`.env.example`](https://github.com/hypo69/FastApiFoundry-Docker/blob/main/.env.example).

### Секреты — хранятся в `.env`

| Переменная | Описание |
|---|---|
| `HF_TOKEN` | Токен HuggingFace для закрытых моделей (Gemma, Llama, Mistral) |
| `API_KEY` | Ключ для защиты FastAPI эндпоинтов (optional) |
| `SECRET_KEY` | JWT секрет (optional) |
| `FOUNDRY_API_KEY` | Ключ Foundry API (optional) |
| `OPENAI_API_KEY` | Ключ OpenAI |
| `ANTHROPIC_API_KEY` | Ключ Anthropic |
| `GEMINI_API_KEY` | Ключ Google Gemini |
| `OPENROUTER_API_KEY` | Ключ OpenRouter |
| `MISTRAL_API_KEY` | Ключ Mistral |
| `GROQ_API_KEY` | Ключ Groq |
| `DEEPSEEK_API_KEY` | Ключ DeepSeek |
| `XAI_API_KEY` | Ключ xAI (Grok) |
| `GITHUB_PAT` | GitHub Personal Access Token |
| `SMTP_PASSWORD` | Пароль SMTP сервера |
| `REDIS_PASSWORD` | Пароль Redis |

### Служебные — выставляются `start.ps1` автоматически

Эти переменные **не нужно задавать вручную** — `start.ps1` выставляет их сам в процесс после обнаружения сервисов:

| Переменная | Кто выставляет | Описание |
|---|---|---|
| `FOUNDRY_BASE_URL` | `start.ps1` | Полный URL Foundry API |
| `FOUNDRY_DYNAMIC_PORT` | `start.ps1` | Порт, найденный автоматически |
| `LLAMA_BASE_URL` | `start.ps1` | URL llama.cpp после запуска |
| `LLAMA_SERVER_PATH` | `.env` (optional) | Явный путь к `llama-server.exe` |

### Настройки поведения — хранятся в `config.json`

| Параметр | Секция | Описание |
|---|---|---|
| `port`, `host` | `fastapi_server` | Порт и хост FastAPI |
| `mode` | `fastapi_server` | `dev` = hot-reload, `prod` = без reload |
| `auto_find_free_port`, `workers` | `fastapi_server` | Автопоиск порта, количество воркеров |
| `base_url`, `default_model`, `auto_load_default` | `foundry_ai` | URL, модель по умолчанию, автозагрузка |
| `temperature`, `max_tokens` | `foundry_ai` | Параметры генерации |
| `startup_model_mode`, `startup_custom_model` | `foundry_ai` | Режим загрузки модели при старте |
| `port`, `host`, `model_path`, `auto_start` | `llama_cpp` | Основные настройки llama.cpp |
| `models_dir`, `default_model` | `llama_cpp` | Директория GGUF моделей, модель по умолчанию |
| `models`, `rag`, `hf_models` | `directories` | Директории GGUF, RAG индексов, HuggingFace моделей |
| `enabled`, `index_dir`, `chunk_size` | `rag_system` | Настройки RAG |
| `level`, `file`, `max_bytes_mb`, `backup_count` | `logging` | Уровень, файл, ротация логов |
| `console`, `structured`, `errors_file` | `logging` | Вывод в консоль, JSONL логи, отдельный файл ошибок |
| `enabled`, `port` | `docs_server` | Запуск MkDocs при старте, порт |
| `max_loaded_models`, `ttl_seconds`, `max_ram_percent` | `model_manager` | Лимиты памяти и TTL для загруженных моделей |
| `language` | `app` | Язык интерфейса: `en` / `ru` / `he` |

---

# Консоль
### Детальный разбор вывода консоли при старте системы

При запуске `start.ps1` система проходит через несколько этапов подготовки окружения и запуска вспомогательных сервисов. Ниже приведен детальный разбор каждой строки лога.

```
(venv) PS D:\repos\public_repositories\FastApiFoundry-Docker> ./start
🚀 FastAPI Foundry Smart Launcher - Запуск
============================================================
🔄 Проверка обновлений...
   Текущая версия : v0.6.0
   Последний тег  : v0.5.0
✅ Версия актуальна (v0.5.0)
✅ venv активирован
⚙️ Loading .env variables...
  ✓ TELEGRAM_ADMIN_TOKEN = ***
  ✓ TELEGRAM_ADMIN_IDS =
  ✓ TELEGRAM_HELPDESK_TOKEN = ***
  ✓ GITHUB_PAT = ***
  ✓ API_KEY = ***
  ✓ SECRET_KEY = ***
  ✓ OPENAI_API_KEY = ***
  ✓ ANTHROPIC_API_KEY = ***
  ✓ HF_TOKEN = ***
  ✓ GEMINI_API_KEY = ***
  ✓ FOUNDRY_API_KEY = ***
  ✓ LLAMA_SERVER_PATH = ***
✅ Environment variables loaded: 12
🔍 Local Foundry check...
✅ API Foundry найден на порту 62376
✅ Foundry уже запущен на порту 62376
🔗 FOUNDRY_BASE_URL = http://localhost:62376/v1/
🔍 Проверка конфигурации сервера документации...
✅ Предыдущий MkDocs (PID: 32492) остановлен
📚 Сборка документации MkDocs...

 │  ⚠  Warning from the Material for MkDocs team
 │
 │  MkDocs 2.0, the underlying framework of Material for MkDocs,
 │  will introduce backward-incompatible changes, including:
 │
 │  × All plugins will stop working – the plugin system has been removed
 │  × All theme overrides will break – the theming system has been rewritten
 │  × No migration path exists – existing projects cannot be upgraded
 │  × Closed contribution model – community members can't report bugs
 │  × Currently unlicensed – unsuitable for production use
 │
 │  Our full analysis:
 │
 │  https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/

✅ Документация собрана
🚀 Запуск сервера MkDocs на порту 9697...
✅ Сервер MkDocs запущен на http://localhost:9697 (PID: 24992)
📦 Extracting llama-b8802-bin-win-cpu-x64.zip → bin/llama-b8802-bin-win-cpu-x64/ ...
✅ Extracted: D:\repos\public_repositories\FastApiFoundry-Docker\bin\llama-b8802-bin-win-cpu-x64
⚠️  Could not update config.json: Exception setting "bin_version": "The property 'bin_version' cannot be found on this object. Verify that the property exists and can be set."
💡 llama.cpp: no model_path set in config.json (skipping)
🐍 FastAPI server launch...
🔗 FOUNDRY_DYNAMIC_PORT = 62376
🌐 FastAPI Foundry starting...
📱 Веб-интерфейс будет доступен по адресу: http://localhost:9696
============================================================
💾 PID 8000 сохранён в C:\Users\onela\AppData\Local\Temp\fastapi-foundry.pid
INFO:     Will watch for changes in these directories: ['D:\\repos\\public_repositories\\FastApiFoundry-Docker']
INFO:     Uvicorn running on http://0.0.0.0:9696 (Press CTRL+C to quit)
INFO:     Started reloader process [21740] using WatchFiles
INFO:     Started server process [26552]
INFO:     Waiting for application startup.
12:18:08 | WARNING | fastapi-foundry | ⚠️ RAG index not found at C:\Users\onela\.aiassistant\rag\default_index\faiss.index, skipping load
⚠️ RAG system not initialized
INFO:     Application startup complete.

════════════════════════════════════════════════════════════

  ✅  FastAPI Foundry — startup complete
  🌐  http://localhost:9696

════════════════════════════════════════════════════════════

INFO:     127.0.0.1:51455 - "GET /api/v1/system/stats HTTP/1.1" 200 OK
INFO:     127.0.0.1:51455 - "GET /api/v1/hf/models HTTP/1.1" 200 OK
INFO:     127.0.0.1:51455 - "GET /api/v1/hf/models HTTP/1.1" 200 OK
INFO:     127.0.0.1:51454 - "GET /api/v1/foundry/models/loaded HTTP/1.1" 200 OK
INFO:     127.0.0.1:51455 - "GET /api/v1/foundry/models/loaded HTTP/1.1" 200 OK
INFO:     127.0.0.1:51460 - "GET /api/v1/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:51456 - "GET /api/v1/llama/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51455 - "GET /api/v1/llama/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51455 - "GET /api/v1/system/stats HTTP/1.1" 200 OK
INFO:     127.0.0.1:51460 - "GET /api/v1/hf/models HTTP/1.1" 200 OK
INFO:     127.0.0.1:51455 - "GET /api/v1/foundry/models/loaded HTTP/1.1" 200 OK
```

#### 1. Инициализация и проверка обновлений
*   **`(venv) PS D:\repos\public_repositories\FastApiFoundry-Docker> ./start`**: Это команда, которую вы вводите для запуска системы. `(venv)` указывает на то, что активировано виртуальное окружение Python, а `PS D:\repos\public_repositories\FastApiFoundry-Docker>` — это текущий рабочий каталог в PowerShell.
*   **`🚀 FastAPI Foundry Smart Launcher - Запуск`**: Приветственное сообщение скрипта-оркестратора `start.ps1`.

*   **`🔄 Проверка обновлений...`**: Запуск скрипта `Update-Project.ps1`. Он проверяет локальную версию в файле `VERSION` и сравнивает её с последними тегами (tags) в Git-репозитории.
*   **`Текущая версия : v0.6.0` / `Последний тег : v0.5.0`**: Информационные строки, показывающие состояние вашего кода относительно репозитория.
*   **`✅ Версия актуальна (v0.5.0)`**: Подтверждение того, что обновление не требуется.

#### 2. Подготовка окружения Python
*   **`✅ venv активирован`**: Скрипт успешно нашел и активировал виртуальное окружение Python в папке `venv`.
*   **`⚙️ Loading .env variables...`**: Начало процесса чтения файла `.env`.
*   **`✓ VARIABLE_NAME = ***`**: Успешная загрузка переменной окружения. Значения чувствительных данных (токены, ключи) маскируются символами `***` для безопасности.
*   **`✅ Environment variables loaded: 12`**: Резюме — общее количество загруженных настроек из файла `.env`.

#### 3. Обнаружение AI-бэкенда (Foundry Local)
*   **`🔍 Local Foundry check...`**: Система ищет запущенный процесс `Inference.Service.Agent` (Microsoft Foundry Local).
*   **`✅ API Foundry найден на порту 62376`**: Скрипт просканировал открытые порты процесса и нашел тот, который отвечает на запросы к API.
*   **`✅ Foundry уже запущен на порту 62376`**: Подтверждение, что сервис активен и не требует повторного запуска.
*   **`🔗 FOUNDRY_BASE_URL = http://localhost:62376/v1/`**: Динамический URL, который будет использоваться FastAPI сервером для связи с моделями.

#### 4. Сервер документации (MkDocs)
*   **`🔍 Проверка конфигурации сервера документации...`**: Чтение секции `docs_server` из `config.json`.
*   **`✅ Предыдущий MkDocs (PID: 32492) остановлен`**: Если порт документации (9697) был занят, скрипт завершил старый процесс, чтобы избежать конфликтов.
*   **`📚 Сборка документации MkDocs...`**: Запуск генерации статических HTML-страниц из Markdown-файлов папки `docs/`.
*   **Баннер предупреждения от Material for MkDocs:**
    ```
     │  ⚠  Warning from the Material for MkDocs team
     │
     │  MkDocs 2.0, the underlying framework of Material for MkDocs,
     │  will introduce backward-incompatible changes, including:
     │
     │  × All plugins will stop working – the plugin system has been removed
     │  × All theme overrides will break – the theming system has been rewritten
     │  × No migration path exists – existing projects cannot be upgraded
     │  × Closed contribution model – community members can't report bugs
     │  × Currently unlicensed – unsuitable for production use
     │
     │  Our full analysis:
     │
     │  https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/
    ```
    *   **Пояснение к предупреждению MkDocs:** Это сообщение является сатирическим баннером от разработчика темы Material for MkDocs (squidfunk). Оно не означает, что MkDocs 2.0 с такими радикальными изменениями действительно существует или планируется к выпуску в ближайшее время. Цель этого предупреждения — привлечь внимание к проблемам и медленному развитию основного фреймворка MkDocs, а также выразить обеспокоенность по поводу потенциальных будущих проблем с обратной совместимостью, если эти вопросы не будут решены. Это не влияет на текущую работу вашей документации с Material for MkDocs.
    *   **Как подавить этот баннер:** Чтобы скрыть это предупреждение, вы можете установить переменную окружения `NO_MKDOCS_2_WARNING` со значением `1` перед запуском скрипта. Например, в PowerShell:
        ```powershell
        $env:NO_MKDOCS_2_WARNING = "1"
        ./start
        ```
*   **`✅ Документация собрана`**: Процесс генерации файлов успешно завершен.
*   **`🚀 Запуск сервера MkDocs на порту 9697...`**: Запуск локального веб-сервера для просмотра документации.
*   **`✅ Сервер MkDocs запущен на http://localhost:9697 (PID: 24992)`**: Подтверждение запуска с указанием идентификатора процесса.

#### 5. Локальный инференс (llama.cpp)
*   **`📦 Extracting llama-b8802-bin-win-cpu-x64.zip → bin/llama-b8802-bin-win-cpu-x64/ ...`**: Скрипт обнаружил новый архив с бинарными файлами llama.cpp и автоматически распаковывает его для актуализации версии.
*   **`✅ Extracted: D:\repos\public_repositories\FastApiFoundry-Docker\bin\llama-b8802-bin-win-cpu-x64`**: Подтверждение успешной распаковки бинарных файлов.
*   **`⚠️ Could not update config.json: Exception setting "bin_version": "The property 'bin_version' cannot be found on this object. Verify that the property exists and can be set."`**: Системное предупреждение о том, что скрипту не удалось автоматически прописать версию бинарника в `config.json` (обычно из-за отсутствия нужного свойства в объекте конфигурации). Не критично.
*   **`💡 llama.cpp: no model_path set in config.json (skipping)`**: Скрипт не нашел путь к модели GGUF в настройках, поэтому пропустил запуск сервера `llama-server`.

#### 6. Запуск основного сервера FastAPI
*   **`🐍 FastAPI server launch...`**: Переход к финальному этапу — запуску приложения на Python.
*   **`🔗 FOUNDRY_DYNAMIC_PORT = 62376`**: Передача найденного порта Foundry в процесс Python.
*   **`🌐 FastAPI Foundry starting...`**: Старт приложения `run.py`.
*   **`📱 Веб-интерфейс будет доступен по адресу: http://localhost:9696`**: Информационное сообщение о том, по какому адресу будет доступен веб-интерфейс приложения.

*   **`💾 PID 8000 сохранён в C:\Users\onela\AppData\Local\Temp\fastapi-foundry.pid`**: Идентификатор процесса FastAPI записан во временный файл. Это нужно, чтобы при следующем запуске скрипт мог корректно остановить сервер.
*   **`INFO: Will watch for changes in these directories: ['D:\\repos\\public_repositories\\FastApiFoundry-Docker']`**: Сообщение от Uvicorn (движка сервера). В режиме `dev` система следит за изменениями в коде и автоматически перезагружается при сохранении файлов.
*   **`INFO: Uvicorn running on http://0.0.0.0:9696 (Press CTRL+C to quit)`**: Основное сообщение от Uvicorn, подтверждающее, что сервер запущен и доступен по указанному адресу.
*   **`INFO: Started reloader process [21740] using WatchFiles` / `INFO: Started server process [26552]`**: Запуск управляющего процесса и рабочего процесса сервера.

#### 7. Инициализация приложения (Lifespan)
*   **`INFO: Waiting for application startup.`**: Uvicorn ожидает завершения инициализации приложения FastAPI.
*   **`12:18:08 | WARNING | fastapi-foundry | ⚠️ RAG index not found at C:\Users\onela\.aiassistant\rag\default_index\faiss.index, skipping load`**: Система RAG (поиск по документам) попыталась загрузить индекс, но не нашла его по стандартному пути.
*   **`⚠️ RAG system not initialized`**: Предупреждение о том, что поиск по знаниям (RAG) пока недоступен (нужно собрать индекс во вкладке RAG).
*   
*   **`INFO: Application startup complete.`**: Сервер полностью готов к работе.
*   
*   **`════════════════════════════════════════════════════════════`**
*   
    **`✅ FastAPI Foundry — startup complete`**
    
    **`🌐 http://localhost:9696`**
    
    **`════════════════════════════════════════════════════════════`**

#### 8. Логи запросов (Runtime)
*   **`INFO: 127.0.0.1:51455 - "GET /api/v1/system/stats HTTP/1.1" 200 OK`**: Это логи в реальном времени. В данном случае мы видим, как фронтенд (веб-интерфейс) после открытия страницы начал опрашивать API для получения статистики системы, списка моделей и статуса сервисов. `200 OK` означает, что запрос был успешно обработан.

---


## Что дальше

- [Установка](installation.md) — первичная настройка, install.ps1
- [Работа с моделями](models_guide.md) — Foundry, HuggingFace, llama.cpp
- [Веб-интерфейс](web_interface.md) — описание всех вкладок
