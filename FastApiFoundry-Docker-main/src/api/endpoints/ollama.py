# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Ollama Provider API Endpoints
# =============================================================================
# Description:
#   REST endpoints for managing Ollama local model server.
#   Ollama exposes an OpenAI-compatible API at /v1, so it can be used
#   as a drop-in provider alongside Foundry, HuggingFace, and llama.cpp.
#
# Examples:
#   GET  /api/v1/ollama/status
#   GET  /api/v1/ollama/models
#   POST /api/v1/ollama/models/pull    {"model": "qwen2.5:0.5b"}
#   POST /api/v1/ollama/models/delete  {"model": "qwen2.5:0.5b"}
#   POST /api/v1/ollama/generate       {"prompt": "Hello", "model": "qwen2.5:0.5b"}
#
# File: src/api/endpoints/ollama.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
from fastapi import APIRouter, HTTPException

from ...models.ollama_client import ollama_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ollama", tags=["ollama"])


@router.get("/status")
async def ollama_status() -> dict:
    """Ollama server status — running, version, URL.

    Returns:
        dict: success, running (bool), url, openai_url, version.
    """
    return await ollama_client.get_status()


@router.get("/models")
async def ollama_list_models() -> dict:
    """List locally available Ollama models.

    Returns:
        dict: success, models (list of {name, size_gb, modified_at, digest}), count.
    """
    return await ollama_client.list_models()


@router.post("/models/pull")
async def ollama_pull_model(request: dict) -> dict:
    """Pull (download) a model from Ollama Hub.

    Args:
        request: JSON body с полями:
            model (str): Model name, e.g. 'qwen2.5:0.5b' (обязательно).

    Returns:
        dict: success, model, status on success; success=False, error on failure.

    Raises:
        HTTPException 400: model не передан.
    """
    model: str = request.get("model", "")
    if not model:
        raise HTTPException(status_code=400, detail="model is required")
    logger.info(f"📥 Ollama pull requested: {model}")
    return await ollama_client.pull_model(model)


@router.post("/models/delete")
async def ollama_delete_model(request: dict) -> dict:
    """Delete a local Ollama model to free disk space.

    Args:
        request: JSON body с полями:
            model (str): Model name, e.g. 'qwen2.5:0.5b' (обязательно).

    Returns:
        dict: success, model on success; success=False, error on failure.

    Raises:
        HTTPException 400: model не передан.
    """
    model: str = request.get("model", "")
    if not model:
        raise HTTPException(status_code=400, detail="model is required")
    return await ollama_client.delete_model(model)


@router.post("/generate")
async def ollama_generate(request: dict) -> dict:
    """Generate text via Ollama.

    Args:
        request: JSON body с полями:
            model (str):       Model name (обязательно).
            prompt (str):      Input text (обязательно).
            max_tokens (int):  Max tokens to generate (default: 512).
            temperature (float): Sampling temperature (default: 0.7).

    Returns:
        dict: success, content, model on success; success=False, error on failure.

    Raises:
        HTTPException 400: model или prompt не переданы.
    """
    model: str = request.get("model", "")
    prompt: str = request.get("prompt", "")
    max_tokens: int = request.get("max_tokens", 512)
    temperature: float = request.get("temperature", 0.7)

    if not model:
        raise HTTPException(status_code=400, detail="model is required")
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    return await ollama_client.generate(prompt, model, max_tokens, temperature)
