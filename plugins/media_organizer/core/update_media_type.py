#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Служебный скрипт для обновления media_type в БД."""

import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'media.db'


def determine_media_type(path: str) -> str:
    """Определяет media_type по пути."""
    path_lower = path.lower()
    
    # Фильмы в папке "фильмы"
    if '\\фильмы\\' in path_lower or '/фильмы/' in path_lower:
        return 'movie'
    
    # Сериалы в папке "сериалы"
    if '\\сериалы\\' in path_lower or '/сериалы/' in path_lower:
        # Проверяем, это сезон или эпизод
        season_match = re.search(r'season[\s._-]*(\d+)', path_lower, re.IGNORECASE)
        if season_match:
            # Это сезон
            return 'season'
        
        # Проверяем на эпизод (файл внутри сезона)
        ep_match = re.search(r'[^\\]+[\s._-]*(?:episode|серия)[\s._-]*\d+', path_lower, re.IGNORECASE)
        if ep_match:
            return 'episode'
        
        # Если это директория сериала (без Season), то series
        return 'series'
    
    return 'unknown'


def update_media_type():
    """Обновляет media_type для всех записей в БД."""
    print("🔧 Обновление media_type в БД...")
    print(f"  База данных: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        # Получаем все записи с NULL media_type
        rows = conn.execute(
            "SELECT id, path, media_type FROM media WHERE media_type IS NULL"
        ).fetchall()

        print(f"Найдено {len(rows)} записей с NULL media_type")

        updated = 0
        for row_id, path, current_type in rows:
            new_type = determine_media_type(path)
            if new_type != 'unknown':
                conn.execute(
                    "UPDATE media SET media_type = ? WHERE id = ?",
                    (new_type, row_id)
                )
                updated += 1

        conn.commit()

    print(f"✅ Обновлено {updated} записей!")


if __name__ == '__main__':
    update_media_type()
