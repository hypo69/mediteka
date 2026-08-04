# AI Assistant (ai_assist) — Product Overview

**Version:** 0.7.1
**Project:** AI Assistant (ai_assist)

---

## Purpose

AI Assistant is a local AI model orchestrator with a rich REST API. It provides a single unified access point to multiple local AI backends — Microsoft Foundry Local, HuggingFace Transformers, llama.cpp, and Ollama — through a standardized REST API with an integrated RAG system, web interface, and MCP servers.

The core value proposition: any HTTP client (browser, Python script, Go app, Telegram bot, Claude Desktop via MCP) can interact with local AI models through one consistent API, regardless of which backend is running.

---

## Key Features

### AI Model Orchestration
- Single `/api/v1/generate` endpoint routes to the correct backend by model prefix
- Prefix routing: `foundry::`, `hf::`, `llama::`, `ollama::`
- Unified response shape across all backends: `{"success": bool, "content": str, "model": str, "usage": {...}}`
- Supported models: DeepSeek, Qwen, Mistral, Llama, Gemma and others

### Backends
- **Microsoft Foundry Local** — ONNX-based local inference, auto-discovery of running service port
- **HuggingFace Transformers** — PyTorch-based inference, supports Hub models and local cache
- **llama.cpp** — GGUF model inference on CPU/GPU via OpenAI-compatible HTTP API
- **Ollama** — Integration with locally running Ollama service

### RAG System
- FAISS vector index + SentenceTransformers embeddings
- Switchable profiles (multiple knowledge bases)
- Text extraction from 40+ formats: PDF, DOCX, XLSX, PPTX, HTML, images (OCR), ZIP/7z, source code
- Search cache for repeated queries
- Index integrity validation before load

### Web Interface (SPA)
- Bootstrap 5, Vanilla JS, no framework dependencies
- Tabs: Chat, Models, Foundry, HuggingFace, llama.cpp, Ollama, RAG, Agent, MCP, Logs, Settings, Editor, Docs
- i18n support: Russian, English, Hebrew (`data-i18n` attributes + locale JSON files)
- Real-time streaming via SSE

### MCP Servers
- Python STDIO servers: `local_models_mcp.py`, `huggingface_mcp.py`, `ftp_mcp.py`, `docs_deploy_mcp.py`
- PowerShell STDIO server: `McpSTDIOServer.ps1`
- PowerShell HTTPS server: `McpHttpsServer.ps1`
- Compatible with Claude Desktop and any MCP client

### Additional Capabilities
- Interactive chat with session history and SSE streaming
- Batch text generation
- API key security and CORS protection
- Health monitoring endpoints
- Telegram admin bot and HelpDesk bot
- GGUF → ONNX model converter
- AI agents: RAG agent, PowerShell agent, MCP agent, Google agent, recommender
- Model manager with LRU eviction, TTL, and RAM guard
- Docker support

---

## Target Users

- **Developers** building applications on top of local AI models
- **Researchers** experimenting with multiple local LLM backends
- **Teams** needing a self-hosted AI API without cloud dependencies
- **Power users** wanting a unified interface to manage Foundry, HuggingFace, llama.cpp, and Ollama

---

## Use Cases

| Use Case | How |
|---|---|
| Chat with local LLM | Web UI at `http://localhost:9696` or POST `/api/v1/chat/message` |
| Integrate AI into any app | Standard HTTP POST to `/api/v1/generate` |
| RAG over local documents | Index docs via `/api/v1/rag/build`, search via `/api/v1/rag/search` |
| Use with Claude Desktop | Configure MCP server pointing to `local_models_mcp.py` |
| Run in Docker | `docker-compose up` |
| Manage Foundry models | Web UI Foundry tab or `/api/v1/foundry/models` endpoints |
| Extract text from files | POST `/api/v1/rag/extract/file` (40+ formats) |
| Monitor service health | GET `/api/v1/health` |

---

## Access Points

| Client | Connection |
|---|---|
| Browser | `http://localhost:9696` |
| Python/PowerShell | `requests.post("http://localhost:9696/api/v1/generate", ...)` |
| Any language | Standard HTTP client |
| Claude Desktop | MCP STDIO server |
| Docker container | `http://host.docker.internal:9696/api/v1/generate` |
| Telegram | Built-in HelpDesk bot or custom via API |

---

## Ports

| Service | Port |
|---|---|
| FastAPI (main) | 9696 |
| MkDocs docs | 9697 |
| llama.cpp | 9780 |
| Docker mapped | 8000 |
| MCP HTTPS | 8090 |
| Foundry Local | auto-detected |
