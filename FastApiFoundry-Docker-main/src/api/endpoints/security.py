# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Security — API Key Management
# =============================================================================
# Description:
#   REST endpoints for managing the local FastAPI server API key.
#
#   The API key protects all /api/v1/* routes when enabled.
#   It is stored in .env as API_KEY and in config.json security.api_key.
#
#   Workflow:
#     POST /api/v1/security/api-key/generate
#       → generates a cryptographically secure random key (32 bytes hex)
#       → writes to .env (API_KEY) and config.json (security.api_key)
#       → returns the new key (only time it is returned in plain text)
#
#     GET /api/v1/security/api-key/status
#       → returns whether a key is configured (never returns the key itself)
#
#     DELETE /api/v1/security/api-key
#       → removes the key from .env and config.json
#       → disables API key protection
#
#   Middleware (in app.py):
#     If API_KEY is set in environment, every request to /api/v1/* must
#     include header  X-API-Key: <key>  or query param  api_key=<key>.
#     Requests to /static/* and /docs, /openapi.json are always allowed.
#
# File: src/api/endpoints/security.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Changes in 0.8.0:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import os
import secrets
import json
import logging
from fastapi import APIRouter
from ...core.config import config

logger = logging.getLogger(__name__)
router = APIRouter()

_ENV_PATH = ".env"
_CONFIG_PATH = "config.json"


def _read_env() -> dict[str, str]:
    """Read .env file into a key-value dict, skipping comments and blanks.

    Returns:
        dict[str, str]: Parsed environment variables.
    """
    result: dict[str, str] = {}
    if not os.path.exists(_ENV_PATH):
        return result
    with open(_ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip()
    return result


def _write_env(data: dict[str, str]) -> None:
    """Write key-value dict back to .env file.

    Args:
        data (dict[str, str]): Variables to persist.
    """
    lines = [f"{k}={v}" for k, v in data.items()]
    with open(_ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _patch_config_api_key(value: str) -> None:
    """Update security.api_key in config.json.

    Args:
        value (str): New API key value (empty string to clear).
    """
    if not os.path.exists(_CONFIG_PATH):
        return
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg.setdefault("security", {})["api_key"] = value
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    config.reload_config()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/security/api-key/generate")
async def generate_api_key() -> dict:
    """Generate a new cryptographically secure API key for this server.

    Generates 32 random bytes encoded as a 64-character hex string.
    Writes the key to .env (API_KEY) and config.json (security.api_key).
    Sets the key in the current process environment immediately.

    Returns:
        dict: ``{"success": True, "api_key": "<new key>"}``

    Example:
        >>> POST /api/v1/security/api-key/generate
        {"success": true, "api_key": "a3f1..."}
    """
    new_key = secrets.token_hex(32)

    # Persist to .env
    env = _read_env()
    env["API_KEY"] = new_key
    _write_env(env)

    # Apply to current process immediately (no restart needed)
    os.environ["API_KEY"] = new_key

    # Persist to config.json
    _patch_config_api_key(new_key)

    logger.info("✅ New API key generated and saved")
    return {"success": True, "api_key": new_key}


@router.get("/security/api-key/status")
async def get_api_key_status() -> dict:
    """Return whether an API key is currently configured.

    Never returns the key value itself — only its presence and a masked preview.

    Returns:
        dict: ``{"success": True, "configured": bool, "preview": "abcd...ef12"}``

    Example:
        >>> GET /api/v1/security/api-key/status
        {"success": true, "configured": true, "preview": "a3f1...cd89"}
    """
    env = _read_env()
    key = env.get("API_KEY", "") or os.environ.get("API_KEY", "")
    configured = bool(key)
    preview = (key[:4] + "…" + key[-4:]) if len(key) >= 8 else ("••••" if key else "")
    return {"success": True, "configured": configured, "preview": preview}


@router.delete("/security/api-key")
async def delete_api_key() -> dict:
    """Remove the API key, disabling key-based protection.

    Removes API_KEY from .env and clears security.api_key in config.json.
    Unsets the key from the current process environment.

    Returns:
        dict: ``{"success": True, "message": "API key removed"}``

    Example:
        >>> DELETE /api/v1/security/api-key
        {"success": true, "message": "API key removed"}
    """
    env = _read_env()
    env.pop("API_KEY", None)
    _write_env(env)

    os.environ.pop("API_KEY", None)
    _patch_config_api_key("")

    logger.info("🗑️ API key removed")
    return {"success": True, "message": "API key removed"}
