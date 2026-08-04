# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Recommender Agent — персональная рекомендательная система
# =============================================================================
# Description:
#   Серверный агент, который принимает историю просмотров пользователя
#   (URL + время на странице + заголовок), анализирует интересы через AI
#   и возвращает персональные рекомендации.
#
#   Workflow:
#     Browser Extension
#       │  POST /api/v1/recommender/track  (page_view events)
#       │  GET  /api/v1/recommender/recommendations
#       ▼
#     RecommenderAgent.run()
#       ├─ analyze_interests  → AI анализирует топики из истории
#       └─ generate_recommendations → AI формирует список рекомендаций
#
# File: src/agents/recommender_agent.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import BaseAgent, ToolDefinition

logger = logging.getLogger(__name__)

# In-memory store: user_id → list of page_view dicts
# For production replace with persistent storage (Redis / SQLite)
_page_views: Dict[str, List[Dict]] = defaultdict(list)

# Retention window for page views
_RETENTION_DAYS = 30
# Minimum time on page (seconds) to count as "read"
_MIN_TIME_SECONDS = 10


def record_page_view(
    user_id: str,
    url: str,
    title: str,
    time_spent: int,
    timestamp: Optional[str] = None,
) -> None:
    """Store a page view event for a user.

    Args:
        user_id: Unique identifier for the browser session / user.
        url: Full URL of the visited page.
        title: Page title extracted by the extension.
        time_spent: Seconds the user spent on the page.
        timestamp: ISO-8601 timestamp; defaults to now.
    """
    _page_views[user_id].append({
        "url": url,
        "title": title,
        "time_spent": time_spent,
        "timestamp": timestamp or datetime.utcnow().isoformat(),
    })
    # Keep only recent views
    cutoff = (datetime.utcnow() - timedelta(days=_RETENTION_DAYS)).isoformat()
    _page_views[user_id] = [
        v for v in _page_views[user_id] if v["timestamp"] >= cutoff
    ]


def get_page_views(user_id: str, min_time: int = _MIN_TIME_SECONDS) -> List[Dict]:
    """Return filtered page views for a user.

    Args:
        user_id: User identifier.
        min_time: Minimum seconds on page to include.

    Returns:
        List[Dict]: Filtered and sorted page view records.
    """
    views = [v for v in _page_views.get(user_id, []) if v["time_spent"] >= min_time]
    return sorted(views, key=lambda v: v["time_spent"], reverse=True)


class RecommenderAgent(BaseAgent):
    """Персональный рекомендательный агент на основе истории просмотров.

    Анализирует, какие страницы пользователь читал дольше всего,
    определяет топики интересов и генерирует рекомендации.

    Tools:
        analyze_interests: Извлекает топики из истории просмотров.
        generate_recommendations: Формирует список рекомендаций.

    Example:
        >>> agent = RecommenderAgent(foundry_client)
        >>> result = await agent.run(
        ...     user_message=json.dumps({"user_id": "u1", "top_k": 5}),
        ...     model="foundry::qwen3-0.6b",
        ... )
        >>> print(result.answer)
    """

    name = "recommender"
    description = "Анализирует историю просмотров и генерирует персональные рекомендации"

    @property
    def tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="analyze_interests",
                description=(
                    "Анализирует историю просмотров пользователя и возвращает "
                    "список топиков интересов с весами."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "ID пользователя"},
                        "top_n": {
                            "type": "integer",
                            "description": "Количество топ-страниц для анализа",
                            "default": 20,
                        },
                    },
                    "required": ["user_id"],
                },
            ),
            ToolDefinition(
                name="generate_recommendations",
                description=(
                    "На основе топиков интересов формирует список рекомендаций "
                    "(темы, запросы, типы контента)."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "interests": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Список топиков интересов",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Количество рекомендаций",
                            "default": 5,
                        },
                    },
                    "required": ["interests"],
                },
            ),
        ]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a recommender tool.

        Args:
            name: Tool name ('analyze_interests' or 'generate_recommendations').
            arguments: Tool arguments dict.

        Returns:
            str: JSON-encoded tool result.
        """
        if name == "analyze_interests":
            return self._analyze_interests(arguments)
        if name == "generate_recommendations":
            return self._generate_recommendations(arguments)
        return f"❌ Unknown tool: {name}"

    def _analyze_interests(self, args: Dict) -> str:
        """Extract interest topics from page view history.

        Args:
            args: Dict with user_id (str) and optional top_n (int).

        Returns:
            str: JSON with interests list and page view summary.
        """
        user_id: str = args.get("user_id", "")
        top_n: int = int(args.get("top_n", 20))

        views = get_page_views(user_id)[:top_n]
        if not views:
            return json.dumps({"interests": [], "message": "No page views found"})

        # Build a compact summary for the AI to analyse
        summary = [
            {"title": v["title"], "url": v["url"], "seconds": v["time_spent"]}
            for v in views
        ]
        return json.dumps({"page_views": summary, "total": len(views)})

    def _generate_recommendations(self, args: Dict) -> str:
        """Format interests for the AI recommendation step.

        Args:
            args: Dict with interests (list) and optional top_k (int).

        Returns:
            str: JSON with interests and requested count.
        """
        interests: List[str] = args.get("interests", [])
        top_k: int = int(args.get("top_k", 5))
        return json.dumps({"interests": interests, "top_k": top_k})
