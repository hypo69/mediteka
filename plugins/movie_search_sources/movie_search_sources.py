# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Плагин поиска источников фильмов
# =============================================================================
# Описание:
#   Загружает внешний файл source.json с каталогом сайтов для поиска фильмов.
#   При запросах пользователя о фильмах/сериалах (где посмотреть, плеер и т.д.)
#   последовательно обращается к источникам и сообщает об этом в чат-окно
#   через streaming status-сообщения.
#
# File: movie_search_sources.py
# Project: mediteka
# Package: plugins.movie_search_sources
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import asyncio
from pathlib import Path
from typing import AsyncIterator

from plugins.plugin import BasePlugin
from src.logger import logger

# Путь к файлу с источниками
_SOURCE_FILE = Path(__file__).parent / 'sources.json'

# Ключевые слова для определения запроса о поиске фильмов/сериалов
_SEARCH_KEYWORDS = (
    'где посмотреть', 'где можно посмотреть', 'где скачать', 'онлайн',
    'стриминг', 'плеер', 'iframe', 'vidsrc', 'embed', 'смотреть онлайн',
    'источник', 'источники фильм', 'сайт фильм', 'сайт сериал',
    'where to watch', 'streaming', 'watch online', 'player', 'film player',
    'justwatch', 'reelgood', 'kinogo', 'rezka', 'hdrezka', 'seasonvar',
    'hdvb', '2embed', 'superembed', 'tmdb', 'imdb api', 'omdb',
)

# Ключевые слова общего характера для фильмов
_MEDIA_KEYWORDS = (
    'фильм', 'сериал', 'кино', 'movie', 'series', 'film', 'cinema',
    'мультфильм', 'аниме', 'anime', 'шоу', 'show',
)


def _load_sources() -> dict | None:
    """Загрузка source.json."""
    if not _SOURCE_FILE.exists():
        logger.warning(f'[movie_search_sources] Файл source.json не найден: {_SOURCE_FILE}')
        return None
    try:
        with open(_SOURCE_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'[movie_search_sources] Ошибка загрузки source.json', e)
        return None


def _format_source_context(sources: dict) -> str:
    """Собирает текстовый контекст из source.json для AI-модели."""
    lines = ['=== КАТАЛОГ ИСТОЧНИКОВ ДЛЯ ПОИСКА ФИЛЬМОВ ===\n']

    sections = {
        'metadata_apis': '📋 Базы метаданных (TMDb, OMDb, IMDb)',
        'streaming_search': '🔍 Агрегаторы стриминга (JustWatch, Reelgood)',
        'video_search': '🎥 Видеопоиск (Yandex Video, Google Video)',
        'iframe_players': '📺 Встроенные плееры (VidSrc, 2Embed и др.)',
        'direct_sites': '🌐 Прямые сайты (Rezka, Kinogo, Seasonvar)',
        'torrent_trackers': '🧲 Торрент-трекеры (Rutracker, NNMClub)',
        'infrastructure': '⚙️ Инфраструктура (StreamDB)',
        'open_source_tools': '🛠 Open-source инструменты (yt-dlp, Jackett и др.)',
    }

    for key, label in sections.items():
        items = sources.get(key, [])
        if not items:
            continue
        lines.append(f'\n{label}:')
        for item in items:
            if not item.get('enabled', True):
                continue
            name = item['name']
            url = item.get('url', '')
            desc = item.get('description', '')
            api_key = ' [требует API-ключ]' if item.get('requires_api_key') else ''
            ytdlp_tag = ' [Поддерживает скачивание/стриминг через yt-dlp]' if item.get('supports_ytdlp') else ''
            lines.append(f'  - {name} ({url}){api_key}{ytdlp_tag}: {desc}')

    return '\n'.join(lines)


