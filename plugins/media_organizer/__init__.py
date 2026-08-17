# -*- coding: utf-8 -*-
# =============================================================================
# Media Organizer Plugin
# =============================================================================
# Плагин для управления медиатекой с RAG-поиском
#
# Provides:
# - MediaDatabase: SQLite-база данных медиатеки
# - GeminiRAG: Векторный поиск через Gemini Embedding API
# - RAG Functions: Gemini Function Calling инструменты
# =============================================================================

from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core.media_rag import (
    build_media_rag,
    get_media_rag,
    rag_search_tool,
)
from plugins.media_organizer.core.media_rag_functions import (
    search_media,
    get_media_card,
    find_by_exact_title,
    get_random_media,
    rebuild_rag_index,
    get_rag_status,
    get_media_tools,
    dispatch_media_tool_call,
    ask_with_media_rag,
)
from plugins.plugin import BasePlugin

__all__ = [
    # Database
    'MediaDatabase',
    # RAG
    'build_media_rag',
    'get_media_rag',
    'rag_search_tool',
    # Functions
    'search_media',
    'get_media_card',
    'find_by_exact_title',
    'get_random_media',
    'rebuild_rag_index',
    'get_rag_status',
    'get_media_tools',
    'dispatch_media_tool_call',
    'ask_with_media_rag',
    # Plugin
    'plugin',
]


class MediaOrganizerPlugin(BasePlugin):
    """Плагин для управления медиатекой с RAG-поиском.
    
    Этот плагин не перехватывает сообщения чата, а предоставляет
    функции для работы с медиатекой через Function Calling.
    """
    
    name = 'media_organizer'

    def can_handle(self, message: str) -> bool:
        return False
    
    async def _handle(self, message: str) -> str | None:
        """Плагин не перехватывает веб-запросы."""
        return None


# Create plugin instance
plugin = MediaOrganizerPlugin