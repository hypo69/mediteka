# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Инициализация и миграция базы данных media.db
# =============================================================================
# Описание:
#   Идемпотентный скрипт: создаёт недостающие таблицы и индексы в media.db.
#   Безопасно запускать несколько раз — уже существующие объекты не трогает.
#   Запускается: python init_media_db.py
#
# File: init_media_db.py
# Project: mediteka
# Package: <root>
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / 'plugins' / 'media_organizer' / 'data' / 'media.db'


def init_db(db_path: Path) -> bool:
    """Создаёт недостающие таблицы и индексы в media.db.

    Args:
        db_path: Путь к файлу базы данных.

    Returns:
        True при успехе.
    """
    with sqlite3.connect(db_path) as conn:
        # ── Таблица media_vector (для RAG-эмбеддингов) ─────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS media_vector (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
            )
        """)

        # ── Таблица search_history ──────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                query         TEXT NOT NULL,
                timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP,
                results_count INTEGER
            )
        """)

        # ── Индексы для быстрого поиска ─────────────────────────────────────────
        conn.execute("CREATE INDEX IF NOT EXISTS idx_media_disk_name ON media(disk_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_media_title     ON media(title)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_media_title_ru  ON media(title_ru)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_media_year      ON media(year)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_media_type      ON media(media_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_media_parent    ON media(parent_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vector_media_id ON media_vector(media_id)")

        conn.commit()
    return True


if __name__ == '__main__':
    print('=' * 60)
    print('  Инициализация media.db')
    print(f'  Путь: {DB_PATH}')
    print('=' * 60)

    if not DB_PATH.exists():
        print(f'  ❌ Файл БД не найден: {DB_PATH}')
        sys.exit(1)

    success = init_db(DB_PATH)

    if success:
        # Выводим итоговое состояние
        with sqlite3.connect(DB_PATH) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            indexes = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
            ).fetchall()
            row_count = conn.execute("SELECT COUNT(*) FROM media").fetchone()[0]

        print(f'  ✅ Готово.')
        print(f'  Таблицы ({len(tables)}): {", ".join(t[0] for t in tables)}')
        print(f'  Индексы ({len(indexes)}): {", ".join(i[0] for i in indexes)}')
        print(f'  Записей в media: {row_count}')
    else:
        print('  ❌ Ошибка инициализации.')
        sys.exit(1)
