# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Antigravity (AGY) Web Search MCP Server
# =============================================================================
# Описание:
#   MCP-сервер на базе FastMCP, предоставляющий доступ к поиску в интернете
#   через Google Antigravity SDK и встроенные инструменты (SEARCH_WEB).
#
# File: agy_search_mcp_server.py
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
from plugins.web_search.agy_searcher import AgyWebSearcher

# Инициализация FastMCP сервера
mcp = FastMCP("Antigravity-Search-Server")


@mcp.tool()
async def agy_web_search(query: str, model: str = "agy-flash") -> str:
    """Выполнить веб-поиск через агентный поиск Google Antigravity.

    Использует возможности Antigravity SDK с инструментами BuiltinTools.SEARCH_WEB
    и READ_URL_CONTENT для извлечения актуальной информации из сети.

    Args:
        query: Поисковый запрос пользователя.
        model: Имя модели Antigravity (по умолчанию 'agy-flash').
    """
    try:
        searcher = AgyWebSearcher(model_id=model)
        result = await searcher.search_and_extract(query=query)
        return result
    except Exception as e:
        logger.error(f"[agy_search_mcp_server] Ошибка agy_web_search: {e}")
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
