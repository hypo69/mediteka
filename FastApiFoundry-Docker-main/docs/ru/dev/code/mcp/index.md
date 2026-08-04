# MCP Servers

**Проект:** AI Assistant
**Автор:** hypo69
**Copyright:** © 2024 - 2026 hypo69
**Лицензия:** MIT

MCP (Model Context Protocol) серверы для интеграции с AI-клиентами (Claude Desktop, gemini-cli и др.).

Управляются через FastAPI Foundry REST API (`/api/v1/mcp-powershell/*`) или напрямую через `settings.json`.

---

## Структура

```
mcp/
├── src/
│   ├── servers/                   # Серверы
│   │   ├── McpSTDIOServer.ps1     # PowerShell STDIO (JSON-RPC 2.0)
│   │   ├── McpHttpsServer.ps1     # PowerShell HTTPS REST API
│   │   ├── McpWPCLIServer.ps1     # WordPress CLI
│   │   ├── McpHuggingFaceServer.ps1  # HuggingFace (PowerShell, устарело)
│   │   ├── local_models_mcp.py    # Локальные AI модели через FastAPI Foundry
│   │   ├── huggingface_mcp.py     # HuggingFace Inference API (Python)
│   │   └── ftp_mcp.py             # FTP операции
│   ├── config/                    # Конфигурации серверов
│   │   ├── Config-McpHTTPS.json
│   │   └── Config-McpWPCLI.json
│   └── clients/                   # Примеры клиентов
│       ├── python_client.py
│       ├── nodejs.js
│       └── powershell.ps1
├── settings.json                  # Реестр серверов
├── requirements.txt               # Python зависимости
└── Start-MCPServers.ps1           # Скрипт запуска всех серверов
```

---

## Серверы

### `local_models_mcp.py` — Локальные AI модели

Проксирует запросы к FastAPI Foundry (`http://localhost:9696`).

**Требования:** FastAPI Foundry должен быть запущен.

| Инструмент | Описание |
|---|---|
| `generate` | Генерация текста |
| `chat` | Чат с историей сессии |
| `list_models` | Список всех локальных моделей |
| `rag_search` | Поиск по RAG индексу |
| `health` | Статус сервиса |

Маршрутизация по префиксу модели:

| Префикс | Бэкенд |
|---|---|
| *(без префикса)* | Foundry Local (ONNX) |
| `llama::<path>` | llama.cpp |
| `ollama::<name>` | Ollama |
| `hf::<model_id>` | HuggingFace Transformers |

---

### `huggingface_mcp.py` — HuggingFace Inference API

Генерация текста через облачный HuggingFace API. Требует `HF_TOKEN` в `.env`.

| Инструмент | Описание |
|---|---|
| `text_generation` | Генерация текста через HuggingFace модель |

---

### `ftp_mcp.py` — FTP операции

Работа с FTP сервером. Требует `FTP_HOST`, `FTP_USER`, `FTP_PASSWORD` в `.env`.

| Инструмент | Описание |
|---|---|
| `ftp_list` | Список файлов в директории |
| `ftp_upload` | Загрузить файл на FTP |
| `ftp_download` | Скачать файл с FTP |
| `ftp_delete` | Удалить файл на FTP |
| `ftp_rename` | Переименовать / переместить файл |

---

### `docs_deploy_mcp.py` — Деплой документации

Загрузка собранной MkDocs документации (`site/`) на FTP.
Требует `FTP_*` и `FTP_DOCS_RU`, `FTP_DOCS_EN` в `.env`.

| Инструмент | Описание |
|---|---|
| `docs_deploy_ru` | Загрузить `site/ru/` на FTP (`FTP_DOCS_RU`) |
| `docs_deploy_en` | Загрузить `site/en/` на FTP (`FTP_DOCS_EN`) |
| `docs_deploy_all` | Загрузить оба языка |
| `docs_build_and_deploy` | `mkdocs build` + загрузка (парам: `lang`: `ru`/`en`/`all`) |
| `docs_status` | Проверить удалённые директории на FTP |

