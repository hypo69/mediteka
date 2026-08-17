# MCP Серверы проекта Mediteka (`.mcp/`)

В данной директории расположены локальные **MCP-серверы** (Model Context Protocol), построенные на базе библиотеки `FastMCP` (`mcp.server.fastmcp`) и Node.js. Они позволяют внешним агентам и LLM-клиентам (Claude Desktop, Cursor, Antigravity, VS Code и локальным скриптам) стандартизированно взаимодействовать с сервисами Mediteka.

---

## 📋 Список серверов

| Сервер | Файл | Описание | Основные инструменты (Tools) |
|---|---|---|---|
| **LangChain Media Agent** | [`langchain_mcp_server.py`](file:///c:/mediteka/.mcp/langchain_mcp_server.py) | Автономный поиск медиа (ReAct-агент, Playwright-трекеры, TMDb, стриминг) | `media_agent_search`, `media_search_torrents`, `media_get_metadata`, `media_get_streaming_sources`, `media_build_player_url`, `media_add_torrent_download` |
| **Gemini Search Grounding** | [`gemini_search_mcp_server.py`](file:///c:/mediteka/.mcp/gemini_search_mcp_server.py) | Прямой поиск Google с Grounding и автоматической ротацией пула API-ключей | `gemini_web_search`, `gemini_key_pool_status` |
| **Antigravity Search** | [`agy_search_mcp_server.py`](file:///c:/mediteka/.mcp/agy_search_mcp_server.py) | Агентный веб-поиск через встроенные инструменты Google Antigravity | `agy_web_search` |
| **FastAPI Client** | [`fastapi_mcp_server.py`](file:///c:/mediteka/.mcp/fastapi_mcp_server.py) | Интеграция с локальным FastAPI бэкендом | `fastapi_chat`, `fastapi_media_list`, `fastapi_qbittorrent_info` |
| **Unicorn Manager** | [`unicorn_mcp_server.py`](file:///c:/mediteka/.mcp/unicorn_mcp_server.py) | Управление процессами Uvicorn / Unicorn | `unicorn_start`, `unicorn_stop`, `unicorn_status` |
| **Auto-Commits Helper** | [`auto_commits.py`](file:///c:/mediteka/.mcp/auto_commits.py) | Автоматическое версионирование и коммиты при изменениях | Фоновый наблюдатель изменений файлов |
| **Playwright MCP** | [`playwright/`](file:///c:/mediteka/.mcp/playwright) | Node/Express оркестратор для прямого взаимодействия с браузером | Эндпоинты `POST /precommit`, `POST /apply` |

---

## 🚀 Запуск серверов

### 1. Gemini Search Grounding MCP Server (Python / FastMCP)
```bash
python .mcp/gemini_search_mcp_server.py
```

### 2. Antigravity Search MCP Server (Python / FastMCP)
```bash
python .mcp/agy_search_mcp_server.py
```

### 3. LangChain Media MCP Server (Python / FastMCP)
```bash
python .mcp/langchain_mcp_server.py
```

### 4. FastAPI Client MCP Server (Python / FastMCP)
```bash
python .mcp/fastapi_mcp_server.py
```

### 5. Unicorn Manager MCP Server (Python / FastMCP)
```bash
python .mcp/unicorn_mcp_server.py
```

---

## ⚙️ Подключение к MCP-клиентам (например, Claude Desktop / Cursor)

В файл конфигурации `claude_desktop_config.json` или `cursor-mcp.json`:

```json
{
  "mcpServers": {
    "mediteka-gemini-search": {
      "command": "C:\\mediteka\\venv\\Scripts\\python.exe",
      "args": ["C:\\mediteka\\.mcp\\gemini_search_mcp_server.py"]
    },
    "mediteka-agy-search": {
      "command": "C:\\mediteka\\venv\\Scripts\\python.exe",
      "args": ["C:\\mediteka\\.mcp\\agy_search_mcp_server.py"]
    },
    "mediteka-langchain": {
      "command": "C:\\mediteka\\venv\\Scripts\\python.exe",
      "args": ["C:\\mediteka\\.mcp\\langchain_mcp_server.py"]
    },
    "mediteka-fastapi": {
      "command": "C:\\mediteka\\venv\\Scripts\\python.exe",
      "args": ["C:\\mediteka\\.mcp\\fastapi_mcp_server.py"]
    },
    "mediteka-unicorn": {
      "command": "C:\\mediteka\\venv\\Scripts\\python.exe",
      "args": ["C:\\mediteka\\.mcp\\unicorn_mcp_server.py"]
    }
  }
}
```

---

## 🛡️ Стандарты разработки MCP-серверов
1. Все Python MCP-серверы используют единый стандартный стек: `from mcp.server.fastmcp import FastMCP`.
2. Логирование выполняется строго через `from src.logger import logger`.
3. Конфигурация считывается из `config.json` в корне проекта.
4. Отсутствие прямого использования `None` / `is None` в соответствии с `GEMINI.md`.
5. Все публичные инструменты оформлены через декоратор `@mcp.tool()` с явными тайпхинтами и docstring на русском языке.
