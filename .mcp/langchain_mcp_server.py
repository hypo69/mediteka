# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: LangChain Media MCP Server
# =============================================================================
# Описание:
#   MCP-сервер на базе FastMCP, предоставляющий доступ к агенту поиска медиа
#   и отдельным инструментам LangChain (поиск торрентов, метаданные, источники,
#   формирование URL плеера) для любого внешнего MCP-клиента.
#
# File: langchain_mcp_server.py
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
from src.ai.langchain_agent import MediaSearchAgent
from src.ai.langchain_tools import (
    search_torrents,
    get_movie_metadata,
    get_streaming_sources,
    build_player_url,
    add_torrent_download,
)

# Инициализация FastMCP сервера
mcp = FastMCP("LangChain-Media-Agent")

# Путь к конфигурации
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


@mcp.tool()
async def media_agent_search(query: str) -> str:
    """Выполнить автономный поиск фильма или сериала через LangChain ReAct-агента.

    Агент самостоятельно определяет нужные инструменты, ищет торренты или
    стриминговые источники и возвращает структурированный JSON с действием:
    'player', 'torrent' или 'info'.

    Args:
        query: Поисковый запрос пользователя (напр. 'найди фильм Начало 1080p').
    """
    try:
        agent = MediaSearchAgent(config_path=_CONFIG_PATH)
        result = await agent.search(query)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[langchain_mcp_server] Ошибка media_agent_search: {e}")
        return json.dumps({"action": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
async def media_search_torrents(query: str) -> str:
    """Поиск торрентов на Rutracker и NNMClub через Playwright.

    Args:
        query: Название фильма или сериала для поиска.
    """
    try:
        return await search_torrents.ainvoke(query)
    except Exception as e:
        logger.error(f"[langchain_mcp_server] Ошибка media_search_torrents: {e}")
        return json.dumps([], ensure_ascii=False)


@mcp.tool()
async def media_get_metadata(title: str) -> str:
    """Получение метаданных о фильме (рейтинг, описание, год, постер) из TMDb.

    Args:
        title: Название фильма для поиска.
    """
    try:
        return await get_movie_metadata.ainvoke(title)
    except Exception as e:
        logger.error(f"[langchain_mcp_server] Ошибка media_get_metadata: {e}")
        return json.dumps({}, ensure_ascii=False)


@mcp.tool()
def media_get_streaming_sources(title: str) -> str:
    """Получение каталога активных стриминг-источников и iframe-плееров.

    Args:
        title: Название фильма (для контекста поиска).
    """
    try:
        return get_streaming_sources.invoke(title)
    except Exception as e:
        logger.error(f"[langchain_mcp_server] Ошибка media_get_streaming_sources: {e}")
        return json.dumps({}, ensure_ascii=False)


@mcp.tool()
def media_build_player_url(url: str, provider: str) -> str:
    """Формирование URL для встроенного плеера CosmicPlayer.

    Args:
        url: Исходный URL или ID фильма (tmdb_id).
        provider: Имя провайдера (youtube, vk, rutube, seasonvar, hdrezka, kinogo, direct, vidsrc).
    """
    try:
        return build_player_url.invoke({"url": url, "provider": provider})
    except Exception as e:
        logger.error(f"[langchain_mcp_server] Ошибка media_build_player_url: {e}")
        return json.dumps({}, ensure_ascii=False)


@mcp.tool()
async def media_add_torrent_download(url: str, source: str, title: str) -> str:
    """Добавление торрента на скачивание в qBittorrent.

    Args:
        url: URL или magnet-ссылка торрента.
        source: Трекер (rutracker, nnmclub).
        title: Название торрента.
    """
    try:
        return await add_torrent_download.ainvoke({"url": url, "source": source, "title": title})
    except Exception as e:
        logger.error(f"[langchain_mcp_server] Ошибка media_add_torrent_download: {e}")
        return f"Ошибка: {e}"


if __name__ == "__main__":
    logger.info("[langchain_mcp_server] Запуск LangChain Media FastMCP сервера...")
    mcp.run()
