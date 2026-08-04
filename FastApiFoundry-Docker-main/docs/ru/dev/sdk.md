# SDK — Microsoft Foundry Local + FastAPI Foundry

В директории `sdk/` проекта находятся два SDK:

| SDK | Назначение |
|---|---|
| `microsoft_foundry_sdk/` | Обёртки над Microsoft Foundry Local SDK + Agent Framework + MCP |
| `fastapi_foundry_sdk/` | HTTP-клиент для FastAPI Foundry сервера (порт 9696) |

---

## Установка

```bash
# Microsoft Foundry Local SDK
pip install foundry-local-sdk

# Microsoft Agent Framework (для агентов с инструментами)
pip install agent-framework --pre

# Model Context Protocol
pip install mcp

# Всё сразу
pip install foundry-local-sdk agent-framework mcp --pre
```

| Пакет | Назначение |
|---|---|
| `foundry-local-sdk` | Microsoft Foundry Local SDK (manager, chat) |
| `agent-framework` | Microsoft Agent Framework (FoundryAgent + MCP tools) |
| `mcp` | Model Context Protocol (MCPConnector, MCPPowerShellClient) |

Foundry Local CLI (Windows):

```powershell
winget install Microsoft.FoundryLocal
```

---

## microsoft_foundry_sdk

Обёртки над официальным `foundry-local-sdk` и `agent-framework`.

### Структура

```
sdk/microsoft_foundry_sdk/
├── manager.py        — FoundryManager: жизненный цикл моделей
├── chat.py           — FoundryChat: чат с историей и стримингом
├── agent.py          — FoundryAgent: агент с инструментами (agent-framework)
├── mcp_connector.py  — MCPConnector: подключение MCP серверов
└── examples/
    ├── 01_model_lifecycle.py     — инициализация, каталог, load/unload
    ├── 02_chat.py                — чат, история, стриминг
    ├── 03_agent_with_mcp.py      — агент + PowerShell MCP STDIO
    ├── 04_multiple_mcp_servers.py — несколько MCP серверов
    └── 05_remote_mcp_sse.py      — удалённый MCP через SSE / ngrok
```

### FoundryManager

Управляет жизненным циклом моделей Foundry Local.

```python
from sdk.microsoft_foundry_sdk import FoundryManager

mgr = FoundryManager(app_name="my_app")
mgr.initialize()

models = mgr.list_models()
# [{"alias": "phi-4", "id": "...", "size": "...", "quantization": "..."}]

mgr.load_model("phi-4")

status = mgr.get_model_status("phi-4")
# {"alias": "phi-4", "loaded": True, "endpoint_url": "http://localhost:50477/v1"}

client = mgr.get_chat_client("phi-4")  # OpenAI-совместимый клиент

mgr.unload_model("phi-4")
```

### FoundryChat

Чат-интерфейс с историей диалога и стримингом.

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
r = chat.send("What is my name?")  # знает имя из истории

# Стриминг
for chunk in chat.stream("Count from 1 to 5."):
    print(chunk, end="", flush=True)

# Очистить историю
chat.clear_history()
```

### FoundryAgent

Агент с поддержкой инструментов через Microsoft Agent Framework.

```python
import asyncio
from sdk.microsoft_foundry_sdk import FoundryAgent, MCPConnector

async def main():
    connector = MCPConnector()
    ps_tool = connector.powershell_stdio_server(
        "mcp-powershell-servers/src/servers/McpSTDIOServer.ps1"
    )

    async with FoundryAgent(
        base_url="http://localhost:50477/v1",
        model_id="phi-4",
        instructions="You are a helpful assistant with PowerShell tools.",
        tools=[ps_tool],
    ) as agent:

        # Одиночный запрос
        response = await agent.run("What PowerShell version is installed?")
        print(response)

        # Стриминг
        async for chunk in agent.stream("List files in current directory."):
            print(chunk, end="", flush=True)

        # Новый тред (сброс истории)
        agent.new_thread()

asyncio.run(main())
```

### MCPConnector

Подключение MCP серверов к агенту.

```python
from sdk.microsoft_foundry_sdk import MCPConnector

connector = MCPConnector()

# PowerShell STDIO сервер (локальный)
ps_tool = connector.powershell_stdio_server(
    "mcp-powershell-servers/src/servers/McpSTDIOServer.ps1"
)

# Python STDIO сервер (локальный)
hf_tool = connector.python_stdio_server(
    "mcp-powershell-servers/src/servers/huggingface_mcp.py"
)

# npx сервер
fs_tool = connector.npx_server("@modelcontextprotocol/server-filesystem", "/path")

