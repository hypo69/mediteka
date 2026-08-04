# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Models Management API
# =============================================================================
# Description:
#   API endpoints for Foundry models.
#   Keep lifecycle semantics simple:
#     - GET /v1/models lists models known to the running Foundry service.
#     - "load" is a warm-up inference request.
#     - "unload" is best-effort via foundry_client.
#
#   Foundry Local API endpoints used:
#     GET    /v1/models              — list available/registered models
#     GET    /openai/models          — list cached models (native)
#     GET    /openai/loadedmodels    — list loaded models (native)
#     GET    /openai/load/{name}     — load model into memory (native)
#     GET    /openai/unload/{name}   — unload model from memory (native)
#     POST   /v1/chat/completions    — inference (via foundry_client)
#     POST   /v1/completions         — text completion (via foundry_client)
#     POST   /v1/embeddings          — embeddings (via foundry_client)
#
#   CLI used only for:
#     foundry model download <id>    — no HTTP API alternative
#
# Примеры:
#   GET  /api/v1/foundry/models/catalog        — полный каталог Foundry (foundry model list CLI)
#   GET  /api/v1/foundry/models/available
#   GET  /api/v1/foundry/models/loaded
#   GET  /api/v1/foundry/models/cached
#   POST /api/v1/foundry/models/completions   {"prompt": "...", "model": "..."}
#   POST /api/v1/foundry/models/embeddings    {"input": "...", "model": "..."}
#   POST /api/v1/foundry/models/download      {"model_id": "qwen2.5-0.5b-..."}
#   GET  /api/v1/foundry/models/download/status/{pid}
#   POST /api/v1/foundry/models/load          {"model_id": "qwen2.5-0.5b-..."}
#   POST /api/v1/foundry/models/unload        {"model_id": "qwen2.5-0.5b-..."}
#
# File: src/api/endpoints/foundry_models.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Added /completions proxy (Foundry /v1/completions)
#   - Added /embeddings proxy (Foundry /v1/embeddings)
#   - Replaced CLI subprocess calls with Foundry HTTP API (load, list_available)
# Changes in 0.7.2:
#   - Removed hardcoded AVAILABLE_MODELS fallback
#   - Added catalog cache mechanism
#   - Simplified load/unload to use native /openai/load and /openai/unload
#   - Removed SDK dependency from foundry_client
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import subprocess
import logging
import os
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from ...utils.foundry_utils import is_foundry_model_cached, _get_foundry_cache_dir
from ...utils.process_utils import run_command, DEFAULT_SUBPROCESS_KWARGS
from ...utils.api_utils import api_response_handler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/foundry/models", tags=["foundry-models"])

# Catalog cache file path
_CATALOG_CACHE_FILE = Path("config/foundry_catalog.json")

# Background download processes: {pid: {"model_id": str, "process": Popen}}
_download_processes: dict = {}


def _get_foundry_base_url() -> str:
    """Return Foundry service base URL from environment or config."""
    return os.getenv("FOUNDRY_BASE_URL", "http://localhost:63995/v1/")


