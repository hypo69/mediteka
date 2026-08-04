# FastAPI Foundry — Project Structure

## Directory Layout

```
FastApiFoundry-Docker/
├── src/                        # Core Python application
│   ├── api/                    # FastAPI layer
│   │   ├── app.py              # Application factory (create_app)
│   │   ├── main.py             # ASGI entry point (app instance)
│   │   ├── models.py           # Pydantic request/response schemas
│   │   └── endpoints/          # Route handlers (one file per domain)
│   │       ├── health.py       # GET /api/v1/health
│   │       ├── generate.py     # POST /api/v1/generate
│   │       ├── chat_endpoints.py
│   │       ├── foundry.py / foundry_management.py / foundry_models.py
│   │       ├── hf_models.py    # HuggingFace endpoints
│   │       ├── llama_cpp.py    # llama.cpp endpoints
│   │       ├── ollama.py       # Ollama endpoints
│   │       ├── rag.py          # RAG search endpoints
│   │       ├── agent.py        # AI agent endpoints
│   │       ├── mcp_powershell.py
│   │       ├── converter.py    # GGUF→ONNX converter endpoints
│   │       ├── config.py       # Config read/write endpoints
│   │       └── logs.py         # Log streaming endpoints
│   ├── models/                 # AI backend clients
│   │   ├── foundry_client.py   # Microsoft Foundry Local (aiohttp, async)
│   │   ├── enhanced_foundry_client.py
│   │   ├── hf_client.py        # HuggingFace Transformers
│   │   ├── ollama_client.py    # Ollama
│   │   └── model_manager.py    # Unified model manager
│   ├── rag/                    # RAG system
│   │   ├── rag_system.py       # Main RAG orchestrator
│   │   └── indexer.py          # FAISS indexing
│   ├── agents/                 # AI agents
│   │   ├── base.py             # Base agent class
│   │   └── powershell_agent.py
│   ├── converter/              # GGUF → ONNX conversion
│   │   └── gguf_to_onnx.py
│   ├── translator/             # Translation module
│   │   └── translator.py
│   ├── core/
│   │   └── config.py           # Re-exports config from config_manager.py
│   ├── logger/
│   │   └── __init__.py         # Logger initialization
│   └── utils/
│       ├── env_processor.py    # .env loading
│       ├── foundry_finder.py   # Foundry port discovery
│       ├── logging_config.py   # Logging setup
│       ├── logging_system.py
│       └── log_analyzer.py
├── static/                     # Web UI (SPA)
│   ├── index.html              # Main SPA shell
│   ├── app.js                  # SPA router/init
│   ├── js/                     # Feature modules (one per tab)
│   │   ├── chat.js, models.js, foundry.js, hf.js, llama.js
│   │   ├── rag.js, agent.js, mcp.js, ollama.js
│   │   ├── config.js, editor.js, i18n.js, ui.js
│   │   └── providers.js, providers-registry.js, sdk.js
│   ├── partials/               # HTML tab fragments (_tab_*.html)
│   ├── locales/                # i18n JSON (en, ru, he)
│   └── css/main.css
├── mcp-powershell-servers/     # MCP server implementations
│   ├── src/
│   │   ├── servers/            # PowerShell MCP servers
│   │   ├── clients/            # Python MCP clients
│   │   └── config/             # MCP configuration
│   └── Start-MCPServers.ps1
├── extensions/                 # Browser extensions
│   ├── browser-extension-summarizer/   # AI page summarizer
│   └── browser-extension-locator-editor/ # Element locator (React/TS)
├── docs/                       # MkDocs source (ru + en)
├── site/                       # Built MkDocs static site
├── check_engine/               # Diagnostic scripts
├── scripts/                    # Operational PowerShell scripts
├── install/                    # Installation scripts
├── bin/                        # llama.cpp Windows x64 binaries
├── rag_index/                  # FAISS index storage
├── logs/                       # Application logs
├── SANDBOX/                    # SDK experiments
├── utils/                      # Standalone Python utilities
├── examples/                   # API usage examples
├── config_manager.py           # Central config class (reads config.json + .env)
├── config.json                 # Public configuration
├── .env / .env.example         # Secrets and environment variables
├── run.py                      # Python entry point
├── start.ps1                   # Windows full startup script
├── install.ps1                 # Dependency installer
├── docker-compose.yml          # Docker deployment
├── Dockerfile
├── requirements.txt
└── mkdocs.yml                  # Documentation config
```

## Core Architectural Patterns

### Application Factory
`src/api/app.py` exports `create_app()` which wires all routers, middleware, and lifespan hooks. `src/api/main.py` calls it to produce the ASGI `app` object used by uvicorn.

### Configuration Flow
```
config.json + .env
      ↓
config_manager.py (ConfigManager class, singleton `config`)
      ↓
src/core/config.py (re-exports `config`)
      ↓
All modules import from src.core.config
```

### AI Backend Abstraction
Each backend has its own client class with consistent interface:
- `health_check()` → status dict
- `generate_text(prompt, **kwargs)` → `{success, content, model}`
- `generate_stream(prompt, **kwargs)` → async generator
- `list_available_models()` → `{success, models, count}`

Global singleton instances: `foundry_client`, `hf_client`, `ollama_client`

### Router Registration
All routers registered in `create_app()` with `/api/v1` prefix (except `main.router` for UI routes).

### Lifespan Management
`@asynccontextmanager async def lifespan(app)` in `app.py` handles:
1. RAG system initialization
2. Auto-loading default Foundry model
3. Closing aiohttp sessions on shutdown

### Web UI Architecture
SPA with tab-based navigation. Each tab has:
- `static/partials/_tab_<name>.html` — HTML fragment
- `static/js/<name>.js` — tab logic module
- i18n via `static/js/i18n.js` + `static/locales/<lang>.json`

## Key Relationships
- `run.py` → discovers Foundry port → sets `config.foundry_base_url` → starts uvicorn
- `FoundryClient._update_base_url()` → reads `config.foundry_base_url` or auto-discovers
- `rag_system` initialized at startup, used by `/api/v1/rag/*` endpoints
- MCP servers run as separate processes, communicated via HTTP from `mcp_powershell.py` endpoint
