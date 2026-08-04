# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Models Aggregation Endpoint
# =============================================================================
# Description:
#   GET /api/v1/models          — all local models from all providers with prefixes
#   GET /api/v1/models/connected — connected/loaded models only
#
#   Aggregates data from:
#     - Foundry Local  (cached on disk)  → prefix foundry::
#     - HuggingFace    (downloaded)      → prefix hf::
#     - llama.cpp      (GGUF on disk)    → prefix llama::
#     - Ollama         (local models)    → prefix ollama::
#
# Examples:
#   >>> import requests
#   >>> models = requests.get('http://localhost:9696/api/v1/models').json()['models']
#   >>> [m['id'] for m in models]
#   ['foundry::qwen3-0.6b-generic-cpu:4', 'hf::Qwen/Qwen2.5-0.5B-Instruct', ...]
#
# File: models.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Changes in 0.8.0:
#   - Rewritten to aggregate all providers (Foundry, HF, llama.cpp, Ollama)
#   - All models now include provider prefix in id field
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


async def _safe_get(coro) -> dict:
    """Execute a coroutine and return its result or empty dict on failure."""
    try:
        return await coro
    except Exception:
        return {"success": False}


async def _collect_foundry() -> list[dict]:
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


async def _collect_hf() -> list[dict]:
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


async def _collect_llama() -> list[dict]:
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


async def _collect_ollama() -> list[dict]:
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


@router.post("/models/{model_id:path}/load")
async def load_model(model_id: str) -> dict:
    """Prepare a model by prefixed model id.

    Routes to the correct backend by prefix in the URL path.
    For Foundry this performs a warm-up inference request, because Foundry
    Local does not expose a reliable HTTP load-into-RAM endpoint.

    Args:
        model_id: Provider-prefixed model id, e.g.:
            foundry::qwen3-0.6b-generic-cpu:4
            hf::Qwen/Qwen2.5-0.5B-Instruct
            llama::D:/models/gemma-4-E4B-it-Q4_K_M.gguf
            ollama::qwen2.5:0.5b

    Returns:
        dict: success, model_id, provider, status on success; success=False, error on failure.

    Examples:
        POST /api/v1/models/foundry::qwen3-0.6b-generic-cpu:4/load
        POST /api/v1/models/hf::Qwen%2FQwen2.5-0.5B-Instruct/load
        POST /api/v1/models/llama::D:%2Fmodels%2Fgemma.gguf/load
        POST /api/v1/models/ollama::qwen2.5:0.5b/load
    """
    if "::" not in model_id:
        return {"success": False, "error": f"model_id must include provider prefix (foundry::, hf::, llama::, ollama::), got: {model_id}"}

    prefix, clean_id = model_id.split("::", 1)

    if prefix == "foundry":
        from .foundry_models import load_model as foundry_load
        result = await foundry_load({"model_id": clean_id})
        return {**result, "provider": "foundry", "model_id": model_id}

    if prefix == "hf":
        import asyncio
        from ...models.hf_client import hf_client
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: hf_client.load_model(clean_id, "auto")
        )
        return {**result, "provider": "huggingface", "model_id": model_id}

    if prefix == "llama":
        from .llama_cpp import llama_start
        result = await llama_start({"model_path": clean_id})
        return {**result, "provider": "llama.cpp", "model_id": model_id}

    if prefix == "ollama":
        from ...models.ollama_client import ollama_client
        result = await ollama_client.pull_model(clean_id)
        return {**result, "provider": "ollama", "model_id": model_id}

    return {"success": False, "error": f"Unknown provider prefix: '{prefix}'. Use foundry::, hf::, llama:: or ollama::"}


