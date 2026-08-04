# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Support Endpoints
# =============================================================================
# Description:
#   REST endpoints for the Telegram support bot web UI tab.
#   Provides dialog history, RAG profile list, and profile management.
#
# File: src/api/endpoints/support.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["support"])

_DIALOGS_FILE = Path("logs/support_dialogs.jsonl")


def _load_dialogs() -> List[Dict]:
    """Load all dialog entries from the JSONL log file."""
    if not _DIALOGS_FILE.exists():
        return []
    entries: List[Dict] = []
    with open(_DIALOGS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


@router.get("/support/dialogs")
async def get_dialogs() -> Dict:
    """Return all support dialogs grouped by chat_id.

    Returns:
        Dict: {success, dialogs: {chat_id: [{role, text, ts, username}]}}
    """
    entries = _load_dialogs()
    grouped: Dict[str, List] = defaultdict(list)
    for e in entries:
        key = str(e.get("chat_id", "unknown"))
        grouped[key].append({
            "role": e.get("role"),
            "text": e.get("text"),
            "ts": e.get("ts"),
            "username": e.get("username"),
        })
    return {"success": True, "dialogs": dict(grouped)}


@router.get("/support/rag-profiles")
async def get_rag_profiles() -> Dict:
    """Return available RAG profiles.

    Returns:
        Dict: {success, profiles: [...]}
    """
    from ...rag.rag_profile_manager import rag_profile_manager
    return {"success": True, "profiles": rag_profile_manager.list_profiles()}


@router.post("/support/rag-profiles")
async def create_rag_profile(body: Dict) -> Dict:
    """Create a new RAG profile directory.

    Args:
        body (Dict): {name, description}

    Returns:
        Dict: {success, path}
    """
    from ...rag.rag_profile_manager import rag_profile_manager
    name = (body.get("name") or "").strip()
    if not name:
        return {"success": False, "error": "name is required"}
    path = rag_profile_manager.create_profile(name, body.get("description", ""))
    return {"success": True, "path": str(path)}


@router.delete("/support/rag-profiles/{name}")
async def delete_rag_profile(name: str) -> Dict:
    """Soft-delete a RAG profile (rename with ~ suffix).

    Args:
        name (str): Profile name.

    Returns:
        Dict: {success}
    """
    from ...rag.rag_profile_manager import rag_profile_manager
    ok = rag_profile_manager.delete_profile(name)
    return {"success": ok, "error": None if ok else "Profile not found"}


@router.get("/support/config")
async def get_support_config() -> Dict:
    """Return current support bot configuration.

    Returns:
        Dict: {success, enabled, rag_profile}
    """
    from ...core.config import config
    return {
        "success": True,
        "enabled": bool(config.telegram_support_token),
        "rag_profile": config.telegram_support_rag_profile,
    }
