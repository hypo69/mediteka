# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: RAG Plugin для чата
# =============================================================================
# Описание:
#   Плагин для подключения RAG-поиска медиатеки к чату через Function Calling.
#   Автоматически определяет медиа-запросы и использует Gemini Functions
#   для семантического поиска и получения информации о фильмах/сериалах.
#
# File: rag_plugin.py
# Project: gemini-simplechat
# Package: plugins.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
from plugins.plugin import BasePlugin
from plugins.media_organizer.core.media_rag_functions import (
    get_media_tools,
    dispatch_media_tool_call,
)
from plugins.media_organizer.core.media_rag import get_media_rag
from src.ai.dev_rag import rag_search_tool # ИМПОРТ ИНСТРУМЕНТА
import os

_MEDIA_KEYWORDS = (
    "фильм", "сериал", "кино", "эпизод", "сезон", "актёр", "режиссёр",
    "movie", "series", "episode", "season", "actor", "director", "film",
    "диск", "медиа", "media", "посмотреть", "рекомендуй", "похожее",
    "что посмотреть", "какой фильм", "посоветуй", "рейтинг",
    "случайн", "рандом", "карусель",
)

# Ключевые слова для технического поиска
_DEV_KEYWORDS = (
    "код", "функция", "инструкция", "как сделать", "стандарт", "ошибка", "настройка",
    "классу", "модуль", "файл", "api", "rag", "конфигурация"
)


