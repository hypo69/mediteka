# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Gemini Web Search MCP Server
# =============================================================================
# Описание:
#   MCP-сервер на базе FastMCP, предоставляющий доступ к веб-поиску Google
#   Search Grounding через официальный google-genai SDK с автоматической
#   ротацией API-ключей (Round-Robin) при исчерпании лимитов.
#
# File: gemini_search_mcp_server.py
# Project: mediteka
# Package: .mcp
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import asyncio
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from src.logger import logger
from plugins.web_search.gemini_searcher import GeminiWebSearcher, GeminiKeyPool

# Инициализация FastMCP сервера
mcp = FastMCP("Gemini-Search-Server")


@mcp.tool()
async def gemini_web_search(query: str, model: str = "gemini-2.5-flash") -> str:
    """Выполнить веб-поиск в Google через Gemini Search Grounding.

    Использует официальный SDK Google GenAI со встроенным поисковым
    инструментом Google Search и автоматической ротацией API-ключей при ошибках 429.

    Args:
        query: Поисковый запрос пользователя.
        model: Название модели (по умолчанию 'gemini-2.5-flash').
    """
    try:
        searcher = GeminiWebSearcher()
        result_markdown = await searcher.search_and_extract(query=query, model=model)
        return result_markdown
    except Exception as e:
        logger.error(f"[gemini_search_mcp_server] Ошибка поиска: {e}")
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def gemini_key_pool_status() -> str:
    """Получить статус пула API-ключей Gemini и активного ключа."""
    try:
        pool = GeminiKeyPool()
        return json.dumps({
            "status": "ok",
            "total_keys": len(pool.api_keys),
            "active_key_masked": f"...{pool._current_key[-6:]}" if len(pool._current_key) >= 6 else "***"
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[gemini_search_mcp_server] Ошибка статуса пула ключей: {e}")
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
