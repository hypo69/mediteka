# src/api/endpoints

FastAPI route handlers. One file per feature area.

## Files

| File | Prefix | Description |
|---|---|---|
| `health.py` | `/v1/health` | Service health check |
| `generate.py` | `/v1/generate` | Single-shot text generation |
| `chat_endpoints.py` | `/v1/chat` | Session-aware chat |
| `models.py` | `/v1/models` | Model list / connected models |
| `foundry.py` | `/v1/foundry` | Foundry status |
| `foundry_management.py` | `/v1/foundry` | Start / stop Foundry service |
| `foundry_models.py` | `/v1/foundry/models` | Load / unload Foundry models |
| `rag.py` | `/v1/rag` | RAG status, search, build, profiles |
| `translation.py` | `/v1/translation` | Text translation (LLM / DeepL / Google / Helsinki) |
| `config.py` | `/v1/config` | Read / write config.json and .env |
| `logs.py` | `/v1/logs` | Log streaming |
| `hf_models.py` | `/v1/hf` | HuggingFace model download / inference |
| `llama_cpp.py` | `/v1/llama` | llama.cpp server control |
| `mcp_powershell.py` | `/v1/mcp-powershell` | PowerShell MCP server proxy |
| `agent.py` | `/v1/agent` | AI agent with tool calls |
| `converter.py` | `/v1/converter` | GGUF → ONNX conversion |

## Pattern

Each file registers its own `APIRouter`. Routers are imported and mounted in `src/api/app.py`:

```python
from .endpoints.translation import router as translation_router
app.include_router(translation_router, prefix="/v1")
```

All handlers return a consistent dict:

```python
# success
{"success": True, "data": ...}

# failure
{"success": False, "error": "Human-readable message"}
```
