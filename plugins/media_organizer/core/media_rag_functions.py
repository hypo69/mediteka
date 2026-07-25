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
    """Получение API ключа Gemini из переменных окружения или менеджера ключей.

    Returns:
        str: API ключ или пустая строка если не найден.

    Examples:
        >>> key = _get_gemini_api_key()
    """
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
    """Семантический поиск фильмов и сериалов по описанию.

    Использует RAG-индекс для поиска по смыслу, а не только по названию.
    Подходит для запросов типа "фильм про космос", "сериал похожий на...", etc.

    Args:
        query (str): Поисковый запрос на естественном языке.
        top_k (int): Количество результатов (по умолчанию 5).
        category (str, optional): Фильтр по категории (Боевики, Триллеры, etc).
        media_type (str, optional): Фильтр по типу: 'movie' или 'series'.
        year_from (int, optional): Год от.
        year_to (int, optional): Год до.

    Returns:
        str: JSON-список найденных записей с метаданными и score.

    Examples:
        >>> result = search_media("фильм про космос с Леонардо ДиКаприо", top_k=3)
        >>> result = search_media("сериал про полицию похожий на Кейна", category="Расследования")
    """
    api_key = _get_gemini_api_key()
    if not api_key:
        return json.dumps({'error': 'GEMINI_API_KEY не найден'}, ensure_ascii=False)

    try:
        results_json = rag_search_tool(query, top_k=top_k, api_key=api_key)
        results = json.loads(results_json)

        if isinstance(results, dict) and 'error' in results:
            return results_json

        # Пост-фильтрация если нужна
        if category or media_type or year_from or year_to:
            filtered = []
            for item in results:
                meta = item.get('meta', {})
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
            results = filtered

        # Формируем читаемый ответ
        if not results:
            return json.dumps({
                'message': 'Ничего не найдено по запросу',
                'query': query,
                'results': []
            }, ensure_ascii=False)

        response = {
            'query': query,
            'found': len(results),
            'results': [
                {
                    'title': r['meta'].get('title', r['id'].split('::')[-1] if '::' in r['id'] else r['id']),
                    'type': r['meta'].get('type', ''),
                    'category': r['meta'].get('main_category', ''),
                    'year': r['meta'].get('year', ''),
                    'disk_name': r['meta'].get('disk_name', ''),
                    'score': r['score'],
                }
                for r in results
            ]
        }
        return json.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка поиска: {e}", exc_info=True)
        return json.dumps({'error': str(e)}, ensure_ascii=False)


def get_media_card(disk_name: str, title: str, media_type: str) -> str:
    """Получение полной карточки фильма/сериала из базы.

    Возвращает всю информацию о медиа: описание, актёры, оценки, факты, etc.

    Args:
        disk_name (str): Имя диска (например "ДИСК 1").
        title (str): Название фильма или сериала.
        media_type (str): Тип: 'movie' или 'series'.

    Returns:
        str: JSON с полной карточкой медиа или ошибка.

    Examples:
        >>> card = get_media_card("ДИСК 1", "Титаник", "movie")
        >>> card = get_media_card("ДИСК 3", "Чёрный список", "series")
    """
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
    """Точный поиск медиа по названию (без RAG).

    Ищет точное совпадение в базе. Используй когда знаешь название.

    Args:
        title (str): Название фильма или сериала.
        media_type (str, optional): Фильтр по типу: 'movie' или 'series'.

    Returns:
        str: JSON со списком найденных записей.

    Examples:
        >>> find = find_by_exact_title("Титаник")
        >>> find = find_by_exact_title("Крепкий орешек", "movie")
    """
    try:
        db = MediaDatabase(_DB_FILE)
        all_records = db.export_all()

        results = []
        title_lower = title.lower()
        for record in all_records:
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
                'message': 'Ничего не найдено',
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
    """Получение случайной рекомендации из медиатеки.

    Args:
        category (Optional[str]): Категория (Боевики, Триллеры, etc).
        media_type (Optional[str]): Тип: 'movie' или 'series'.
        mood (Optional[str]): Настроение (для вечера пятницы, для выходных, etc).

    Returns:
        str: JSON со случайной записью или ошибка.

    Examples:
        >>> rec = get_random_media(category="Боевики")
        >>> rec = get_random_media(media_type="series", mood="для вечера с бокалом вина")
    """
    try:
        db = MediaDatabase(_DB_FILE)
        records = db.export_all()

        if not records:
            return json.dumps({'error': 'База медиатеки пуста'}, ensure_ascii=False)

        # Фильтрация
        filtered = records
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
                'error': 'Нет записей по заданным критериям',
                'filters': {'category': category, 'type': media_type, 'mood': mood}
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


import shutil
from datetime import datetime

