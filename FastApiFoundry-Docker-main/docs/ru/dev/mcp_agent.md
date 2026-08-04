# MCP Agent — Foundry + локальные MCP серверы

**Версия:** 0.6.1

mcp Agent позволяет модели Foundry Local использовать ваши локальные MCP серверы как инструменты (function calling). Агент автоматически обнаруживает все инструменты из `mcp/settings.json` и передаёт их модели в формате OpenAI tools.

---

## Как это работает

```
Пользователь → POST /api/v1/agent/run (agent: "mcp")
                        │
                   McpAgent.run()
                        │
              Foundry Local (function calling)
                        │
              model выбирает tool_call
                        │
         McpAgent._execute_tool("mcp__server__tool", args)
                        │
              MCP STDIO server (pwsh / python)
                        │
                   tools/call → результат
                        │
              Foundry формирует финальный ответ
```

Именование инструментов: `mcp__<server_name>__<tool_name>`

Пример: `mcp__powershell-stdio__run-script`, `mcp__local-models__generate_text`

---

## Быстрый старт

### 1. Запустить агента

```bash
POST /api/v1/agent/run
Content-Type: application/json

{
  "agent": "mcp",
  "message": "Покажи список файлов в текущей директории",
  "model": "qwen3-0.6b-generic-cpu:4"
}
```

Ответ:
```json
{
  "success": true,
  "answer": "В текущей директории находятся: run.py, config.json, ...",
  "tool_calls": [
    {
      "tool": "mcp__powershell-stdio__run-script",
      "arguments": {"script": "Get-ChildItem"},
      "result": "Mode  LastWriteTime  Name\n..."
    }
  ],
  "iterations": 2,
  "agent": "mcp"
}
```

### 2. Посмотреть доступные инструменты

```bash
GET /api/v1/mcp-agent/tools
```

```json
{
  "success": true,
  "total": 8,
  "tools": [
    {
      "name": "mcp__powershell-stdio__run-script",
      "server": "powershell-stdio",
      "mcp_tool": "run-script",
      "description": "[MCP:powershell-stdio] Run a PowerShell script"
    }
  ]
}
```

### 3. Обновить список инструментов

После запуска новых MCP серверов или изменения `settings.json`:

```bash
POST /api/v1/mcp-agent/refresh-tools
```

---

## API Reference

### `POST /api/v1/agent/run`

Запустить агента. Используйте `"agent": "mcp"` для MCP агента.

| Поле | Тип | По умолчанию | Описание |
|---|---|---|---|
| `message` | string | — | Запрос пользователя |
| `agent` | string | `"powershell"` | Имя агента: `"mcp"` |
| `model` | string | из config.json | ID модели Foundry |
| `temperature` | float | `0.7` | Температура генерации |
| `max_tokens` | int | `2048` | Максимум токенов |
| `max_iterations` | int | `5` | Максимум итераций tool-call |

---

### `GET /api/v1/mcp-agent/tools`

Список всех инструментов, обнаруженных у MCP серверов.

**Ответ:**
```json
{
  "success": true,
  "total": 8,
  "tools": [
    {
      "name": "mcp__powershell-stdio__run-script",
      "server": "powershell-stdio",
      "mcp_tool": "run-script",
      "description": "[MCP:powershell-stdio] Run a PowerShell script"
    }
  ]
}
```

---

### `POST /api/v1/mcp-agent/refresh-tools`

Повторно опросить все MCP серверы через `tools/list`. Сбрасывает кэш инструментов.

**Ответ:**
```json
{
  "success": true,
  "total": 8,
  "message": "Discovered 8 tool(s)"
}
```

---

### `GET /api/v1/mcp-agent/servers`

Список серверов с количеством инструментов.

**Ответ:**
```json
{
  "success": true,
  "servers": [
    {"name": "powershell-stdio", "tool_count": 3},
    {"name": "local-models", "tool_count": 2},
    {"name": "huggingface", "tool_count": 1}
  ]
}
```

---

## Добавление нового MCP сервера

Добавьте запись в `mcp/settings.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["./mcp/src/servers/my_server.py"],
      "env": {
        "MY_API_KEY": "${MY_API_KEY}"
      },
      "description": "Мой кастомный MCP сервер"
    }
  }
}
```

Затем обновите инструменты:
```bash
POST /api/v1/mcp-agent/refresh-tools
```

Сервер должен реализовывать MCP STDIO протокол: отвечать на `initialize` и `tools/list`.

---

## Архитектура

```
src/agents/mcp_agent.py          — McpAgent (BaseAgent)
src/api/endpoints/
  mcp_agent_endpoints.py         — /mcp-agent/* endpoints
  agent.py                       — реестр агентов (включает "mcp")
mcp/
  settings.json                  — конфигурация MCP серверов
  src/servers/
    McpSTDIOServer.ps1           — PowerShell STDIO сервер
    local_models_mcp.py          — FastAPI Foundry MCP сервер
    huggingface_mcp.py           — HuggingFace MCP сервер
    ftp_mcp.py                   — FTP MCP сервер
```

---

## Отличие от PowerShell агента

| | PowerShell агент | MCP агент |
|---|---|---|
| Инструменты | Фиксированные (run_powershell, run_wp_cli, http_get) | Динамические — из всех MCP серверов |
| Добавление инструментов | Изменение кода Python | Добавление записи в settings.json |
| Серверы | McpSTDIOServer + McpWPCLIServer | Все серверы из settings.json |
| Обновление | Перезапуск сервера | POST /mcp-agent/refresh-tools |

---

## Примеры запросов

### PowerShell через MCP

```json
{
  "agent": "mcp",
  "message": "Проверь свободное место на диске C:",
  "model": "qwen3-0.6b-generic-cpu:4"
}
```

### Генерация текста через local-models MCP

```json
{
  "agent": "mcp",
  "message": "Используй local-models сервер чтобы сгенерировать краткое описание FastAPI",
  "model": "qwen3-0.6b-generic-cpu:4",
  "max_iterations": 3
}
```

### Поиск на HuggingFace

```json
{
  "agent": "mcp",
  "message": "Найди топ-5 моделей для суммаризации текста на HuggingFace",
  "model": "qwen3-0.6b-generic-cpu:4"
}
```
