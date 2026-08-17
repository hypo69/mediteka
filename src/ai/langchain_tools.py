# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Инструменты LangChain Media Agent
# =============================================================================
# Описание:
#   Набор нативных LangChain-инструментов для агента поиска медиа.
#   Включает поиск торрентов, метаданные, стриминг-источники,
#   построение URL плеера и добавление торрентов в qBittorrent.
#
# File: langchain_tools.py
# Project: mediteka
# Package: src.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import json
import aiohttp
from pathlib import Path
from langchain_core.tools import tool
from src.logger import logger


# Путь к конфигурации источников
_SOURCES_PATH = Path(__file__).parent.parent.parent / 'plugins' / 'movie_search_sources' / 'sources.json'


@tool
async def search_torrents(query: str) -> str:
    """Выполняет поиск торрентов по названию на трекерах Rutracker и NNMClub.

    Возвращает JSON-строку со списком найденных торрентов (до 15 результатов).
    Каждый торрент содержит: title, size_human, seeds, peers, source, view_url, download_url.

    Args:
        query: Название фильма или сериала для поиска.
    """
    try:
        from plugins.torrent_playwright.playwright_searcher import PlaywrightTorrentSearcher
        searcher = PlaywrightTorrentSearcher()
        results = await searcher.search(query)
        if not results:
            return json.dumps([], ensure_ascii=False)
        return json.dumps(results[:15], ensure_ascii=False)
    except Exception as e:
        logger.error(f'[langchain_tools] Ошибка при поиске торрентов: {e}')
        return json.dumps([], ensure_ascii=False)


@tool
async def get_movie_metadata(title: str) -> str:
    """Получает метаданные о фильме из TMDb API: название, год, рейтинг, описание, постер.

    Args:
        title: Название фильма для поиска метаданных.
    """
    try:
        api_key = os.environ.get('TMDB_API_KEY', '')
        if not api_key:
            logger.warning('[langchain_tools] TMDB_API_KEY не задан в .env')
            return json.dumps({}, ensure_ascii=False)

        url = (
            f'https://api.themoviedb.org/3/search/movie'
            f'?api_key={api_key}&query={title}&language=ru-RU'
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status != 200:
                    logger.warning(f'[langchain_tools] TMDb вернул статус {response.status}')
                    return json.dumps({}, ensure_ascii=False)

                data = await response.json()
                results = data.get('results', [])
                if not results:
                    return json.dumps({}, ensure_ascii=False)

                first = results[0]
                release_date = first.get('release_date', '')
                poster_path = first.get('poster_path', '')

                result_data = {
                    'title': first.get('title', ''),
                    'year': release_date[:4] if release_date else '',
                    'rating': first.get('vote_average', 0),
                    'overview': first.get('overview', ''),
                    'poster_url': f'https://image.tmdb.org/t/p/w500{poster_path}' if poster_path else '',
                    'tmdb_id': first.get('id', 0),
                }
                return json.dumps(result_data, ensure_ascii=False)
    except Exception as e:
        logger.error(f'[langchain_tools] Ошибка при получении метаданных TMDb: {e}')
        return json.dumps({}, ensure_ascii=False)


@tool
def get_streaming_sources(title: str) -> str:
    """Возвращает доступные источники для просмотра фильма из каталога sources.json.

    Фильтрует только активные (enabled) источники и группирует по категориям:
    iframe_players, direct_sites, streaming_search.

    Args:
        title: Название фильма (используется для контекста, фильтрация по каталогу).
    """
    try:
        if not _SOURCES_PATH.exists():
            logger.warning(f'[langchain_tools] sources.json не найден: {_SOURCES_PATH}')
            return json.dumps({}, ensure_ascii=False)

        with open(_SOURCES_PATH, encoding='utf-8') as f:
            data = json.load(f)

        # Фильтруем только категории со списками источников
        relevant_categories = (
            'iframe_players', 'direct_sites', 'streaming_search', 'video_search',
        )
        active_sources = {}
        for category in relevant_categories:
            items = data.get(category, [])
            if not isinstance(items, list):
                continue
            enabled = [s for s in items if s.get('enabled', True)]
            if enabled:
                active_sources[category] = enabled

        return json.dumps(active_sources, ensure_ascii=False)
    except Exception as e:
        logger.error(f'[langchain_tools] Ошибка при чтении источников: {e}')
        return json.dumps({}, ensure_ascii=False)


@tool
def build_player_url(url: str, provider: str) -> str:
    """Формирует URL для встроенного плеера CosmicPlayer.

    Поддерживаемые провайдеры: youtube, vk, rutube, seasonvar, hdrezka, kinogo, direct.
    Также может строить embed-URL для iframe_players по TMDb/IMDb ID
    (например, vidsrc.cc: https://vidsrc.cc/v2/embed/movie/{tmdb_id}).

    Args:
        url: Исходный URL видео или ID фильма (tmdb_id/imdb_id).
        provider: Имя провайдера (youtube, vk, rutube, seasonvar, hdrezka, kinogo, direct, vidsrc).
    """
    try:
        embed_url = url

        # YouTube: преобразование watch-ссылки в embed
        if provider == 'youtube' and 'watch?v=' in url:
            video_id = url.split('watch?v=')[-1].split('&')[0]
            embed_url = f'https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0'

        # VidSrc: построение по tmdb_id
        elif provider == 'vidsrc' and url.isdigit():
            embed_url = f'https://vidsrc.cc/v2/embed/movie/{url}'

        # RuTube
        elif provider == 'rutube' and 'rutube.ru' in url:
            import re
            match = re.search(r'video/([a-f0-9]{32})', url)
            if match:
                embed_url = f'https://rutube.ru/play/embed/{match.group(1)}?autoplay=1'

        result = {
            'player_url': url,
            'provider': provider,
            'embed_url': embed_url,
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f'[langchain_tools] Ошибка при формировании URL плеера: {e}')
        return json.dumps({}, ensure_ascii=False)


@tool
async def add_torrent_download(url: str, source: str, title: str) -> str:
    """Добавляет торрент на скачивание в qBittorrent через API сервера.

    Args:
        url: URL или магнет-ссылка торрента для скачивания.
        source: Источник (rutracker, nnmclub).
        title: Читаемое название торрента.
    """
    try:
        api_url = 'http://localhost:3000/api/torrents/download'
        payload = {
            'url': url,
            'source': source,
            'title': title,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 200:
                    return f'✅ Торрент "{title}" успешно добавлен на скачивание'
                error_text = await response.text()
                return f'❌ Ошибка добавления торрента (HTTP {response.status}): {error_text}'
    except Exception as e:
        logger.error(f'[langchain_tools] Ошибка при добавлении торрента: {e}')
        return f'❌ Ошибка соединения с API: {e}'
