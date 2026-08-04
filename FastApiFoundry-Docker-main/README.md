![Version](https://img.shields.io/badge/version-0.8.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Docker-informational)
![Docker](https://img.shields.io/badge/Docker-supported-2496ED?logo=docker&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?logo=huggingface&logoColor=black)
![llama.cpp](https://img.shields.io/badge/llama.cpp-GGUF-8B5CF6)
![Ollama](https://img.shields.io/badge/Ollama-local-black?logo=ollama&logoColor=white)
![Microsoft Foundry](https://img.shields.io/badge/Microsoft_Foundry-Local-0078D4?logo=microsoft&logoColor=white)
![AI](https://img.shields.io/badge/AI-Orchestrator-FF6B35?logo=openai&logoColor=white)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/11ibP2Ys2eIbjb51t6ZXNyL0BKqy8sGQ_)


# Наш интеллектуальный помощник

![Coverage](docs/ru/assets/coverage.svg)

**Оркестратор локальных AI-моделей с богатым REST API**

`ai_assist` — универсальный оркестратор для локальных AI-моделей.
Единая точка доступа к Microsoft Foundry Local, HuggingFace Transformers, llama.cpp и Ollama
через стандартизированный REST API с интегрированной RAG-системой, веб-интерфейсом и MCP-серверами.

## Для нового участника проекта

Если вы ничего не знаете о проекте, начинайте отсюда:

| Что нужно понять | Где смотреть |
|---|---|
| Как запустить проект | `start.ps1`, раздел [Быстрый старт](#-быстрый-старт) |
| Что открывать в браузере | `http://localhost:9696` |
| Где FastAPI приложение | `src/api/app.py`, `src/api/endpoints/` |
| Где веб-интерфейс | `static/interface/index.html`, `static/interface/app.js`, `static/interface/partials/` |
| Где переводы интерфейса | `static/interface/locales/ru.json`, `en.json`, `he.json` |
| Где документация | `docs/ru/` и `mkdocs.yml` |
| Где конфигурация | `config.json`, `.env` |
| Где тесты | `tests/`, `check_engine/` |

Текущий главный сценарий: Windows + PowerShell + локальный FastAPI сервер. Docker поддерживается, но операционные скрипты проекта сейчас в основном ориентированы на Windows.

## Статус документации

Документация в проекте есть, но она пока не является полностью завершенной “единой системой знаний”.

Сейчас уже есть:

- `README.md` как входная точка для проекта.
- `docs/ru/` как основная MkDocs-документация.
- `docs/en/` как начатая английская ветка.
- `docs/ru/dev/code/` с автогенерируемыми/полуавтогенерируемыми описаниями кода.
- `static/interface/locales/*.json` для переводов веб-интерфейса через i18n.

Что важно: i18n веб-интерфейса и мультиязычная документация — это разные слои. Сейчас интерфейс уже переводится через JSON-словари, а документация собирается MkDocs из `docs/ru`. Следующий крупный шаг — привести документацию к той же дисциплине мультиязычности, но отдельным pipeline.

## Мультиязычность

Веб-интерфейс уже построен вокруг i18n:

- HTML partials используют `data-i18n`, `data-i18n-placeholder`, `data-i18n-title`.
- Переводы лежат в `static/interface/locales/`.
- Язык выбирается в UI и сохраняется в конфигурацию.
- RTL-направление включается для языков вроде иврита.

Правило для интерфейса: не писать пользовательские строки прямо в JS/HTML, если они видны пользователю. Новые строки должны получать ключ в локалях `ru`, `en`, `he`.

Для документации целевая схема другая:

- Markdown-документы должны жить по языковым деревьям: `docs/ru`, `docs/en`, далее `docs/he` и другие языки.
- Русский сейчас считается основным источником правды.
- Переводы документации должны генерироваться и обновляться автоматизированно, но проходить ручную проверку для важных страниц.
- Навигация MkDocs должна поддерживать языковые версии без копипасты всей конфигурации.

Рекомендуемый следующий инструмент для этого проекта: `mkdocs-static-i18n` поверх текущего `mkdocs-material`. Он хорошо ложится на существующий MkDocs, позволяет держать несколько языков рядом и не ломает текущую структуру. Для генерации черновиков переводов можно добавить отдельный скрипт, который берет Markdown из базового языка, переводит только текст, сохраняет кодовые блоки/ссылки/таблицы и пишет результат в соответствующее языковое дерево.

Пока это не внедрено полностью, любые изменения документации нужно делать минимум в `docs/ru/` и отмечать, какие страницы требуют перевода.

## WordPress-блоки и локальный источник контента

Для материалов, которые должны быть понятны пользователю “с первой страницы”, MkDocs не всегда лучший носитель. В проекте появился отдельный контур для поддерживаемых контентных блоков:

- источник данных хранится в репозитории: `content/blocks/*.json`;
- локальный FastAPI сервер отдает блок как JSON и как безопасный HTML;
- WordPress показывает этот материал через динамический Gutenberg-блок;
- обновление смысла происходит в JSON под версионным контролем, а WordPress остается редакционным слоем.

Первый блок:

| Блок | Источник | Локальный API | WordPress plugin |
|---|---|---|---|
| `dimitrieva` | `content/blocks/dimitrieva.json` | `/api/v1/content/blocks/dimitrieva` | `wordpress/fastapi-foundry-blocks` |

HTML-версия для WordPress:

```text
http://localhost:9696/api/v1/content/blocks/dimitrieva/html
```

Важно: `localhost` для WordPress означает машину, где запущен WordPress. Если WordPress и FastAPI Foundry работают на разных машинах, в настройках блока нужно указать доступный URL FastAPI сервера.

## ✨ Возможности

- 🎛️ **Оркестрация моделей** — единый API для Foundry, HuggingFace, llama.cpp, Ollama
- 🤖 **Генерация текста** через локальные AI модели (DeepSeek, Qwen, Mistral, Llama, Gemma)
- 💬 **Интерактивный чат** с поддержкой истории сессии и потоковой передачи (SSE)
- ⚙️ **Управление Foundry** — запуск, остановка и мониторинг через веб-интерфейс
- 🤗 **HuggingFace** — работа с моделями и inference Hub
- 🦙 **llama.cpp** — запуск GGUF моделей на CPU/GPU
- 🐋 **Ollama** — интеграция с локальным Ollama-сервисом
- 🔍 **RAG система** — векторный поиск по документации (FAISS + SentenceTransformers)
- 📄 **Извлечение текста** из 40+ форматов (PDF, DOCX, XLSX, изображения OCR, HTML, архивы)
- 📦 **Пакетная обработка** множественных запросов
- 🔐 **Безопасность** через API ключи и CORS защиту
- 📊 **Мониторинг** здоровья сервиса и моделей
- 🐳 **Docker** поддержка
- 🌐 **Веб-интерфейс** (SPA) для управления всеми компонентами
- 🔌 **MCP серверы** для STDIO (PowerShell), HTTP и других протоколов
- 🌍 **i18n** — интерфейс на русском, английском, иврите

## 🏗️ Архитектура оркестратора

```
Browser / API Client / MCP Client
              │ HTTP / SSE / WebSocket
              ▼
    AI Assistant (ai_assist)
       FastAPI — port 9696
              │
   ┌──────────┼──────────────┬──────────────┐
   ▼          ▼              ▼              ▼
Foundry   HuggingFace   llama.cpp       Ollama
Local     Transformers  (GGUF / CPU)    (local)
(ONNX)    (PyTorch)
              │
         ┌────┴────┐
         ▼         ▼
       FAISS     Text
       (RAG)   Extractor
              (40+ formats)
```

### Маршрутизация моделей

Оркестратор выбирает бэкенд по префиксу в поле `model`:

| Префикс | Бэкенд |
|---|---|
| `foundry::model-id` | Microsoft Foundry Local |
| `hf::model-id` | HuggingFace Transformers |
| `llama::path/to/model.gguf` | llama.cpp |
| `ollama::model-name` | Ollama |

Все бэкенды возвращают одинаковый формат ответа.
Без префикса — ошибка (устаревшие bare ID пробрасываются в Foundry с предупреждением).

## 🚀 Быстрый старт

```powershell
# Первый запуск — установит зависимости автоматически
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

После запуска интерфейс доступен по адресу: **http://localhost:9696**

## 📦 Релизы и CI/CD

Проект поддерживает автоматизированный цикл сборки и контроля качества:

1.  **Контроль качества (QA):** При каждом Pull Request запускается `Invoke-Qa.ps1` (линтеры, тесты, аудит безопасности).
2.  **Управление версиями:** Скрипт `scripts/New-Release.ps1` помогает поднять версию и создать Git-тег.
3.  **Автоматическая сборка:** При пуше тега `v*.*.*` GitHub Actions автоматически запускает сборку релизного архива.
4.  **Локальная сборка:** Скрипт `scripts/Build-Release.ps1` позволяет собрать ZIP-архив проекта вручную после прохождения всех проверок.

Подробности в документации: CI/CD и автоматизация

### Git Hooks
В проекте используются Git Hooks для предотвращения коммита некачественного кода. При запуске `Invoke-Qa.ps1` система автоматически предлагает установить хуки, которые будут проверять код перед каждым коммитом.

### Что происходит при запуске

`start.ps1` последовательно:

1. Проверяет `venv\` → если нет, запускает `install.ps1`
2. Загружает переменные из `.env`
3. Ищет запущенный Foundry → если не найден, запускает `foundry service start`
4. Опционально запускает MkDocs (`docs_server.enabled` в `config.json`)
5. Опционально запускает llama.cpp (если задан `llama_cpp.model_path`)
6. Запускает `venv\Scripts\python.exe run.py`

Подробный workflow: [Быстрый старт](docs/ru/user/getting_started.md)

### Запуск через Python (если Foundry уже запущен)

```powershell
venv\Scripts\python.exe run.py
```

### Docker

```powershell
docker-compose up
```

## 📁 Структура проекта

```
ai_assist/  (FastApiFoundry-Docker)
├── src/                    # Исходный код Python
│   ├── api/               # FastAPI: app.py, endpoints/
│   ├── models/            # AI клиенты: foundry, hf, llama, ollama
│   ├── rag/               # RAG система (FAISS + text extractor)
│   │   └── text_extractors/   # Экстракторы текста
│   │       ├── text_extractor_4_rag/  # 40+ форматов (PDF, DOCX, OCR...)
│   │       └── markitdown/    # Microsoft MarkItDown (Markdown-ориентированный)
│   ├── agents/            # AI агенты
│   ├── converter/         # GGUF → ONNX конвертер
│   └── utils/             # Утилиты (translator, logging, etc.)
├── static/                # Веб-интерфейс (SPA)
├── docs/                  # MkDocs документация
├── extensions/            # Браузерные расширения
├── mcp/                   # MCP серверы
│   └── src/servers/       #   local_models_mcp.py, huggingface_mcp.py, ftp_mcp.py, McpSTDIOServer.ps1
├── scripts/               # Операционные скрипты
├── scripts/Install/       # Скрипты установки
├── check_engine/          # Диагностика и тесты
├── sdk/                   # Python SDK (fastapi_foundry, microsoft_foundry)
├── bin/                   # Нативные бинарники (llama.cpp, Windows x64)
├── rag_index/             # FAISS индекс
├── logs/                  # Логи
├── start.ps1              # Точка входа (Windows)
├── run.py                 # Python точка входа
├── install.ps1            # Установщик
├── config.json            # Конфигурация
├── .env                   # Переменные окружения (секреты)
├── docker-compose.yml     # Docker
└── requirements.txt       # Python зависимости
```

## 🌐 Универсальный доступ: любой клиент, любая сеть

Наш интеллектуальный помощник — обычный HTTP-сервер с REST API. К нему подключается любая программа, умеющая делать HTTP-запросы:

| Клиент | Как подключается |
|---|---|
| Браузер | Встроенный веб-интерфейс на `http://localhost:9696` |
| Python / PowerShell скрипт | `requests.post("http://localhost:9696/api/v1/generate", ...)` |
| Go / Java / C++ / Rust / любой язык | Стандартный HTTP-клиент — `net/http`, `HttpClient`, `libcurl` |
| Telegram бот | Встроенный HelpDesk бот или свой через API |
| Браузерное расширение | Встроенное расширение-суммарайзер |
| Claude Desktop | Через MCP сервер (STDIO) |
| Любой другой MCP-клиент | Через MCP STDIO или HTTP протокол |
| Docker-контейнер | `http://host.docker.internal:9696/api/v1/generate` |

Сервер не привязан к языку или платформе клиента — если есть HTTP, есть доступ.

## 🔧 Технологии

| Компонент | Технология |
|---|---|
| Web framework | FastAPI + Uvicorn |
| AI: Foundry | Microsoft Foundry Local CLI (ONNX) |
| AI: HuggingFace | transformers + huggingface_hub (PyTorch) |
| AI: GGUF | llama.cpp (CPU/GPU) |
| AI: Ollama | Ollama HTTP API |
| RAG | FAISS + sentence-transformers |
| OCR | Tesseract + pytesseract + Pillow |
| PDF | pdfplumber + PyPDF2 |
| Office документы | python-docx + python-pptx + openpyxl |
| HTML/XML | BeautifulSoup4 + lxml |
| Контейнеризация | Docker |
| Язык | Python 3.11+ |

## ⚙️ Конфигурация

### Файлы настроек

| Файл | Назначение |
|---|---|
| `config.json` | Публичные настройки (порты, модели, RAG) |
| `.env` | Секреты (токены, ключи, пути) |
| `docker-compose.yml` | Docker настройки |

### Настройка .env

```powershell
Copy-Item .env.example .env
notepad .env
```

Ключевые переменные:

```env
# Foundry (если не определяется автоматически)
FOUNDRY_BASE_URL=http://localhost:50477/v1

# HuggingFace (для закрытых моделей: Gemma, Llama)
HF_TOKEN=hf_ваш_токен
HF_MODELS_DIR=D:\models

# llama.cpp (опционально)
LLAMA_MODEL_PATH=D:\models\qwen2.5-0.5b-q4_k_m.gguf
```

### Автозагрузка модели при старте

```json
{
  "foundry_ai": {
    "auto_load_default": true,
    "default_model": "qwen3-0.6b-generic-cpu:4"
  }
}
```

## 🗂️ Скачивание GGUF моделей

```powershell
pip install huggingface_hub
hf auth login
hf download bartowski/gemma-7b-it-GGUF --include "*Q4_K_M.gguf" --local-dir D:\models
```

| Квантование | Размер | Рекомендация |
|---|---|---|
| Q4_K_M | ~4–5 GB | Лучший баланс — по умолчанию |
| Q5_K_M | ~5–6 GB | Лучше качество при достаточной RAM |
| Q8_0 | ~8–9 GB | Максимальное качество |

## 🔍 Диагностика

```powershell
venv\Scripts\python.exe check_env.py
venv\Scripts\python.exe diagnose.py
venv\Scripts\python.exe check_engine\smoke_all_endpoints.py
```

## 📚 Документация

**Онлайн документация:** **https://davidka.net/ai_assist/site/**

| Раздел | Описание |
|---|---|
| [Быстрый старт](docs/ru/user/getting_started.md) | Запуск и startup workflow |
| [Установка](docs/ru/user/installation.md) | install.ps1, зависимости |
| [Работа с моделями](docs/ru/user/models_guide.md) | Foundry, HuggingFace, llama.cpp, Ollama |
| [Веб-интерфейс](docs/ru/user/web_interface.md) | Описание всех вкладок |
| [Архитектура](docs/ru/dev/architecture.md) | Структура кода, паттерны |
| [API Reference](docs/ru/dev/api_reference.md) | Все REST endpoints |
| [RAG система](docs/ru/dev/rag_system.md) | FAISS, индексация, поиск |
| [Агенты](docs/ru/dev/agents.md) | Создание AI агентов |
| [CI/CD](docs/ru/dev/cicd_docs.md) | GitHub Actions, MkDocs |

### План рефакторинга документации

1. Зафиксировать `docs/ru` как canonical source.
2. Подключить `mkdocs-static-i18n` и описать языки в `mkdocs.yml`.
3. Создать языковые деревья `docs/en` и `docs/he` с той же структурой URL.
4. Добавить скрипт генерации черновиков переводов Markdown.
5. Добавить проверку CI: битые ссылки, отсутствующие переводы, валидность MkDocs build.
6. Разделить документацию по аудиториям: пользователю, администратору, разработчику, тестеру (QA).
7. Синхронизировать документацию с новой верхней роль-ориентированной навигацией веб-интерфейса.

## 📞 Поддержка

- **Swagger UI**: http://localhost:9696/docs
- **Health Check**: http://localhost:9696/api/v1/health
- **GitHub**: https://github.com/hypo69/FastApiFoundry-Docker

## 📄 Лицензия

MIT License — https://opensource.org/licenses/MIT

---

**Наш интеллектуальный помощник (ai_assist) v0.8.0** | Python 3.11+ | Windows

