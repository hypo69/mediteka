# FastAPI Foundry — Development Guidelines

## File Header Standard (ALL files)

Every file must start with this header block:

### Python
```python
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: <Short descriptive name>
# =============================================================================
# Description:
#   <What the module does, what APIs it uses>
#
# File: <filename.py>
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Changes in 0.6.0:
#   - <description of changes>
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
```

### JavaScript
```javascript
/**
 * <module-name>.js — <Short description>
 *
 * <Detailed description of purpose, conventions, and behavior>
 */
```

### PowerShell
```powershell
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: <Short descriptive name>
# =============================================================================
# Description:
#   <What the script does>
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\script.ps1
#
# File: script.ps1
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
```

---

## Python Coding Patterns

### Module-level logger (always)
```python
import logging
logger = logging.getLogger(__name__)
```
Never use `print()` for application output — use `logger.info/warning/error`.

### Global singleton pattern
Every client/service module exposes a module-level singleton:
```python
# At bottom of module
foundry_client = FoundryClient()
rag_system = RAGSystem()
translator = Translator()
```

### Singleton class pattern (Config)
```python
class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
```

### Consistent return dict pattern
All service methods return a dict with `success` key:
```python
# Success
return {"success": True, "content": result, "model": model_id, "usage": {}}

# Failure
return {"success": False, "error": "Description of what went wrong"}
```
Never raise exceptions from public API methods — catch and return `{"success": False, "error": ...}`.

### Guard clause / early return
```python
if not text or not text.strip():
    return self._err("Empty text")

if not self.loaded:
    return []
```
Prefer early returns over nested if-blocks.

### Async HTTP session management
```python
async def _get_session(self) -> aiohttp.ClientSession:
    if self._session is None or self._session.closed:
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
    return self._session

async def close(self) -> None:
    if self._session and not self._session.closed:
        await self._session.close()
```
Always lazy-create and reuse sessions. Close in lifespan shutdown.

### Optional dependency guard
```python
RAG_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    RAG_AVAILABLE = True
except ImportError:
    logger.warning('⚠️ RAG dependencies not installed. Run: pip install ...')
```
Use feature flags for optional heavy dependencies (torch, faiss, onnx).

### Async + blocking code
```python
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, blocking_function, arg)
```
Always offload blocking I/O (FAISS, model loading) to executor.

### Async lock for shared state
```python
self._lock = asyncio.Lock()

async def initialize(self) -> bool:
    async with self._lock:
        return await self._load_index()
```

### Type annotations
```python
from typing import Any, Dict, List, Optional

async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
async def translate(self, text: str, *, provider: str = "llm") -> dict:
def find_free_port(start_port: int = 9696, end_port: int = 9796) -> int | None:
```
Use `int | None` union syntax (Python 3.10+). Use `Optional[X]` for older compat.

### Docstring format
```python
async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Find relevant chunks for a query.

    Args:
        query: Search query text.
        top_k: Number of results to return.

    Returns:
        List of matching chunks with score field added.
    """
```

### Exception handling with context
```python
try:
    self.model = await loop.run_in_executor(None, SentenceTransformer, self.model_name)
except Exception as e:
    # Model name wrong, no internet, or transformers version mismatch
    logger.error(f'❌ Failed to load embedding model "{self.model_name}": {e}')
    return False
```
Always add a comment explaining WHY the exception can occur.

### Emoji in log messages (project convention)
```python
logger.info('✅ RAG loaded: 100 vectors')
logger.warning('⚠️ RAG not available — missing dependencies')
logger.error('❌ Failed to load model: ...')
logger.info('🔍 Searching for Foundry...')
logger.info('📥 Loading model: ...')
```

### __init__.py exports
```python
# -*- coding: utf-8 -*-
from .translator import Translator, translator
__all__ = ["Translator", "translator"]
```
Keep `__init__.py` minimal — just re-export the public API.

---

## FastAPI Patterns

### Router structure
```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/health")
async def health_check():
    ...
```
One router per domain file. All registered in `create_app()` with `/api/v1` prefix.

### Lifespan for startup/shutdown
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await rag_system.initialize()
    yield
    # shutdown
    await foundry_client.close()
```

### Global exception handler
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Error: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal Server Error", "detail": str(exc)})
```

### Request logging middleware
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({process_time:.3f}s)")
    return response
```

---

## Configuration Patterns

### Accessing config
```python
from ..core.config import config  # inside src/
from src.core.config import config  # from root
```
Never read `config.json` directly — always use the `config` singleton.

### Config properties use `.get()` with defaults
```python
@property
def api_port(self) -> int:
    return self._config_data.get('fastapi_server', {}).get('port') or 9696
