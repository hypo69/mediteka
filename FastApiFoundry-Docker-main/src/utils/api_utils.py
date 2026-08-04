# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: API Utilities — Response Handler
# =============================================================================
# Description:
#   Shared decorator for FastAPI endpoints.
#   Normalises all endpoint responses to a consistent shape:
#     {"success": bool, ...payload}
#
#   Workflow:
#     endpoint() → result
#       ├─ dict without "success" → inject "success": True
#       ├─ dict with "success"    → return as-is
#       ├─ None                   → {"success": True}
#       ├─ HTTPException          → {"success": False, "error": detail}
#       └─ Exception              → {"success": False, "error": str(e)}  + log
#
# File: src/utils/api_utils.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Added workflow diagram to header
#   - Enriched docstring with examples
#   - Added return type annotation
# Changes in 0.6.0:
#   - MIT License update
#   - Unified headers
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import functools
import logging
from typing import Any, Callable
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def api_response_handler(func: Callable) -> Callable:
    """Decorator that normalises FastAPI endpoint responses.

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
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> dict:
        try:
            result = await func(*args, **kwargs)

            if isinstance(result, dict):
                # Inject success flag only if missing
                if "success" not in result:
                    return {"success": True, **result}
                return result

            # None return → background task started or no payload
            if result is None:
                return {"success": True}

            return result

        except HTTPException as e:
            # FastAPI HTTP errors — return as structured failure
            return {"success": False, "error": e.detail}

        except Exception as e:
            # Unexpected errors — log with full traceback, return safe message
            logger.exception(f"Unhandled API error in {func.__name__}: {e}")
            return {"success": False, "error": str(e)}

    return wrapper
