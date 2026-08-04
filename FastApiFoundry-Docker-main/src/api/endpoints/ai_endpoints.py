# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Enhanced AI Endpoints
# =============================================================================
# Description:
#   Extended AI endpoints for AI Assistant orchestrator.
#   All generation routes use router.route_generate() — no direct backend calls.
#   POST /api/v1/ai/generate        — text generation with optional RAG context
#   POST /api/v1/ai/generate/stream — streaming text generation (SSE, Foundry only)
#   POST /api/v1/ai/chat            — stateful chat (messages array, RAG, system_prompt)
#   POST /api/v1/ai/chat/stream     — streaming chat with session history persistence
#   POST /api/v1/ai/optimize        — suggest optimal model for task type
#
#   Removed (use canonical endpoints instead):
#   GET /ai/models          → GET /api/v1/models
#   GET /ai/models/recommended → GET /api/v1/models
#   GET /ai/health          → GET /api/v1/health
#   POST /ai/models/{id}/load   → POST /api/v1/foundry/models/load
#   POST /ai/models/{id}/unload → POST /api/v1/foundry/models/unload
#
# File: ai_endpoints.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Changes in 0.8.0:
#   - Removed dead stub endpoints: /ai/models, /ai/models/recommended,
#     /ai/health, /ai/models/{id}/load, /ai/models/{id}/unload
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import asyncio
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.logger import logger
from ...models.foundry_client import foundry_client
from ...models.router import route_generate
from ...utils.text_utils import count_tokens_approx
try:
    from ...rag.rag_system import rag_system
except Exception:
    class DummyRAGSystem:
        """Заглушка для системы RAG при отсутствии зависимостей."""

        async def search(self, query, top_k=3):
            return []

        async def reload_index(self, index_dir: str) -> bool:
            return False

        def _profile_index_dir(self, name: str):
            return Path.home() / ".rag" / name

        def format_context(self, results: list) -> str:
            return ""

        def filter_by_score(self, results: list, min_score: float) -> list:
            return results

    rag_system = DummyRAGSystem()

router = APIRouter()


