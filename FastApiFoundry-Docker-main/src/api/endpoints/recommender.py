# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Recommender Endpoints — API для рекомендательного агента
# =============================================================================
# Description:
#   POST /api/v1/recommender/track          — принять page_view от расширения
#   GET  /api/v1/recommender/recommendations — получить рекомендации для user_id
#   GET  /api/v1/recommender/history        — история просмотров пользователя
#
# File: src/api/endpoints/recommender.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ...agents.recommender_agent import RecommenderAgent, record_page_view, get_page_views
from ...models.foundry_client import foundry_client
from ...core.config import config

logger = logging.getLogger(__name__)
router = APIRouter()

_agent: Optional[RecommenderAgent] = None


def _get_agent() -> RecommenderAgent:
    global _agent
    if _agent is None:
        _agent = RecommenderAgent(foundry_client)
    return _agent


# ── Schemas ───────────────────────────────────────────────────────────────────

class PageViewEvent(BaseModel):
    user_id: str
    url: str
    title: str
    time_spent: int          # seconds
    timestamp: Optional[str] = None


class RecommendRequest(BaseModel):
    user_id: str
    model: Optional[str] = None
    top_k: int = 5


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/recommender/track")
async def track_page_view(event: PageViewEvent) -> dict:
    """Record a page view event from the browser extension.

    Args:
        event: PageViewEvent with user_id, url, title, time_spent, timestamp.

    Returns:
        dict: success status and total views count for the user.
    """
    record_page_view(
        user_id=event.user_id,
        url=event.url,
        title=event.title,
        time_spent=event.time_spent,
        timestamp=event.timestamp,
    )
    total = len(get_page_views(event.user_id, min_time=0))
    logger.info(f"📊 Tracked page view for {event.user_id}: {event.url} ({event.time_spent}s)")
    return {"success": True, "total_views": total}


@router.post("/recommender/recommendations")
async def get_recommendations(request: RecommendRequest) -> dict:
    """Generate AI-powered recommendations based on browsing history.

    Args:
        request: RecommendRequest with user_id, optional model, top_k.

    Returns:
        dict: success, answer (recommendations text), tool_calls log.
    """
    model = request.model or config.foundry_default_model
    if not model:
        return {"success": False, "error": "Model not specified and not set in config.json"}

    views = get_page_views(request.user_id)
    if not views:
        return {"success": False, "error": "No browsing history found for this user"}

    prompt = json.dumps({
        "user_id": request.user_id,
        "top_k": request.top_k,
        "instruction": (
            "Analyze the user's browsing history using analyze_interests tool, "
            "then call generate_recommendations with the extracted interests. "
            "Return a concise list of recommendations."
        ),
    })

    agent = _get_agent()
    result = await agent.run(user_message=prompt, model=model)

    return {
        "success": result.success,
        "answer": result.answer,
        "tool_calls": [
            {"tool": tc.tool, "arguments": tc.arguments, "result": tc.result}
            for tc in result.tool_calls
        ],
        "iterations": result.iterations,
        **( {"error": result.error} if result.error else {}),
    }


@router.get("/recommender/history")
async def get_history(user_id: str, min_time: int = 10) -> dict:
    """Return filtered browsing history for a user.

    Args:
        user_id: User identifier.
        min_time: Minimum seconds on page to include (default 10).

    Returns:
        dict: success, user_id, views list, count.
    """
    views = get_page_views(user_id, min_time=min_time)
    return {"success": True, "user_id": user_id, "views": views, "count": len(views)}
