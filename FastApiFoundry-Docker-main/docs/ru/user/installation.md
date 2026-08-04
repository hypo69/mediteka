# Установка FastAPI Foundry

## Шаг 0 — Получить код проекта

Перед установкой нужно скачать или склонировать код проекта в нужную папку.

### Вариант A — через Git (рекомендуется)

**1. Откройте терминал в нужной папке**

Перейдите в проводнике в папку, где будет установлен проект, например `C:\Projects`.

!!! tip "Если установлен Windows Terminal или VS Code"
    ПКМ по папке в проводнике → **Открыть в терминале** (или **Open in Terminal**).
    Терминал откроется сразу в этой папке.

!!! tip "Если нет ничего — через поиск Windows"
    Нажмите `Win+R`, введите `powershell`, нажмите Enter.
    Затем в открывшемся окне перейдите в нужную папку:
    ```powershell
    cd C:\Projects
    ```

**2. Склонируйте репозиторий**

```powershell
git clone https://github.com/hypo69/FastApiFoundry-Docker.git
cd FastApiFoundry-Docker
```

!!! note "Если git не установлен"
    Проверьте: введите `git --version` в терминале. Если ошибка — установите:
    ```powershell
    winget install Git.Git
    ```
    После установки закройте и снова откройте терминал.

**3. Запустите установку**

```powershell
install.bat
```

Или через PowerShell напрямую:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

После установки запустите сервер:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

### Вариант B — скачать ZIP-архивом

Если git нет или нет доступа к GitHub:

