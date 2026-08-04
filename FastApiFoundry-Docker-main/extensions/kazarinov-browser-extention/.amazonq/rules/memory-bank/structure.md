# AI Assistant (ai_assist) — Project Structure

**Version:** 0.7.1
**Project:** AI Assistant (ai_assist)

---

## Root Directory Layout

```
FastApiFoundry-Docker/
├── src/                    # Core Python application code
├── static/                 # Web interface (SPA)
├── docs/                   # MkDocs documentation
├── mcp/                    # MCP servers (Python + PowerShell)
├── extensions/             # Browser extensions (Chrome)
├── sdk/                    # Python SDKs
├── scripts/                # PowerShell operational scripts
├── install/                # Installation scripts
├── check_engine/           # Diagnostics and smoke tests
├── tests/                  # Test suite
├── utils/                  # Standalone utilities
├── bin/                    # Native binaries (llama.cpp, Windows x64)
├── rag_index/              # FAISS index (runtime, gitignored)
├── logs/                   # Application logs (runtime)
├── archive/                # Rotated logs and session history
├── assets/                 # Reference PDFs and icons
├── examples/               # Usage examples
├── telegram/               # Telegram bot modules
├── notebooks/              # Jupyter notebooks
├── SANDBOX/                # Experimental sandbox
├── config.json             # Public configuration (all settings)
├── config_manager.py       # Config singleton (root-level, imported everywhere)
├── .env / .env.example     # Secrets (tokens, keys, paths)
├── run.py                  # Python entry point
├── start.ps1               # Windows launcher (venv + Foundry + run.py)
├── install.ps1             # Dependency installer
├── stop.ps1                # Stop all services
├── docker-compose.yml      # Docker deployment
├── Dockerfile              # Docker image
├── requirements.txt        # Python dependencies
├── pytest.ini              # Test configuration
├── mkdocs.yml              # Documentation site config
└── VERSION                 # Current version string
```

---

## src/ — Core Application

```
src/
├── api/
│   ├── app.py              # FastAPI app factory (create_app, lifespan)
│   ├── main.py             # ASGI entry point (app = create_app())
│   ├── models.py           # Pydantic request/response models
│   ├── websocket_manager.py
│   ├── docs_generator.py
│   └── endpoints/          # One file per feature area
│       ├── health.py
│       ├── generate.py
│       ├── ai_endpoints.py
│       ├── chat_endpoints.py
│       ├── foundry.py
│       ├── foundry_management.py
│       ├── foundry_models.py
│       ├── hf_models.py
│       ├── llama_cpp.py
│       ├── ollama.py
│       ├── rag.py
│       ├── config.py
│       ├── logs.py
│       ├── agent.py
│       ├── mcp_powershell.py
│       ├── mcp_agent_endpoints.py
│       ├── converter.py
│       ├── system_stats.py
│       ├── support.py
│       ├── helpdesk.py
│       ├── training.py
│       ├── recommender.py
│       └── translator.py
├── models/
│   ├── router.py           # Central routing: detect_backend() + route_generate()
│   ├── foundry_client.py   # Foundry Local HTTP client (singleton)
│   ├── enhanced_foundry_client.py
│   ├── hf_client.py        # HuggingFace Transformers client (singleton)
│   ├── ollama_client.py    # Ollama HTTP client (singleton)
│   └── model_manager.py    # LRU/TTL/RAM model lifecycle manager
├── rag/
│   ├── rag_system.py       # RAGSystem class (singleton: rag_system)
│   ├── indexer.py          # Document indexing pipeline
│   ├── rag_profile_manager.py
│   └── text_extractor_4_rag/  # 40+ format text extractors
├── agents/
│   ├── base.py             # BaseAgent abstract class
│   ├── rag_agent.py
│   ├── powershell_agent.py
│   ├── mcp_agent.py
│   ├── qa_agent.py
│   ├── google_agent.py
│   ├── keystroke_agent.py
│   ├── recommender_agent.py
│   └── windows_os_agent.py
├── core/
│   ├── config.py           # Re-exports config from config_manager.py
│   └── __init__.py
├── converter/
│   ├── gguf_to_onnx.py     # GGUF → ONNX converter
│   └── __init__.py
├── logger/
│   └── __init__.py         # Logger setup, re-exported as `from src.logger import logger`
├── training/
│   ├── dataset_store.py
│   └── trainer.py
└── utils/
    ├── api_utils.py        # @api_response_handler decorator
    ├── env_processor.py    # .env loading
    ├── foundry_finder.py   # Auto-detect Foundry port
    ├── foundry_utils.py    # Foundry CLI helpers
    ├── logging_config.py   # setup_logging()
    ├── logging_system.py
    ├── log_analyzer.py
    ├── process_utils.py
    ├── telegram_bot.py     # Admin bot
    ├── telegram_support_bot.py
    ├── text_utils.py
    └── translator.py
```