def rebuild_rag_index(fresh: bool = False) -> str:
    """Перестроение RAG-индекса медиатеки.

    Args:
        fresh (bool): Если True, выполняет бэкап и полное удаление старого индекса.

    Returns:
        str: JSON с результатом переиндексации.
    """
    api_key = _get_gemini_api_key()
    if not api_key:
        return json.dumps({'error': 'GEMINI_API_KEY не найден'}, ensure_ascii=False)

    try:
        if fresh and _RAG_DB.exists():
            # Бэкап
            timestamp = datetime.now().strftime('%m%d-%H%M%S')
            backup_path = _RAG_DB.with_name(f"{_RAG_DB.name}.{timestamp}")
            shutil.copy2(_RAG_DB, backup_path)
            logger.info(f"Создан бэкап RAG-индекса: {backup_path}")
            
            # Удаление
            os.remove(_RAG_DB)
            logger.info(f"Старый RAG-индекс удален: {_RAG_DB}")

        db = MediaDatabase(_DB_FILE)
        records = db.export_all()

        if not records:
            return json.dumps({'error': 'База медиатеки пуста'}, ensure_ascii=False)

        count_before = len(records)

        # Перестраиваем индекс
        rag = build_media_rag(api_key)
        count_after = rag.count()

        return json.dumps({
            'success': True,
            'records_processed': count_before,
            'index_documents': count_after,
            'message': f'RAG-индекс перестроен. Документов в индексе: {count_after}'
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка перестроения индекса: {e}", exc_info=True)
        return json.dumps({'error': str(e)}, ensure_ascii=False)


def get_rag_status() -> str:
    """Получение статуса RAG-индекса.

    Returns:
        str: JSON со статусом индекса и базы.

    Examples:
        >>> status = get_rag_index()
    """
    try:
        db = MediaDatabase(_DB_FILE)
        records = db.export_all()

        api_key = _get_gemini_api_key()
        rag = get_media_rag(api_key) if api_key else None

        # Категории в базе
        categories = {}
        types_count = {'movie': 0, 'series': 0}
        for r in records:
            cat = r.get('main_category', 'Без категории')
            categories[cat] = categories.get(cat, 0) + 1
            t = r.get('type', '')
            if t in types_count:
                types_count[t] += 1

        response = {
            'database': {
                'total_records': len(records),
                'by_type': types_count,
                'by_category': categories,
            },
            'rag_index': {
                'exists': rag is not None,
                'documents': rag.count() if rag else 0,
                'db_path': str(_RAG_DB),
            } if rag else {'exists': False, 'documents': 0}
        }

        return json.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}", exc_info=True)
        return json.dumps({'error': str(e)}, ensure_ascii=False)


# =============================================================================
# Tool Definitions
# =============================================================================

def get_media_tools() -> List[types.Tool]:
    """Получение списка инструментов для Gemini Function Calling.

    Returns:
        List[types.Tool]: Список инструментов для передачи в model.generate_content.

    Examples:
        >>> from google.genai import types
        >>> tools = get_media_tools()
        >>> config = types.GenerateContentConfig(tools=tools)
    """
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name='search_media',
                    description='Семантический поиск фильмов и сериалов по смыслу. Используй для запросов типа "фильм про...", "сериал похожий на...", "что посмотреть про...".',
                    parameters=types.Schema(
                        type='object',
                        properties={
                            'query': types.Schema(
                                type='string',
                                description='Поисковый запрос на естественном языке'
                            ),
                            'top_k': types.Schema(
                                type='integer',
                                description='Максимальное количество результатов',
                                default=5,
                                minimum=1,
                                maximum=20
                            ),
                            'category': types.Schema(
                                type='string',
                                description='Фильтр по категории: Боевики, Триллеры, Военные, Аферы, Приключения, Семейные, Исторические/Костюмированные, Расследования, Деньги/Корпорации, Шпионы, Мюзиклы'
                            ),
                            'media_type': types.Schema(
                                type='string',
                                description='Фильтр по типу медиа',
                                enum=['movie', 'series']
                            ),
                            'year_from': types.Schema(
                                type='integer',
                                description='Год от (включительно)'
                            ),
                            'year_to': types.Schema(
                                type='integer',
                                description='Год до (включительно)'
                            ),
                        },
                        required=['query'],
                    ),
                ),
                types.FunctionDeclaration(
                    name='get_media_card',
                    description='Получение полной карточки фильма или сериала. Используй когда пользователь спрашивает конкретный фильм/сериал и нужна подробная информация.',
                    parameters=types.Schema(
                        type='object',
                        properties={
                            'disk_name': types.Schema(
                                type='string',
                                description='Имя диска где находится медиа (например "ДИСК 1", "HDD 2")'
                            ),
                            'title': types.Schema(
                                type='string',
                                description='Название фильма или сериала'
                            ),
                            'media_type': types.Schema(
                                type='string',
                                description='Тип медиа',
                                enum=['movie', 'series']
                            ),
                        },
                        required=['disk_name', 'title', 'media_type'],
                    ),
                ),
                types.FunctionDeclaration(
                    name='find_by_exact_title',
                    description='Точный поиск медиа по названию. Используй когда пользователь знает точное название фильма или хочет проверить есть ли он в базе.',
                    parameters=types.Schema(
                        type='object',
                        properties={
                            'title': types.Schema(
                                type='string',
                                description='Название для поиска'
                            ),
                            'media_type': types.Schema(
                                type='string',
                                description='Фильтр по типу: movie или series',
                                enum=['movie', 'series']
                            ),
                        },
                        required=['title'],
                    ),
                ),
                types.FunctionDeclaration(
                    name='get_random_media',
                    description='Получение случайной рекомендации. Используй когда пользователь хочет что-то посмотреть, но не знает что именно.',
                    parameters=types.Schema(
                        type='object',
                        properties={
                            'category': types.Schema(
                                type='string',
                                description='Категория: Боевики, Триллеры, Военные, Аферы, Приключения, Семейные, Исторические/Костюмированные, Расследования, Деньги/Корпорации, Шпионы, Мюзиклы'
                            ),
                            'media_type': types.Schema(
                                type='string',
                                description='Фильтр по типу: movie или series',
                                enum=['movie', 'series']
                            ),
                            'mood': types.Schema(
                                type='string',
                                description='Желаемое настроение: для вечера пятницы, для выходных, для романтического вечера, чтобы поржать, etc.'
                            ),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name='rebuild_rag_index',
                    description='Перестроение RAG-индекса. Используй только если индекс повреждён или добавлены новые данные в базу. Это долгая операция!',
                    parameters=types.Schema(
                        type='object',
                        properties={},
                    ),
                ),
                types.FunctionDeclaration(
                    name='get_rag_status',
                    description='Получение статуса RAG-индекса и базы медиатеки. Используй для диагностики.',
                    parameters=types.Schema(
                        type='object',
                        properties={},
                    ),
                ),
            ]
        ),
    ]


