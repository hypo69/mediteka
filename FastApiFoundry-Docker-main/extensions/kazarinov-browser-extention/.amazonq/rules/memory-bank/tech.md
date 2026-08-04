# AI Assistant (ai_assist) — Technology Stack

**Version:** 0.7.1
**Project:** AI Assistant (ai_assist)

---

## Runtime Requirements

| Requirement | Version |
|---|---|
| Python | 3.11+ (primary), 3.12 compatible |
| Platform | Windows (primary), Linux (Docker) |
| Current version | v0.7.1 |

---

## Core Framework

| Component | Package | Version |
|---|---|---|
| Web framework | `fastapi` | 0.136.0 |
| ASGI server | `uvicorn` | 0.44.0 |
| Data validation | `pydantic` | 2.13.2 |
| Pydantic settings | `pydantic-settings` | 2.14.0 |
| ASGI toolkit | `starlette` | 1.0.0 |
| SSE streaming | `sse-starlette` | 3.3.4 |
| WebSockets | `websockets` | 16.0 |
| HTTP client (async) | `aiohttp` | 3.13.5 |
| HTTP client (sync) | `requests` | 2.33.1 |
| HTTP client (modern) | `httpx` | 0.28.1 |

---

## AI / ML Stack

| Component | Package | Version |
|---|---|---|
| HuggingFace Hub | `huggingface_hub` | 0.36.2 |
| Transformers | `transformers` | 4.57.6 |
| PyTorch | `torch` | 2.11.0 |
| ONNX Runtime | `onnxruntime` | 1.25.0 |
| ONNX | `onnx` | 1.21.0 |
| Optimum (ONNX export) | `optimum` | 2.1.0 |
| Sentence Transformers | `sentence-transformers` | 5.4.1 |
| FAISS (CPU) | `faiss-cpu` | 1.13.2 |
| NumPy | `numpy` | 2.4.4 |
| Scikit-learn | `scikit-learn` | 1.8.0 |
| Foundry Local SDK | `foundry-local-sdk` | latest |
| MCP protocol | `mcp` | 1.27.0 |
| Accelerate | `accelerate` | 1.13.0 |

---

## Text Extraction (RAG)

| Format | Package |
|---|---|
| PDF | `pdfplumber`, `PyPDF2` |
| Word/DOCX | `python-docx` |
| PowerPoint/PPTX | `python-pptx` |
| Excel/XLSX | `openpyxl`, `pandas` |
| HTML/XML | `beautifulsoup4`, `lxml` |
| OCR (images) | `pytesseract`, `Pillow` |
| ODF | `odfpy` |
| RTF | `striprtf` |
| RAR archives | `rarfile` |
| 7z archives | `py7zr` |
| XML dict | `xmltodict` |

---

## Infrastructure & Utilities

| Component | Package | Version |
|---|---|---|
| Environment vars | `python-dotenv` | 1.2.2 |
| Process monitoring | `psutil` | 7.2.2 |
| Telegram bots | `pyTelegramBotAPI` | 4.33.0 |
| JWT | `PyJWT` | 2.12.1 |
| Cryptography | `cryptography` | 46.0.7 |
| Colorized logging | `coloredlogs` | 15.0.1 |
| Rich terminal | `rich` | 15.0.0 |
| Windows API | `pywin32` | 311 |
| YAML | `PyYAML` | 6.0.3 |
| Multipart forms | `python-multipart` | 0.0.26 |

---

## Documentation

| Component | Package | Version |
|---|---|---|
| Docs site | `mkdocs` | 1.6.1 |
| Material theme | `mkdocs-material` | 9.7.6 |
| i18n plugin | `mkdocs-static-i18n` | 1.3.1 |
| Auto-reference | `mkdocs-autorefs` | 1.4.4 |
| Docstring docs | `mkdocstrings-python` | 2.0.3 |

---

## Testing

| Component | Package | Version |
|---|---|---|
| Test runner | `pytest` | 9.0.3 |
| Async tests | `pytest-asyncio` | 1.3.0 |

### Test Configuration (pytest.ini)
```ini
[pytest]
testpaths = tests
norecursedirs = extensions .git .venv venv build dist
asyncio_mode = auto
addopts = -v --tb=short
```

### Test Structure
```
tests/
├── agents/          # Agent tests
├── integration/     # Integration tests (e.g., PowerShell MCP)
├── unit/            # Unit tests (e.g., JSON utils)
└── reports/         # Test reports
```

---

## Docker

```yaml
# docker-compose.yml
services:
  fastapi-foundry:
    image: fastapi-foundry:0.2.1
    ports: ["${PORT:-8000}:8000"]
    volumes:
      - ./logs:/app/logs
      - ./rag_index:/app/rag_index
    healthcheck:
      test: curl -f http://localhost:9696/api/v1/health
      interval: 30s
```

---

## Development Commands

### Start (Windows)
```powershell
# Full start (installs deps, starts Foundry, launches server)
powershell -ExecutionPolicy Bypass -File .\start.ps1

# Python only (Foundry already running)
venv\Scripts\python.exe run.py

# Docker
docker-compose up
```

### Install
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

### Tests
```powershell
venv\Scripts\python.exe -m pytest tests/ -v
venv\Scripts\python.exe -m pytest tests/unit/ -v
venv\Scripts\python.exe -m pytest tests/integration/ -v
```

### Diagnostics
```powershell
venv\Scripts\python.exe check_env.py
venv\Scripts\python.exe diagnose.py
venv\Scripts\python.exe check_engine\smoke_all_endpoints.py
```

### Documentation
```powershell
# Serve docs locally
mkdocs serve -a localhost:9697

# Build docs
mkdocs build
```

### Stop
```powershell
powershell -ExecutionPolicy Bypass -File .\stop.ps1
```

---

## Key Environment Variables (.env)

| Variable | Purpose |
|---|---|
| `FOUNDRY_BASE_URL` | Foundry URL (if not auto-detected) |
| `HF_TOKEN` | HuggingFace token (for gated models) |
| `HF_MODELS_DIR` | HuggingFace models directory |
| `LLAMA_MODEL_PATH` | Path to GGUF file |
| `LLAMA_AUTO_START` | Auto-start llama.cpp |
| `API_KEY` | API security key |
| `TELEGRAM_ADMIN_TOKEN` | Admin Telegram bot token |
| `TELEGRAM_ADMIN_IDS` | Comma-separated admin user IDs |
| `TELEGRAM_HELPDESK_TOKEN` | HelpDesk bot token |
| `FTP_HOST` / `FTP_USER` / `FTP_PASSWORD` | FTP for MCP server |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, etc.) |

---

## Web Interface Technologies

| Component | Technology |
|---|---|
| CSS framework | Bootstrap 5 |
| JavaScript | Vanilla JS (ES6+), no framework |
| API calls | `fetch` API |
| Streaming | SSE (EventSource) |
| i18n | Custom `i18n.js` + JSON locale files |
| HTML templating | Static partials (server-assembled) |

---

## Browser Extensions

| Extension | Technology |
|---|---|
| `browser-extension-summarizer` | Vanilla JS |
| `browser-extension-locator-editor` | TypeScript + React + Vite |
| `browser-extension-review-parser` | Vanilla JS |
| `browser-extension-recommender` | Vanilla JS |
