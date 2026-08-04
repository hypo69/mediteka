# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Microsoft Foundry Local SDK — Full Reference
# =============================================================================
# Description:
#   Complete description of Microsoft Foundry Local SDK capabilities:
#   model lifecycle management, chat interface, agent creation,
#   MCP server integration, streaming, and Azure migration path.
#
# File: README.md
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

# Microsoft Foundry Local SDK

## Install

```bash
pip install foundry-local-sdk
pip install agent-framework --pre   # for agents + MCP
```

## Core Concepts

| Concept | Description |
|---|---|
| `FoundryLocalManager` | Singleton — manages Foundry Local process lifecycle |
| `Configuration` | App-level config (name, model cache dir) |
| `model.load()` | Loads model into memory, starts local endpoint |
| `model.get_chat_client()` | Returns OpenAI-compatible client |
| `ChatAgent` | Microsoft Agent Framework — orchestrates tools + MCP |
| `StdioClientTransport` | Connects to local MCP server via stdin/stdout |

## Capabilities

### 1. Model Lifecycle
- Initialize Foundry Local manager
- List available models from catalog
- Download models from catalog
- Load / unload models
- Get model status

### 2. Chat Interface
- OpenAI-compatible chat client
- Streaming responses
- System prompts
- Temperature / max_tokens control
- Multi-turn conversation history

### 3. Agent Framework
- `ChatAgent` with tool use
- Automatic tool selection from user input
- Streaming agent responses
- Thread-based conversation state

### 4. MCP Integration
- Connect local MCP servers via `StdioClientTransport`
- Connect remote MCP servers via `SseClientTransport`
- Register MCP tools in agent
- Agent auto-calls MCP tools when needed

### 5. Azure Migration
- Same `ChatAgent` API works with Azure AI Foundry
- Swap `FoundryLocalManager` → `AzureAIClient`
- Local MCP servers need tunnel (ngrok) or remote deployment



# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: SDK Documentation — Microsoft Foundry Local SDK
# =============================================================================
# File: docs/microsoft_foundry_sdk.md
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

# Microsoft Foundry Local SDK — Документация

## Установка

```bash
pip install foundry-local-sdk
pip install agent-framework --pre   # для агентов
pip install mcp                     # для MCP
```

Foundry Local CLI (Windows):
```powershell
winget install Microsoft.FoundryLocal
```

---

## Архитектура

```
FoundryManager          — жизненный цикл моделей
    └── FoundryChat     — чат-интерфейс (OpenAI-compatible)
    └── FoundryAgent    — агент с инструментами (agent-framework)
            └── MCPConnector — подключение MCP серверов
                    ├── STDIO  — локальные серверы (PowerShell, Python)
                    └── SSE    — удалённые серверы (ngrok, Azure)
```

---

## FoundryManager

Управляет жизненным циклом моделей Foundry Local.

```python
from sdk.microsoft_foundry_sdk import FoundryManager

mgr = FoundryManager(app_name="my_app")
mgr.initialize()

# Список моделей в каталоге
models = mgr.list_models()
# [{"alias": "phi-4", "id": "...", "size": "...", "quantization": "..."}]

# Загрузить модель (скачает если нужно)
mgr.load_model("phi-4")

# Статус модели
status = mgr.get_model_status("phi-4")
# {"alias": "phi-4", "loaded": True, "endpoint_url": "http://localhost:50477/v1"}

# Выгрузить модель
mgr.unload_model("phi-4")

# Получить OpenAI-совместимый клиент
client = mgr.get_chat_client("phi-4")
```

---

## FoundryChat

Чат-интерфейс с историей диалога.

```python
from sdk.microsoft_foundry_sdk import FoundryManager, FoundryChat

mgr = FoundryManager()
mgr.initialize()
mgr.load_model("phi-4")
client = mgr.get_chat_client("phi-4")

chat = FoundryChat(
    client=client,
    model_id="phi-4",
    system_prompt="You are a helpful assistant.",
    temperature=0.7,
    max_tokens=2048,
)

# Одиночный запрос
response = chat.send("What is Python?")
# {"success": True, "content": "...", "model": "phi-4", "usage": {...}}

# Многоходовой диалог (история сохраняется автоматически)
chat.send("My name is Alex.")
r = chat.send("What is my name?")  # Знает имя из истории

# Стриминг
for chunk in chat.stream("Count from 1 to 5."):
    print(chunk, end="", flush=True)

# Очистить историю
chat.clear_history()

# Просмотр истории
print(chat.history)
```