---

## static/ — Web Interface

```
static/
├── index.html              # Main SPA entry point
├── app.js                  # App bootstrap
├── css/main.css
├── js/
│   ├── ui.js               # Tab switching, modals, notifications
│   ├── chat.js             # Chat logic
│   ├── foundry.js          # Foundry management
│   ├── rag.js              # RAG search and indexing
│   ├── config.js           # Settings
│   ├── i18n.js             # Internationalization
│   ├── model-badge.js      # Active model badge
│   ├── hf.js, llama.js, ollama.js, mcp.js, agent.js
│   └── ...
├── locales/
│   ├── en.json
│   ├── ru.json
│   └── he.json
└── partials/               # HTML tab fragments (_tab_chat.html, etc.)
```

---

## mcp/ — MCP Servers

```
mcp/
└── src/
    ├── servers/
    │   ├── local_models_mcp.py     # Proxies to FastAPI (Python STDIO)
    │   ├── huggingface_mcp.py      # HuggingFace Inference API
    │   ├── ftp_mcp.py              # FTP operations
    │   ├── docs_deploy_mcp.py      # Deploy docs to FTP
    │   └── McpSTDIOServer.ps1      # PowerShell STDIO MCP
    ├── clients/
    │   └── python_client.py        # MCP client for testing
    └── config/
```

---

## Key Architectural Patterns

### Singleton Pattern
Used for all stateful services:
- `config = Config()` in `config_manager.py` — single config instance
- `foundry_client = FoundryClient()` in `src/models/foundry_client.py`
- `hf_client = HFClient()` in `src/models/hf_client.py`
- `ollama_client = OllamaClient()` in `src/models/ollama_client.py`
- `rag_system = RAGSystem()` in `src/rag/rag_system.py`

### Prefix-Based Routing
`src/models/router.py` is the orchestrator core:
```
request.model → detect_backend() → (backend, clean_id)
                                 → _generate_foundry / _generate_hf / _generate_llama / _generate_ollama
                                 → unified {"success": bool, "content": str, "model": str, "usage": {...}}
```

### Application Factory
`src/api/app.py` uses `create_app()` factory pattern with `lifespan` context manager for startup/shutdown.

### Config Hierarchy
```
.env (secrets) → overrides → config.json → read via → Config singleton
```
Config is accessed everywhere via `from src.core.config import config`.

### Guard Clause Pattern
All functions use early return on invalid input:
```python
if not prompt:
    return {"success": False, "error": "Prompt is required"}
```

---

## Configuration Files

| File | Purpose |
|---|---|
| `config.json` | All public settings (ports, models, RAG, logging, etc.) |
| `.env` | Secrets: tokens, API keys, paths |
| `docker-compose.yml` | Docker deployment |
| `pytest.ini` | Test runner config |
| `mkdocs.yml` | Documentation site |
| `mcp/settings.json` | MCP server configurations |

### config.json Sections
- `fastapi_server` — host, port, mode, workers, reload, log_level
- `foundry_ai` — base_url, default_model, auto_load_default, temperature, max_tokens
- `rag_system` — enabled, index_dir, model, chunk_size, top_k, source_dirs
- `llama_cpp` — model_path, models_dir, port, host
- `huggingface` — models_dir, device, default_max_new_tokens
- `security` — api_key, enable_https
- `logging` — retention_hours, history_retention_days, archive_max_size_gb
- `model_manager` — max_loaded_models, ttl_seconds, max_ram_percent
- `telegram` / `telegram_helpdesk` — bot tokens and settings
- `port_management` — auto_find_free_port, port_range_start/end
- `docs_server` — enabled, port (9697)
- `translator` — enabled, default_provider
- `dialogs` — dir, retention_days, max_size_mb

---

## Startup Flow

```
start.ps1
  [1] Check venv/ → run install.ps1 if missing
  [2] Load .env variables
  [3] Find Foundry port → start "foundry service start" if not found
  [4] Start MkDocs if docs_server.enabled
  [5] Start llama.cpp if llama_cpp.model_path set
  [6] Kill previous FastAPI process
  [7] python run.py (blocking)

run.py
  - UTF-8 setup (Windows)
  - load_env_variables()
  - Config() singleton init
  - cleanup_log_temp_files()
  - cleanup_session_history()
  - cleanup_archive_size()
  - resolve_foundry_base_url() → config.foundry_base_url = url
  - get_server_port()
  - uvicorn.run("src.api.main:app", ...)

lifespan(app) [in app.py]
  startup:
    - await rag_system.initialize()
    - if auto_load_default: subprocess foundry model load <model>
  yield
  shutdown:
    - await foundry_client.close()
```
