# Hf Client

**Файл:** `src/models/hf_client.py`  
**Тип:** `.py`

---

### `_get_models_dir` — Функция

```python
def _get_models_dir() -> Path
```

Return HuggingFace models directory.

Priority:
    1. ``directories.hf_models`` from config.json
    2. ``HF_MODELS_DIR`` environment variable (legacy)
    3. ``~/.cache/huggingface/hub`` default (standard HuggingFace cache)

Returns:
    Path: Resolved absolute path to the models directory.

### `_check_transformers` — Функция

```python
def _check_transformers() -> bool
```

Check availability of the transformers library.

Returns:
    bool: True if installed, False otherwise.

### `_check_huggingface_hub` — Функция

```python
def _check_huggingface_hub() -> bool
```

Check availability of the huggingface_hub library.

Returns:
    bool: True if installed, False otherwise.

### `HFClient` — Класс

```python
class HFClient
```

Client for local HuggingFace models.

Responsible for:
- Downloading models via ``huggingface_hub.snapshot_download`` to ``HF_MODELS_DIR``
- Listing cached models via ``huggingface_hub.scan_cache_dir`` (official API)
- Loading into memory via ``transformers.pipeline``
- Inference via loaded pipeline with chat template support
- Unloading from memory with CUDA cache clearing

Global singleton ``hf_client`` is created at module level and shared
across the entire FastAPI process.

Example:
    >>> from src.models.hf_client import hf_client
    >>> hf_client.download_model("Qwen/Qwen2.5-0.5B-Instruct")
    {"success": True, "model_id": "Qwen/Qwen2.5-0.5B-Instruct", "path": "..."}
    >>> hf_client.load_model("Qwen/Qwen2.5-0.5B-Instruct", device="auto")
    {"success": True, "model_id": "Qwen/Qwen2.5-0.5B-Instruct", "device": "cpu"}
    >>> import asyncio
    >>> asyncio.run(hf_client.generate("Hello", model_id="Qwen/Qwen2.5-0.5B-Instruct"))
    {"success": True, "content": "...", "model": "Qwen/Qwen2.5-0.5B-Instruct"}

### `download_model` — Функция

```python
def download_model(self, model_id: str, token: Optional[str]=None, progress_callback: Optional[object]=None) -> dict
```

Download model via huggingface_hub.snapshot_download.

Token is taken from HF_TOKEN in .env.
Model is saved in HF_MODELS_DIR/<author>--<name>.

Args:
    model_id: e.g., 'mistralai/Mistral-7B-Instruct-v0.3'.
    token:    Optional overriding token.
    progress_callback: Optional callable receiving progress event dicts.

Returns:
    dict: {"success": bool, "model_id": str, "path": str, "error": str}

### `load_model` — Функция

```python
def load_model(self, model_id: str, device: str='auto') -> dict
```

Load model into memory for inference.

Uses ``snapshot_download(local_files_only=True)`` to resolve the correct
local snapshot path via the official HuggingFace API. Falls back to manual
snapshot directory search if the API call fails.

Args:
    model_id: Model ID (e.g. 'Qwen/Qwen2.5-0.5B-Instruct') or local path.
    device:   'auto', 'cpu', or 'cuda'.

Returns:
    dict: {"success": bool, "model_id": str, "device": str}

### `unload_model` — Функция

```python
def unload_model(self, model_id: str) -> dict
```

Unload model from memory and free RAM/VRAM.

Args:
    model_id: ID of the loaded model.

Returns:
    dict: {"success": bool, "model_id": str}

### `generate` — Функция

```python
async def generate(self, prompt: str, model_id: str, max_new_tokens: int=512, temperature: float=0.7) -> dict
```

Generate text via a loaded HuggingFace model.

Applies ``tokenizer.apply_chat_template()`` when the tokenizer supports it
(i.e. ``tokenizer.chat_template`` is set). This is required for correct
behaviour with instruction-tuned models (Qwen, Llama, Gemma, Mistral, etc.).
Falls back to the raw prompt for base models without a chat template.

Args:
    prompt:         User input text.
    model_id:       ID of the model to use (must be loaded).
    max_new_tokens: Maximum number of new tokens to generate.
    temperature:    Sampling temperature (0 = greedy, >0 = sampling).

Returns:
    dict: {"success": bool, "content": str, "model": str}

Example:
    >>> result = await hf_client.generate(
    ...     "Explain quantum entanglement",
    ...     model_id="Qwen/Qwen2.5-0.5B-Instruct",
    ... )
    >>> result["content"]
    'Quantum entanglement is...'

### `list_downloaded` — Функция

```python
def list_downloaded(self) -> list
```

List models downloaded to the local HuggingFace cache.

Uses ``huggingface_hub.scan_cache_dir()`` (official API) to enumerate
cached repositories. Falls back to manual filesystem scan if the API
call fails (e.g. older huggingface_hub version or corrupted cache).

Scans both ``HF_MODELS_DIR`` and ``~/.cache/huggingface/hub`` when they
differ, deduplicating results by model ID.

Returns:
    list: [{"id": str, "path": str, "loaded": bool, "size_mb": float, "source": str}]

Example:
    >>> hf_client.list_downloaded()
    [{"id": "Qwen/Qwen2.5-0.5B-Instruct", "path": "...", "loaded": False,
      "size_mb": 987.3, "source": "/home/user/.cache/huggingface/hub"}]

### `list_loaded` — Функция

```python
def list_loaded(self) -> list
```

List models currently loaded into memory.

Returns:
    list: [{"id": str, "status": "loaded"}]

### `_dir_size_mb` — Функция

```python
def _dir_size_mb(d: Path) -> float
```

### `_scan_dir` — Функция

```python
def _scan_dir(base: Path, source: str) -> list
```

### `_run` — Функция

```python
def _run() -> str
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
