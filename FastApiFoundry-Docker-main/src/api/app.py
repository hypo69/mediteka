# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Assistant — Application Factory
# =============================================================================
# Description:
#   Orchestrator for local AI models (Foundry, HuggingFace, llama.cpp, Ollama, LM Studio).
#   Creates and configures the FastAPI application instance.
#   Manages lifespan (RAG init, session cleanup).
#   Registers all API routers under /api/v1 prefix.
#   Mounts static files and configures CORS + request-logging middleware.
#   Model routing by prefix: hf:: / llama:: / ollama:: / lmstudio:: / (none=Foundry).
#
# File: app.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Changes in 0.8.0:
#   - Added lmstudio:: backend support
#   - lmstudio_client session closed in lifespan shutdown
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import time
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from ..models.foundry_client import foundry_client
from ..rag.rag_system import rag_system
from ..logger import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle.

    Startup: initializes RAG system.
    Shutdown: closes aiohttp session of foundry_client.

    Args:
        app: FastAPI application instance.
    """
    logger.info("Starting FastAPI Foundry...")
    
    rag_initialized = await rag_system.initialize()
    if rag_initialized:
        logger.info("✅ RAG system initialized")
    else:
        logger.warning("⚠️ RAG system not initialized")

    # Auto-load default model if it points to a specific backend
    try:
        import asyncio
        from ..core.config import config as _cfg
        from ..models.hf_client import hf_client as _hf_client
        default_model: str = _cfg.foundry_default_model or ""

        if default_model.startswith("hf::"):
            # HuggingFace: load model into FastAPI process memory at startup
            hf_model_id = default_model[len("hf::"):]
            if hf_model_id:
                logger.info("🤗 Auto-loading HF default model: %s", hf_model_id)
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, _hf_client.load_model, hf_model_id)
                if result.get("success"):
                    logger.info("✅ HF model loaded: %s on %s", hf_model_id, result.get("device"))
                else:
                    logger.warning("⚠️ HF model auto-load failed: %s", result.get("error"))

        elif default_model and not default_model.startswith(("llama::", "ollama::", "lmstudio::", "hf::")):
            # Foundry model: auto-load if configured
            if _cfg.foundry_auto_load_default:
                import subprocess
                foundry_model_id = default_model.removeprefix("foundry::")
                logger.info("🤖 Auto-loading Foundry default model: %s", foundry_model_id)
                subprocess.Popen(
                    ["foundry", "model", "load", foundry_model_id],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
    except Exception as e:
        logger.warning("⚠️ Auto-load default model failed: %s", e)

    try:
        from ..core.config import config as _cfg
        if _cfg.get_section("opencode").get("auto_start", False):
            from ..models.opencode_client import opencode_client
            result = await opencode_client.start()
            if result.get("success"):
                logger.info("✅ OpenCode auto-started at %s", result.get("base_url"))
            else:
                logger.warning("⚠️ OpenCode auto-start failed: %s", result.get("error"))
    except Exception as e:
        logger.warning("⚠️ OpenCode auto-start failed: %s", e)

    print("\n" + "═" * 60)
    print("  ✅  FastAPI Foundry — startup complete")
    print("  🌐  http://localhost:9696")
    print("═" * 60 + "\n")

    yield
    
    logger.info("Stopping FastAPI Foundry...")
    await foundry_client.close()
    try:
        from ..models.lmstudio_client import lmstudio_client
        await lmstudio_client.close()
    except Exception:
        pass
    try:
        from ..models.opencode_client import opencode_client
        if opencode_client.pid:
            await opencode_client.stop()
    except Exception:
        pass

def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Mounts static files, adds CORS and request-logging middleware,
    registers global exception handler, and includes all API routers.

    Returns:
        FastAPI: Configured application instance ready for uvicorn.
    """
    
    app = FastAPI(
        title="AI Assistant",
        description="Local AI model orchestrator (Foundry, HuggingFace, llama.cpp, Ollama, LM Studio) with RAG",
        version="0.7.0",
        lifespan=lifespan
    )
    
    # Static files
    app.mount("/static/interface",  StaticFiles(directory="static/interface"),  name="static-interface")
    app.mount("/static/gui-install", StaticFiles(directory="static/gui-install"), name="static-install")
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -- API Key guard -------------------------------------------------------
    # When API_KEY env var is set, every /api/v1/* request must supply the key
    # via header X-API-Key or query param api_key.
    # /api/v1/security/api-key/* and /api/v1/health are always exempt.
    @app.middleware("http")
    async def api_key_guard(request: Request, call_next):
        required_key: str = os.environ.get("API_KEY", "").strip()
        if not required_key:
            return await call_next(request)
        path: str = request.url.path
        exempt = ("/static", "/docs", "/openapi.json", "/redoc",
                  "/api/v1/security/api-key", "/api/v1/health")
        if any(path.startswith(p) for p in exempt):
            return await call_next(request)
        if not path.startswith("/api/v1"):
            return await call_next(request)
        provided = (request.headers.get("X-API-Key", "")
                    or request.query_params.get("api_key", ""))
        if provided != required_key:
            return JSONResponse(status_code=401,
                content={"success": False, "error": "Invalid or missing API key"})
        return await call_next(request)

    # Middleware for request logging
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        import asyncio
        import logging
        logger = logging.getLogger(__name__)

        start_time = time.time()
        try:
            response = await call_next(request)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(
                "Unhandled request exception: %s %s: %s",
                request.method,
                request.url.path,
                exc,
                exc_info=True,
            )
            raise
        process_time = time.time() - start_time
        if response.status_code >= 500:
            logger.error(
                "HTTP %s %s -> %s (%.3fs)",
                request.method,
                request.url.path,
                response.status_code,
                process_time,
            )
        elif response.status_code >= 400:
            logger.warning(
                "HTTP %s %s -> %s (%.3fs)",
                request.method,
                request.url.path,
                response.status_code,
                process_time,
            )
        return response
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error("Unhandled application error at %s: %s", request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc)
            }
        )
    
    # Connect all routers
    from .endpoints import main, models, health, generate, foundry, config, logs, rag, opencode
    from .endpoints import install as install_router
    from .endpoints.ai_endpoints import router as ai_router
    from .endpoints.chat_endpoints import router as chat_router
    from .endpoints.translator import router as translator_router
    from .endpoints.foundry_management import router as foundry_mgmt_router
    from .endpoints.foundry_models import router as foundry_models_router
    from .endpoints.hf_models import router as hf_router
    from .endpoints.llama_cpp import router as llama_router
    from .endpoints.ollama import router as ollama_router
    from .endpoints.lmstudio import router as lmstudio_router
    from .endpoints.mcp_powershell import router as mcp_ps_router
    from .endpoints.agent import router as agent_router
    from .endpoints.converter import router as converter_router
    from .endpoints.system_stats import router as system_stats_router
    from .endpoints.support import router as support_router
    from .endpoints.helpdesk import router as helpdesk_router
    from .endpoints.mcp_agent_endpoints import router as mcp_agent_router
    from .endpoints.training import router as training_router
    from .endpoints.recommender import router as recommender_router
    from .endpoints.content_blocks import router as content_blocks_router
    from .endpoints.security import router as security_router
    from .endpoints.openai_models import router as openai_models_router

    app.include_router(main.router)
    app.include_router(install_router.page_router)          # GET /install  (no prefix)
    app.include_router(install_router.api_router, prefix="/api/v1")  # /api/v1/install/*
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(models.router, prefix="/api/v1")
    app.include_router(openai_models_router)                # GET /v1/models (OpenAI compat)
    app.include_router(foundry.router, prefix="/api/v1")
    app.include_router(foundry_mgmt_router, prefix="/api/v1")
    app.include_router(foundry_models_router, prefix="/api/v1")
    app.include_router(generate.router, prefix="/api/v1")
    app.include_router(ai_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(translator_router, prefix="/api/v1")
    app.include_router(rag.router, prefix="/api/v1")
    app.include_router(opencode.router, prefix="/api/v1")
    app.include_router(config.router, prefix="/api/v1")
    app.include_router(logs.router, prefix="/api/v1")
    app.include_router(hf_router, prefix="/api/v1")
    app.include_router(llama_router, prefix="/api/v1")
    app.include_router(ollama_router, prefix="/api/v1")
    app.include_router(lmstudio_router, prefix="/api/v1")
    app.include_router(mcp_ps_router, prefix="/api/v1")
    app.include_router(agent_router, prefix="/api/v1")
    app.include_router(converter_router, prefix="/api/v1")
    app.include_router(system_stats_router, prefix="/api/v1")
    app.include_router(support_router, prefix="/api/v1")
    app.include_router(helpdesk_router, prefix="/api/v1")
    app.include_router(mcp_agent_router, prefix="/api/v1")
    app.include_router(training_router, prefix="/api/v1")
    app.include_router(recommender_router, prefix="/api/v1")
    app.include_router(content_blocks_router, prefix="/api/v1")
    app.include_router(security_router, prefix="/api/v1")

    return app
