# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: RAG-индексация медиатеки
# =============================================================================
# Описание:
#   Построение RAG-индекса из таблицы media SQLite.
#   Каждая запись сериализуется в текстовый документ для векторизации.
#   Предоставление инструмента семантического поиска для плагина.
#
# File: media_rag.py
# Project: gemini-simplechat
# Package: plugins.media_organizer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
from pathlib import Path

from src.ai.gemini.rag import GeminiRAG
from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core import MEDIA_DB, MEDIA_RAG_DB


def _record_to_text(record: dict) -> str:
    """Сериализация записи медиа в текст для векторизации.

    Args:
        record (dict): Запись из таблицы media с десериализованными полями.

    Returns:
        str: Текстовое представление записи.

    Examples:
        >>> text = _record_to_text({'title': 'Титаник', 'plot': '...', ...})
    """
    parts = [
        record.get('title', ''),
        record.get('title_ru', ''),
        record.get('title_orig', ''),
        f"Год: {record.get('year', '')}",
        f"Тип: {record.get('type', '')}",
        f"Категория: {record.get('main_category', '')}",
        f"Страна: {record.get('country', '')}",
        f"Жанры: {', '.join(record.get('genres') or [])}",
        f"Режиссёры: {', '.join(record.get('directors') or [])}",
        f"В ролях: {', '.join(record.get('cast') or [])}",
        record.get('plot', ''),
        record.get('atmosphere', ''),
        record.get('why_watch', ''),
        record.get('mood', ''),
        record.get('final_verdict', ''),
        record.get('quote', ''),
        ' '.join(record.get('facts') or []),
        ' '.join(record.get('similar') or []),
    ]
    review = record.get('review') or {}
    if review:
        parts.append(f"Мнение: {review.get('liked', '')} {review.get('disliked', '')}")
    return ' '.join(p for p in parts if p).strip()


def build_media_rag(api_key: str) -> GeminiRAG:
    """Построение RAG-индекса из всех записей медиатеки.

    Индексирует все записи таблицы media. Существующий индекс очищается
    и перестраивается полностью.

    Args:
        api_key (str): Ключ Gemini API для векторизации.

    Returns:
        GeminiRAG: Готовый к поиску индекс.

    Examples:
        >>> rag = build_media_rag(os.getenv('GEMINI_API_KEY'))
        >>> results = rag.search('фильм про войну')
    """
    db = MediaDatabase(MEDIA_DB)
    records = db.export_all()
    rag = GeminiRAG(api_key=api_key, db_path=MEDIA_RAG_DB)
    rag.clear()
    docs = [
        {
            'id': f"{r.get('disk_name', '')}::{r.get('type', '')}::{r.get('title', '')}",
            'text': _record_to_text(r),
            'meta': {
                'title': r.get('title', ''),
                'type': r.get('type', ''),
                'disk_name': r.get('disk_name', ''),
                'main_category': r.get('main_category', ''),
                'year': r.get('year', 0),
            },
        }
        for r in records
        if r.get('title')
    ]
    added = rag.add_documents(docs)
    return rag


def get_media_rag(api_key: str) -> GeminiRAG:
    """Получение существующего RAG-индекса или создание пустого.

    Не перестраивает индекс — использует уже накопленные эмбеддинги.
    Для перестройки используй build_media_rag().

    Args:
        api_key (str): Ключ Gemini API.

    Returns:
        GeminiRAG: Экземпляр индекса.

    Examples:
        >>> rag = get_media_rag(api_key)
        >>> rag.search('детектив про маньяка')
    """
    return GeminiRAG(api_key=api_key, db_path=MEDIA_RAG_DB)


def rag_search_tool(query: str, top_k: int = 5, api_key: str = '') -> str:
    """Семантический поиск по медиатеке через RAG-индекс.

    Args:
        query (str): Поисковый запрос на естественном языке.
        top_k (int): Количество результатов.
        api_key (str): Ключ Gemini API.

    Returns:
        str: JSON-строка со списком найденных записей и их score.

    Examples:
        >>> result = rag_search_tool('романтика на корабле', top_k=3, api_key='...')
    """
    rag = get_media_rag(api_key)
    if rag.count() == 0:
        return json.dumps({'error': 'RAG-индекс пуст. Выполни команду: rebuild_rag'}, ensure_ascii=False)
    results = rag.search(query, top_k=top_k, threshold=0.3)
    return json.dumps(results, ensure_ascii=False, indent=2)
