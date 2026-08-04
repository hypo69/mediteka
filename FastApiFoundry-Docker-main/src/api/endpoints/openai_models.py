# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: OpenAI-Compatible Models Endpoint
# =============================================================================
# Description:
#   GET /v1/models              — all local models in OpenAI format
#
#   Aggregates data from:
#     - Foundry Local  (cached on disk)  → prefix foundry::
#     - HuggingFace    (downloaded)      → prefix hf::
#     - llama.cpp      (GGUF on disk)    → prefix llama::
#     - Ollama         (local models)    → prefix ollama::
#
#   Maps provider-prefixed IDs to OpenAI-compatible format:
#     foundry::model-id → foundry-model-id
#     hf::model-id      → hf-model-id
#     llama::path.gguf  → llama-path.gguf
#     ollama::model     → ollama-model
#
# File: openai_models.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
import time
import asyncio
import json
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ...models.router import route_generate

logger = logging.getLogger(__name__)
router = APIRouter()


async def _safe_get(coro) -> dict:
    """Execute a coroutine and return its result or empty dict on failure."""
    try:
        return await coro
    except Exception:
        return {"success": False}


def map_to_openai_id(provider_prefixed_id: str) -> str:
    """Convert provider-prefixed ID to OpenAI-compatible format.
    
    Replaces '::' with '-' for provider prefixes.
    Non-prefixed IDs pass through unchanged.
    
    Args:
        provider_prefixed_id: Model ID with provider prefix (e.g., 'foundry::model-id')
    
    Returns:
        OpenAI-compatible model ID (e.g., 'foundry-model-id')
    """
    if "::" not in provider_prefixed_id:
        return provider_prefixed_id
    return provider_prefixed_id.replace("::", "-", 1)


def map_from_openai_id(openai_id: str) -> str:
    """Convert an OpenAI-facing model ID back to the internal provider prefix."""
    for provider in ("foundry", "hf", "llama", "ollama", "lmstudio"):
        prefix = f"{provider}-"
        if openai_id.startswith(prefix):
            return f"{provider}::{openai_id[len(prefix):]}"
    return openai_id


async def _safe_collect(coro) -> list:
    """Execute collection coroutine and return empty list on failure."""
    try:
        result = await coro
        return result if isinstance(result, list) else []
    except Exception as e:
        logger.error("Provider collection failed: %s", e)
        return []


async def _collect_foundry() -> list:
    """Get Foundry cached models with foundry:: prefix."""
    from .foundry_models import list_cached_models
    data = await _safe_get(list_cached_models())
    models = []
    for m in data.get("items", []):
        mid = m.get("id", "")
        if not mid:
            continue
        models.append({
            "id":       f"foundry::{mid}",
            "name":     m.get("name") or m.get("alias") or mid,
            "provider": "foundry",
            "prefix":   f"foundry::{mid}",
            "loaded":   m.get("loaded", False),
            "cached":   True,
            "size":     m.get("size", ""),
            "device":   m.get("device", ""),
        })
    return models


async def _collect_hf() -> list:
    """Get HuggingFace downloaded models with hf:: prefix."""
    from ...models.hf_client import hf_client
    downloaded = hf_client.list_downloaded()
    loaded_ids = {m.get("id") for m in hf_client.list_loaded()}
    models = []
    for m in downloaded:
        mid = m.get("id", "")
        if not mid:
            continue
        models.append({
            "id":       f"hf::{mid}",
            "name":     mid,
            "provider": "huggingface",
            "prefix":   f"hf::{mid}",
            "loaded":   mid in loaded_ids,
            "cached":   True,
            "size":     f"{m.get('size_mb', '')} MB" if m.get("size_mb") else "",
            "device":   "",
        })
    return models


async def _collect_llama() -> list:
    """Get llama.cpp GGUF models with llama:: prefix."""
    from .llama_cpp import llama_scan_models, llama_status
    disk_data = await _safe_get(llama_scan_models())
    status_data = await _safe_get(llama_status())
    running = status_data.get("running", False)
    loaded_name = status_data.get("model_name", "") if running else ""
    models = []
    for m in disk_data.get("models", []):
        mid = m.get("path") or m.get("name", "")
        if not mid:
            continue
        name = m.get("name") or mid.split("/")[-1].split("\\")[-1]
        is_loaded = running and (loaded_name == mid or loaded_name == m.get("name"))
        models.append({
            "id":       f"llama::{mid}",
            "name":     name,
            "provider": "llama.cpp",
            "prefix":   f"llama::{mid}",
            "loaded":   is_loaded,
            "cached":   True,
            "size":     f"{m.get('size_gb', '')} GB" if m.get("size_gb") else "",
            "device":   m.get("dir", ""),
        })
    return models


