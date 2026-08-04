# AI Assistant (ai_assist) — Development Guidelines

**Version:** 0.8.0
**Project:** AI Assistant (ai_assist)

---

## 0. Encoding Rule — ABSOLUTE

**Every file in the project MUST be saved as UTF-8 without BOM.**

This applies to ALL file types: `.py`, `.js`, `.ts`, `.css`, `.html`, `.php`, `.ps1`, `.json`, `.md`, `.yaml`, `.env`.

File headers MUST declare encoding explicitly:

- Python / PowerShell: `# -*- coding: utf-8 -*-` as the first line
- JavaScript / TypeScript: `// @charset "utf-8"` in the file header block
- CSS / SCSS: `@charset "UTF-8";` as the very first line
- HTML: `<meta charset="UTF-8">` inside `<head>`
- PHP: `// @charset utf-8` in the file header block (PHP files are always UTF-8)

**Never use any other encoding. Never save files with BOM.**

---



Every Python file MUST start with this exact header block:

```python
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: <Short descriptive name of what the module does>
# =============================================================================
# Description:
#   <Detailed description of the module's purpose>
#   <Include workflow diagrams for complex modules>
#
# File: <filename.py>
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Changes in 0.8.0:
#   - <what changed>
# Author: hypo69
# Copyright: © 2024 - 2026 hypo69
# License: MIT
# =============================================================================
```

PowerShell files use the same structure with `#` comments.

**Rules:**
- `# -*- coding: utf-8 -*-` is always the first line
- Version must match the current project version (0.8.0)
- Project name is always "AI Assistant (ai_assist)"
- Lines starting with `#` in headers are NEVER modified

---

## 2. Docstring Format

All public functions, methods, and classes require docstrings in this exact order:

```python
def function_name(param: str, optional: int = 0) -> dict | None:
    """Short one-line description.

    Optional longer explanation of why this approach was chosen.

    Args:
        param (str): Description of the parameter.
        optional (int): Optional parameter. Default: 0.

    Returns:
        dict | None: What is returned and when. None on empty input.

    Exceptions:
        ValueError: When param is empty.

    Example:
        >>> result = function_name("data")
        >>> result["status"]
        'ok'
    """
```

**Rules:**
- Section order: Short description → Long description → Args → Returns → Exceptions → Example
- Use `Args:` not `Params:` — `Params:` is forbidden
- Use `Exceptions:` not `Raises:` — `Raises:` is forbidden
- Omit sections that don't apply (no empty sections)
- Minimum one example per public function
- ReStructuredText blocks (`:param:`, `.. module::`) are forbidden

---

## 3. Type Annotations

All functions must have complete type annotations:

```python
# ✅ Correct
async def generate_text(prompt: str, model: str | None = None,
                        temperature: float = 0.7) -> dict:

# ✅ Union types use | syntax (Python 3.10+)
def detect_backend(model: str | None) -> tuple[str, str]:

# ✅ Async generators
async def generate_stream(...) -> AsyncIterator[dict]:

# ✅ kwargs with type
async def generate_text(self, prompt: str, **kwargs: object) -> dict:

# ✅ None-returning functions
def close_session(self) -> None:
```

---

## 4. Guard Clause Pattern

Always use early return instead of deep nesting:

```python
# ✅ Correct — guard clause
async def generate_text(prompt: str) -> dict:
    if not prompt:
        return {"success": False, "error": "Prompt is required"}
    if not self.base_url:
        return {"success": False, "error": "Foundry недоступен"}
    # ... main logic

# ❌ Wrong — deep nesting
async def generate_text(prompt: str) -> dict:
    if prompt:
        if self.base_url:
            # ... main logic
```

Use `if not condition:` pattern, not `if condition is None:`.

---

## 5. Unified API Response Shape

All API endpoints MUST return `{"success": bool, ...}`:

```python
# Success
return {"success": True, "content": "...", "model": "foundry::qwen3", "usage": {...}}

# Failure
return {"success": False, "error": "Description of what went wrong"}

# Special error with code
return {
    "success": False,
    "error": "Model not loaded",
    "error_code": "model_not_loaded",
    "model_id": model_id,
}
```

Use the `@api_response_handler` decorator on all endpoints — it automatically injects `"success": True` if missing and catches exceptions:

```python
from ...utils.api_utils import api_response_handler

@router.post("/generate")
@api_response_handler
async def generate_text(request: dict) -> dict:
    if not request.get("prompt"):
        return {"success": False, "error": "Prompt is required"}
    # ... if no "success" key returned, decorator injects "success": True
    return {"content": "result"}  # → {"success": True, "content": "result"}
```

---

