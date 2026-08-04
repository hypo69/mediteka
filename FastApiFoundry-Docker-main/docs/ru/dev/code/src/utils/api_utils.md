# Api Utils

**Файл:** `src/utils/api_utils.py`  
**Тип:** `.py`

---

### `api_response_handler` — Функция

```python
def api_response_handler(func: Callable) -> Callable
```

Decorator that normalises FastAPI endpoint responses.

Ensures every endpoint returns ``{"success": bool, ...}`` regardless of
whether the handler raises an exception or returns a plain dict.

Workflow::

    @router.post("/generate")
    @api_response_handler          ← wraps the handler
    async def generate(req: dict) -> dict:
        ...
        return {"content": "..."}  ← "success": True injected automatically

Args:
    func: Async endpoint function to wrap.

Returns:
    Callable: Wrapped async function with unified response shape.

Example:
    Basic usage — success flag injected automatically::

        @router.get("/status")
        @api_response_handler
        async def get_status() -> dict:
            return {"status": "ok"}
        # → {"success": True, "status": "ok"}

    Explicit success flag — returned as-is::

        @router.post("/generate")
        @api_response_handler
        async def generate(req: dict) -> dict:
            return {"success": True, "content": "Hello"}
        # → {"success": True, "content": "Hello"}

    Failure — return error dict::

        @router.post("/load")
        @api_response_handler
        async def load_model(req: dict) -> dict:
            return {"success": False, "error": "Model not found"}
        # → {"success": False, "error": "Model not found"}

    Exception — caught and converted::

        @router.get("/risky")
        @api_response_handler
        async def risky() -> dict:
            raise ValueError("Something broke")
        # → {"success": False, "error": "Something broke"}

### `wrapper` — Функция

```python
@functools.wraps(func)
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
