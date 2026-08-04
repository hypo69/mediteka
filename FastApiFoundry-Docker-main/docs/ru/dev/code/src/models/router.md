# Router

**Файл:** `src/models/router.py`  
**Тип:** `.py`

---

### `detect_backend` — Функция

```python
def detect_backend(model: Optional[str]) -> tuple[str, str]
```

Detect backend and strip prefix from model ID.

Workflow:
    model string → prefix check → (backend_name, clean_id)

Args:
    model: Raw model string from request. Supported formats:
        - ``'foundry::qwen3-0.6b-generic-cpu:4'``
        - ``'hf::Qwen/Qwen2.5-0.5B-Instruct'``
        - ``'llama::D:/models/gemma-2b-q4.gguf'``
        - ``'ollama::qwen2.5:0.5b'``
        - ``'lmstudio::ibm/granite-4-micro'``
        - ``None`` or ``''`` → defaults to Foundry with empty model ID

Returns:
    tuple[str, str]: ``(backend, clean_model_id)``

        - ``backend``: one of ``'foundry'``, ``'hf'``, ``'llama'``, ``'ollama'``
        - ``clean_model_id``: model ID with prefix stripped

Example:
    >>> detect_backend("foundry::qwen3-0.6b")
    ('foundry', 'qwen3-0.6b')

    >>> detect_backend("hf::Qwen/Qwen2.5-0.5B")
    ('hf', 'Qwen/Qwen2.5-0.5B')

    >>> detect_backend("llama::D:/models/q4.gguf")
    ('llama', 'D:/models/q4.gguf')

    >>> detect_backend("ollama::mistral")
    ('ollama', 'mistral')

    >>> detect_backend("lmstudio::ibm/granite-4-micro")
    ('lmstudio', 'ibm/granite-4-micro')

    >>> detect_backend(None)
    ('foundry', '')

    >>> detect_backend("bare-model-id")  # legacy, warns
    ('foundry', 'bare-model-id')

### `_default_temperature` — Функция

```python
def _default_temperature() -> float
```

Return default temperature from config.defaults, fallback 0.7.

### `_default_max_tokens` — Функция

```python
def _default_max_tokens() -> int
```

Return default max_tokens from config.defaults, fallback 2048.

### `route_generate` — Функция

```python
async def route_generate(prompt: str, model: Optional[str]=None, temperature: Optional[float]=None, max_tokens: Optional[int]=None) -> dict
```

Route a generation request to the correct backend.

Workflow:
    prompt + model → detect_backend() → backend call → unified response

Args:
    prompt:      Input text (required, non-empty).
    model:       Model ID with prefix, e.g. ``'foundry::qwen3-0.6b'``.
                 If ``None``, routes to Foundry and uses its first loaded model.
    temperature: Sampling temperature (0.0–2.0, default from config.defaults.temperature).
    max_tokens:  Maximum tokens to generate (default from config.defaults.max_tokens).

Returns:
    dict: On success::

        {"success": True, "content": "...", "model": "foundry::...", "usage": {...}}

    On failure::

        {"success": False, "error": "description"}

    Special error on Foundry model not loaded::

        {"success": False, "error": "...", "error_code": "model_not_loaded", "model_id": "..."}

Example:
    >>> result = await route_generate("Hello", model="foundry::qwen3-0.6b")
    >>> result["success"]
    True

    >>> result = await route_generate("Summarize", model="hf::Qwen/Qwen2.5-0.5B")

    >>> result = await route_generate("Code review", model="ollama::codellama")

    >>> result = await route_generate("Translate", model="llama::D:/models/q4.gguf")

    >>> result = await route_generate("Summarize", model="lmstudio::ibm/granite-4-micro")

### `_generate_foundry` — Функция

```python
async def _generate_foundry(prompt: str, model: Optional[str], temperature: float, max_tokens: int) -> dict
```

Call Foundry Local backend.

Args:
    prompt: Input text.
    model: Foundry model ID (without prefix), or None to use first loaded.
    temperature: Sampling temperature.
    max_tokens: Max tokens to generate.

Returns:
    dict: Unified response with ``model`` prefixed as ``foundry::<id>``.

### `_generate_hf` — Функция

```python
async def _generate_hf(prompt: str, model: str, temperature: float, max_tokens: int) -> dict
```

Call HuggingFace Transformers backend.

Args:
    prompt: Input text.
    model: HuggingFace model ID (without prefix), e.g. ``'Qwen/Qwen2.5-0.5B'``.
    temperature: Sampling temperature.
    max_tokens: Max new tokens to generate.

Returns:
    dict: Unified response with ``model`` prefixed as ``hf::<id>``.

### `_generate_llama` — Функция

```python
async def _generate_llama(prompt: str, model: str, temperature: float, max_tokens: int) -> dict
```

Call llama.cpp backend via its OpenAI-compatible HTTP API.

Requires llama.cpp server to be running (started via ``/api/v1/llama/start``).

Args:
    prompt: Input text.
    model: Path to GGUF file (without prefix), used only for response labeling.
    temperature: Sampling temperature.
    max_tokens: Max tokens to generate.

Returns:
    dict: Unified response with ``model`` prefixed as ``llama::<path>``.

### `_generate_ollama` — Функция

```python
async def _generate_ollama(prompt: str, model: str, temperature: float, max_tokens: int) -> dict
```

Call Ollama backend.

Requires Ollama service running locally (default port 11434).

Args:
    prompt: Input text.
    model: Ollama model name (without prefix), e.g. ``'qwen2.5:0.5b'``.
    temperature: Sampling temperature.
    max_tokens: Max tokens to generate.

Returns:
    dict: Unified response with ``model`` prefixed as ``ollama::<name>``.

### `_generate_lmstudio` — Функция

```python
async def _generate_lmstudio(prompt: str, model: str, temperature: float, max_tokens: int) -> dict
```

Call LM Studio backend via native REST API v1.

Requires LM Studio server running locally (default http://localhost:1234).

Args:
    prompt: Input text.
    model: LM Studio model key (without prefix), e.g. ``'ibm/granite-4-micro'``.
    temperature: Sampling temperature.
    max_tokens: Max output tokens.

Returns:
    dict: Unified response with ``model`` prefixed as ``lmstudio::<key>``.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
