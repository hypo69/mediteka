# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: HelpDesk Endpoints
# =============================================================================
# Description:
#   REST endpoints for the Telegram helpdesk bot web UI tab.
#   Provides dialog history, RAG profile list, and profile management.
#
# File: src/api/endpoints/helpdesk.py
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
from ...core.config import config as app_config

logger = logging.getLogger(__name__)
router = APIRouter(tags=["helpdesk"])


def _dialogs_file() -> Path:
    """Return path to helpdesk JSONL log inside config.dir_dialogs."""
    d = Path(app_config.dir_dialogs)
    d.mkdir(parents=True, exist_ok=True)
    return d / "helpdesk_dialogs.jsonl"


def _load_dialogs() -> List[Dict]:
    """Load all dialog entries from the JSONL log file."""
    dialogs_file = _dialogs_file()
    if not dialogs_file.exists():
        return []
    entries: List[Dict] = []
    with open(dialogs_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


@router.get("/helpdesk/dialogs")
async def get_dialogs() -> Dict:
    """Return all helpdesk dialogs grouped by chat_id.

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


@router.get("/helpdesk/rag-profiles")
async def get_rag_profiles() -> Dict:
    """Return available RAG profiles.

    Returns:
        Dict: {success, profiles: [...]}
    """
    from ...rag.rag_profile_manager import rag_profile_manager
    return {"success": True, "profiles": rag_profile_manager.list_profiles()}


@router.post("/helpdesk/rag-profiles")
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


@router.delete("/helpdesk/rag-profiles/{name}")
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


@router.get("/helpdesk/config")
async def get_helpdesk_config() -> Dict:
    """Return current helpdesk bot configuration.

    Returns:
        Dict: {success, enabled, rag_profile}
    """
    from ...core.config import config
    return {
        "success": True,
        "enabled": bool(config.telegram_helpdesk_token),
        "rag_profile": config.telegram_helpdesk_rag_profile,
    }