class MovieSearchSourcesPlugin(BasePlugin):
    """Плагин для ответов о поиске фильмов с перечислением обращаемых источников.

    При запросе пользователя о фильмах (где посмотреть, API, плееры и т.д.)
    последовательно информирует о каждом опрашиваемом источнике через
    статусные сообщения, затем генерирует финальный ответ через AI.
    """

    name = 'movie_search_sources'

    def __init__(self, ai_model) -> None:
        super().__init__(ai_model)
        self._sources = _load_sources()
        if self._sources:
            logger.info(
                f'[movie_search_sources] Загружен source.json: '
                f'{sum(len(v) for v in self._sources.values() if isinstance(v, list))} источников'
            )

    def _is_search_query(self, message: str) -> bool:
        """Проверяет, относится ли запрос к поиску фильмов/плееров/источников."""
        low = message.lower()
        return any(kw in low for kw in _SEARCH_KEYWORDS)

    def _is_media_query(self, message: str) -> bool:
        """Проверяет, является ли запрос медиа-запросом общего характера."""
        low = message.lower()
        return any(kw in low for kw in _MEDIA_KEYWORDS)

    def can_handle(self, message: str) -> bool:
        """Плагин активируется только на запросы о поиске источников фильмов."""
        if not self._sources:
            return False
        return self._is_search_query(message)

    async def _handle(self, message: str, **kwargs) -> AsyncIterator[dict]:
        """Поток: статусы → список источников → AI-ответ."""
        if not self._sources:
            return

        yield {'status': '📚 Загрузка каталога источников (source.json)...'}
        await asyncio.sleep(0.05)

        # Перебираем категории источников и уведомляем пользователя
        section_labels = {
            'metadata_apis': '📋 Базы метаданных',
            'streaming_search': '🔍 Агрегаторы стриминга',
            'video_search': '🎥 Видеопоиск',
            'iframe_players': '📺 Iframe-плееры',
            'direct_sites': '🌐 Прямые сайты',
            'torrent_trackers': '🧲 Торрент-трекеры',
            'infrastructure': '⚙️ Инфраструктура',
            'open_source_tools': '🛠 Open-source инструменты',
        }

        # Определяем релевантные категории по содержимому запроса
        relevant_sections = self._get_relevant_sections(message)

        for section_key in relevant_sections:
            items = self._sources.get(section_key, [])
            enabled_items = [i for i in items if i.get('enabled', True)]
            if not enabled_items:
                continue

            section_label = section_labels.get(section_key, section_key)
            for item in enabled_items:
                name = item['name']
                url = item.get('url', '')
                yield {'status': f'{section_label}: Обращение к {name} ({url})...'}
                await asyncio.sleep(0.08)

        yield {'status': '🤖 Формирование ответа...'}

        # Строим контекст из источников для AI
        sources_context = _format_source_context(self._sources)
        system_prompt = (
            'Ты — ассистент по поиску фильмов и сериалов.\n'
            'Тебе предоставлен каталог реальных источников: сайты, API, плееры и трекеры.\n'
            'Используй только этот каталог. Отвечай структурированно, по-русски.\n'
            'Если пользователь спрашивает о конкретном фильме — дай ему лучший способ посмотреть или скачать.\n\n'
            + sources_context
        )

        system_instruction = kwargs.get('system_instruction') or ''
        full_system = f'{system_instruction}\n\n{system_prompt}'.strip() if system_instruction else system_prompt

        response = await self.ai.chat(
            message,
            system_instruction=full_system,
            history=kwargs.get('history', []),
        )

        yield {'text': response or 'Не удалось получить ответ от AI.'}

    def _get_relevant_sections(self, message: str) -> list[str]:
        """Определяет релевантные разделы source.json по тексту запроса."""
        low = message.lower()
        all_sections = [
            'metadata_apis',
            'streaming_search',
            'video_search',
            'iframe_players',
            'direct_sites',
            'torrent_trackers',
            'infrastructure',
            'open_source_tools',
        ]

        # Если вопрос явно о торрентах — добавляем трекеры
        if any(kw in low for kw in ('торрент', 'скачать', 'torrent', 'rutracker', 'nnm')):
            priority = ['torrent_trackers', 'metadata_apis']
        # Если о плеерах/iframe — плееры в приоритете
        elif any(kw in low for kw in ('плеер', 'iframe', 'embed', 'vidsrc', '2embed', 'player')):
            priority = ['iframe_players', 'metadata_apis', 'direct_sites']
        # Если о стриминге/где посмотреть
        elif any(kw in low for kw in ('где посмотреть', 'стриминг', 'онлайн', 'streaming', 'watch online', 'justwatch')):
            priority = ['streaming_search', 'iframe_players', 'direct_sites', 'metadata_apis']
        # Если об API/разработке
        elif any(kw in low for kw in ('api', 'tmdb', 'omdb', 'imdb api', 'python', 'библиотека', 'library')):
            priority = ['metadata_apis', 'open_source_tools', 'iframe_players']
        else:
            # Общий вопрос — перебираем всё
            priority = all_sections

        # Оставляем только уникальные, сохраняя порядок
        seen = set()
        result = []
        for s in priority + all_sections:
            if s not in seen:
                seen.add(s)
                result.append(s)
        return result
