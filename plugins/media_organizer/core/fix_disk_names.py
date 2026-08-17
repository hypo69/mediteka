#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Служебный скрипт для исправления имен дисков в БД."""

import sqlite3
from pathlib import Path

# Прямой путь к БД
DB_PATH = Path(__file__).parent.parent / 'data' / 'media.db'


def fix_disk_names():
    """Исправляет имена дисков в БД: 1 -> ДИСК 1, 2 -> ДИСК 2 и т.д."""
    print("🔧 Исправление имен дисков в БД...")
    print(f"  База данных: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        # Получаем все уникальные disk_name
        rows = conn.execute("SELECT DISTINCT disk_name FROM media").fetchall()
        old_names = [r[0] for r in rows]

        print(f"Найдено {len(old_names)} уникальных имен дисков:")
        for name in old_names:
            print(f"  - '{name}'")

        # Формируем новые имена и обновляем
        for old_name in old_names:
            # Если имя - просто число, преобразуем в "ДИСК X"
            if old_name.strip().isdigit():
                new_name = f"ДИСК {old_name.strip()}"
                print(f"  Обновление '{old_name}' -> '{new_name}'")
                conn.execute(
                    "UPDATE media SET disk_name = ? WHERE disk_name = ?",
                    (new_name, old_name)
                )
                conn.execute(
                    "UPDATE duplicates SET disk_name = ? WHERE disk_name = ?",
                    (new_name, old_name)
                )

        conn.commit()

    print("✅ Имена дисков исправлены!")


if __name__ == '__main__':
    fix_disk_names()