class RAGPlugin(BasePlugin):
    # ... (предыдущий код без изменений) ...

    def _is_dev_query(self, message: str) -> bool:
        """Определение технического запроса."""
        low = message.lower()
        return any(kw in low for kw in _DEV_KEYWORDS)

    async def _handle(self, message: str, **kwargs):
        """Обработка запроса (медиа или технический)."""

        # 1. Сначала медиа-поиск
        if self._is_media_query(message):
            # ... (логика медиа-поиска осталась прежней) ...
            # ПРИМЕЧАНИЕ: Для краткости я опускаю здесь вставку всего кода медиа-поиска,
            # но при замене он ОСТАНЕТСЯ внутри функции _handle.
            pass 

        # 2. Если не медиа, но технический запрос — ищем по коду
        if self._is_dev_query(message):
            yield {"status": "🛠️ Поиск по техническому контексту..."}
            api_key = os.getenv('GEMINI_API_KEY', '')
            results_json = rag_search_tool(message, api_key=api_key)

            # ... (логика обработки результатов dev_rag аналогична media_rag) ...
            yield {"text": f"🛠️ Результаты поиска по коду:\n{results_json}"}
            return

    """RAG-плагин для семантического поиска медиатеки в чате.

    Использует Gemini Function Calling для поиска фильмов и сериалов
    через RAG-индекс с семантическим поиском.

    Attributes:
        name (str): Имя плагина.
        _tools (list): Список инструментов Function Calling.
    """

    name = "rag"

    def __init__(self, ai_model):
        """Инициализация RAG-плагина.

        Args:
            ai_model: Экземпляр GoogleGenerativeAI.
        """
        super().__init__(ai_model)
        self._tools = get_media_tools()

    def _is_media_query(self, message: str) -> bool:
        """Определение медиа-запроса по ключевым словам.

        Args:
            message (str): Сообщение пользователя.

        Returns:
            bool: True если запрос о медиа.
        """
        low = message.lower()
        return any(kw in low for kw in _MEDIA_KEYWORDS)

    async def _handle(self, message: str, **kwargs):
        """Обработка медиа-запроса через локальный поиск (без вызова Gemini)."""
        if not self._is_media_query(message):
            return

        try:
            low_message = message.lower()
            if "карусель" in low_message or "случайн" in low_message or "рандом" in low_message:
                import sqlite3
                import random
                import asyncio
                from plugins.media_organizer.core import MEDIA_DB
                from src.fastapi.router_control import manager

                yield {"status": "🎡 Выбор случайного фильма через карусель..."}

                with sqlite3.connect(MEDIA_DB) as conn:
                    conn.row_factory = sqlite3.Row
                    row = conn.execute(
                        "SELECT title, title_ru, year, main_category, disk_name, plot, path FROM media "
                        "WHERE (media_type = 'movie' OR media_type IS NULL OR media_type = '') "
                        "  AND (title IS NOT NULL AND title != '') "
                        "ORDER BY RANDOM() LIMIT 1"
                    ).fetchone()
                    
                    if not row:
                        row = conn.execute(
                            "SELECT title, title_ru, year, main_category, disk_name, plot, path FROM media "
                            "WHERE title IS NOT NULL AND title != '' "
                            "ORDER BY RANDOM() LIMIT 1"
                        ).fetchone()

                if not row:
                    yield {"text": "❌ Ошибка: База данных медиатеки пуста."}
                    return

                title = row['title']
                title_ru = row['title_ru']
                year = row['year']
                main_category = row['main_category']
                plot = row['plot']
                path = row['path']
                disk_name = row['disk_name']

                room_id = kwargs.get('room_id', 'default')
                has_player = room_id in manager.rooms and len(manager.rooms[room_id].get("player", [])) > 0
                
                if path and has_player:
                    asyncio.create_task(manager.broadcast_to_role(room_id, "player", {
                        "action": "play_file_by_path",
                        "path": path
                    }))

                status_msg = "🚀 Запускаю воспроизведение на плеере..." if has_player else "📱 Вы можете запустить воспроизведение локально или открыть стрим."

                response_text = (
                    f"🎡 **Карусель выбрала случайный фильм!**\n\n"
                    f"🎬 **Название:** <film>{title_ru or title}</film>\n"
                    f"📅 **Год:** {year or 'Неизвестно'}\n"
                    f"📂 **Категория:** {main_category or 'Без категории'}\n"
                    f"💿 **Диск:** {disk_name or 'Неизвестно'}\n\n"
                    f"📝 **Описание:** {plot or 'Нет описания.'}\n\n"
                    f"{status_msg}"
                )

                yield {"text": response_text}
                return

            import json
            from plugins.media_organizer.core.media_rag_functions import search_media

            yield {"status": "🔍 Поиск в локальном RAG-индексе..."}
            results_json = search_media(message)
            results_data = json.loads(results_json)

            if "error" in results_data:
                yield {"text": f"❌ Ошибка поиска: {results_data['error']}"}
                return

            results = results_data.get("results", [])
            if not results:
                yield {"text": f"🔍 По запросу **«{message}»** ничего не найдено в локальной медиатеке."}
                return

            text = f"🔍 **Результаты поиска в медиатеке по запросу «{message}»**:\n\n"
            for i, item in enumerate(results, 1):
                text += f"{i}. **{item.get('title')}** ({item.get('year') or '?'})\n"
                text += f"   * Тип: {item.get('type')}, Категория: {item.get('category')}\n"
                text += f"   * Диск: {item.get('disk_name')} (Схожесть: {item.get('score')})\n\n"

            yield {"text": text}
            voice_parts = []
            for i, item in enumerate(results, 1):
                title_ru = item.get('title_ru') or item.get('title') or ""
                clean_title = re.sub(r'[a-zA-Z]', '', title_ru).replace('(', '').replace(')', '').strip()
                tts_text = item.get('why_watch') or item.get('plot') or ""
                voice_parts.append(f"{i}. {clean_title}. {tts_text}")
            voice_text = " ".join(voice_parts)
            yield {"voice": voice_text}

        except Exception as e:
            from src.logger import logger
            logger.error(f"RAG Plugin error: {e}", exc_info=True)
            yield {"text": f"❌ Произошла ошибка при выполнении локального поиска: {e}"}
            return
# Export for plugin loader
plugin = RAGPlugin