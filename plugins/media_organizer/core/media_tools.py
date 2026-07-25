# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: MCP-подобные инструменты поиска в медиатеке
# =============================================================================
# Описание:
#   Определение function-calling инструментов для Gemini.
#   Модель самостоятельно вызывает нужный инструмент при запросах
#   о конкретных фильмах, сериалах или содержимом дисков.
#
# File: media_tools.py
# Project: gemini-simplechat
# Package: plugins.media_organizer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import os
from pathlib import Path
from typing import Any

from google.genai import types

from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core import MEDIA_DB


# ------------------------------------------------------------------
# Реализации инструментов
# ------------------------------------------------------------------

def search_media(query: str, media_type: str = '') -> str:
    """Поиск медиа по названию во всей БД.

    Args:
        query (str): Поисковый запрос (название или его часть).
        media_type (str): Фильтр по типу: 'movie', 'series' или '' для обоих.

    Returns:
        str: JSON-строка со списком найденных записей.

    Examples:
        >>> search_media('Титаник')
        >>> search_media('Breaking', 'series')
    """
    db = MediaDatabase(MEDIA_DB)
    q = query.lower()
    results = [
        r for r in db.export_all()
        if (
            q in r.get('title', '').lower()
            or q in r.get('title_ru', '').lower()
            or q in r.get('title_orig', '').lower()
        )
        and (not media_type or r.get('type') == media_type)
    ]
    return json.dumps(results, ensure_ascii=False, indent=2)


def get_disk_contents(disk_name: str, media_type: str = '') -> str:
    """Получение всех записей диска из БД.

    Args:
        disk_name (str): Имя диска, например 'ДИСК 1'.
        media_type (str): Фильтр по типу: 'movie', 'series' или '' для обоих.

    Returns:
        str: JSON-строка со списком записей диска.

    Examples:
        >>> get_disk_contents('ДИСК 1')
        >>> get_disk_contents('ДИСК 2', 'movie')
    """
    db = MediaDatabase(MEDIA_DB)
    records = db.export_disk(disk_name)
    if media_type:
        records = [r for r in records if r.get('type') == media_type]
    return json.dumps(records, ensure_ascii=False, indent=2)


def get_media_card(title: str, disk_name: str = '') -> str:
    """Получение полной карточки медиа по точному названию.

    Args:
        title (str): Точное название медиа.
        disk_name (str): Имя диска для уточнения (опционально).

    Returns:
        str: JSON-строка с записью или сообщение об отсутствии.

    Examples:
        >>> get_media_card('Титаник (Titanic, 1997)')
        >>> get_media_card('Фауда', 'ДИСК 1')
    """
    db = MediaDatabase(MEDIA_DB)
    if disk_name:
        for media_type in ('movie', 'series'):
            record = db.get_media(disk_name, title, media_type)
            if record:
                return json.dumps(record, ensure_ascii=False, indent=2)
    record = db.find_any_disk(title, 'movie') or db.find_any_disk(title, 'series')
    if record:
        return json.dumps(record, ensure_ascii=False, indent=2)
    return json.dumps({'error': f'Запись не найдена: {title}'}, ensure_ascii=False)


# ------------------------------------------------------------------
# Диспетчер вызовов
# ------------------------------------------------------------------

def _rag_search_wrapper(query: str, top_k: int = 5) -> str:
    """RAG-поиск через семантический индекс (обёртка для диспетчера)."""
    from plugins.media_organizer.core.media_rag import rag_search_tool
    api_key = os.getenv('GEMINI_API_KEY', '')
    return rag_search_tool(query, top_k=top_k, api_key=api_key)


_TOOL_HANDLERS: dict[str, Any] = {
    'search_media': search_media,
    'get_disk_contents': get_disk_contents,
    'get_media_card': get_media_card,
    'rag_search': _rag_search_wrapper,
}


def dispatch_tool_call(name: str, args: dict) -> str:
    """Вызов инструмента по имени с переданными аргументами.

    Args:
        name (str): Имя инструмента.
        args (dict): Аргументы вызова от модели.

    Returns:
        str: Результат выполнения инструмента.

    Examples:
        >>> dispatch_tool_call('search_media', {'query': 'Титаник'})
    """
    handler = _TOOL_HANDLERS.get(name)
    if not handler:
        return json.dumps({'error': f'Неизвестный инструмент: {name}'}, ensure_ascii=False)
    return handler(**args)


# ------------------------------------------------------------------
# Определения инструментов для Gemini (google.genai types)
# ------------------------------------------------------------------

MEDIA_TOOLS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name='search_media',
            description='Search for movies or series in the local media library by title (full or partial match).',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'query': types.Schema(type=types.Type.STRING, description='Title or part of the title to search for.'),
                    'media_type': types.Schema(type=types.Type.STRING, description='Filter by type: "movie", "series", or empty string for both.'),
                },
                required=['query'],
            ),
        ),
        types.FunctionDeclaration(
            name='get_disk_contents',
            description='Get all media records stored on a specific disk, e.g. "ДИСК 1".',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'disk_name': types.Schema(type=types.Type.STRING, description='Disk name, e.g. "ДИСК 1" or "ДИСК 3".'),
                    'media_type': types.Schema(type=types.Type.STRING, description='Filter by type: "movie", "series", or empty string for both.'),
                },
                required=['disk_name'],
            ),
        ),
        types.FunctionDeclaration(
            name='get_media_card',
            description='Get the full metadata card for a media item by its exact title.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'title': types.Schema(type=types.Type.STRING, description='Exact title of the movie or series.'),
                    'disk_name': types.Schema(type=types.Type.STRING, description='Optional disk name to narrow the search.'),
                },
                required=['title'],
            ),
        ),
        types.FunctionDeclaration(
            name='rag_search',
            description=(
                'Semantic search across the entire media library using natural language. '
                'Use this when the user describes a mood, plot, genre, or atmosphere '
                'rather than an exact title. Examples: "film about love on a ship", '
                '"dark detective series", "something funny for the evening".'
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'query': types.Schema(type=types.Type.STRING, description='Natural language description of what to find.'),
                    'top_k': types.Schema(type=types.Type.INTEGER, description='Number of results to return (default 5).'),
                },
                required=['query'],
            ),
        ),
    ]
)
