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


def _record_to_text(record: dict, seasons_data: list = []) -> str:
    """Сериализация записи медиа в текст для векторизации.

    Args:
        record (dict): Запись из таблицы media с десериализованными полями.
        seasons_data (list): Список связанных записей сезонов и эпизодов для сериала.

    Returns:
        str: Текстовое представление записи.

    Examples:
        >>> text = _record_to_text({'title': 'Титаник', 'plot': '...'})
    """
    media_type = record.get('media_type', '')
    type_label = "Сериал" if media_type == 'series' else "Фильм"

    parts = [
        record.get('title', ''),
        record.get('title_ru', ''),
        record.get('title_orig', ''),
        f"Тип: {type_label}",
        f"Год: {record.get('year', '')}",
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

    if media_type == 'series':
        num_seasons = record.get('num_of_seasons', 0)
        if num_seasons:
            parts.append(f"Количество сезонов: {num_seasons}")

        if seasons_data:
            seasons_parts = []
            for s in seasons_data:
                s_title = s.get('title', '')
                s_plot = s.get('plot', '')
                s_verdict = s.get('final_verdict', '')
                episodes = s.get('episodes', [])

                s_text = f"[{s_title}]: {s_plot} {s_verdict}".strip()
                if episodes:
                    ep_texts = [f"{ep.get('title', '')}: {ep.get('plot', '')}".strip() for ep in episodes if ep.get('plot')]
                    if ep_texts:
                        s_text += " Эпизоды: " + "; ".join(ep_texts)
                if s_text:
                    seasons_parts.append(s_text)
            if seasons_parts:
                parts.append("Содержание сезонов: " + " | ".join(seasons_parts))

    review = record.get('review') or {}
    if review:
        parts.append(f"Мнение: {review.get('liked', '')} {review.get('disliked', '')}")
    return ' '.join(p for p in parts if p).strip()


def build_media_rag(api_key: str) -> GeminiRAG:
    """Построение RAG-индекса из всех верхнеуровневых записей медиатеки.

    Индексирует фильмы и сериалы. Отдельные записи сезонов и эпизодов не создают
    изолированных документов RAG, а агрегируются в единый документ своего сериала.
    Существующий индекс очищается и перестраивается полностью.

    Args:
        api_key (str): Ключ Gemini API для векторизации.

    Returns:
        GeminiRAG: Готовый к поиску индекс.

    Examples:
        >>> rag = build_media_rag(os.getenv('GEMINI_API_KEY'))
        >>> results = rag.search('фильм про космос')
    """
    db = MediaDatabase(MEDIA_DB)
    records = db.export_all()

    top_records = []
    seasons_by_parent = {}
    episodes_by_season = {}

    for r in records:
        m_type = r.get('media_type', '')
        parent_id = r.get('parent_id') or 0
        r_id = r.get('id') or 0

        if m_type == 'episode':
            if parent_id:
                episodes_by_season.setdefault(parent_id, []).append(r)
        elif m_type == 'season':
            if parent_id:
                seasons_by_parent.setdefault(parent_id, []).append(r)
        elif m_type in ('movie', 'series') or not parent_id:
            top_records.append(r)

    rag = GeminiRAG(api_key=api_key, db_path=MEDIA_RAG_DB)
    rag.clear()

    docs = []
    for r in top_records:
        title = r.get('title', '')
        if not title:
            continue

        m_type = r.get('media_type') or ('series' if r.get('num_of_seasons', 0) > 0 else 'movie')
        r_id = r.get('id') or 0

        seasons_data = []
        if m_type == 'series' and r_id and r_id in seasons_by_parent:
            for s in seasons_by_parent[r_id]:
                s_id = s.get('id') or 0
                s_copy = dict(s)
                if s_id and s_id in episodes_by_season:
                    s_copy['episodes'] = episodes_by_season[s_id]
                seasons_data.append(s_copy)

        disk_name = r.get('disk_name', '')
        text = _record_to_text(r, seasons_data=seasons_data)

        docs.append({
            'id': f"{disk_name}::{m_type}::{title}",
            'text': text,
            'meta': {
                'title': title,
                'title_ru': r.get('title_ru', ''),
                'title_orig': r.get('title_orig', ''),
                'media_type': m_type,
                'disk_name': disk_name,
                'main_category': r.get('main_category', ''),
                'year': r.get('year', 0),
                'num_of_seasons': r.get('num_of_seasons', 0),
                'path': r.get('path', ''),
            },
        })

    added = rag.add_documents(docs)
    _cached_media_rag[str(MEDIA_RAG_DB)] = rag
    return rag


_cached_media_rag: dict[str, GeminiRAG] = {}


def get_media_rag(api_key: str = '') -> GeminiRAG:
    """Получение существующего RAG-индекса (синглтон/кэш для быстрого доступа).

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
    global _cached_media_rag
    db_key = str(MEDIA_RAG_DB)
    if db_key in _cached_media_rag:
        inst = _cached_media_rag[db_key]
        if api_key:
            inst.api_key = api_key
        return inst
    inst = GeminiRAG(api_key=api_key, db_path=MEDIA_RAG_DB)
    _cached_media_rag[db_key] = inst
    return inst


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
        return json.dumps({
            'message': 'RAG-индекс пуст. База данных медиатеки ещё не проиндексирована. Чтобы осуществлять семантический поиск, необходимо запустить перестроение индекса (команда rebuild_rag).',
            'results': []
        }, ensure_ascii=False)
    results = rag.search(query, top_k=top_k, threshold=0.60)
    return json.dumps(results, ensure_ascii=False, indent=2)
