# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Gemini Functions для работы с RAG медиатеки
# =============================================================================
# Описание:
#   Инструменты function calling для поиска и получения информации о медиа
#   через семантический RAG-индекс на базе media.db
#
# File: media_rag_functions.py
# Project: gemini-simplechat
# Package: plugins.media_organizer.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.genai import types

from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core.media_rag import (
    build_media_rag,
    get_media_rag,
    rag_search_tool,
)
from src.logger import logger

_DB_FILE = Path(__file__).parent.parent / 'data' / 'media.db'
_RAG_DB = Path(__file__).parent.parent / 'data' / 'media_rag.db'


def _get_gemini_api_key() -> str:
    """Получение API ключа Gemini из переменных окружения или менеджера ключей."""
    from dotenv import load_dotenv
    try:
        from header import __root__
        load_dotenv(__root__ / '.env')
    except Exception:
        load_dotenv()

    for key_name in ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GEMINI_API_KEY_1']:
        key = os.getenv(key_name, '').strip()
        if key:
            return key

    try:
        from src.secrets.api_key_state import load_api_keys
        api_keys, _, _ = load_api_keys()
        if api_keys:
            return api_keys[0]
    except Exception as e:
        logger.error(f"Ошибка при получении ключа через load_api_keys: {e}")

    return ''

def _get_active_paths() -> List[str]:
    """Получает список актуальных путей дисков из переменных окружения."""
    connected_drives_str = os.environ.get('CONNECTED_DRIVES', '')
    return [d.strip().rstrip('\\') for d in connected_drives_str.split(',') if d.strip()]

# =============================================================================
# Инструменты Function Calling
# =============================================================================

