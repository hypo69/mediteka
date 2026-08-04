# Copilot instructions for FastApiFoundry-Docker

This file gives concise, actionable guidance for AI coding agents working in this repository.

1) Purpose and big picture
- Service: a FastAPI-based REST server that exposes local AI models (Foundry) and a RAG (FAISS) retrieval layer.
- Key runtime flow: application factory (`src/api/app.py`) sets up lifespan hooks -> initializes `rag_system` -> checks `foundry_client` -> mounts routers under `/api/v1`.

2) High-value files and where to look first
- Project overview: [README.md](README.md)
- App factory & routers: [src/api/app.py](src/api/app.py) and [src/api/main.py](src/api/main.py)
- Configuration: [src/core/config.py](src/core/config.py) (Pydantic `Settings`, reads `.env`)
- Model management: [src/models/model_manager.py](src/models/model_manager.py) and [src/models/foundry_client.py](src/models/foundry_client.py)
- RAG: [src/rag/rag_system.py](src/rag/rag_system.py) and `rag_index/`
- Logging: [src/utils/logging_system.py](src/utils/logging_system.py) — structured JSONL logs in `logs/`
- Entry scripts: `run.py` (dev/run helper) and `docker-compose.yml` (containerized runs)

3) Developer workflows (concrete commands)
- Local dev (recommended):
	- Create venv and install: `pip install -r requirements.txt`
	- Launch: `python run.py` (this sets `FASTAPI_FOUNDRY_MODE=dev`, tries to free the port, and opens the browser)
	- Or run uvicorn directly: `uvicorn src.api.main:app --reload --port 8000` (settings in `src/core/config.py`)
- Docker: `docker-compose up -d` or `docker-compose up --build -d` to rebuild
- Tests: `pytest` (tests are standard FastAPI TestClient tests in `tests/` when present)

4) Project-specific conventions and patterns
- API routers are grouped and mounted with prefixes; most API endpoints use `/api/v1` (see `app.include_router(..., prefix="/api/v1")`).
- Use `get_logger` from `src/utils/logging_system.py` for new modules to keep structured logs and JSONL output.
- Config comes from environment variables and `.env` via Pydantic `Settings` in `src/core/config.py` — add new config fields there.
- Add endpoints by creating a new module in `src/api/endpoints/` and importing it in `src/api/app.py` (see `docs/development.md` examples).
- RAG index lives under `rag_index/` and is managed by `src/rag/rag_system.py`; avoid hard-coding paths — use `settings.rag_index_dir`.

5) Integration points and external dependencies
- Foundry LLM API: `FOUNDRY_BASE_URL` and model settings in `src/core/config.py`.
- RAG uses FAISS index files in `rag_index/` and transformer/embedder models (see `settings.rag_model`).
- MCP integrations live in `mcp-servers/` (e.g. `mcp-servers/Ai Assistant-foundry/`) and may run separate servers that the main app talks to.

6) Debugging & common fixes
- If import errors occur, run `pip install -r requirements.txt` and re-run `python run.py` (the script logs import failures). See `run.py` for port-killing helper and SSL checks.
- Check structured logs in `logs/` and `logs/*-structured.jsonl` for machine-readable traces.
- To change logging mode, set `FASTAPI_FOUNDRY_MODE` env var (defaults to `dev`).

7) What to edit and how to test small changes
- Add endpoint: create `src/api/endpoints/my_feature.py`, then add `from .endpoints import my_feature` and `app.include_router(my_feature.router, prefix="/api/v1")` in `src/api/app.py`.
- Add config: update `src/core/config.py` `Settings` with a new Field and reference `settings.<name>` in code.
- Add dependency: append to `requirements.txt` and include rebuild instructions in docs or Dockerfile if necessary.

8) Style and safety
- Keep handlers async when performing I/O (consistent with FastAPI/uvicorn). Follow existing Pydantic models in `src/api/models.py` for request/response shapes.
- Avoid exposing secrets in code; prefer `.env` and `src/core/config.py` env bindings.

9) Quick checklist for PRs
- Run lint/tests locally, verify `python run.py` starts, and check `http://localhost:8000/docs`.
- Update `requirements.txt` and `README.md` when adding runtime deps or new top-level behavior.

If any area above is unclear or you'd like more examples (router, logging, or RAG index lifecycle), tell me which section to expand.