@router.post("/models/{model_id:path}/unload")
async def unload_model(model_id: str) -> dict:
    """Unload a model from memory by prefixed model id.

    Args:
        model_id: Provider-prefixed model id in the URL path.

    Returns:
        dict: success, model_id, provider on success; success=False, error on failure.

    Examples:
        POST /api/v1/models/hf::Qwen%2FQwen2.5-0.5B-Instruct/unload
        POST /api/v1/models/foundry::qwen3-0.6b-generic-cpu:4/unload
    """
    if "::" not in model_id:
        return {"success": False, "error": f"model_id must include provider prefix, got: {model_id}"}

    prefix, clean_id = model_id.split("::", 1)

    if prefix == "foundry":
        from .foundry_models import unload_model as foundry_unload
        result = await foundry_unload({"model_id": clean_id})
        return {**result, "provider": "foundry", "model_id": model_id}

    if prefix == "hf":
        from ...models.hf_client import hf_client
        result = hf_client.unload_model(clean_id)
        return {**result, "provider": "huggingface", "model_id": model_id}

    if prefix == "llama":
        from .llama_cpp import llama_stop
        result = await llama_stop()
        return {**result, "provider": "llama.cpp", "model_id": model_id}

    if prefix == "ollama":
        return {"success": True, "provider": "ollama", "model_id": model_id, "message": "Ollama manages memory automatically"}

    return {"success": False, "error": f"Unknown provider prefix: '{prefix}'. Use foundry::, hf::, llama:: or ollama::"}


@router.get("/models")
async def get_all_models() -> dict:
    """Get all local models from all providers with provider prefixes.

    Returns a flat list of all models grouped by provider.
    Each model id includes the routing prefix (foundry::, hf::, llama::, ollama::).

    Returns:
        dict: success, models (list), count, by_provider (dict with counts per provider).
    """
    import asyncio
    results = await asyncio.gather(
        _collect_foundry(),
        _collect_hf(),
        _collect_llama(),
        _collect_ollama(),
        return_exceptions=True,
    )

    models: list[dict] = []
    by_provider: dict[str, int] = {}
    for result in results:
        if isinstance(result, list):
            models.extend(result)
            for m in result:
                p = m["provider"]
                by_provider[p] = by_provider.get(p, 0) + 1

    return {"success": True, "models": models, "count": len(models), "by_provider": by_provider}


@router.get("/models/connected")
async def get_connected_models() -> dict:
    """Get models currently ready/connected across providers.

    For Foundry, this uses `foundry service list` through
    /foundry/models/loaded so the result is the runtime loaded set.

    Returns:
        dict: success, models (list), count.
    """
    import asyncio
    from ...models.hf_client import hf_client
    from .foundry_models import list_loaded_models as _foundry_loaded
    from .llama_cpp import llama_status as _llama_status

    results = await asyncio.gather(
        _safe_get(_foundry_loaded()),
        _safe_get(_llama_status()),
        return_exceptions=True,
    )

    foundry_data = results[0] if not isinstance(results[0], Exception) else {}
    llama_data = results[1] if not isinstance(results[1], Exception) else {}

    models: list[dict] = []

    # Foundry running models from `foundry service list`.
    for m in foundry_data.get("models", []):
        mid = m.get("id", "")
        if mid:
            models.append({
                "id":       f"foundry::{mid}",
                "name":     m.get("name") or mid,
                "provider": "foundry",
                "prefix":   f"foundry::{mid}",
                "status":   "loaded",
            })

    # HuggingFace loaded
    for m in hf_client.list_loaded():
        mid = m.get("id", "")
        if mid:
            models.append({
                "id":       f"hf::{mid}",
                "name":     mid,
                "provider": "huggingface",
                "prefix":   f"hf::{mid}",
                "status":   "loaded",
            })

    # llama.cpp running
    if llama_data.get("running"):
        loaded_name = llama_data.get("model_name", "llama-server")
        models.append({
            "id":       f"llama::{loaded_name}",
            "name":     loaded_name.split("/")[-1].split("\\")[-1] or "llama.cpp",
            "provider": "llama.cpp",
            "prefix":   f"llama::{loaded_name}",
            "status":   "loaded",
        })

    # Ollama — always available when service is running
    from ...models.ollama_client import ollama_client
    ollama_data = await _safe_get(ollama_client.list_models())
    for m in ollama_data.get("models", []):
        mid = m.get("name") or m.get("id", "")
        if mid:
            models.append({
                "id":       f"ollama::{mid}",
                "name":     mid,
                "provider": "ollama",
                "prefix":   f"ollama::{mid}",
                "status":   "available",
            })

    return {"success": True, "models": models, "count": len(models)}