def search_media(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None,
    media_type: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> str:
    """Семантический поиск фильмов и сериалов по описанию с учетом подключенных дисков."""
    api_key = _get_gemini_api_key()
    if not api_key:
        return json.dumps({'error': 'GEMINI_API_KEY не найден'}, ensure_ascii=False)

    try:
        results_json = rag_search_tool(query, top_k=top_k, api_key=api_key)
        results = json.loads(results_json)

        if isinstance(results, dict) and 'error' in results:
            return results_json

        # Получаем актуальные диски
        active_paths = _get_active_paths()

        # Пост-фильтрация по подключенным дискам и критериям
        filtered = []
        for item in results:
            meta = item.get('meta', {})
            # Фильтр по дискам
            path = meta.get('path', '')
            if path and not any(path.upper().startswith(p.upper()) for p in active_paths):
                continue

            if category and meta.get('main_category') != category:
                continue
            if media_type and meta.get('type') != media_type:
                continue
            year = meta.get('year', 0)
            if year_from and year < year_from:
                continue
            if year_to and year > year_to:
                continue
            filtered.append(item)
        
        # Формируем читаемый ответ
        if not filtered:
            return json.dumps({
                'message': 'Ничего не найдено по запросу на подключенных дисках',
                'query': query,
                'results': []
            }, ensure_ascii=False)

        response = {
            'query': query,
            'found': len(filtered),
            'results': [
                {
                    'title': r['meta'].get('title', r['id'].split('::')[-1] if '::' in r['id'] else r['id']),
                    'type': r['meta'].get('type', ''),
                    'category': r['meta'].get('main_category', ''),
                    'year': r['meta'].get('year', ''),
                    'disk_name': r['meta'].get('disk_name', ''),
                    'score': r['score'],
                }
                for r in filtered
            ]
        }
        return json.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка поиска: {e}", exc_info=True)
        return json.dumps({'error': str(e)}, ensure_ascii=False)


def get_media_card(disk_name: str, title: str, media_type: str) -> str:
    """Получение полной карточки фильма/сериала из базы."""
    try:
        db = MediaDatabase(_DB_FILE)
        record = db.get_media(disk_name, title, media_type)

        if not record:
            return json.dumps({
                'error': 'Запись не найдена',
                'disk_name': disk_name,
                'title': title,
                'type': media_type
            }, ensure_ascii=False)

        # Форматируем для удобного чтения
        response = {
            'title': record.get('title', ''),
            'title_ru': record.get('title_ru', ''),
            'title_orig': record.get('title_orig', ''),
            'type': record.get('type', ''),
            'year': record.get('year', ''),
            'main_category': record.get('main_category', ''),
            'country': record.get('country', ''),
            'genres': record.get('genres', []),
            'directors': record.get('directors', []),
            'cast': record.get('cast', []),
            'plot': record.get('plot', ''),
            'atmosphere': record.get('atmosphere', ''),
            'why_watch': record.get('why_watch', ''),
            'mood': record.get('mood', ''),
            'rating': record.get('rating', {}),
            'quote': record.get('quote', ''),
            'facts': record.get('facts', []),
            'similar': record.get('similar', []),
            'review': record.get('review', {}),
        }

        if media_type == 'series':
            response['num_of_seasons'] = record.get('num_of_seasons', '')
            response['num_episodes_per_season'] = record.get('num_episodes_per_season', [])
            response['status'] = record.get('status', '')

        return json.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка получения карточки: {e}", exc_info=True)
        return json.dumps({'error': str(e)}, ensure_ascii=False)


def find_by_exact_title(title: str, media_type: Optional[str] = '') -> str:
    """Точный поиск медиа по названию (без RAG) с учетом подключенных дисков."""
    try:
        db = MediaDatabase(_DB_FILE)
        all_records = db.export_all()

        # Получаем актуальные диски
        active_paths = _get_active_paths()

        results = []
        title_lower = title.lower()
        for record in all_records:
            # Фильтр по подключенным дискам
            path = record.get('path', '')
            if path and not any(path.upper().startswith(p.upper()) for p in active_paths):
                continue

            record_title = record.get('title', '').lower()
            record_title_ru = record.get('title_ru', '').lower() if record.get('title_ru') else ''
            record_title_orig = record.get('title_orig', '').lower() if record.get('title_orig') else ''

            # Проверяем совпадение в любом из названий
            match = (
                title_lower in record_title or
                title_lower in record_title_ru or
                title_lower in record_title_orig or
                record_title.startswith(title_lower) or
                record_title_ru.startswith(title_lower)
            )

            if match:
                if media_type and record.get('type') != media_type:
                    continue
                results.append({
                    'title': record.get('title', ''),
                    'type': record.get('type', ''),
                    'year': record.get('year', ''),
                    'main_category': record.get('main_category', ''),
                    'disk_name': record.get('disk_name', ''),
                })

        if not results:
            return json.dumps({
                'message': 'Ничего не найдено на подключенных дисках',
                'query': title,
                'type_filter': media_type
            }, ensure_ascii=False)

        return json.dumps({
            'query': title,
            'found': len(results),
            'results': results
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка поиска: {e}", exc_info=True)
        return json.dumps({'error': str(e)}, ensure_ascii=False)


def get_random_media(
    category: Optional[str] = '',
    media_type: Optional[str] = '',
    mood: Optional[str] = '',
) -> str:
    """Получение случайной рекомендации из медиатеки с учетом подключенных дисков."""
    try:
        db = MediaDatabase(_DB_FILE)
        records = db.export_all()

        if not records:
            return json.dumps({'error': 'База медиатеки пуста'}, ensure_ascii=False)

        # Получаем актуальные диски из памяти (переменная окружения)
        active_paths = _get_active_paths()
        
        # Фильтрация по наличию пути на подключенном диске
        filtered = [
            r for r in records 
            if any(r.get('path', '').upper().startswith(path.upper()) for path in active_paths)
        ]
        
        if category:
            filtered = [r for r in filtered if r.get('main_category') == category]
        if media_type:
            filtered = [r for r in filtered if r.get('type') == media_type]
        if mood:
            # Ищем по mood или why_watch
            filtered = [
                r for r in filtered
                if mood.lower() in (r.get('mood', '') or '').lower() or
                   mood.lower() in (r.get('why_watch', '') or '').lower()
            ]

        if not filtered:
            return json.dumps({
                'error': 'Нет записей по заданным критериям на подключенных дисках',
                'filters': {'category': category, 'type': media_type, 'mood': mood},
                'active_drives': active_paths
            }, ensure_ascii=False)

        # Случайный выбор
        record = random.choice(filtered)

        return json.dumps({
            'suggestion': 'Случайный выбор из медиатеки',
            'title': record.get('title', ''),
            'type': record.get('type', ''),
            'year': record.get('year', ''),
            'main_category': record.get('main_category', ''),
            'plot': record.get('plot', '')[:200] + '...' if record.get('plot') else '',
            'why_watch': record.get('why_watch', ''),
            'rating': record.get('rating', {}),
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка получения рекомендации: {e}", exc_info=True)
        return json.dumps({'error': str(e)}, ensure_ascii=False)

# [.... ОСТАЛЬНЫЕ ФУНКЦИИ БЕЗ ИЗМЕНЕНИЙ ....]
