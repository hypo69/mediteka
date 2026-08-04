# Client

**Файл:** `sdk/fastapi_foundry_sdk/client.py`  
**Тип:** `.py`

---

### `FastAPIFoundryClient` — Класс

```python
class FastAPIFoundryClient
```

Async client for FastAPI Foundry REST API.

Covers all endpoints exposed by the FastAPI Foundry server (port 9696).
Use as async context manager.

Example:
    >>> async with FastAPIFoundryClient("http://localhost:9696") as client:
    ...     health = await client.health()
    ...     response = await client.generate("What is Python?")
    ...     print(response["content"])

### `__init__` — Функция

```python
def __init__(self, base_url: str='http://localhost:9696', api_key: Optional[str]=None, timeout: int=60) -> None
```

### `__aenter__` — Функция

```python
async def __aenter__(self) -> 'FastAPIFoundryClient'
```

### `__aexit__` — Функция

```python
async def __aexit__(self, *args: Any) -> None
```

### `_get` — Функция

```python
async def _get(self, path: str) -> Dict[str, Any]
```

### `_post` — Функция

```python
async def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]
```

### `_patch` — Функция

```python
async def _patch(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]
```

### `health` — Функция

```python
async def health(self) -> Dict[str, Any]
```

GET /api/v1/health — service health check.

Returns:
    dict: status, foundry_status, llama_status, rag_status, models_count.

### `list_models` — Функция

```python
async def list_models(self) -> Dict[str, Any]
```

GET /api/v1/models — list all available models across all backends.

### `load_model` — Функция

```python
async def load_model(self, model_id: str) -> Dict[str, Any]
```

POST /api/v1/foundry/load — load a Foundry model.

Args:
    model_id: Model alias, e.g. 'phi-4' or 'qwen3-0.6b-generic-cpu:4:4'.

### `unload_model` — Функция

```python
async def unload_model(self, model_id: str) -> Dict[str, Any]
```

POST /api/v1/foundry/unload — unload a Foundry model.

### `foundry_models` — Функция

```python
async def foundry_models(self) -> Dict[str, Any]
```

GET /api/v1/foundry/models — list Foundry catalog models.

### `generate` — Функция

```python
async def generate(self, prompt: str, model: Optional[str]=None, temperature: float=0.7, max_tokens: int=2048, use_rag: bool=False, system_prompt: Optional[str]=None) -> Dict[str, Any]
```

POST /api/v1/generate — generate text with any backend model.

Args:
    prompt: Input text.
    model: Model ID (Foundry alias, 'hf::model', 'llama::model', 'ollama::model').
    temperature: Sampling temperature.
    max_tokens: Max output tokens.
    use_rag: Inject RAG context into prompt.
    system_prompt: Optional system instruction.

Returns:
    dict: success, content, model, usage.

### `batch_generate` — Функция

```python
async def batch_generate(self, prompts: List[str], model: Optional[str]=None, temperature: float=0.7, max_tokens: int=2048, use_rag: bool=False) -> Dict[str, Any]
```

POST /api/v1/batch-generate — generate text for multiple prompts.

Args:
    prompts: List of input texts.

Returns:
    dict: success, results (list), total, succeeded, failed.

### `rag_search` — Функция

```python
async def rag_search(self, query: str, top_k: int=5) -> Dict[str, Any]
```

POST /api/v1/rag/search — vector search in FAISS index.

Args:
    query: Search query text.
    top_k: Number of results to return.

Returns:
    dict: results (list of chunks with score, source, section).

### `rag_reload` — Функция

```python
async def rag_reload(self) -> Dict[str, Any]
```

POST /api/v1/rag/reload — reload FAISS index from disk.

### `rag_status` — Функция

```python
async def rag_status(self) -> Dict[str, Any]
```

GET /api/v1/rag/status — RAG system status.

### `get_config` — Функция

```python
async def get_config(self) -> Dict[str, Any]
```

GET /api/v1/config — read current config.json.

### `patch_config` — Функция

```python
async def patch_config(self, patch: Dict[str, Any]) -> Dict[str, Any]
```

PATCH /api/v1/config — update config values.

Args:
    patch: Flat dict with dot-notation keys, e.g.
           {'foundry_ai.default_model': 'phi-4', 'foundry_ai.temperature': 0.5}

### `hf_list_models` — Функция

```python
async def hf_list_models(self) -> Dict[str, Any]
```

GET /api/v1/hf/models — list downloaded HuggingFace models.

### `hf_generate` — Функция

```python
async def hf_generate(self, prompt: str, model_id: str, max_new_tokens: int=512, temperature: float=0.7) -> Dict[str, Any]
```

POST /api/v1/hf/generate — generate with HuggingFace Transformers.

Args:
    model_id: HuggingFace model ID, e.g. 'microsoft/phi-2'.

### `hf_load_model` — Функция

```python
async def hf_load_model(self, model_id: str) -> Dict[str, Any]
```

POST /api/v1/hf/load — load a HuggingFace model into memory.

### `llama_status` — Функция

```python
async def llama_status(self) -> Dict[str, Any]
```

GET /api/v1/llama/status — llama.cpp server status.

### `llama_generate` — Функция

```python
async def llama_generate(self, prompt: str, max_tokens: int=512, temperature: float=0.7) -> Dict[str, Any]
```

POST /api/v1/llama/generate — generate with llama.cpp (GGUF model).

### `llama_start` — Функция

```python
async def llama_start(self, model_path: str) -> Dict[str, Any]
```

POST /api/v1/llama/start — start llama.cpp server with a GGUF model.

Args:
    model_path: Absolute path to .gguf file.

### `llama_stop` — Функция

```python
async def llama_stop(self) -> Dict[str, Any]
```

POST /api/v1/llama/stop — stop llama.cpp server.

### `ollama_models` — Функция

```python
async def ollama_models(self) -> Dict[str, Any]
```

GET /api/v1/ollama/models — list Ollama models.

### `ollama_generate` — Функция

```python
async def ollama_generate(self, prompt: str, model: str, temperature: float=0.7, max_tokens: int=2048) -> Dict[str, Any]
```

POST /api/v1/ollama/generate — generate with Ollama.

### `agent_run` — Функция

```python
async def agent_run(self, task: str, agent_type: str='default') -> Dict[str, Any]
```

POST /api/v1/agent/run — run an AI agent task.

Args:
    task: Task description for the agent.
    agent_type: Agent type identifier.

### `mcp_status` — Функция

```python
async def mcp_status(self) -> Dict[str, Any]
```

GET /api/v1/mcp/status — MCP servers status.

### `mcp_execute` — Функция

```python
async def mcp_execute(self, server: str, command: str, params: Optional[Dict]=None) -> Dict[str, Any]
```

POST /api/v1/mcp/execute — execute a command on an MCP server.

Args:
    server: MCP server name (e.g. 'powershell-stdio').
    command: Command/tool name to execute.
    params: Optional parameters dict.

### `restart_service` — Функция

```python
async def restart_service(self, service: str) -> Dict[str, Any]
```

POST /api/v1/restart/{service} — restart a background service.

Args:
    service: One of 'foundry', 'llama', 'docs', 'rag'.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