## 6. Logging Pattern

Use `logging.getLogger(__name__)` — never `print()`:

```python
import logging
logger = logging.getLogger(__name__)

# Emoji conventions:
logger.info("✅ RAG system initialized")
logger.info("🤖 Generating: model=qwen3")
logger.warning("⚠️ Foundry not found")
logger.error("❌ Connection failed: {e}")
logger.debug("🔍 Searching port range...")
```

**Emoji conventions:**
- `✅` — success/initialized
- `⚠️` — warning/degraded
- `❌` — error/failure
- `🤖` — AI model operation
- `🔍` — search/discovery
- `📥` / `📤` — load/unload
- `🔧` — tool execution (agents)

Import logger from `src.logger` in module-level code:
```python
from src.logger import logger  # in src/ modules
```

Or use `logging.getLogger(__name__)` for standard Python logging.

---

## 7. Singleton Pattern

All stateful services use the Singleton pattern:

```python
class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:  # Check for existing instance (Singleton)
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

# Module-level singleton instance
config = Config()
```

Access pattern everywhere:
```python
from src.core.config import config  # re-exports from config_manager.py
```

Other singletons follow the same pattern:
```python
foundry_client = FoundryClient()   # src/models/foundry_client.py
hf_client = HFClient()             # src/models/hf_client.py
ollama_client = OllamaClient()     # src/models/ollama_client.py
rag_system = RAGSystem()           # src/rag/rag_system.py
```

---

## 8. Async HTTP Client Pattern

Use `aiohttp` for async HTTP. Session is lazy-initialized and reused:

```python
class FoundryClient:
    def __init__(self) -> None:
        self.session: aiohttp.ClientSession | None = None
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
```

Always close sessions in the lifespan shutdown:
```python
yield
await foundry_client.close()
```

---

## 9. Model Prefix Routing

The routing system in `src/models/router.py` is the single source of truth for backend dispatch:

```python
# Prefix constants — always use these, never hardcode strings
PREFIX_FOUNDRY = "foundry::"
PREFIX_HF      = "hf::"
PREFIX_LLAMA   = "llama::"
PREFIX_OLLAMA  = "ollama::"

# Usage
backend, clean_model = detect_backend(model_string)
result = await route_generate(prompt, model="foundry::qwen3-0.6b")
```

Never dispatch to backends directly from endpoints — always go through `route_generate()`.

---

## 10. Config Access Pattern

```python
from src.core.config import config

# Property access (all typed)
port = config.api_port           # int
host = config.api_host           # str
url = config.foundry_base_url    # str (runtime-settable)
enabled = config.rag_enabled     # bool

# Section access
hf_section = config.get_section("huggingface")  # dict

# Full config
raw = config.get_raw_config()    # dict copy

# Update and persist
config.update_config(new_dict)   # writes to config.json

# Runtime override (used in run.py after Foundry discovery)
config.foundry_base_url = discovered_url
```

---

## 11. CPU-Bound Work in Async Context

For blocking operations in async functions, use `run_in_executor`:

```python
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, blocking_function, arg1, arg2)
```

For lazy-loaded heavy models (SentenceTransformers, etc.), use lazy initialization:

```python
def _get_model(self) -> Any:
    """Lazy model initialization — avoids startup delay."""
    if self.model is None:
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(config.rag_model)
    return self.model
```

---

## 12. Error Handling

Wrap external calls in try/except and return structured errors:

```python
try:
    async with session.post(url, json=payload) as response:
        if response.status == 200:
            data = await response.json()
            return {"success": True, "content": data["choices"][0]["message"]["content"]}
        elif response.status == 400:
            # Specific error code for known failure modes
            return {
                "success": False,
                "error": f"Model {model} not loaded",
                "error_code": "model_not_loaded",
                "model_id": model,
            }
        else:
            error_text = await response.text()
            return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
except Exception as e:
    logger.error(f"❌ Exception: {e}")
    return {"success": False, "error": str(e)}
```

**Never** let exceptions propagate from API endpoints — always catch and return `{"success": False, "error": ...}`.

---

## 13. FastAPI Router Pattern

One file per feature area in `src/api/endpoints/`:

```python
from fastapi import APIRouter
from ...utils.api_utils import api_response_handler

router = APIRouter()

@router.post("/generate")
@api_response_handler
async def generate_text(request: dict) -> dict:
    """Endpoint docstring with Args/Returns."""
    prompt = request.get("prompt", "")
    if not prompt:
        return {"success": False, "error": "Prompt is required"}
    # ...
    return {"content": result}
```

Register in `app.py`:
```python
from .endpoints import generate
app.include_router(generate.router, prefix="/api/v1")
```

