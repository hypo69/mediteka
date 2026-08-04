# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Chat Endpoints
# =============================================================================
# Description:
#   Session-based chat endpoints for interactive AI conversations.
#   POST   /api/v1/chat/start              — create new session (UUID)
#   POST   /api/v1/chat/message            — send message, get response
#   POST   /api/v1/chat/stream             — streaming message (SSE)
#   GET    /api/v1/chat/history/{id}       — get in-memory session history
#   DELETE /api/v1/chat/session/{id}       — delete in-memory session
#   POST   /api/v1/chat/history/save       — persist history to disk
#   GET    /api/v1/chat/history/list       — list saved dialogs from disk
#   GET    /api/v1/chat/history/file/{fn}  — load one saved dialog from disk
#   POST   /api/v1/chat/history/cleanup    — delete old/oversized dialogs
#   GET    /api/v1/chat/models             — list available Foundry models
#
#   Sessions are stored in-memory (chat_sessions dict).
#   Persisted dialogs go to config.dir_dialogs (~/.aiassistant/dialogs/).
#   Auto-translation: enabled via config translator.enabled.
#
# File: chat_endpoints.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - save_chat_history: path from config.dir_dialogs (was hardcoded)
#   - Added GET /chat/history/list
#   - Added GET /chat/history/file/{filename}
#   - Added POST /chat/history/cleanup (retention_days + max_size_mb)
#   - Fixed docstring: actual storage path
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path

from ...models.foundry_client import foundry_client
from ...models.router import route_generate
from ...utils.translator import translator
from ...core.config import config as app_config
from ...db.chat_db import get_chat_db

logger = logging.getLogger(__name__)
router = APIRouter()


def _translate_enabled() -> bool:
    return app_config.get_raw_config().get("translator", {}).get("enabled", False)


async def _chat_should_translate(request: dict) -> bool:
    """Per-request translate_model_dialog overrides global config."""
    return await translator.should_translate(request)


def _dialogs_dir() -> Path:
    """Return resolved dialogs directory path, creating it if needed."""
    p = Path(app_config.dir_dialogs)
    p.mkdir(parents=True, exist_ok=True)
    return p


# In-memory session store
chat_sessions: Dict[str, List[Dict]] = {}


async def _ensure_session_loaded(session_id: str) -> bool:
    """Load a persisted chat session into memory if it exists."""
    if session_id in chat_sessions:
        return True
    try:
        db = await get_chat_db()
        if not await db.session_exists(session_id):
            return False
        history = await db.get_session_history(session_id)
        chat_sessions[session_id] = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]
        return True
    except Exception as exc:
        logger.warning("Could not load persisted chat session %s: %s", session_id, exc)
        return False


async def _persist_chat_message(session_id: str, role: str, content: str) -> None:
    """Best-effort persistence for shared chat context."""
    try:
        db = await get_chat_db()
        if not await db.session_exists(session_id):
            await db.create_session(session_id=session_id)
        await db.save_message(session_id=session_id, role=role, content=content)
    except Exception as exc:
        logger.warning("Could not persist chat message for %s: %s", session_id, exc)


@router.post("/chat/start")
async def start_chat_session(request: dict) -> dict:
    """Start a new chat session.

    Args:
        request: JSON body with fields:
            model (str): Model ID (default: 'default').

    Returns:
        dict: success, session_id (UUID), model, message.
    """
    session_id = str(uuid.uuid4())
    model = request.get("model", "default")
    chat_sessions[session_id] = []
    try:
        db = await get_chat_db()
        await db.create_session(session_id=session_id, model=model, title=request.get("title", ""))
    except Exception as exc:
        logger.warning("Could not persist chat session %s: %s", session_id, exc)
    return {"success": True, "session_id": session_id, "model": model, "message": "Сессия чата начата"}


