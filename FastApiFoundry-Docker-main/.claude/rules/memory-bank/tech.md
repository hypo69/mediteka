# FastAPI Foundry — Technology Stack

## Languages & Runtimes
| Layer | Technology | Version |
|---|---|---|
| Backend | Python | 3.11+ (primary), 3.12 compatible |
| Web UI | JavaScript (ES modules) | Vanilla JS, no framework |
| Browser Extensions | JavaScript + TypeScript (React) | Vite build |
| Scripts | PowerShell | 5.1+ / 7+ |
| Containers | Docker | Compose v3 |

## Core Python Dependencies
| Package | Version | Purpose |
|---|---|---|
| fastapi | 0.136.0 | Web framework |
| uvicorn | 0.44.0 | ASGI server |
| starlette | 1.0.0 | ASGI toolkit (FastAPI base) |
| pydantic | 2.13.2 | Data validation / schemas |
| aiohttp | 3.13.5 | Async HTTP client (Foundry, Ollama) |
| requests | 2.33.1 | Sync HTTP (port discovery) |
| python-dotenv | 1.2.2 | .env loading |
| faiss-cpu | 1.13.2 | Vector search (RAG) |
| sentence-transformers | 5.4.1 | Text embeddings (RAG) |
| transformers | 4.57.6 | HuggingFace model inference |
| torch | 2.11.0 | PyTorch backend |
| huggingface_hub | 0.36.2 | Model downloads |
| onnx + onnxruntime | 1.21.0 / 1.24.4 | ONNX inference |
| optimum | 2.1.0 | HuggingFace ONNX optimization |
| psutil | 7.2.2 | Process/system monitoring |
| colorama + coloredlogs | 0.4.6 / 15.0.1 | Colored console output |
| pytest + pytest-asyncio | 9.0.3 / 1.3.0 | Testing |
| mkdocs-material | 9.7.6 | Documentation site |

## AI Backends
| Backend | Protocol | Port | Notes |
|---|---|---|---|
| Microsoft Foundry Local | OpenAI-compatible REST | dynamic (auto-discovered) | ONNX inference, Windows |
| HuggingFace Transformers | In-process Python | — | PyTorch, local models |
| llama.cpp | REST (llama-server.exe) | 9780 | GGUF models, CPU/GPU |
| Ollama | REST | 11434 | Standard Ollama API |

## Configuration System
- `config.json` — public settings (ports, models, RAG, logging)
- `.env` — secrets (HF_TOKEN, FOUNDRY_BASE_URL, API keys)
- `config_manager.py` — singleton `Config` class, reads both files
- `src/core/config.py` — re-exports `config` for internal imports
- Runtime override: `config.foundry_base_url` set dynamically by `run.py`

## Key config.json Sections
```json
{
  "fastapi_server": { "host", "port": 9696, "workers", "mode" },
  "foundry_ai":     { "base_url", "default_model", "temperature", "max_tokens", "auto_load_default" },
  "rag_system":     { "enabled", "index_dir", "chunk_size" },
  "security":       { "api_key", "https_enabled" },
  "logging":        { "level", "file" },
  "docs_server":    { "enabled", "port": 9697 },
  "llama_cpp":      { "port": 9780, "host", "bin_version" },
  "ollama":         { "base_url", "default_model" },
  "huggingface":    { "models_dir", "device", "default_max_new_tokens" },
  "directories":    { "models", "rag", "hf_models" }
}
```

## Key .env Variables
```env
FOUNDRY_BASE_URL=http://localhost:50477/v1    # Override Foundry URL
FOUNDRY_DYNAMIC_PORT=50477                    # Legacy port override
HF_TOKEN=hf_...                               # HuggingFace token
HF_MODELS_DIR=D:\models                       # HF models directory
LLAMA_MODEL_PATH=D:\models\model.gguf         # llama.cpp model
LLAMA_AUTO_START=false                        # Auto-start llama server
LOG_LEVEL=INFO                                # Logging level
API_KEY=                                      # Optional API key
_UVICORN_CHILD=1                              # Set by run.py to suppress duplicate output
```

## Development Commands

### Start Server
```powershell
# Full startup (recommended first run)
powershell -ExecutionPolicy Bypass -File .\start.ps1

# Direct Python launch
venv\Scripts\python.exe run.py

# Docker
docker-compose up
```

### Install Dependencies
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
# or
venv\Scripts\pip install -r requirements.txt
```

### Diagnostics
```powershell
venv\Scripts\python.exe check_env.py
venv\Scripts\python.exe diagnose.py
venv\Scripts\python.exe check_engine\smoke_all_endpoints.py
```

### Testing
```powershell
venv\Scripts\python.exe -m pytest tests/ -v
```

### Documentation
```powershell
# Serve docs locally
venv\Scripts\mkdocs serve -f mkdocs.yml --dev-addr 0.0.0.0:9697

# Build docs
venv\Scripts\mkdocs build
```

### Syntax Check (pre-commit)
```powershell
python -m py_compile src/**/*.py
python -m flake8 src/ --max-line-length=120
```

## Ports Reference
| Service | Port | Notes |
|---|---|---|
| FastAPI server | 9696 | Main API + Web UI |
| MkDocs docs | 9697 | Optional, config-controlled |
| llama.cpp server | 9780 | Optional, auto-start |
| Ollama | 11434 | External process |
| Foundry Local | dynamic | Auto-discovered (common: 50477, 62171) |

## Docker
- `Dockerfile` — Python 3.11 base, installs requirements, runs `run.py`
- `docker-compose.yml` — single service, port 9696 exposed
- `docker-compose.docs.yml` — MkDocs documentation server
- `.dockerignore` — excludes venv, logs, models, bin

## CI/CD
- `.github/workflows/deploy-docs.yml` — deploys MkDocs to GitHub Pages
- `.github/workflows/docs.yml` — builds docs on PR
- Published at: https://hypo69.github.io/FastApiFoundry-Docker/

## llama.cpp Binaries
Pre-built Windows x64 binaries in `bin/llama-b8802-bin-win-cpu-x64/`:
- `llama-server.exe` — HTTP inference server
- `llama-cli.exe` — CLI inference
- Multiple CPU-optimized DLLs (AVX2, AVX512, Haswell, Skylake, etc.)
