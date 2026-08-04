# App

**Файл:** `src/api/app.py`  
**Тип:** `.py`

---

### `lifespan` — Функция

```python
@asynccontextmanager
```

Manage application lifecycle.

Startup: initializes RAG system.
Shutdown: closes aiohttp session of foundry_client.

Args:
    app: FastAPI application instance.

### `create_app` — Функция

```python
def create_app() -> FastAPI
```

Create and configure the FastAPI application.

Mounts static files, adds CORS and request-logging middleware,
registers global exception handler, and includes all API routers.

Returns:
    FastAPI: Configured application instance ready for uvicorn.

### `api_key_guard` — Функция

```python
@app.middleware('http')
```

### `log_requests` — Функция

```python
@app.middleware('http')
```

### `global_exception_handler` — Функция

```python
@app.exception_handler(Exception)
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
