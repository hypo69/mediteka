# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Модуль дополнения данных медиатеки
# =============================================================================
# Описание:
#   Общий модуль для выполнения полного сканирования и классификации контента
#   для заданного диска. Используется для устранения расхождений между
#   файловой системой и базой данных.
#
# File: data_completer.py
# Project: gemini-simplechat
# Package: plugins.media_organizer.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
from pathlib import Path
from typing import Optional

from src.ai import GoogleGenerativeAI
from src.logger import logger
from plugins.media_organizer.core import MEDIA_DB, SYSTEM_INSTRUCTION_RESEARCH, SYSTEM_INSTRUCTION_CHAT, SYSTEM_INSTRUCTION_TTS
from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core.media_scanner import MediaScanner, TMDBClient
from plugins.media_organizer.core.genre_classifier import PersistentGenreClassifier

async def complete_disk_data(disk_name: str, tmdb_key: str) -> bool:
    """Выполняет полное сканирование и классификацию контента для диска.

    Args:
        disk_name (str): Имя диска.
        tmdb_key (str): Ключ API TMDB.

    Returns:
        bool: True если успех, False если ошибка.
    """
    from plugins.media_organizer.core.media_tracker import load_media_paths, _filter_paths_by_disk

    media_paths = load_media_paths()
    disk_paths = _filter_paths_by_disk(media_paths, disk_name)
    if not disk_paths:
        logger.error(f"Не найдены пути для диска '{disk_name}'")
        return False

    print(f"=== Запуск принудительного дополнения данных для: {disk_name} ===")
    
    ai_research = GoogleGenerativeAI(system_instruction=SYSTEM_INSTRUCTION_RESEARCH)
    ai_chat = GoogleGenerativeAI(system_instruction=SYSTEM_INSTRUCTION_CHAT)
    ai_tts = GoogleGenerativeAI(system_instruction=SYSTEM_INSTRUCTION_TTS)
    db = MediaDatabase(MEDIA_DB)
    scanner = MediaScanner()

    # 1. Сканирование
    print("1/3: Сканирование файловой структуры...")
    scanner.scan_paths(disk_paths)
    
    # ФИЛЬТРАЦИЯ: Оставляем только те, которых нет в БД
    existing_records = db.export_disk(disk_name)
    existing_paths = {Path(r['path']).resolve() for r in existing_records if r.get('path')}
    
    # Фильтруем фильмы
    new_movies = [m for m in scanner.movies if Path(m['path']).resolve() not in existing_paths]
    
    # Фильтруем сериалы (сложнее, так как это папки)
    new_series = {}
    for title, data in scanner.series.items():
        if Path(data['path']).resolve() not in existing_paths:
            new_series[title] = data
            
    print(f"   Найдено новых: фильмов — {len(new_movies)}, сериалов — {len(new_series)}")
    
    # 2. Классификация и сохранение (только новых)
    print("2/3: Классификация и сохранение в БД новых записей...")
    tmdb = TMDBClient(tmdb_key)
    classifier = PersistentGenreClassifier(tmdb, ai_research, ai_chat, ai_tts, db, disk_name)
    await classifier.classify_media(new_movies, new_series)
    
    # 3. Глубокое сканирование сериалов
    print("3/3: Глубокое сканирование эпизодов...")
    
    saved_seasons = 0
    saved_episodes = 0
    # Используем отфильтрованные новые сериалы
    for series_title, series_data in new_series.items():
        series_record = db.find_any_disk(series_title)
        if not series_record:
            continue
        series_id = series_record.get('id', 0)
        seasons = series_data.get('seasons', {})
        for season_num, season_data in seasons.items():
            season_record = {
                'path': season_data.get('path', ''),
                'title': f"{series_title} (сезон {season_num})",
                'type': 'season',
                'parent_id': series_id,
            }
            db.save_media(disk_name, 'season', season_record)
            saved_seasons += 1
            season_id = db.get_media(disk_name, season_record['title']).get('id', 0)
            
            for ep in season_data.get('episodes', []):
                ep_record = {
                    'path': ep.get('path') or ep.get('filepath', ''),
                    'filename': ep.get('filename', ''),
                    'title': f"{series_title} S{season_num:02d}E{ep.get('episode', 0):02d} {ep.get('filename', '')}",
                    'type': 'episode',
                    'parent_id': season_id,
                    'size_mb': round(ep.get('size', 0) / 1024 / 1024, 2),
                    'year': series_record.get('year', 0),
                    'country': series_record.get('country', ''),
                    'main_category': series_record.get('main_category', ''),
                }
                db.save_media(disk_name, 'episode', ep_record)
                saved_episodes += 1
    print(f"   Сохранено сезонов: {saved_seasons}, эпизодов: {saved_episodes}")

    print("=== Процесс завершен ===")
    return True