def dispatch_media_tool_call(name: str, args: Dict[str, Any]) -> str:
    """Диспетчер вызовов медиа-инструментов.

    Args:
        name (str): Имя вызванной функции.
        args (Dict[str, Any]): Аргументы вызова.

    Returns:
        str: Результат выполнения в JSON-формате.

    Examples:
        >>> result = dispatch_media_tool_call('search_media', {'query': 'фильм про космос'})
    """
    functions = {
        'search_media': search_media,
        'get_media_card': get_media_card,
        'find_by_exact_title': find_by_exact_title,
        'get_random_media': get_random_media,
        'rebuild_rag_index': rebuild_rag_index,
        'get_rag_status': get_rag_status,
    }

    func = functions.get(name)
    if not func:
        return json.dumps({'error': f'Неизвестная функция: {name}'}, ensure_ascii=False)

    try:
        result = func(**args)
        return result
    except Exception as e:
        logger.error(f"Ошибка вызова {name}: {e}", exc_info=True)
        return json.dumps({'error': str(e)}, ensure_ascii=False)


# =============================================================================
# Агентная функция для использования с ask_with_tools
# =============================================================================

async def ask_with_media_rag(
    question: str,
    ai_model: 'GoogleGenerativeAI',
) -> str:
    """Запрос к модели с использованием медиа-RAG функций.

    Args:
        question (str): Вопрос пользователя о фильмах/сериалах.
        ai_model (GoogleGenerativeAI): Экземпляр модели.

    Returns:
        str: Ответ модели с возможными вызовами функций.

    Examples:
        >>> from plugins.media_organizer.media_rag_functions import ask_with_media_rag
        >>> answer = await ask_with_media_rag("Порекомендуй фильм на вечер", ai)
    """
    from google.genai import types

    tools = get_media_tools()
    return await ai_model.ask_with_tools(question, tools, dispatch_media_tool_call)


# =============================================================================
# Main / Test
# =============================================================================

if __name__ == '__main__':
    # Тестирование функций
    import os
    os.chdir(Path(__file__).parent)

    print("=== Тест RAG Functions ===\n")

    # Статус
    print("1. Статус RAG:")
    print(get_rag_status())

    # Поиск
    print("\n2. Поиск 'фильм про космос':")
    print(search_media("фильм про космос с Леонардо ДиКаприо"))

    # Рекомендация
    print("\n3. Случайная рекомендация (Боевики):")
    print(get_random_media(category="Боевики"))

    print("\n=== Готово ===")