1. Скачайте архив: **[https://davidka.net/ai_assist/aiassist.zip](https://davidka.net/ai_assist/aiassist.zip)**
2. Распакуйте в нужную папку (ПКМ по архиву → **Извлечь всё...**)
3. Откройте терминал в распакованной папке (любым способом из описанных выше)

!!! warning "Путь без кириллицы"
    Выбирайте папку без кириллицы в пути, например `C:\Projects\ai_assist`.
    Кириллица в пути может вызвать проблемы с `powershell.exe` и некоторыми зависимостями.

---

## Системные требования

- Windows 10/11
- Python 3.11+
- PowerShell 7+
- Интернет-соединение

### Производительность зависит от железа

AI модели — вычислительно тяжёлые программы. Чем мощнее железо, тем быстрее ответ.

| Конфигурация | Что работает | Скорость ответа |
|---|---|---|
| 8 GB RAM, без GPU | Малые модели (0.5–1.5B параметров) | 5–15 сек |
| 16 GB RAM, без GPU | Средние модели (3–7B параметров) | 15–60 сек |
| 16 GB RAM + GPU 8 GB VRAM | Средние модели с GPU-ускорением | 2–10 сек |
| 32 GB RAM + GPU 16+ GB VRAM | Большие модели (13–34B параметров) | 3–15 сек |

### RAG-индекс: размер и время построения

Размер индекса и время его построения зависят от количества проиндексированных документов и выбранной модели эмбеддингов.

!!! info "Что считается документом"
    Один документ ≈ один текстовый файл (`.md`, `.txt`, `.pdf` и т.д.).
    Каждый документ нарезается на чанки по ~1000 символов с перекрытием 50.
    Среднее количество чанков на документ: **5–15** (зависит от размера файла).

#### Размер индекса на диске

| Документов | Чанков (примерно) | `faiss.index` | `chunks.json` | Итого |
|---|---|---|---|---|
| 5 000 | ~40 000 | ~120 MB | ~80 MB | **~200 MB** |
| 50 000 | ~400 000 | ~1.2 GB | ~800 MB | **~2 GB** |
| 100 000 | ~800 000 | ~2.4 GB | ~1.6 GB | **~4 GB** |

!!! note "Размер зависит от модели эмбеддингов"
    - `all-mpnet-base-v2` — вектор 768 float32 = **3 KB на чанк** (рекомендуется)
    - `all-MiniLM-L6-v2` — вектор 384 float32 = **1.5 KB на чанк** (в 2 раза компактнее)

#### Время построения индекса

| Документов | CPU (без GPU) | Google Colab T4 GPU | Рекомендация |
|---|---|---|---|
| 5 000 | 10–30 мин | 1–3 мин | Локально или Colab |
| 50 000 | 2–5 часов | 15–40 мин | [Colab](https://colab.research.google.com/github/hypo69/FastApiFoundry-Docker/blob/master/notebooks%5Crag_colab.ipynb) |
| 100 000 | 5–12 часов | 30–90 мин | [Colab](https://colab.research.google.com/github/hypo69/FastApiFoundry-Docker/blob/master/notebooks%5Crag_colab.ipynb) |

!!! tip "Большие корпусы — строить в Colab"
    При 50 000+ документов локальное построение на CPU занимает часы.
    Google Colab предоставляет бесплатный GPU T4, который ускоряет процесс в 10–20 раз.
    Готовый индекс скачивается как `rag_index.zip` и распаковывается в `~/.aiassistant/rag/<profile>/`.

#### RAM при поиске (runtime)

Построенный индекс загружается в оперативную память целиком при старте сервера.

| Документов | RAM под индекс | Минимум RAM для сервера |
|---|---|---|
| 5 000 | ~200 MB | 8 GB |
| 50 000 | ~2 GB | 16 GB |
| 100 000 | ~4 GB | 32 GB |

!!! warning "Права администратора <span class='badge-red'>ВАЖНО</span>"
    Для полноценной установки и запуска рекомендуется запускать сессию PowerShell
    **от имени администратора**. Это необходимо для:

    - установки Foundry Local через `winget`
    - установки Tesseract OCR
    - регистрации задачи в Планировщике задач Windows
    - создания ярлыков на рабочем столе

    Без прав администратора установка завершится частично: venv и зависимости
    установятся, но Foundry, Tesseract и автозапуск — нет.

    Чтобы открыть PowerShell от администратора: `Win+X` → **Windows PowerShell (администратор)**
    или найдите `PowerShell` в поиске → ПКМ → **Запускать от имени администратора**.

---

## Два способа установки

| | `install.bat` | `install.ps1` |
|---|---|---|
| **Запуск** | Двойной клик | PowerShell |
| **Python** | Из `bin\Python-3.11.9`  | Из `bin\Python-3.11.9` |
| **Когда** | Первая установка, нет PS7 | Повторная установка, CI |

Оба варианта — только терминал, без браузера.

---

## Через install.bat (рекомендуется для первой установки)

```
install.bat
  ├─ Проверяет PowerShell 7+ (устанавливает через winget/curl/MSI если нет)
  └─ Запускает install.ps1 через pwsh.exe
```

Двойной клик по `install.bat` в проводнике.

---

## Через install.ps1 (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

### Параметры

| Параметр | Описание |
|---|---|
| `-Force` | Пересоздать venv (архивирует текущий `requirements.txt`) |
| `-SkipRag` | Пропустить RAG-зависимости (~3-5 GB) |
| `-SkipTesseract` | Пропустить установку Tesseract OCR |
| `-SkipLMStudio` | Пропустить проверку и установку LM Studio |

### Что делает install.ps1

```
install.ps1
  ├─ [PS < 7] → ошибка, выход
  ├─ [python не найден]
  │     ├─ [bin\Python-3.11.9.zip есть] → распаковать
  │     └─ [нет] → ошибка, выход
  ├─ [venv есть + -Force] → архивировать requirements.txt, удалить venv
  ├─ [venv нет] → создать venv
  ├─ pip install -r requirements.txt          ← основной стек
  ├─ [опциональные зависимости — интерактивно]
  │     ├─ requirements-qa.txt?      (y/N)    ← pytest, ruff, mypy, httpx
  │     ├─ requirements-google.txt?  (y/N)    ← Google Workspace / GoogleAgent
  │     ├─ docs/requirements.txt?    (y/N)    ← MkDocs плагины
  │     └─ mcp/requirements.txt?    (y/N)    ← Python MCP серверы
  ├─ [-SkipRag?] → пропустить sentence-transformers / faiss-cpu
  ├─ [-SkipTesseract?] → пропустить install-tesseract.ps1
  ├─ [.env нет] → скопировать .env.example
  ├─ [logs/ нет] → создать logs/
  ├─ [llama zip найден] → распаковать в bin/, записать LLAMA_SERVER_PATH в .env
  ├─ [foundry не установлен]
  │     ├─ [winget есть] → интерактивно: winget install Microsoft.FoundryLocal
  │     └─ [winget нет] → сообщение с ручной ссылкой
  ├─ [LM Studio не установлен] → интерактивно: install\Install-LMStudio.ps1
  ├─ [первая установка] → интерактивно: загрузить модели по умолчанию
  └─ создать ярлыки на рабочем столе
```

### LM Studio

`install.ps1` вызывает отдельный скрипт `install\Install-LMStudio.ps1`.
Он сначала ищет CLI `lms` в PATH и стандартных путях пользователя. Если LM Studio
не найден, установщик задаёт вопрос:

```text
Install LM Studio now? (y/N)
```

При ответе `y` запускается официальная команда LM Studio для Windows:

```powershell
irm https://lmstudio.ai/install.ps1 | iex
```

!!! warning "Что такое irm"
    `irm` — стандартный alias PowerShell для `Invoke-RestMethod`. Он скачивает
    HTTP/HTTPS содержимое. Официальная команда LM Studio использует `irm`, чтобы
    скачать bootstrap-скрипт установки, а `iex` выполняет его.

    Если `irm` или `Invoke-RestMethod` недоступны, шаг установки LM Studio
    останавливается с объяснением. Основной `install.ps1` записывает ошибку
    в install-log и продолжает установку остальных компонентов.

После установки LM Studio провайдер доступен в оркестраторе как:

```json
{
  "model": "lmstudio::<model-key>"
}
```

Например:

```powershell
Invoke-RestMethod http://localhost:9696/api/v1/lmstudio/status
Invoke-RestMethod http://localhost:9696/api/v1/chat/message -Method POST -ContentType 'application/json' -Body '{"session_id":"...","message":"Привет","model":"lmstudio::google/gemma-4-e4b"}'
```

Лог установки пишется в:

```text
logs/aiassistant-install.log
```

После запуска FastAPI этот файл доступен в интерфейсе:
**Logs** → выбор файла `aiassistant-install.log`.

---

## Ручная установка (CLI)

Для автоматизации или Docker:

```powershell
# 1. Создать venv
python -m venv venv

# 2. Установить зависимости
venv\Scripts\pip.exe install -r requirements.txt

# 3. Создать .env
Copy-Item .env.example .env
notepad .env

# 4. Установить Foundry (опционально)
winget install Microsoft.FoundryLocal

# 5. Запустить
.\start.ps1
```

---

## Настройка .env

После установки отредактируйте `.env`:

```env
# Foundry (определяется автоматически если пусто)
FOUNDRY_BASE_URL=http://localhost:50477/v1

# HuggingFace (для закрытых моделей: Gemma, Llama)
HF_TOKEN=hf_ваш_токен
HF_MODELS_DIR=D:\models

# llama.cpp (опционально)
LLAMA_MODEL_PATH=D:\models\model.gguf
LLAMA_AUTO_START=false
```

Или через мастер настройки:

```powershell
.\install\setup-env.ps1
```

---

## Tesseract OCR

Нужен для OCR изображений при RAG-индексации (PNG, JPG, TIFF, изображения в PDF).

```powershell
# Автоматически
.\install\install-tesseract.ps1

# Или вручную
winget install UB-Mannheim.TesseractOCR
```

После установки `install-tesseract.ps1` добавляет в `config.json`:

```json
{
  "text_extractor": {
    "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
  }
}
```

Без Tesseract: изображения пропускаются при индексации, всё остальное работает нормально.

---

## Скрипты директории install/

Директория `install/` содержит вспомогательные скрипты для первичной настройки.
`install.ps1` вызывает их автоматически, но каждый можно запустить отдельно.

| Скрипт | Назначение |
|---|---|
| `install-foundry.ps1` | Установка Microsoft Foundry Local через `winget`, запуск сервиса, загрузка модели по умолчанию |
| `Install-LMStudio.ps1` | Проверка и установка LM Studio через официальную команду `irm https://lmstudio.ai/install.ps1 \| iex` |
| `install-models.ps1` | Загрузка моделей: Foundry (qwen2.5-0.5b), HuggingFace (all-MiniLM-L6-v2), выбор GGUF для llama.cpp |
| `install-huggingface-cli.ps1` | Установка `huggingface_hub`, `transformers`, `accelerate`; авторизация через `HF_TOKEN` |
| `install-tesseract.ps1` | Загрузка и тихая установка Tesseract OCR 5.x, добавление в PATH, запись пути в `config.json` |
| `install-shortcuts.ps1` | Создание ярлыков на рабочем столе: «AI Assistant» и «AI Assistant (Silent)» |
| `install-autostart.ps1` | Регистрация задачи в Планировщике Windows (`AtLogOn`), удаление через `-Uninstall` |
| `setup-env.ps1` | Интерактивный мастер создания `.env`: GitHub, API-ключи, Foundry URL, среда |
| `_setup_env.py` | Python-хелпер: создаёт `.env` из `.env.example` если файл отсутствует |
| `make-ico.ps1` | Конвертация PNG-иконок из `assets/icons/` в `icon.ico` для ярлыков |

### Примеры запуска

```powershell
# Установить только Foundry (если пропустили при первой установке)
.\install\install-foundry.ps1

# Скачать модели интерактивно
.\install\install-models.ps1

# Установить HuggingFace CLI и авторизоваться
.\install\install-huggingface-cli.ps1

# Установить Tesseract OCR
.\install\install-tesseract.ps1

# Установить LM Studio
.\install\Install-LMStudio.ps1

# Создать ярлыки на рабочем столе
.\install\install-shortcuts.ps1

# Настроить .env интерактивно
.\install\setup-env.ps1

# Настроить .env с автогенерацией ключей
.\install\setup-env.ps1 -GenerateKeys

# Зарегистрировать автозапуск
.\install\install-autostart.ps1

# Удалить автозапуск
.\install\install-autostart.ps1 -Uninstall
```

### Параметры скриптов

**install-foundry.ps1**

| Параметр | По умолчанию | Описание |
|---|---|---|
| `-Model` | `qwen3-0.6b-generic-cpu:4` | Модель для загрузки после установки |

**install-models.ps1**

| Параметр | Описание |
|---|---|
| `-SkipFoundry` | Пропустить загрузку модели Foundry |
| `-SkipHuggingFace` | Пропустить загрузку модели HuggingFace |
| `-SkipLlama` | Пропустить выбор GGUF модели для llama.cpp |

**install-huggingface-cli.ps1**

| Параметр | Описание |
|---|---|
| `-Token` | HuggingFace токен (иначе читается из `.env`) |
| `-SkipAuth` | Только установка пакетов, без авторизации |
| `-SkipInstall` | Только авторизация, без установки пакетов |

**install-tesseract.ps1**

| Параметр | Описание |
|---|---|
| `-ConfigFile` | Путь к `config.json` (по умолчанию — в корне проекта) |
| `-Force` | Переустановить даже если Tesseract уже установлен |
| `-SkipIfExists` | Пропустить загрузку если `tesseract.exe` уже найден |

**Install-LMStudio.ps1**

| Параметр | Описание |
|---|---|
| `-SkipIfExists` | Завершить без действий, если `lms` уже найден |
| `-DiagnosticsOnly` | Только проверить наличие LM Studio, без установки |
| `-AssumeYes` | Не задавать вопрос и сразу запускать официальный установщик |

**setup-env.ps1**

| Параметр | Описание |
|---|---|
| `-Force` | Перезаписать существующий `.env` без подтверждения |
| `-GenerateKeys` | Автоматически сгенерировать `API_KEY` и `SECRET_KEY` |

---

## Файлы зависимостей

| Файл | Назначение | Установка |
|---|---|---|
| `requirements.txt` | Основной стек: FastAPI, RAG, ML, PDF, OCR, Telegram, MkDocs | Автоматически при установке |
| `requirements-qa.txt` | Инструменты тестирования и QA: pytest, ruff, mypy, httpx, coverage | Интерактивно при установке (y/N) |
| `requirements-google.txt` | Google Workspace интеграция (GoogleAgent) | Интерактивно при установке (y/N) |
| `docs/requirements.txt` | MkDocs плагины (только для сборки документации) | Интерактивно при установке (y/N) |
| `mcp/requirements.txt` | Зависимости Python MCP серверов | Интерактивно при установке (y/N) |

`install.ps1` автоматически устанавливает `requirements.txt`, затем для каждого из остальных файлов задаёт вопрос `(y/N)`. Если файл отсутствует в проекте — шаг пропускается автоматически.

Установить вручную в любой момент:

```powershell
# QA / тестирование
venv\Scripts\pip.exe install -r requirements-qa.txt

# Google Workspace
venv\Scripts\pip.exe install -r requirements-google.txt

# MkDocs плагины
venv\Scripts\pip.exe install -r docs/requirements.txt

# MCP серверы
venv\Scripts\pip.exe install -r mcp/requirements.txt
```

---

## Директории, создаваемые при установке

После выполнения `install.ps1` в корне проекта появятся:

```
FastApiFoundry-Docker/
├── venv/                        # Python виртуальное окружение
│   ├── Scripts/
│   │   ├── python.exe           # Интерпретатор
│   │   ├── pip.exe
│   │   └── Activate.ps1
│   └── .first_install_done      # Маркер первой установки
│
├── logs/                        # Логи приложения (шаг 7)
│   ├── fastapi-foundry.log      # Основной лог FastAPI
│   ├── aiassistant-install.log  # Лог install.ps1 и install\Install-*.ps1 шагов
│   ├── autostart.log            # Лог автозапуска (при использовании планировщика)
│   └── helpdesk_dialogs.jsonl   # Диалоги Telegram HelpDesk бота
│
├── rag_index/                   # FAISS индекс (создаётся при первой индексации)
│   ├── faiss.index
│   └── chunks.json
│
├── archive/                     # Архив ротированных логов (создаётся автоматически)
│
└── bin/                         # Бинарные файлы
    ├── Python-3.11.9/           # Локальный Python (портативная версия)
    └── llama-bXXXX-bin-win-x64/ # Распакованный сервер llama.cpp
```

### Глобальные директории (в профиле пользователя `~ / %USERPROFILE%`)

Система хранит тяжелые данные вне папки проекта для удобства обновлений:

*   `~/.models/` — Основное хранилище для GGUF моделей (**llama.cpp**).
*   `~/.foundry/` — Кэш и данные моделей **Microsoft Foundry Local**.
*   `~/.lmstudio/` — CLI, кэш и локальные данные **LM Studio**.
*   `~/.cache/huggingface/hub/` — Стандартный кэш моделей **HuggingFace**.
*   `~/.aiassistant/rag/` — Индексы и чанки **RAG** (разбиты по профилям).
*   `~/.hf_models/` — Альтернативный путь для HF моделей (если задан в `config.json`).

### Временные файлы

*   `%TEMP%\fastapi-foundry.pid` — PID запущенного процесса сервера.
*   `%TEMP%\mcp-stdio-server.log` — Логи серверов MCP.
*   `install\.installer.pid` — PID временного сервера установщика.

!!! note "Директории создаются лениво"
    `rag_index/`, `archive/` и `~/.aiassistant/rag/` создаются не при установке, а при
    первом использовании соответствующей функции. Если RAG не используется — эти директории
    не появятся.

!!! tip "Изменить расположение моделей HuggingFace"
    По умолчанию модели кэшируются в `~/.cache/huggingface/hub/` и могут занять
    десятки гигабайт. Чтобы перенести на другой диск, задайте в `.env`:
    ```env
    HF_MODELS_DIR=D:\models
    ```

---

## Автозапуск при входе в Windows

### Как это работает

```
Вход пользователя
  └─ Планировщик задач Windows (AtLogOn)
       └─ autostart.ps1 (скрыто, без окна)
            └─ start.ps1 (весь вывод → logs/autostart.log)
                 └─ FastAPI сервер на http://localhost:9696
```

`autostart.ps1` — обёртка над `start.ps1`:
- запускает его через `powershell.exe -NonInteractive -NoProfile -WindowStyle Hidden`
- перехватывает stdout/stderr, очищает ANSI-коды, пишет в `logs/autostart.log`
- опционально устанавливает PowerShell 7 из `bin/PowerShell-7.4.6-win-x64.msi` если не найден

### Регистрация в Планировщике задач (Task Scheduler)

Требует запуска от имени администратора:

```powershell
# Установить автозапуск
powershell -ExecutionPolicy Bypass -File .\install\install-autostart.ps1

# Удалить автозапуск
powershell -ExecutionPolicy Bypass -File .\install\install-autostart.ps1 -Uninstall
```

Что регистрирует `install-autostart.ps1`:

| Параметр | Значение |
|---|---|
| Имя задачи | `FastApiFoundry-Autostart` |
| Триггер | `AtLogOn` — при входе любого пользователя |
| Уровень прав | `RunLevel Highest` (администратор) |
| Окно | Скрыто (`-WindowStyle Hidden`) |
| Перезапуски | 3 попытки с интервалом 1 минута |
| Лимит времени | Без ограничений |
| Лог | `logs/autostart.log` |

### Ручная регистрация через Task Scheduler GUI

Если скрипт недоступен или нужна ручная настройка:

!!! tip "Шаг 1 — Открыть Планировщик задач"
    `Win+R` → `taskschd.msc` → Enter

!!! tip "Шаг 2 — Создать задачу"
    В правой панели: **Создать задачу** (не «Создать простую задачу»)

    На вкладке **Общие**:

    - Имя: `FastApiFoundry-Autostart`
    - Установить флаг **Выполнять с наивысшими правами**
    - Настроить для: `Windows 10`

!!! tip "Шаг 3 — Триггер"
    Вкладка **Триггеры** → **Создать**:

    - Начать задачу: **При входе в систему**
    - Любой пользователь (или конкретный)
    - Нажать **ОК**

!!! tip "Шаг 4 — Действие"
    Вкладка **Действия** → **Создать**:

    - Действие: **Запуск программы**
    - Программа: `powershell.exe`
    - Аргументы:

    ```
    -NonInteractive -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\path\to\FastApiFoundry-Docker\autostart.ps1"
    ```

    - Рабочая папка: `C:\path\to\FastApiFoundry-Docker`

    !!! warning "Укажите полный путь"
        Замените `C:\path\to\FastApiFoundry-Docker` на реальный путь к папке проекта.
        Путь не должен содержать кириллицу — это ограничение `powershell.exe`.

!!! tip "Шаг 5 — Параметры"
    Вкладка **Параметры**:

    - Установить флаг **Если задача завершилась с ошибкой, перезапустить через**: 1 минута, до 3 раз
    - Снять флаг **Останавливать задачу, выполняющуюся дольше**
    - Нажать **ОК**

!!! success "Проверка"
    ```powershell
    # Просмотреть зарегистрированную задачу
    Get-ScheduledTask -TaskName 'FastApiFoundry-Autostart'

    # Запустить вручную для теста (без перезагрузки)
    Start-ScheduledTask -TaskName 'FastApiFoundry-Autostart'

    # Проверить лог запуска
    Get-Content logs\autostart.log -Tail 30

    # Убедиться что сервер поднялся
    curl http://localhost:9696/api/v1/health
    ```

### Ярлыки на рабочем столе

`install.ps1` создаёт два ярлыка на рабочем столе:

| Ярлык | Скрипт | Окно |
|---|---|---|
| **AI Assistant** | `start.ps1` | Видимое окно PowerShell |
| **AI Assistant (Silent)** | `autostart.ps1` | Скрытое окно, без консоли |

Создать ярлыки вручную:

```powershell
powershell -ExecutionPolicy Bypass -File .\install\install-shortcuts.ps1
```

### Проверка автозапуска

```powershell
# Просмотреть задачу в планировщике
Get-ScheduledTask -TaskName 'FastApiFoundry-Autostart'

# Просмотреть лог запуска
Get-Content logs\autostart.log -Tail 30

# Запустить задачу вручную (для теста)
Start-ScheduledTask -TaskName 'FastApiFoundry-Autostart'
```

### Остановка всех сервисов

В silent mode нет видимого окна — для остановки используйте `stop.ps1`:

```powershell
# Остановить FastAPI, llama.cpp, MkDocs
powershell -ExecutionPolicy Bypass -File .\stop.ps1

# То же + остановить Foundry Local
powershell -ExecutionPolicy Bypass -File .\stop.ps1 -StopFoundry
```

`stop.ps1` останавливает по порядку:

| Шаг | Сервис | Метод |
|---|---|---|
| 1 | FastAPI (9696) | PID-файл `%TEMP%\fastapi-foundry.pid`, затем по порту |
| 2 | llama.cpp (9780) | По порту из `config.json` |
| 3 | MkDocs (9697) | По порту из `config.json` |
| 4 | Foundry Local | Только с `-StopFoundry` |

!!! warning "Foundry не останавливается по умолчанию"
    Foundry — системный сервис Microsoft. Его остановка выгрузит загруженную модель из памяти.
    Используйте `-StopFoundry` осознанно.

---

## Проверка установки

```powershell
venv\Scripts\python.exe check_env.py
venv\Scripts\python.exe diagnose.py
.\start.ps1
```

После запуска:

- Веб-интерфейс: http://localhost:9696
- Swagger UI: http://localhost:9696/docs
- Health check: http://localhost:9696/api/v1/health

---

## Как «учить» ассистента (База знаний)

Чтобы ассистент помогал вам в работе, ему нужно дать доступ к вашим знаниям: документам, архивам или заметкам. В программе это называется **RAG** (Retrieval-Augmented Generation). 

Если объяснять просто: это **«экзамен с открытой книгой»**. Без этой функции нейросеть полагается только на те знания, которые в неё заложили разработчики при создании. С функцией «обучения» ассистент, получив ваш вопрос, сначала быстро пролистывает вашу «библиотеку» документов, находит нужные страницы и на их основе формулирует точный ответ. Ваши данные при этом никуда не отправляются и остаются только на вашем компьютере.

### Что можно использовать как источник знаний?

Вы можете указать ассистенту путь к целой папке на диске или загрузить отдельные файлы. Система умеет «читать» практически всё:

*   **Офисные документы**: Все форматы Word, Excel и PowerPoint (включая старые версии `.doc` и `.xls`).
*   **PDF и сканы**: Программа не только читает обычные PDF, но и умеет распознавать текст на картинках или отсканированных документах (через встроенный модуль Tesseract).
*   **Архивы**: Если у вас много документов, просто упакуйте их в `.zip`, `.rar` или `.7z` — ассистент сам всё распакует и проиндексирует.
*   **Текстовые заметки**: Обычные текстовые файлы (`.txt`), файлы Markdown (`.md`) или электронные письма (`.eml`, `.msg`).
*   **Интернет-страницы и видео**: Вы можете просто дать ссылку на веб-сайт или YouTube-ролик. Ассистент извлечёт текст со страницы или «послушает» видео и превратит его в базу знаний.
*   **Аудиозаписи**: Диктофонные записи, протоколы встреч или лекции в форматах `.mp3`, `.wav`, `.m4a` будут автоматически расшифрованы в текст и добавлены в память.
*   **Код**: Если вы программист, ассистент поймёт структуру более чем 40 языков программирования.

### Как добавить данные?

1.  **Директория (папка)**: В интерфейсе программы во вкладке **RAG** можно указать путь к любой папке на вашем компьютере (например, `C:\Мои_Документы\Проекты`). Программа просканирует все вложенные папки.
2.  **Отдельные файлы**: Вы можете загружать файлы по одному через веб-интерфейс или просто отправить их в Telegram-бот (если настроен Admin Bot), и они автоматически попадут в обработку.

!!! tip "Подсказка"
    После того как вы указали папку или загрузили новые файлы, не забудьте нажать кнопку **Rebuild Index** (Пересобрать индекс). Это заставит ассистента «прочитать» новинки и обновить свою память.