def _load_catalog_cache() -> list:
    """Load cached catalog from file if it exists and is valid.
    
    Returns:
        list: Cached catalog models or empty list if cache is invalid/missing.
    """
    if not _CATALOG_CACHE_FILE.exists():
        return []
    
    try:
        with open(_CATALOG_CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load catalog cache: {e}")
    
    return []


def _save_catalog_cache(models: list) -> None:
    """Save catalog to cache file.
    
    Args:
        models: List of model dictionaries to cache.
    """
    try:
        # Ensure directory exists
        _CATALOG_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_CATALOG_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
        logger.info(f"Catalog cache saved: {_CATALOG_CACHE_FILE}")
    except OSError as e:
        logger.error(f"Failed to save catalog cache: {e}")


def _refresh_catalog_cache() -> dict:
    """Refresh catalog cache by fetching from Foundry CLI.
    
    Returns:
        dict: Result with success status and models.
    """
    try:
        result = run_command(["foundry", "model", "list"], timeout=15)
    except FileNotFoundError:
        logger.warning("foundry CLI not found — cannot refresh catalog cache")
        return {"success": False, "error": "foundry CLI not found", "models": []}
    except Exception as e:
        logger.warning(f"foundry model list failed: {e} — cannot refresh catalog cache")
        return {"success": False, "error": str(e), "models": []}
    
    output = (result.stdout or "").strip()
    if result.returncode != 0 or not output:
        logger.warning("foundry model list returned no output — cannot refresh catalog cache")
        return {"success": False, "error": "CLI returned no output", "models": []}
    
    # Parse CLI table output
    import re
    parsed: list[dict] = []
    current_alias = ""
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("-") or line.lower().startswith("alias"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 6:
            continue
        alias, device, task, size, license_, model_id = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
        if alias:
            current_alias = alias
        parsed.append({
            "id":      model_id,
            "alias":   current_alias,
            "name":    current_alias or model_id,
            "device":  device,
            "task":    task,
            "size":    size,
            "license": license_,
            "cached":  is_foundry_model_cached(model_id),
            "loaded":  False,
        })
    
    if parsed:
        _save_catalog_cache(parsed)
        logger.info(f"Catalog cache refreshed: {len(parsed)} models")
        return {"success": True, "models": parsed, "count": len(parsed)}
    
    logger.warning("Failed to parse foundry model list output")
    return {"success": False, "error": "Failed to parse CLI output", "models": []}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/auto-load-default")
@api_response_handler
async def auto_load_default_model() -> dict:
    """Warm up the default model from config.json.

    For Foundry, "load" means a tiny inference request that makes the model
    ready for normal requests. Foundry Local does not expose a reliable HTTP
    load-into-RAM endpoint.

    Returns:
        dict: success, model_id, message on success; success=False on failure.
    """
    from ...core.config import config as app_config
    from ...models.foundry_client import foundry_client

    model_id: str = app_config.foundry_default_model
    if not model_id:
        return {"success": False, "message": "default_model not set in config"}

    if not app_config.foundry_auto_load_default:
        return {"success": False, "message": "auto_load_default is disabled in config"}

    logger.info("Loading default model via Foundry API: %s", model_id)
    result = await foundry_client.load_model(model_id)
    if result.get("success"):
        return {"success": True, "model_id": model_id, "message": result.get("message", f"Loading {model_id}")}
    return {"success": False, "model_id": model_id, "error": result.get("error", "Load failed")}


@router.get("")
@router.get("/")
async def list_models_root() -> dict:
    """Alias for /available."""
    return await list_available_models()


@router.get("/catalog")
@api_response_handler
async def list_catalog_models() -> dict:
    """List the full Foundry model catalog via CLI (foundry model list).

    This is the catalog of ALL models available for download from Foundry,
    not just the ones already cached or loaded.
    Uses CLI because Foundry has no HTTP API for the catalog.
    Falls back to cached catalog if CLI is unavailable.

    Returns:
        dict: success, models (list with id, alias, device, task, size, license, cached),
              count, source ('foundry-cli', 'cached', or 'empty').
    """
    import re
    try:
        result = run_command(["foundry", "model", "list"], timeout=15)
    except FileNotFoundError:
        logger.warning("foundry CLI not found — returning cached catalog")
        cached = _load_catalog_cache()
        return {"success": True, "models": cached, "count": len(cached), "source": "cached"}
    except Exception as e:
        logger.warning(f"foundry model list failed: {e} — returning cached catalog")
        cached = _load_catalog_cache()
        return {"success": True, "models": cached, "count": len(cached), "source": "cached"}

    output = (result.stdout or "").strip()
    if result.returncode != 0 or not output:
        logger.warning("foundry model list returned no output — returning cached catalog")
        cached = _load_catalog_cache()
        return {"success": True, "models": cached, "count": len(cached), "source": "cached"}

    # Parse CLI table output:
    # Alias          | Device | Task | File Size | License | Model ID
    # Lines starting with dashes or empty are separators.
    parsed: list[dict] = []
    current_alias = ""
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("-") or line.lower().startswith("alias"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 6:
            continue
        alias, device, task, size, license_, model_id = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
        if alias:
            current_alias = alias
        parsed.append({
            "id":      model_id,
            "alias":   current_alias,
            "name":    current_alias or model_id,
            "device":  device,
            "task":    task,
            "size":    size,
            "license": license_,
            "cached":  is_foundry_model_cached(model_id),
            "loaded":  False,
        })

    if not parsed:
        logger.warning("Failed to parse foundry model list output — returning cached catalog")
        cached = _load_catalog_cache()
        return {"success": True, "models": cached, "count": len(cached), "source": "cached"}

    # Save to cache
    _save_catalog_cache(parsed)
    logger.info("Foundry catalog: %d models from CLI", len(parsed))
    return {"success": True, "models": parsed, "count": len(parsed), "source": "foundry-cli"}


@router.get("/available")
@api_response_handler
async def list_available_models() -> dict:
    """List models reported by the running Foundry service.

    Uses Foundry HTTP API (GET /v1/models).
    Returns empty list when Foundry is unreachable (no hardcoded fallback).

    NOTE: Foundry Local does not expose a reliable separate "loaded in RAM"
    list here. Treat these as available/registered models.

    Returns:
        dict: success, models, count, source ('foundry-api', 'cached', or 'empty').
    """
    from ...models.foundry_client import foundry_client

    result = await foundry_client.list_available_models()
    if result.get("success"):
        models = result.get("models", [])
        # Normalize to consistent shape: ensure id, name, cached fields
        normalized = []
        for m in models:
            mid = m.get("id", "")
            normalized.append({
                "id":      mid,
                "name":    m.get("name") or mid,
                "alias":   m.get("alias", ""),
                "device":  m.get("device") or m.get("type", ""),
                "size":    m.get("size", ""),
                "cached":  True,
                "loaded":  False,
                "status":  "available",
            })
        logger.info("Foundry API returned %d models", len(normalized))
        return {"success": True, "models": normalized, "count": len(normalized), "source": "foundry-api"}

    # No hardcoded fallback - return empty list with warning
    logger.warning("Foundry API unavailable, returning empty model list")
    return {"success": True, "models": [], "count": 0, "source": "empty"}


@router.get("/cached")
@api_response_handler
async def list_cached_models() -> dict:
    """List models downloaded to the local Foundry cache on disk.

    Foundry has no HTTP API for listing cached (not-yet-loaded) models,
    so this endpoint scans the filesystem directly.

    Cache structure: <cache_dir>/Microsoft/<model-dir>/v<version>/

    Returns:
        dict: success, models (list of model_id strings), items (full model dicts),
              count, cache_dir.
    """
    cache_dir = _get_foundry_cache_dir()
    microsoft_dir = cache_dir / "Microsoft"

    # Try Microsoft subdir first, fall back to cache root
    scan_dir = microsoft_dir if microsoft_dir.exists() else cache_dir

    if not scan_dir.exists():
        return {
            "success":   True,
            "models":    [],
            "items":     [],
            "count":     0,
            "cache_dir": str(cache_dir),
        }

    # Scan filesystem — reconstruct model IDs from directory names
    # Directory name format: "qwen3-0.6b-generic-cpu-4" (all colons replaced with dashes)
    # Version subdir format: "v4"
    # Skip empty directories — incomplete/failed downloads
    found_ids: list[str] = []
    for model_dir in sorted(scan_dir.iterdir()):
        if not model_dir.is_dir():
            continue
        dir_name = model_dir.name

        version_dirs = [d for d in model_dir.iterdir() if d.is_dir() and d.name.startswith("v")]
        if version_dirs:
            for vdir in sorted(version_dirs):
                version = vdir.name[1:]  # strip leading "v"
                # Reconstruct: "qwen3-0.6b-generic-cpu-4" + "4" → "qwen3-0.6b-generic-cpu:4"
                if dir_name.endswith(f"-{version}"):
                    base = dir_name[: -(len(version) + 1)]
                    found_ids.append(f"{base}:{version}")
                else:
                    found_ids.append(dir_name)
        # Skip directories with no version subdirs — incomplete downloads

    items = []
    for mid in found_ids:
        items.append({
            "id":     mid,
            "name":   mid,
            "alias":  "",
            "device": "CPU",
            "size":   "",
            "cached": True,
            "loaded": False,
        })

    logger.info("Found %d cached Foundry models in %s", len(items), scan_dir)
    return {
        "success":   True,
        "models":    found_ids,
        "items":     items,
        "count":     len(items),
        "cache_dir": str(scan_dir),
    }


@router.get("/loaded")
@api_response_handler
async def list_loaded_models() -> dict:
    """List models actually running in the Foundry service.

    Uses `foundry service list`, because Foundry's OpenAI-compatible
    `GET /v1/models` reports available/registered models, not the runtime
    loaded set.

    Returns:
        dict: success, models (list of {id, name, status}), count.
    """
    from ...models.foundry_client import foundry_client

    result = await foundry_client.list_running_models()
    if not result.get("success"):
        return {"success": False, "models": [], "count": 0, "error": result.get("error", "Foundry runtime list unavailable")}

    return {
        "success": True,
        "models": result.get("models", []),
        "count": result.get("count", 0),
        "source": result.get("source", "foundry-service-list"),
    }


@router.post("/download")
@api_response_handler
async def download_model(request: dict) -> dict:
    """Download a model to the Foundry cache via CLI.

    Foundry has no HTTP API for downloading models — CLI is the only option.
    Launches download in background and returns PID immediately.

    Args:
        request: {"model_id": "qwen3-0.6b-generic-cpu:4"}

    Returns:
        dict: success, model_id, status ('downloading'/'already_cached'), pid.
    """
    model_id: str = request.get("model_id", "")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")

    if is_foundry_model_cached(model_id):
        return {"success": True, "model_id": model_id, "status": "already_cached"}

    process = subprocess.Popen(
        ["foundry", "model", "download", model_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **DEFAULT_SUBPROCESS_KWARGS,
    )
    _download_processes[process.pid] = {"model_id": model_id, "process": process}
    logger.info("Downloading model %s (PID: %d)", model_id, process.pid)
    return {"success": True, "model_id": model_id, "status": "downloading", "pid": process.pid}


@router.get("/download/status/{pid}")
@api_response_handler
async def get_download_status(pid: int) -> dict:
    """Check status of a background download process.

    Args:
        pid: PID returned by /download.

    Returns:
        dict: success, pid, model_id, status ('downloading'/'done'/'error').
    """
    entry = _download_processes.get(pid)
    if not entry:
        return {"success": False, "error": f"PID {pid} not found"}

    process = entry["process"]
    model_id = entry["model_id"]
    retcode = process.poll()

    if retcode is None:
        return {"success": True, "pid": pid, "model_id": model_id, "status": "downloading"}

    stdout = (process.stdout.read() or b"").decode("utf-8", errors="replace") if process.stdout else ""
    stderr = (process.stderr.read() or b"").decode("utf-8", errors="replace") if process.stderr else ""
    del _download_processes[pid]

    cached = is_foundry_model_cached(model_id)
    if retcode == 0 or cached:
        logger.info("Download complete: %s", model_id)
        return {"success": True, "pid": pid, "model_id": model_id, "status": "done", "cached": cached}

    logger.error("Download failed: %s — %s", model_id, stderr)
    return {
        "success": False,
        "pid":      pid,
        "model_id": model_id,
        "status":   "error",
        "error":    stderr.strip() or stdout.strip() or "Foundry download failed",
    }


@router.post("/load")
@api_response_handler
async def load_model(request: dict) -> dict:
    """Warm up a model in Foundry.

    The client sends a short chat completion request. This is intentionally
    simpler and more reliable than trying to track an internal loaded state.

    Args:
        request: {"model_id": "qwen3-0.6b-generic-cpu:4"}

    Returns:
        dict: success, model_id, message on success; success=False, error on failure.
    """
    from ...models.foundry_client import foundry_client

    model_id: str = request.get("model_id", "")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")

    logger.info("Warming up Foundry model: %s", model_id)
    result = await foundry_client.load_model(model_id)
    if result.get("success"):
        return {"success": True, "model_id": model_id, "message": result.get("message", f"Ready {model_id}"), "status": "ready"}
    return {"success": False, "model_id": model_id, "error": result.get("error", "Load failed")}


@router.post("/unload")
@api_response_handler
async def unload_model(request: dict) -> dict:
    """Best-effort unload of a Foundry model.

    Args:
        request: {"model_id": "qwen3-0.6b-generic-cpu:4"}

    Returns:
        dict: success, model_id, message on success; success=False, error on failure.
    """
    from ...models.foundry_client import foundry_client

    model_id: str = request.get("model_id", "")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")

    result = await foundry_client.unload_model(model_id)
    if result.get("success"):
        return {"success": True, "model_id": model_id, "message": result.get("message", f"Unloaded {model_id}")}
    return {"success": False, "model_id": model_id, "error": result.get("error", "Unload failed")}


@router.get("/status/{model_id:path}")
@api_response_handler
async def get_model_status(model_id: str) -> dict:
    """Get model status: running in service and/or cached on disk.

    Args:
        model_id: Model identifier (path parameter).

    Returns:
        dict: success, model_id, loaded (bool), cached (bool), status.
    """
    loaded_result = await list_loaded_models()
    is_loaded = loaded_result.get("success") and any(
        m["id"] == model_id for m in loaded_result.get("models", [])
    )
    is_cached = is_foundry_model_cached(model_id)
    return {
        "success":  True,
        "model_id": model_id,
        "available": is_cached,
        "loaded":   is_loaded,
        "cached":   is_cached,
        "status":   "loaded" if is_loaded else ("cached" if is_cached else "not_downloaded"),
    }


@router.post("/catalog/refresh")
@api_response_handler
async def refresh_catalog() -> dict:
    """Force refresh the model catalog cache from Foundry CLI.

    Returns:
        dict: success, models, count, source ('foundry-cli' or error reason).
    """
    return _refresh_catalog_cache()


# ── Foundry API proxy: completions + embeddings ────────────────────────────────

@router.post("/completions")
@api_response_handler
async def foundry_completions(request: dict) -> dict:
    """Text completion через Foundry /v1/completions.

    Args:
        request: {"prompt": str, "model": str (optional),
                  "temperature": float, "max_tokens": int, ...}

    Returns:
        dict: OpenAI-совместимый ответ или success=False.
    """
    from ...models.foundry_client import foundry_client
    prompt: str = request.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    return await foundry_client.completions(
        prompt=prompt,
        model=request.get("model"),
        temperature=float(request.get("temperature", 0.7)),
        max_tokens=int(request.get("max_tokens", 512)),
    )


@router.post("/embeddings")
@api_response_handler
async def foundry_embeddings(request: dict) -> dict:
    """Эмбеддинги через Foundry /v1/embeddings.

    Args:
        request: {"input": str | list[str], "model": str (optional)}

    Returns:
        dict: success, data (list of embedding vectors), usage.
    """
    from ...models.foundry_client import foundry_client
    inp = request.get("input")
    if not inp:
        raise HTTPException(status_code=400, detail="input is required")
    return await foundry_client.embeddings(input=inp, model=request.get("model"))
