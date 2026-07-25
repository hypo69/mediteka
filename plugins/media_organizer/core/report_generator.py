# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Экспорт медиа-данных в JSON и Markdown
# =============================================================================
# Описание:
#   Функции экспорта данных из БД в форматы JSON и Markdown.
#   Модуль ReportGenerator для форматирования отдельных записей.
#
# File: report_generator.py
# Project: gemini-simplechat
# Package: plugins.media_organizer.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from src.logger import logger

from plugins.media_organizer.core.database import MediaDatabase


def _safe_json_loads(value):
    """Safely parse JSON from string, return empty list/dict for empty/null values."""
    if value is None or (isinstance(value, str) and value.strip() == ''):
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


# =============================================================================
# КОНВЕРТОРЫ: media -> JSON / MD
# =============================================================================

def _split_records(records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Разделение записей на сериалы и фильмы с сортировкой по категории и названию.

    Args:
        records (List[Dict]): Плоский список записей из БД.

    Returns:
        Tuple[List[Dict], List[Dict]]: Отсортированные списки (series, movies).
    """
    key = lambda r: (r.get('main_category', ''), r.get('title', ''))
    series = sorted([r for r in records if r.get('type') == 'series'], key=key)
    movies = sorted([r for r in records if r.get('type') == 'movie'], key=key)
    return series, movies


def export_disk_json(db: MediaDatabase, disk_name: str, output_dir: Path) -> Path:
    """Экспорт всех записей диска из БД в JSON-файл.

    Args:
        db (MediaDatabase): Экземпляр базы данных.
        disk_name (str): Имя диска.
        output_dir (Path): Директория для сохранения файла.

    Returns:
        Path: Путь к сохранённому JSON-файлу.

    Examples:
        >>> path = export_disk_json(db, 'ДИСК 1', OUTPUT_DIR)
    """
    records = db.export_disk(disk_name)
    series, movies = _split_records(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', disk_name).strip()
    out_file = output_dir / f"{safe_name}.json"
    out_file.write_text(
        json.dumps({
            'generated_at': datetime.now().isoformat(),
            'disk_name': disk_name,
            'series': series,
            'movies': movies,
        }, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    return out_file


def _record_to_md(item: Dict, idx: int = 0) -> str:
    """Форматирование одной записи медиа в блок Markdown по пользовательскому шаблону.
    """
    id_val = item.get('id') or idx
    title_ru = item.get('title_ru') or item.get('title', '')
    year = item.get('year', 0)
    country = item.get('country', '')
    genres = ', '.join(item.get('genres') or [])
    
    rating = item.get('rating') or {}
    rating_parts = []
    if rating.get('imdb'):
        rating_parts.append(f"IMDb: {rating['imdb']}")
    if rating.get('tmdb'):
        rating_parts.append(f"TMDB: {rating['tmdb']}")
    if rating.get('кинопоиск'):
        rating_parts.append(f"Кинопоиск: {rating['кинопоиск']}")
    rating_str = ' | '.join(rating_parts)
    
    awards = ', '.join(item.get('awards') or [])
    awards_and_rating = f"{awards}, {rating_str}" if awards and rating_str else (awards or rating_str)
    
    directors = ', '.join(item.get('directors') or [])
    cast = ', '.join(item.get('cast') or [])
    
    plot = item.get('plot', '')
    review = item.get('review') or {}
    liked = review.get('liked', '')
    disliked = review.get('disliked', '')
    why_watch = item.get('why_watch', '')
    
    lines = [
        f"### [{id_val}] {title_ru}",
        f"\t- {year}, {country}, {genres}",
        f"\t- {awards_and_rating}",
        f"\t- Режиссер: {directors}",
        f"\t- Актеры: {cast}",
        f"",
        f"\t{plot}",
        f"",
        f"\tПонравилось: {liked}. Не понравилось: {disliked}." if (liked or disliked) else "",
        f"",
        f"\tПочему стоит смотреть: {why_watch}" if why_watch else ""
    ]
    
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        if line == "":
            if not prev_empty:
                cleaned_lines.append("")
                prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False
            
    return '\n'.join(cleaned_lines)


def export_disk_md(db: MediaDatabase, disk_name: str, output_dir: Path) -> Path:
    """Экспорт всех записей диска из БД в Markdown-файл.

    Args:
        db (MediaDatabase): Экземпляр базы данных.
        disk_name (str): Имя диска.
        output_dir (Path): Директор��я для сохранения файла.

    Returns:
        Path: Путь к сохранённому MD-файлу.

    Examples:
        >>> path = export_disk_md(db, 'ДИСК 1', OUTPUT_DIR)
    """
    records = db.export_disk(disk_name)
    series, movies = _split_records(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', disk_name).strip()
    out_file = output_dir / f"{safe_name}.md"

    blocks = [f"# {disk_name}\n", '## **СЕРИАЛЫ**']
    by_cat: Dict[str, List[Dict]] = {}
    for item in series:
        by_cat.setdefault(item.get('main_category', 'Прочее'), []).append(item)
    for cat, items in sorted(by_cat.items()):
        blocks.append(f'\n### *{cat}*\n')
        for idx, item in enumerate(items, 1):
            blocks.append(_record_to_md(item, idx))

    blocks.append('\n\n---\n\n## **ФИЛЬМЫ**')
    by_cat_m: Dict[str, List[Dict]] = {}
    for item in movies:
        by_cat_m.setdefault(item.get('main_category', 'Прочее'), []).append(item)
    for cat, items in sorted(by_cat_m.items()):
        blocks.append(f'\n### *{cat}*\n')
        for idx, item in enumerate(items, 1):
            blocks.append(_record_to_md(item, idx))

    out_file.write_text('\n\n'.join(blocks), encoding='utf-8')
    return out_file


# =============================================================================
# REPORT GENERATOR
# =============================================================================

class ReportGenerator:
    """Генератор отчётов для отдельных медиа-записей.

    Предоставляет методы для форматирования медиа-данных в Markdown.
    """