---

## FoundryAgent

Агент с поддержкой инструментов (MCP и кастомных).

```python
import asyncio
from sdk.microsoft_foundry_sdk import FoundryAgent

async def main():
    async with FoundryAgent(
        base_url="http://localhost:50477/v1",
        model_id="phi-4",
        instructions="You are a helpful assistant.",
        tools=[...],  # MCP tool configs
    ) as agent:

        # Одиночный запрос
        response = await agent.run("What files are in the current directory?")
        print(response)

        # Стриминг
        async for chunk in agent.stream("Explain Python in 3 sentences."):
            print(chunk, end="", flush=True)

        # Новый тред (сброс истории)
        agent.new_thread()

asyncio.run(main())
```

---

## MCPConnector

Подключение MCP серверов к агенту.

### Локальный PowerShell STDIO сервер

```python
from sdk.microsoft_foundry_sdk import MCPConnector

connector = MCPConnector()

# PowerShell MCP сервер
ps_tool = connector.powershell_stdio_server(
    "mcp-powershell-servers/src/servers/McpSTDIOServer.ps1"
)

# Python MCP сервер
py_tool = connector.python_stdio_server(
    "mcp-powershell-servers/src/servers/huggingface_mcp.py"
)

# npx MCP сервер
fs_tool = connector.npx_server("@modelcontextprotocol/server-filesystem", "/path")
```

### Произвольный STDIO сервер

```python
tool = connector.build_stdio_params(
    command="pwsh",
    args=["-File", "my-server.ps1"],
    env={"MY_VAR": "value"},
)
```

### Удалённый SSE сервер (для Azure)

```python
remote_tool = connector.build_sse_params(
    url="https://xxxx.ngrok.io/mcp",
    headers={"Authorization": "Bearer token"},
)
```

### Инструкция по ngrok (миграция в Azure)

```python
print(connector.ngrok_tunnel_note())
```

---

## Полный пример: Агент + PowerShell MCP

```python
import asyncio
from sdk.microsoft_foundry_sdk import FoundryManager, FoundryAgent, MCPConnector

async def main():
    # Загрузить модель
    mgr = FoundryManager(app_name="demo")
    mgr.initialize()
    mgr.load_model("phi-4")

    # Настроить MCP
    connector = MCPConnector()
    ps_tool = connector.powershell_stdio_server(
        "mcp-powershell-servers/src/servers/McpSTDIOServer.ps1"
    )

    # Запустить агента
    async with FoundryAgent(
        base_url="http://localhost:50477/v1",
        model_id="phi-4",
        instructions="You are a helpful assistant with PowerShell tools.",
        tools=[ps_tool],
    ) as agent:
        response = await agent.run("What PowerShell version is installed?")
        print(response)

asyncio.run(main())
```

---

## Примеры

| Файл | Что демонстрирует |
|---|---|
| `examples/01_model_lifecycle.py` | Инициализация, каталог, load/unload |
| `examples/02_chat.py` | Чат, история, стриминг |
| `examples/03_agent_with_mcp.py` | Агент + PowerShell MCP STDIO |
| `examples/04_multiple_mcp_servers.py` | Несколько MCP серверов одновременно |
| `examples/05_remote_mcp_sse.py` | Удалённый MCP через SSE / ngrok |

---

## Наши MCP серверы

| Сервер | Тип | Назначение |
|---|---|---|
| `McpSTDIOServer.ps1` | PowerShell STDIO | Системные команды Windows |
| `McpHttpsServer.ps1` | PowerShell HTTPS | REST API для сетевых клиентов |
| `McpWPCLIServer.ps1` | PowerShell STDIO | WordPress CLI |
| `huggingface_mcp.py` | Python STDIO | HuggingFace Hub |

---

## Миграция в Azure AI Foundry

1. Замените `FoundryLocalManager` на `AzureAIClient`
2. Локальные STDIO серверы → туннель через ngrok или деплой как HTTP endpoint
3. Используйте `connector.build_sse_params(url=ngrok_url)` вместо `powershell_stdio_server()`
4. Логика агента (`FoundryAgent`) остаётся без изменений

