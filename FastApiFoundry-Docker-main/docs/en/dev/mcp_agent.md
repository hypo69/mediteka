# MCP Agent — Foundry + Local MCP Servers

**Version:** 0.6.1

MCP Agent enables Foundry Local models to use your local MCP servers as tools (function calling). The agent automatically discovers all tools from `mcp-powershell-servers/settings.json` and exposes them to the model in OpenAI tools format.

---

## How It Works

```
User → POST /api/v1/agent/run (agent: "mcp")
                │
           McpAgent.run()
                │
      Foundry Local (function calling)
                │
      model selects tool_call
                │
 McpAgent._execute_tool("mcp__server__tool", args)
                │
      MCP STDIO server (pwsh / python)
                │
           tools/call → result
                │
      Foundry generates final answer
```

Tool naming: `mcp__<server_name>__<tool_name>`

Example: `mcp__powershell-stdio__run-script`, `mcp__local-models__generate_text`

---

## Quick Start

### 1. Run the agent

```bash
POST /api/v1/agent/run
Content-Type: application/json

{
  "agent": "mcp",
  "message": "List files in current directory",
  "model": "qwen3-0.6b-generic-cpu:4"
}
```

Response:
```json
{
  "success": true,
  "answer": "Current directory contains: run.py, config.json, ...",
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

### 2. List available tools

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

### 3. Refresh tool list

After starting new MCP servers or changing `settings.json`:

```bash
POST /api/v1/mcp-agent/refresh-tools
```

---

## API Reference

### `POST /api/v1/agent/run`

Run an agent. Use `"agent": "mcp"` for MCP agent.

| Field | Type | Default | Description |
|---|---|---|---|
| `message` | string | — | User query |
| `agent` | string | `"powershell"` | Agent name: `"mcp"` |
| `model` | string | from config.json | Foundry model ID |
| `temperature` | float | `0.7` | Generation temperature |
| `max_tokens` | int | `2048` | Max tokens |
| `max_iterations` | int | `5` | Max tool-call iterations |

---

### `GET /api/v1/mcp-agent/tools`

List all tools discovered from MCP servers.

**Response:**
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

Re-query all MCP servers via `tools/list`. Clears tool cache.

**Response:**
```json
{
  "success": true,
  "total": 8,
  "message": "Discovered 8 tool(s)"
}
```

---

### `GET /api/v1/mcp-agent/servers`

List servers with tool counts.

**Response:**
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

## Adding a New MCP Server

Add an entry to `mcp-powershell-servers/settings.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["./mcp-powershell-servers/src/servers/my_server.py"],
      "env": {
        "MY_API_KEY": "${MY_API_KEY}"
      },
      "description": "My custom MCP server"
    }
  }
}
```

Then refresh tools:
```bash
POST /api/v1/mcp-agent/refresh-tools
```

Server must implement MCP STDIO protocol: respond to `initialize` and `tools/list`.

---

## Architecture

```
src/agents/mcp_agent.py          — McpAgent (BaseAgent)
src/api/endpoints/
  mcp_agent_endpoints.py         — /mcp-agent/* endpoints
  agent.py                       — agent registry (includes "mcp")
mcp-powershell-servers/
  settings.json                  — MCP server configuration
  src/servers/
    McpSTDIOServer.v2.ps1        — PowerShell STDIO server
    local_models_mcp.py          — FastAPI Foundry MCP server
    huggingface_mcp.py           — HuggingFace MCP server
```

---

## Difference from PowerShell Agent

| | PowerShell Agent | MCP Agent |
|---|---|---|
| Tools | Fixed (run_powershell, run_wp_cli, http_get) | Dynamic — from all MCP servers |
| Adding tools | Change Python code | Add entry to settings.json |
| Servers | McpSTDIOServer + McpWPCLIServer | All servers from settings.json |
| Update | Restart server | POST /mcp-agent/refresh-tools |

---

## Example Requests

### PowerShell via MCP

```json
{
  "agent": "mcp",
  "message": "Check free space on C: drive",
  "model": "qwen3-0.6b-generic-cpu:4"
}
```

### Text generation via local-models MCP

```json
{
  "agent": "mcp",
  "message": "Use local-models server to generate a brief description of FastAPI",
  "model": "qwen3-0.6b-generic-cpu:4",
  "max_iterations": 3
}
```

### Search on HuggingFace

```json
{
  "agent": "mcp",
  "message": "Find top-5 models for text summarization on HuggingFace",
  "model": "qwen3-0.6b-generic-cpu:4"
}
```