```

### Environment variable override pattern
```python
foundry_url = os.getenv('FOUNDRY_BASE_URL')
if foundry_url:
    return foundry_url
# fall through to auto-discovery
```
Env vars always take priority over config.json values.

### Uvicorn reload guard
```python
_in_reloader_child = os.getenv('_UVICORN_CHILD') == '1'
if not _in_reloader_child:
    os.environ['_UVICORN_CHILD'] = '1'
    print("startup message")  # only once
```
Prevents duplicate output when `reload=True`.

---

## JavaScript Patterns (Web UI)

### ES module exports
```javascript
export async function initI18n(lang) { ... }
export async function switchLang(lang) { ... }
export function applyTranslations() { ... }
```
All JS files use ES module syntax. Imported in `app.js`.

### i18n attribute conventions
```html
<button data-i18n="btn.save">Save</button>
<input data-i18n-placeholder="input.search">
<span data-i18n-title="tooltip.help">?</span>
```
Never hardcode user-visible text in HTML — always use `data-i18n` attributes.

### i18n in JavaScript
```javascript
const val = i18next.t('key.name');
```

### API calls pattern
```javascript
fetch(`${window.API_BASE}/config`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 'app.language': lang }),
}).catch(() => {});  // silent fail for non-critical calls
```
Use `window.API_BASE` for all API URLs (set in `app.js`).

### Inline comments in English
```javascript
// Initialize menu toggle on DOM ready
function initMenuToggle() { ... }

// Lazy-load locale bundle if not yet loaded
if (!i18next.hasResourceBundle(lang, 'translation')) { ... }
```
All code comments in English. User-facing strings via i18n keys.

### RTL support
```javascript
const RTL_LANGS = new Set(['he', 'ar', 'fa']);
document.documentElement.setAttribute('dir', RTL_LANGS.has(lang) ? 'rtl' : 'ltr');
```

---

## PowerShell Patterns

### Error handling at top
```powershell
$ErrorActionPreference = 'Stop'
```

### Constants in UPPER_SNAKE_CASE
```powershell
$PROJECT_PATH = 'D:\repos\project'
$CONFIG_FILE = Join-Path $env:TEMP 'config.wsb'
```

### Function docstrings
```powershell
function Test-Virtualization {
    <#
    .SYNOPSIS
        Checks whether hardware virtualization is enabled.
    .OUTPUTS
        bool — True if enabled.
    #>
    ...
}
```

### User-facing output with emoji
```powershell
Write-Host '🔍 Проверка окружения...'
Write-Host '✅ Готово'
Write-Host '⚠️ Требуется перезагрузка.'
```

### Main block separator
```powershell
# --- main ---
Write-Host '🚀 Запуск...'
$result = Start-Service
```

---

## Versioning Rules

- Current version: **0.6.0**
- Format: `Major.Minor.Patch`
- Update version in file header on every change
- Add entry to `CHANGELOG.md` with format:
  ```
  ## [0.6.0] - YYYY-MM-DD
  ### Changed
  - <description>
  ```

---

## Git Commit Conventions

| Type | Prefix | Example |
|---|---|---|
| New feature | `feat:` | `feat: add RAG search endpoint` |
| Bug fix | `fix:` | `fix: duplicate startup output` |
| Config change | `config:` | `config: update default model` |
| Documentation | `docs:` | `docs: update API reference` |
| Tests | `test:` | `test: add health check test` |

---

## Documentation Sync Rule

After changing any code file:
1. Update docstring of changed function/class
2. Add entry to `CHANGELOG.md`
3. Update `docs/ru/dev/api_reference.md` if endpoint changed
4. Update `README.md` if architecture or config changed

---

## Model Prefix Conventions

Model IDs use prefixes to route to the correct backend:
```
hf::<model-id>      → HuggingFace client
llama::<model-id>   → llama.cpp client
ollama::<model-id>  → Ollama client
<model-id>          → Foundry Local (no prefix)
```

Check before auto-loading:
```python
if model_id.startswith(("hf::", "llama::", "ollama::")):
    logger.info(f"Skip auto-loading non-Foundry model: {model_id}")
```

---

## Logging Levels

| Level | When to use |
|---|---|
| `DEBUG` | Port checks, URL updates, per-request details |
| `INFO` | Startup events, model loads, successful operations |
| `WARNING` | Missing optional deps, Foundry not found, degraded mode |
| `ERROR` | Failed operations, exceptions caught, HTTP errors |

Suppress noisy libraries:
```python
for noisy in ('watchfiles', 'watchfiles.main', 'uvicorn.access'):
    logging.getLogger(noisy).setLevel(logging.WARNING)
```
