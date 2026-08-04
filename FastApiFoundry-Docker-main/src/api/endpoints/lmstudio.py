# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LM Studio Provider API Endpoints
# =============================================================================
# Description:
#   REST endpoints for managing LM Studio local model server through its
#   native /api/v1 REST API.
#
# File: src/api/endpoints/lmstudio.py
# Project: Ai Assistant (Docker)
# =============================================================================

import logging

from fastapi import APIRouter, HTTPException

from ...models.lmstudio_client import lmstudio_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lmstudio", tags=["lmstudio"])


@router.get("/status")
async def lmstudio_status() -> dict:
    """LM Studio server status."""
    return await lmstudio_client.get_status()


@router.get("/models")
async def lmstudio_list_models() -> dict:
    """List LM Studio models."""
    return await lmstudio_client.list_models()


@router.post("/models/load")
async def lmstudio_load_model(request: dict) -> dict:
    """Load a model in LM Studio."""
    model: str = request.get("model", "")
    if not model:
        raise HTTPException(status_code=400, detail="model is required")

    options = {
        "context_length": request.get("context_length"),
        "eval_batch_size": request.get("eval_batch_size"),
        "flash_attention": request.get("flash_attention"),
        "num_experts": request.get("num_experts"),
        "offload_kv_cache_to_gpu": request.get("offload_kv_cache_to_gpu"),
        "echo_load_config": request.get("echo_load_config"),
    }
    logger.info("LM Studio load requested: %s", model)
    return await lmstudio_client.load_model(model, **options)


@router.post("/models/unload")
async def lmstudio_unload_model(request: dict) -> dict:
    """Unload a loaded LM Studio model instance."""
    instance_id: str = request.get("instance_id", "")
    if not instance_id:
        raise HTTPException(status_code=400, detail="instance_id is required")
    return await lmstudio_client.unload_model(instance_id)


@router.post("/models/download")
async def lmstudio_download_model(request: dict) -> dict:
    """Start an LM Studio model download job."""
    model: str = request.get("model", "")
    if not model:
        raise HTTPException(status_code=400, detail="model is required")
    return await lmstudio_client.download_model(model, request.get("quantization", ""))


@router.get("/models/download/status/{job_id}")
async def lmstudio_download_status(job_id: str) -> dict:
    """Get LM Studio model download status."""
    return await lmstudio_client.download_status(job_id)


@router.post("/generate")
async def lmstudio_generate(request: dict) -> dict:
    """Generate text through LM Studio /api/v1/chat."""
    prompt: str = request.get("prompt", "")
    model: str = request.get("model", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    if not model:
        raise HTTPException(status_code=400, detail="model is required")

    return await lmstudio_client.generate(
        prompt=prompt,
        model=model,
        temperature=request.get("temperature", 0.7),
        max_tokens=request.get("max_tokens", 512),
        context_length=request.get("context_length"),
        reasoning=request.get("reasoning"),
        previous_response_id=request.get("previous_response_id"),
    )