@router.post("/chat/message")
async def send_chat_message(request: dict) -> dict:
    """Send a message to an existing chat session.

    Args:
        request: JSON body with fields:
            session_id (str):    Session ID (required).
            message (str):       Message text (required).
            model (str):         Model ID (optional).
            temperature (float): Sampling temperature (default: 0.7).
            max_tokens (int):    Max tokens (default: 2048).
            source_lang (str):   Input language (default: 'auto').
            locale (str):        Reply language override ('ru', 'he', etc.).

    Returns:
        dict: success, response, session_id.

    Raises:
        HTTPException 400: Invalid session_id or empty message.
        HTTPException 500: Generation error.
    """
    session_id = request.get("session_id")
    message = request.get("message", "")
    source_lang = request.get("source_lang", "auto")
    locale = request.get("locale", "")

    if not session_id or not await _ensure_session_loaded(session_id):
        raise HTTPException(status_code=400, detail="Неверный ID сессии")
    if not message:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")

    translate_on = await _chat_should_translate(request)
    user_language: str | None = request.get("user_language") or None
    model_message = message
    if translate_on:
        user_lang = await translator.resolve_user_lang(message, user_language)
        tr = await translator.translate_for_model(message, source_lang=user_lang)
        if tr["success"] and tr["was_translated"]:
            model_message = tr["translated"]
            source_lang = user_lang

    chat_sessions[session_id].append({"role": "user", "content": model_message})
    await _persist_chat_message(session_id, "user", model_message)
    prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_sessions[session_id]])

    try:
        response = await route_generate(
            prompt,
            model=request.get("model"),
            temperature=request.get("temperature", 0.7),
            max_tokens=request.get("max_tokens", 2048),
        )
        if not response["success"]:
            raise Exception(response.get("error", "Unknown error"))

        ai_response = response.get("content", "")
        chat_sessions[session_id].append({"role": "assistant", "content": ai_response})
        await _persist_chat_message(session_id, "assistant", ai_response)

        reply_lang = locale if locale and locale != "auto" else source_lang
        if translate_on and reply_lang and reply_lang not in ("en", "auto"):
            tr_back = await translator.translate_response(ai_response, reply_lang)
            if tr_back["success"]:
                ai_response = tr_back["translated"]

        return {"success": True, "response": ai_response, "session_id": session_id}

    except Exception as e:
        logger.error("Chat message generation failed for session %s: %s", session_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@router.post("/chat/stream")
async def send_chat_message_stream(request: dict) -> StreamingResponse:
    """Send a message with SSE streaming response.

    Args:
        request: JSON body with fields:
            session_id (str):    Session ID (required).
            message (str):       Message text (required).
            model (str):         Model ID (optional).
            temperature (float): Sampling temperature (default: 0.7).
            max_tokens (int):    Max tokens (default: 2048).

    Returns:
        StreamingResponse: SSE stream with {chunk} events and final {done: True}.

    Raises:
        HTTPException 400: Invalid session_id or empty message.
    """
    session_id = request.get("session_id")
    message = request.get("message", "")

    if not session_id or not await _ensure_session_loaded(session_id):
        raise HTTPException(status_code=400, detail="Неверный ID сессии")
    if not message:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")

    translate_on = await _chat_should_translate(request)
    user_language = request.get("user_language") or None
    prompt_message = message
    user_lang = "en"
    if translate_on:
        user_lang = await translator.resolve_user_lang(message, user_language)
        tr_in = await translator.translate_for_model(message, source_lang=user_lang)
        if tr_in["success"] and tr_in["was_translated"]:
            prompt_message = tr_in["translated"]

    chat_sessions[session_id].append({"role": "user", "content": prompt_message})
    await _persist_chat_message(session_id, "user", prompt_message)
    prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_sessions[session_id]])

    async def generate_stream():
        try:
            model = request.get("model") or ""
            temperature = request.get("temperature")
            max_tokens = request.get("max_tokens")

            # Foundry and LM Studio support native streaming; other backends use route_generate fallback
            if not model or model.startswith("foundry::"):
                accumulated = ""
                clean_model = model[len("foundry::"):] if model.startswith("foundry::") else None
                async for chunk in foundry_client.generate_stream(
                    prompt=prompt,
                    model=clean_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    if chunk["success"] and not chunk.get("finished", False):
                        content = chunk.get("content", "")
                        accumulated += content
                        yield f"data: {json.dumps({'chunk': content})}\n\n"
                    elif chunk.get("finished", False):
                        break
                if translate_on and user_lang not in ("en", "auto") and accumulated:
                    tr_out = await translator.translate_response(accumulated, user_lang)
                    if tr_out["success"]:
                        accumulated = tr_out["translated"]
                        yield f'data: {{"chunk_translated": {json.dumps(accumulated)}}}\n\n'
                chat_sessions[session_id].append({"role": "assistant", "content": accumulated})
                await _persist_chat_message(session_id, "assistant", accumulated)
            elif model.startswith("lmstudio::"):
                from ...models.lmstudio_client import lmstudio_client

                accumulated = ""
                clean_model = model[len("lmstudio::"):]
                async for chunk in lmstudio_client.stream_generate(
                    prompt=prompt,
                    model=clean_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    if chunk.get("success") and not chunk.get("finished", False):
                        content = chunk.get("content", "")
                        accumulated += content
                        yield f"data: {json.dumps({'chunk': content})}\n\n"
                    elif not chunk.get("success"):
                        yield f"data: {json.dumps({'error': chunk.get('error', 'LM Studio stream error')})}\n\n"
                        return
                chat_sessions[session_id].append({"role": "assistant", "content": accumulated})
                await _persist_chat_message(session_id, "assistant", accumulated)
            else:
                # Non-Foundry backends: single call, stream as one chunk
                result = await route_generate(prompt, model=model, temperature=temperature, max_tokens=max_tokens)
                if not result["success"]:
                    yield f"data: {json.dumps({'error': result.get('error', 'Generation error')})}\n\n"
                    return
                content = result.get("content", "")
                chat_sessions[session_id].append({"role": "assistant", "content": content})
                await _persist_chat_message(session_id, "assistant", content)
                yield f"data: {json.dumps({'chunk': content})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            logger.error("Chat stream failed for session %s: %s", session_id, e, exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str) -> dict:
    """Get in-memory session history.

    Args:
        session_id: Chat session UUID.

    Returns:
        dict: success, session_id, history (list of {role, content}).

    Raises:
        HTTPException 404: Session not found.
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return {"success": True, "session_id": session_id, "history": chat_sessions[session_id]}


@router.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str) -> dict:
    """Delete an in-memory chat session.

    Args:
        session_id: Chat session UUID.

    Returns:
        dict: success, message.

    Raises:
        HTTPException 404: Session not found.
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    del chat_sessions[session_id]
    return {"success": True, "message": "Сессия удалена"}


@router.post("/chat/history/save")
async def save_chat_history(request: dict) -> dict:
    """Persist chat history to disk.

    Saves to config.dir_dialogs (~/.ai-assist/dialogs/ by default).

    Args:
        request: JSON body with fields:
            messages (list):  List of {role, content} (required).
            session_id (str): Session UUID (generated if empty).
            model (str):      Model ID (optional).
            title (str):      Dialog title (optional).
            aborted (bool):   Whether chat was aborted (default: False).

    Returns:
        dict: success, file (absolute path), session_id.

    Raises:
        HTTPException 400: messages missing or empty.
    """
    messages: List[Dict] = request.get("messages") or []
    if not messages:
        raise HTTPException(status_code=400, detail="messages is required")

    session_id: str = request.get("session_id") or str(uuid.uuid4())
    model: str = request.get("model") or ""
    title: str = request.get("title") or ""
    aborted: bool = bool(request.get("aborted", False))

    history_dir = _dialogs_dir()
    ts = int(time.time())
    file_path = history_dir / f"{session_id}_{ts}.json"

    payload = {
        "session_id": session_id,
        "title": title,
        "model": model,
        "aborted": aborted,
        "created_at": ts,
        "messages": messages,
    }
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"success": True, "file": str(file_path), "session_id": session_id}


@router.get("/chat/history/list")
async def list_saved_dialogs(limit: int = 50, offset: int = 0) -> dict:
    """List saved dialog files from disk, newest first.

    Args:
        limit (int):  Max number of entries to return (default: 50).
        offset (int): Pagination offset (default: 0).

    Returns:
        dict: success, dialogs (list of metadata), total, dir.
    """
    history_dir = _dialogs_dir()
    files = sorted(history_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    total = len(files)
    page = files[offset: offset + limit]

    dialogs = []
    for f in page:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            dialogs.append({
                "filename": f.name,
                "session_id": data.get("session_id", ""),
                "title": data.get("title", ""),
                "model": data.get("model", ""),
                "created_at": data.get("created_at", 0),
                "message_count": len(data.get("messages", [])),
                "aborted": data.get("aborted", False),
                "size_bytes": f.stat().st_size,
            })
        except Exception as e:
            logger.warning("Could not parse saved dialog %s: %s", f.name, e)
            dialogs.append({"filename": f.name, "error": "parse error"})

    return {"success": True, "dialogs": dialogs, "total": total, "dir": str(history_dir)}


@router.get("/chat/history/file/{filename}")
async def load_saved_dialog(filename: str) -> dict:
    """Load a single saved dialog from disk.

    Args:
        filename: JSON filename (e.g. 'uuid_1234567890.json').

    Returns:
        dict: success + full dialog payload.

    Raises:
        HTTPException 400: Unsafe filename.
        HTTPException 404: File not found.
    """
    # Sanitize: no path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = _dialogs_dir() / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return {"success": True, **data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения: {e}")


@router.post("/chat/history/cleanup")
async def cleanup_dialogs(request: Optional[dict] = None) -> dict:
    """Delete old and oversized dialog files.

    Applies retention_days and max_size_mb from config.dialogs.
    Can be overridden per-request.

    Args:
        request: Optional JSON body with fields:
            retention_days (int): Override retention period.
            max_size_mb (int):    Override size limit.

    Returns:
        dict: success, deleted (count), freed_bytes, remaining.
    """
    req = request or {}
    retention_days: int = req.get("retention_days") or app_config.dialogs_retention_days
    max_size_mb: int = req.get("max_size_mb") or app_config.dialogs_max_size_mb

    history_dir = _dialogs_dir()
    now = time.time()
    cutoff = now - retention_days * 86400
    max_bytes = max_size_mb * 1024 * 1024

    files = sorted(history_dir.glob("*.json"), key=lambda f: f.stat().st_mtime)
    deleted = 0
    freed = 0

    # Delete files older than retention_days
    for f in files:
        if f.stat().st_mtime < cutoff:
            freed += f.stat().st_size
            f.unlink()
            deleted += 1
            logger.info(f"🗑️ cleanup: removed old dialog {f.name}")

    # If total size still exceeds limit, remove oldest first
    files = sorted(history_dir.glob("*.json"), key=lambda f: f.stat().st_mtime)
    total_size = sum(f.stat().st_size for f in files)
    for f in files:
        if total_size <= max_bytes:
            break
        freed += f.stat().st_size
        total_size -= f.stat().st_size
        f.unlink()
        deleted += 1
        logger.info(f"🗑️ cleanup: removed oversized dialog {f.name}")

    remaining = len(list(history_dir.glob("*.json")))
    return {"success": True, "deleted": deleted, "freed_bytes": freed, "remaining": remaining}


@router.get("/chat/models")
async def get_available_models() -> dict:
    """List chat models without probing Foundry.

    Returns:
        dict: success, models (list of {id, name, type, size}), count.
    """
    return {"success": True, "models": [], "count": 0, "source": "not_checked"}