async def _collect_ollama() -> list:
    """Get Ollama local models with ollama:: prefix."""
    from ...models.ollama_client import ollama_client
    data = await _safe_get(ollama_client.list_models())
    models = []
    for m in data.get("models", []):
        mid = m.get("name") or m.get("id", "")
        if not mid:
            continue
        models.append({
            "id":       f"ollama::{mid}",
            "name":     mid,
            "provider": "ollama",
            "prefix":   f"ollama::{mid}",
            "loaded":   False,
            "cached":   True,
            "size":     f"{m.get('size_gb', '')} GB" if m.get("size_gb") else "",
            "device":   "",
        })
    return models


async def collect_all_models() -> List[Dict[str, Any]]:
    """Collect models from all providers.
    
    Uses asyncio.gather to collect from all providers concurrently.
    Continues processing if individual providers fail.
    
    Returns:
        List of all models from all providers
    """
    results = await asyncio.gather(
        _safe_collect(_collect_foundry()),
        _safe_collect(_collect_hf()),
        _safe_collect(_collect_llama()),
        _safe_collect(_collect_ollama()),
        return_exceptions=True,
    )
    
    models = []
    for result in results:
        if isinstance(result, list):
            models.extend(result)
    
    logger.info("Collected %d models from all providers", len(models))
    return models


def build_openai_response(models: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build OpenAI-compatible response from internal models.
    
    Args:
        models: List of provider model objects
    
    Returns:
        OpenAI-compatible response with data array, total count, and by_provider breakdown
    """
    data = []
    by_provider: Dict[str, int] = {}
    
    for model in models:
        openai_id = map_to_openai_id(model["id"])
        data.append({
            "id": openai_id,
            "object": "model",
            "created": int(time.time()),
            "owned_by": model["provider"]
        })
        provider = model["provider"]
        by_provider[provider] = by_provider.get(provider, 0) + 1
    
    return {
        "data": data,
        "total": len(data),
        "by_provider": by_provider
    }


@router.get("/v1/models")
async def get_openai_models() -> Dict[str, Any]:
    """Get models in OpenAI-compatible format.
    
    Returns a list of all available models from all providers in the OpenAI API format.
    The response includes:
    - data: Array of model objects with id, object, created, and owned_by fields
    - total: Total number of models
    - by_provider: Object with model counts per provider
    
    Returns:
        OpenAI-compatible response dictionary
    """
    try:
        models = await collect_all_models()
        response = build_openai_response(models)
        return response
    except Exception as e:
        logger.error("Error collecting models: %s", e, exc_info=True)
        return {"data": [], "total": 0}


@router.post("/v1/chat/completions")
async def create_chat_completion(request: Dict[str, Any]) -> Any:
    """OpenAI-compatible chat completions endpoint for external tools.

    This is intentionally small and routes through the existing backend router,
    so OpenCode and other OpenAI-compatible clients can use FastAPI Foundry as
    their single local provider.
    """
    messages = request.get("messages") or []
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="messages is required")

    prompt_parts: list[str] = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, list):
            content = "\n".join(
                str(part.get("text", "")) if isinstance(part, dict) else str(part)
                for part in content
            )
        if content:
            prompt_parts.append(f"{role.title()}: {content}")

    prompt = "\n".join(prompt_parts).strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="message content is required")

    model = request.get("model")
    internal_model = map_from_openai_id(model) if isinstance(model, str) and model else None

    result = await route_generate(
        prompt=prompt,
        model=internal_model,
        temperature=request.get("temperature", 0.7),
        max_tokens=request.get("max_tokens", request.get("max_completion_tokens", 2048)),
    )
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "generation failed"))

    response_model = model or result.get("model") or "default"
    now = int(time.time())
    content = result.get("content", "")

    if request.get("stream"):
        async def stream_response():
            chunk = {
                "id": f"chatcmpl-{now}",
                "object": "chat.completion.chunk",
                "created": now,
                "model": response_model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": content},
                        "finish_reason": None,
                    }
                ],
            }
            final_chunk = {
                "id": f"chatcmpl-{now}",
                "object": "chat.completion.chunk",
                "created": now,
                "model": response_model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_response(), media_type="text/event-stream")

    return {
        "id": f"chatcmpl-{now}",
        "object": "chat.completion",
        "created": now,
        "model": response_model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": result.get("usage", {}),
    }