# Удалённый SSE сервер (для Azure / ngrok)
remote_tool = connector.build_sse_params(
    url="https://xxxx.ngrok.io/mcp",
    headers={"Authorization": "Bearer token"},
)

# Инструкция по ngrok
print(connector.ngrok_tunnel_note())
```

---

## fastapi_foundry_sdk

HTTP-клиент для нашего FastAPI Foundry сервера (порт 9696).

### Структура

```
sdk/fastapi_foundry_sdk/
├── client.py      — FastAPIFoundryClient: все REST endpoints
├── mcp_client.py  — MCPPowerShellClient: прямой JSON-RPC к MCP серверам
└── examples/
    ├── demo_all.py  — все возможности клиента
    └── demo_mcp.py  — прямое подключение к McpSTDIOServer.ps1
```

### FastAPIFoundryClient

Покрывает все endpoints сервера: health, generate, batch, RAG, config, HuggingFace, llama.cpp, Ollama, agent, MCP.

```python
import asyncio
from sdk.fastapi_foundry_sdk import FastAPIFoundryClient

async def main():
    async with FastAPIFoundryClient("http://localhost:9696") as client:

        # Health
        health = await client.health()
        # {"status": "healthy", "foundry_status": "healthy", "rag_status": "enabled"}

        # Generate (Foundry / HF / llama / Ollama)
        r = await client.generate("What is Python?", temperature=0.5, max_tokens=100)
        print(r["content"])

        # Generate с RAG контекстом
        r = await client.generate("How to configure RAG?", use_rag=True)

        # Batch generate
        batch = await client.batch_generate(
            ["What is FastAPI?", "What is FAISS?"],
            max_tokens=80,
        )

        # RAG поиск
        results = await client.rag_search("how to start server", top_k=5)

        # HuggingFace
        await client.hf_load_model("Qwen/Qwen2.5-0.5B-Instruct")
        r = await client.hf_generate("Hello", model_id="Qwen/Qwen2.5-0.5B-Instruct")

        # llama.cpp
        await client.llama_start("D:/models/model.gguf")
        r = await client.llama_generate("Hello", max_tokens=100)

        # Ollama
        models = await client.ollama_models()
        r = await client.ollama_generate("Hello", model="qwen2.5:0.5b")

        # Config
        cfg = await client.get_config()
        await client.patch_config({"foundry_ai.temperature": 0.5})

        # Agent
        result = await client.agent_run("List running processes", agent_type="powershell")

        # MCP
        status = await client.mcp_status()
        result = await client.mcp_execute("powershell-stdio", "run_powershell", {"command": "Get-Date"})

asyncio.run(main())
```

### MCPPowerShellClient

Прямой JSON-RPC 2.0 клиент для PowerShell MCP STDIO серверов.

```python
import asyncio
from sdk.fastapi_foundry_sdk import MCPPowerShellClient

async def main():
    async with MCPPowerShellClient(
        "mcp-powershell-servers/src/servers/McpSTDIOServer.ps1"
    ) as mcp:

        # Список инструментов
        tools = await mcp.list_tools()
        for tool in tools:
            print(f"{tool['name']}: {tool['description']}")

        # Вызов инструмента
        result = await mcp.call_tool("run_powershell", {"command": "Get-Date"})
        print(result["content"])

        # Список ресурсов
        resources = await mcp.list_resources()

        # Чтение ресурса
        content = await mcp.read_resource("file:///path/to/resource")

asyncio.run(main())
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

## Миграция в Azure AI Foundry

1. Замените `FoundryLocalManager` на `AzureAIClient`
2. Локальные STDIO серверы → туннель через ngrok или деплой как HTTP endpoint
3. Используйте `connector.build_sse_params(url=ngrok_url)` вместо `powershell_stdio_server()`
4. Логика агента (`FoundryAgent`) остаётся без изменений

```python
# Локально
ps_tool = connector.powershell_stdio_server("McpSTDIOServer.ps1")

# В Azure (через ngrok)
ps_tool = connector.build_sse_params("https://xxxx.ngrok.io/mcp")
```

---

## Запуск примеров

```bash
# Запустить сервер
venv\Scripts\python.exe run.py

# Microsoft Foundry SDK
python sdk/microsoft_foundry_sdk/examples/01_model_lifecycle.py
python sdk/microsoft_foundry_sdk/examples/02_chat.py
python sdk/microsoft_foundry_sdk/examples/03_agent_with_mcp.py
python sdk/microsoft_foundry_sdk/examples/04_multiple_mcp_servers.py
python sdk/microsoft_foundry_sdk/examples/05_remote_mcp_sse.py

# FastAPI Foundry SDK
python sdk/fastapi_foundry_sdk/examples/demo_all.py
python sdk/fastapi_foundry_sdk/examples/demo_mcp.py
```