---

### `McpSTDIOServer.ps1` — PowerShell STDIO

Выполнение PowerShell команд и скриптов на локальной машине.

| Инструмент | Описание |
|---|---|
| `run-script` | Выполнить PowerShell скрипт |

---

### `McpHttpsServer.ps1` — PowerShell HTTPS

REST API для удалённого выполнения PowerShell команд. Порт: `8090`.

---

### `McpWPCLIServer.ps1` — WordPress CLI

Управление WordPress через WP-CLI.

---

## Быстрый старт

### Через FastAPI Foundry API

```bash
# Список серверов
GET /api/v1/mcp-powershell/servers

# Запустить сервер
POST /api/v1/mcp-powershell/servers/local-models/start

# Остановить сервер
POST /api/v1/mcp-powershell/servers/local-models/stop

# Статус
GET /api/v1/mcp-powershell/servers/local-models/status
```

### Через MCP агента

```json
POST /api/v1/agent/run
{
  "agent": "mcp",
  "message": "Сгенерируй описание FastAPI",
  "model": "qwen3-0.6b-generic-cpu:4"
}
```

### Вручную

```powershell
# PowerShell STDIO
pwsh -NoProfile -ExecutionPolicy Bypass -File ./mcp/src/servers/McpSTDIOServer.ps1

# Python серверы
python ./mcp/src/servers/local_models_mcp.py
python ./mcp/src/servers/ftp_mcp.py
```

---

## Конфигурация

Все серверы описаны в `mcp/settings.json`. Переменные окружения берутся из `.env` в корне проекта.

### Добавить новый сервер

1. Создать файл в `mcp/src/servers/`
2. Добавить запись в `mcp/settings.json`
3. Обновить инструменты MCP агента: `POST /api/v1/mcp-agent/refresh-tools`

---

## Переменные окружения

| Переменная | Сервер | Описание |
|---|---|---|
| `HF_TOKEN` | huggingface | Токен HuggingFace |
| `FTP_HOST` | ftp, docs-deploy | Хост FTP сервера |
| `FTP_USER` | ftp, docs-deploy | Логин FTP |
| `FTP_PASSWORD` | ftp, docs-deploy | Пароль FTP |
| `FTP_PORT` | ftp, docs-deploy | Порт FTP (default: 21) |
| `FTP_DOCS_RU` | docs-deploy | Удалённый путь для русской документации |
| `FTP_DOCS_EN` | docs-deploy | Удалённый путь для английской документации |
| `GITHUB_PAT` | github | GitHub Personal Access Token |
| `FASTAPI_BASE_URL` | local-models | URL FastAPI Foundry (default: http://localhost:9696) |

---

## Интеграция с Claude Desktop

Добавьте в `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "local-models": {
      "command": "python",
      "args": ["C:\\path\\to\\FastApiFoundry-Docker\\mcp\\src\\servers\\local_models_mcp.py"],
      "env": { "FASTAPI_BASE_URL": "http://localhost:9696" }
    },
    "powershell": {
      "command": "pwsh",
      "args": ["-File", "C:\\path\\to\\FastApiFoundry-Docker\\mcp\\src\\servers\\McpSTDIOServer.ps1"]
    },
    "ftp": {
      "command": "python",
      "args": ["C:\\path\\to\\FastApiFoundry-Docker\\mcp\\src\\servers\\ftp_mcp.py"],
      "env": {
        "FTP_HOST": "your-ftp-host",
        "FTP_USER": "your-user",
        "FTP_PASSWORD": "your-password"
      }
    }
  }
}
```

---

## Логи

| Сервер | Лог файл |
|---|---|
| `McpSTDIOServer.ps1` | `%TEMP%\mcp-powershell-server.log` |
| `local_models_mcp.py` | `%TEMP%\mcp-local-models.log` |
| `huggingface_mcp.py` | консоль |
| `ftp_mcp.py` | консоль |

---

## Python зависимости

```powershell
pip install -r mcp/requirements.txt
```
