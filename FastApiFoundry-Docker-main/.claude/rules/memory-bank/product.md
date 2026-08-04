# FastAPI Foundry — Product Overview

## Purpose
FastAPI Foundry is a REST API server that provides a unified interface for running and interacting with local AI models. It bridges multiple AI backends (Microsoft Foundry Local, HuggingFace Transformers, llama.cpp, Ollama) through a single FastAPI service with an integrated web UI and RAG (Retrieval-Augmented Generation) system.

## Value Proposition
- Run local AI models without cloud dependency
- Unified API across 4 different AI backends
- Built-in RAG for context-aware responses using FAISS vector search
- Web UI for model management, chat, and monitoring — no CLI required
- MCP (Model Context Protocol) server integration for Claude Desktop

## Key Features

### AI Backends
- **Microsoft Foundry Local** — ONNX-based inference (DeepSeek, Qwen, Mistral, Llama)
- **HuggingFace Transformers** — download and run models from Hub (PyTorch)
- **llama.cpp** — GGUF model inference on CPU/GPU (Windows x64 binaries included)
- **Ollama** — local Ollama server integration

### API Capabilities
- Text generation (single and batch)
- Interactive chat with session history
- RAG search and context injection
- Model load/unload management
- Health monitoring endpoints
- API key security + CORS protection

### Web Interface (SPA at port 9696)
Tabs: Chat, Models, Foundry, HuggingFace, llama.cpp, Ollama, RAG, Agent, MCP, Config, Logs, Editor, Docs, Examples, Providers, Settings

### Infrastructure
- Docker support (`docker-compose.yml`)
- MkDocs documentation server (port 9697)
- Browser extensions (summarizer, locator-editor)
- PowerShell MCP servers for Windows automation
- GGUF → ONNX converter

## Target Users
- Developers building AI-powered applications locally
- Researchers needing offline LLM inference
- Teams wanting a self-hosted AI API with web management
- Claude Desktop users needing MCP integration

## Use Cases
- Local AI chat assistant with document context (RAG)
- Batch text processing via REST API
- Model evaluation and comparison across backends
- AI agent workflows via PowerShell MCP servers
- Browser-based AI summarization (extension)

## Entry Points
- `start.ps1` — full startup (installs deps, starts Foundry, launches server)
- `run.py` — direct Python launch (assumes Foundry already running)
- `docker-compose up` — containerized deployment
- Web UI: http://localhost:9696
- Swagger: http://localhost:9696/docs
- Health: http://localhost:9696/api/v1/health

## Version
Current: **0.6.0** | Python 3.11+ | Windows primary platform