def _save_session_history(history: list, session_id: str = "default", chat_type: str = "fastapi") -> None:
    """Автоматическое сохранение истории чата в локальный файл.

    Args:
        history (list): Список сообщений для сохранения.
        session_id (str): Идентификатор сессии. По умолчанию 'default'.
        chat_type (str): Тип источника чата. По умолчанию 'fastapi'.
    """
    history_file: Path = Path("session_history.json")
    try:
        full_history = {
            "session_id": session_id,
            "chat_type": chat_type,
            "timestamp": asyncio.get_event_loop().time(),
            "messages": history,
        }
        history_file.write_text(json.dumps(full_history, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Ошибка при автоматическом сохранении истории: {e}")


@router.post("/ai/generate")
async def generate_text(request: dict):
    """Generate text via AI Assistant orchestrator (all backends).

    Model prefix determines backend:
    foundry:: / hf:: / llama:: / ollama::
    """
    prompt = request.get("prompt", "")
    min_score = float(request.get("min_score", 0.0))

    if not prompt:
        return {"success": False, "error": "Prompt is required"}

    params = {
        "model":       request.get("model"),
        "temperature": request.get("temperature", 0.7),
        "max_tokens":  request.get("max_tokens", 2048),
    }

    if request.get("use_rag", False):
        try:
            rag_results = await rag_system.search(prompt, top_k=3)
            if rag_results and min_score > 0 and hasattr(rag_system, "filter_by_score"):
                rag_results = rag_system.filter_by_score(rag_results, min_score)
            if rag_results:
                context = rag_system.format_context(rag_results) if hasattr(rag_system, "format_context") else ""
                if context:
                    prompt = f"Context:\n{context}\n\nQuestion: {prompt}"
        except Exception as e:
            logger.warning(f"RAG enhancement failed during generation: {e}")

    return await route_generate(prompt=prompt, **params)


@router.post("/ai/generate/stream")
async def generate_text_stream(request: dict):
    """Стриминговая генерация текста (Foundry only)."""
    prompt = request.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    params = {
        "model":       request.get("model"),
        "temperature": request.get("temperature", 0.7),
        "max_tokens":  request.get("max_tokens", 2048),
    }

    async def generate():
        async for chunk in foundry_client.generate_stream(prompt, **params):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/ai/chat")
async def chat_completion(request: dict):
    """Chat with message history via AI Assistant orchestrator (all backends)."""
    messages = request.get("messages", [])
    use_rag = request.get("use_rag", False)
    system_prompt = request.get("system_prompt")
    min_score = float(request.get("min_score", 0.0))

    if not messages:
        return {"success": False, "error": "Messages are required"}

    prompt_parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
        elif role == "system":
            prompt_parts.append(f"System: {content}")

    if use_rag:
        last_user = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
        if last_user:
            try:
                rag_results = await rag_system.search(last_user, top_k=3)
                if rag_results and min_score > 0 and hasattr(rag_system, "filter_by_score"):
                    rag_results = rag_system.filter_by_score(rag_results, min_score)
                if rag_results:
                    context = rag_system.format_context(rag_results) if hasattr(rag_system, "format_context") else ""
                    if context:
                        prompt_parts.insert(0, f"Context:\n{context}")
            except Exception as e:
                logger.warning(f"RAG enhancement failed during chat: {e}")

    if system_prompt:
        prompt_parts.insert(0, f"System: {system_prompt}")

    prompt = "\n".join(prompt_parts)

    try:
        result = await route_generate(
            prompt=prompt,
            model=request.get("model"),
            temperature=request.get("temperature", 0.7),
            max_tokens=request.get("max_tokens", 2048),
        )
    except Exception as e:
        logger.error(f"Chat completion crashed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    if result.get("success"):
        messages.append({"role": "assistant", "content": result["content"]})
        _save_session_history(messages)
        return {
            "id":      f"chatcmpl-{int(asyncio.get_event_loop().time())}",
            "object":  "chat.completion",
            "model":   result["model"],
            "choices": [{"index": 0, "message": {"role": "assistant", "content": result["content"]}, "finish_reason": "stop"}],
            "usage":   result.get("usage", {}),
        }
    logger.error(f"Chat completion failed: {result.get('error', 'unknown error')}")
    return result


@router.post("/ai/chat/stream")
async def chat_completion_stream(request: dict):
    """Стриминговый чат с автоматическим сохранением истории после завершения."""
    session_id: str = request.get("session_id") or str(uuid.uuid4())
    messages: list = request.get("messages", [])
    use_rag: bool = request.get("use_rag", False)
    system_prompt: str = request.get("system_prompt", "")
    min_score: float = float(request.get("min_score", 0.0))
    prompt_parts: list = []

    if not messages:
        raise HTTPException(status_code=400, detail="Messages are required")

    logger.info(f"Запуск стриминга чата. Session ID: {session_id}")

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
        elif role == "system":
            prompt_parts.append(f"System: {content}")

    if use_rag:
        last_user = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
        if last_user:
            try:
                rag_results = await rag_system.search(last_user, top_k=3)
                if rag_results and min_score > 0 and hasattr(rag_system, "filter_by_score"):
                    rag_results = rag_system.filter_by_score(rag_results, min_score)
                if rag_results:
                    context = rag_system.format_context(rag_results) if hasattr(rag_system, "format_context") else ""
                    if context:
                        prompt_parts.insert(0, f"Context:\n{context}")
            except Exception as e:
                logger.warning(f"RAG enhancement failed during streaming chat: {e}")

    if system_prompt:
        prompt_parts.insert(0, f"System: {system_prompt}")

    prompt = "\n".join(prompt_parts)
    params = {
        "model":       request.get("model"),
        "temperature": request.get("temperature", 0.7),
        "max_tokens":  request.get("max_tokens", 2048),
    }

    async def event_generator():
        accumulated_text: str = ""
        try:
            await foundry_client._update_base_url()
            async for chunk in foundry_client.generate_stream(prompt, **params):
                if isinstance(chunk, dict) and chunk.get("success"):
                    accumulated_text += chunk.get("content", "")
                elif isinstance(chunk, dict) and chunk.get("error"):
                    logger.error(f"Streaming chat chunk error: {chunk.get('error')}")
                yield f"data: {json.dumps(chunk)}\n\n"

            if accumulated_text:
                messages.append({"role": "assistant", "content": accumulated_text})
                _save_session_history(messages)
                yield f"data: {json.dumps({'status': 'history_saved'})}\n\n"
        except Exception as e:
            logger.error(f"Streaming chat crashed: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"X-Session-Id": session_id},
    )


@router.post("/ai/optimize")
async def optimize_generation(request: dict):
    """Оптимизация параметров генерации — не реализовано."""
    return {"success": False, "error": "Use /api/v1/models to list available models and choose manually."}