---

## 14. Dataclass Pattern for Structured Data

Use `@dataclass` for structured return types in agents and complex modules:

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class AgentResult:
    success: bool
    answer: str = ""
    tool_calls: List[ToolCallResult] = field(default_factory=list)
    iterations: int = 0
    error: str = ""
    note: str = ""
```

---

## 15. Abstract Base Class Pattern

Agents use ABC for enforcing interface contracts:

```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    name: str = "base"

    @property
    @abstractmethod
    def tools(self) -> List[ToolDefinition]:
        """List of agent tools."""
        ...

    @abstractmethod
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return result as string."""
        ...
```

The `...` marker in abstract methods is a debug marker — **never replace it with `pass`**.

---

## 16. Variable Declaration at Function Top

Declare local variables at the top of function bodies:

```python
async def reload_index(self, index_dir: str) -> bool:
    path: Path = Path(index_dir).expanduser()
    index_file: Path = path / "faiss.index"
    chunks_file: Path = path / "chunks.json"
    loaded_index: Optional[faiss.Index] = None
    loaded_chunks: List[Dict[str, Any]] = []
    model_dim: int = 0
    index_dim: int = 0

    # ... logic follows
```

---

## 17. Inline Comment Style

Comments explain *why*, not *what*. Written in Russian for business logic, English for technical notes:

```python
# Проверка существования экземпляра (Singleton)
if cls._instance is None:

# Runtime override (set by run.py after discovery) takes priority.
if self._foundry_base_url:
    return self._foundry_base_url

# Почему: `finish_reason` может быть `"stop"` даже при наличии `tool_calls`
tool_calls = message.get("tool_calls") or []
```

---

## 18. Module `__init__.py` Pattern

Keep `__init__.py` files minimal — only re-export public API:

```python
# -*- coding: utf-8 -*-
from .gguf_to_onnx import GGUFConverter, ConversionResult

__all__ = ["GGUFConverter", "ConversionResult"]
```

Test `__init__.py` files are empty (marker files only).

---

## 19. Windows / UTF-8 Compatibility

For Windows compatibility in entry points:

```python
import os, sys, codecs
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        pass
```

---

## 20. Versioning Rules

- Current version: **0.8.0**
- All modified files must update their version header to 0.8.0
- Add `Changes in 0.8.0:` section describing what changed
- Update `CHANGELOG.md` with every code change (format: `## [0.8.0] - YYYY-MM-DD`)
- `VERSION` file in root contains the current version string

---

## 21. Documentation Sync Rule

After every code change:
1. Update docstring of the changed function/class
2. Add entry to `CHANGELOG.md`
3. If endpoint changed → update `docs/ru/dev/api_reference.md`
4. If architecture/config changed → update `docs/ru/dev/architecture.md`

---

## 22. PowerShell Code Style

PowerShell scripts follow the same header format and use:
- `Verb-Noun` function naming (`Get-FoundryPort`, `Start-Sandbox`)
- `$UPPER_SNAKE_CASE` for constants
- `$ErrorActionPreference = 'Stop'` at script top
- `Write-Host '✅ Message'` for user output (never `Write-Output`)
- `# --- main ---` separator before entry point code
- `Resolve-Mode` pattern for mode normalization
- Comment-based help with `.SYNOPSIS`, `.DESCRIPTION`, `.EXAMPLE` (never `.PARAMETER`, `.OUTPUTS`, `.NOTES`)

---

## 23. Search Cache Pattern

For expensive repeated operations, use a dict cache with tuple keys:

```python
self._search_cache: Dict[tuple, List[Dict[str, Any]]] = {}

# Check cache first
cache_key = (query, top_k)
if cache_key in self._search_cache:
    return self._search_cache[cache_key]

# ... compute result ...

# Store in cache
self._search_cache[cache_key] = results
return results

# Invalidate on state change
self._search_cache = {}  # clear on index reload
```

---

## 24. Streaming Response Pattern (SSE)

For streaming endpoints, use `AsyncIterator` and yield dicts:

```python
async def generate_stream(self, prompt: str) -> AsyncIterator[dict]:
    """Yields token chunks, then finished=True."""
    try:
        async with session.post(url, json={..., "stream": True}) as response:
            async for line in response.content:
                line_str = line.decode('utf-8').strip()
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str == '[DONE]':
                        yield {"success": True, "finished": True}
                        break
                    data = json.loads(data_str)
                    content = data['choices'][0]['delta'].get('content', '')
                    if content:
                        yield {"success": True, "content": content, "finished": False}
    except Exception as e:
        yield {"success": False, "error": str(e)}
```
