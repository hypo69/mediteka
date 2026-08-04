# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: SDK Root — FastAPI Foundry + Microsoft Foundry Local
# =============================================================================
# File: sdk/README.md
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

# SDK — FastAPI Foundry

Два SDK в одном месте:

| SDK | Назначение |
|---|---|
| `microsoft_foundry_sdk/` | Обёртки над Microsoft Foundry Local SDK + Agent Framework + MCP |
| `fastapi_foundry_sdk/` | HTTP-клиент для нашего FastAPI Foundry сервера (порт 9696) |

---

## Установка

```bash
# Шаг 1: Microsoft Foundry Local SDK
pip install foundry-local-sdk

# Шаг 2: Agent Framework (для агентов)
pip install agent-framework --pre

# Шаг 3: MCP
pip install mcp

# Шаг 4: HTTP клиент
pip install aiohttp

# Всё сразу
pip install foundry-local-sdk agent-framework mcp aiohttp --pre
```

Foundry Local CLI (Windows):
```powershell
winget install Microsoft.FoundryLocal
```

Подробнее: [INSTALL.md](INSTALL.md)

| Пакет | Назначение |
|---|---|
| `foundry-local-sdk` | Microsoft Foundry Local SDK (manager, chat) |
| `agent-framework` | Microsoft Agent Framework (FoundryAgent + MCP tools) |
| `mcp` | Model Context Protocol (MCPConnector, MCPPowerShellClient) |

---

## microsoft_foundry_sdk

Обёртки над официальным `foundry-local-sdk` + `agent-framework`.

```
microsoft_foundry_sdk/
├── __init__.py          # Экспорты
├── manager.py           # FoundryManager — жизненный цикл моделей
├── chat.py              # FoundryChat — чат с историей и стримингом
├── agent.py             # FoundryAgent — агент с инструментами
├── mcp_connector.py     # MCPConnector — подключение MCP серверов
├── README.md            # Справочник по всем классам
└── examples/
    ├── 01_model_lifecycle.py    # Инициализация, каталог, load/unload
    ├── 02_chat.py               # Чат, история, стриминг
    ├── 03_agent_with_mcp.py     # Агент + PowerShell MCP STDIO
    ├── 04_multiple_mcp_servers.py  # Несколько MCP серверов
    └── 05_remote_mcp_sse.py     # Удалённый MCP через SSE / ngrok
```

### Быстрый старт

```python
import asyncio
from sdk.microsoft_foundry_sdk import FoundryManager, FoundryChat, FoundryAgent, MCPConnector

# --- Чат ---
mgr = FoundryManager(app_name="demo")
mgr.initialize()
mgr.load_model("phi-4")
client = mgr.get_chat_client("phi-4")

chat = FoundryChat(client, model_id="phi-4")
response = chat.send("What is Python?")
print(response["content"])

# --- Агент + MCP ---
async def run_agent():
    connector = MCPConnector()
    ps_tool = connector.powershell_stdio_server(
        "mcp-powershell-servers/src/servers/McpSTDIOServer.ps1"
    )
    async with FoundryAgent(
        base_url="http://localhost:50477/v1",
        model_id="phi-4",
        tools=[ps_tool],
    ) as agent:
        print(await agent.run("What PowerShell version is installed?"))

asyncio.run(run_agent())
```

---

## fastapi_foundry_sdk

HTTP-клиент для нашего FastAPI Foundry сервера.

```
fastapi_foundry_sdk/
├── __init__.py          # Экспорты
├── client.py            # FastAPIFoundryClient — все REST endpoints
├── mcp_client.py        # MCPPowerShellClient — прямой JSON-RPC к MCP серверам
└── examples/
    ├── demo_all.py      # Все возможности клиента
    └── demo_mcp.py      # Прямое подключение к PowerShell MCP серверу
```

### Быстрый старт

```python
import asyncio
from sdk.fastapi_foundry_sdk import FastAPIFoundryClient, MCPPowerShellClient

# --- REST API клиент ---
async def demo():
    async with FastAPIFoundryClient("http://localhost:9696") as client:
        health = await client.health()
        print(health["status"])

        response = await client.generate("What is Python?")
        print(response["content"])

        results = await client.rag_search("how to configure RAG", top_k=5)
        for r in results["results"]:
            print(r["source"], r["score"])

asyncio.run(demo())

# --- Прямой MCP клиент ---
async def demo_mcp():
    async with MCPPowerShellClient(
        "mcp-powershell-servers/src/servers/McpSTDIOServer.ps1"
    ) as mcp:
        tools = await mcp.list_tools()
        result = await mcp.call_tool(tools[0]["name"])
        print(result["content"])

asyncio.run(demo_mcp())
```

---

## Наши MCP серверы

| Сервер | Тип | Подключение |
|---|---|---|
| `McpSTDIOServer.ps1` | PowerShell STDIO | `connector.powershell_stdio_server(path)` |
| `McpHttpsServer.ps1` | PowerShell HTTPS | `connector.build_sse_params(url)` |
| `McpWPCLIServer.ps1` | PowerShell STDIO | `connector.powershell_stdio_server(path)` |
| `huggingface_mcp.py` | Python STDIO | `connector.python_stdio_server(path)` |

---

## Документация

- [INSTALL.md](INSTALL.md) — установка pip
- [docs/microsoft_foundry_sdk.md](docs/microsoft_foundry_sdk.md) — полная документация Microsoft Foundry SDK
- [microsoft_foundry_sdk/README.md](microsoft_foundry_sdk/README.md) — справочник классов

---

## Запуск примеров

```bash
# Запустить сервер
venv\Scripts\python.exe run.py

# Microsoft Foundry SDK примеры
python sdk/microsoft_foundry_sdk/examples/01_model_lifecycle.py
python sdk/microsoft_foundry_sdk/examples/02_chat.py
python sdk/microsoft_foundry_sdk/examples/03_agent_with_mcp.py

# FastAPI Foundry SDK примеры
python sdk/fastapi_foundry_sdk/examples/demo_all.py
python sdk/fastapi_foundry_sdk/examples/demo_mcp.py
```
