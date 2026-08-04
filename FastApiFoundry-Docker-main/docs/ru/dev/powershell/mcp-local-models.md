# local_models_mcp.py

**Файл:** `mcp/src/servers/local_models_mcp.py`  
**Протокол:** MCP STDIO  
**Версия:** 0.6.1

## Назначение

Проксирует запросы от MCP клиентов (Claude Desktop и др.) к локальному FastAPI Foundry серверу на `localhost:9696`. Поддерживает все бэкенды оркестратора.

## Инструменты

| Инструмент | Endpoint | Описание |
|---|---|---|
| `generate` | `POST /api/v1/generate` | Генерация текста |
| `chat` | `POST /api/v1/ai/chat` | Чат с историей сессии |
| `list_models` | `GET /api/v1/models` | Список всех доступных моделей |
| `rag_search` | `POST /api/v1/rag/search` | Семантический поиск по RAG |
| `health` | `GET /api/v1/health` | Статус сервиса |

### Маршрутизация моделей

Передаётся в поле `model` инструментов `generate` и `chat`:

| Префикс | Бэкенд |
|---|---|
| без префикса | Foundry Local |
| `llama::path.gguf` | llama.cpp |
| `ollama::model-name` | Ollama |
| `hf::model-name` | HuggingFace |

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `FASTAPI_BASE_URL` | `http://localhost:9696` | URL FastAPI Foundry |
| `MCP_HTTP_TIMEOUT` | `120` | Таймаут HTTP запросов (сек) |

## Запуск

```powershell
venv\Scripts\python.exe mcp/src/servers/local_models_mcp.py
```

## Конфигурация Claude Desktop

```json
{
  "mcpServers": {
    "local-models": {
      "command": "C:/path/to/venv/Scripts/python.exe",
      "args": ["C:/path/to/mcp/src/servers/local_models_mcp.py"],
      "env": {
        "FASTAPI_BASE_URL": "http://localhost:9696"
      }
    }
  }
}
```
