#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Аудит медиатеки (Файлы vs БД)
# =============================================================================
# Описание:
#   Рекурсивно сканирует указанные директории и сверяет найденные файлы
#   с записями в базе данных. Выявляет отсутствующие записи в БД или
#   отсутствующие файлы на диске. Поддерживает структуру сериалов.
#
# File: audit_media.py
# Project: gemini-simplechat
# =============================================================================

import sys
import argparse
from pathlib import Path

# Добавляем корень проекта в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from src.logger import logger
from plugins.media_organizer.core.database import MediaDatabase

MEDIA_DB = Path(__file__).parent / 'plugins' / 'media_organizer' / 'data' / 'media.db'
MEDIA_EXT = {".mkv", ".mp4", ".avi", ".m4v", ".mov", ".ts", ".wmv"}

def main():
    parser = argparse.ArgumentParser(description='Аудит медиатеки: Файлы vs БД')
    parser.add_argument('paths', nargs='+', help='Пути для сканирования')
    args = parser.parse_args()

    logger.info("=== Аудит медиатеки ===")
    db = MediaDatabase(MEDIA_DB)
    
    # 1. Загрузка всех путей из БД
    all_records = db.export_all()
    db_paths = {Path(r['path']).resolve(): r for r in all_records if r.get('path')}
    
    # 2. Сканирование диска
    disk_files = set()
    logger.info(f"Сканирование директорий: {args.paths}")
    
    for p_str in args.paths:
        root = Path(p_str)
        if not root.exists():
            logger.warning(f"❌ Путь не найден: {root}")
            continue
            
        for path in root.rglob('*'):
            if path.is_file() and path.suffix.lower() in MEDIA_EXT:
                disk_files.add(path.resolve())

    # 3. Анализ
    in_disk_not_in_db = disk_files - db_paths.keys()
    in_db_not_in_disk = db_paths.keys() - disk_files

    logger.info(f"\n=== Результаты аудита ===")
    logger.info(f"Всего файлов на диске: {len(disk_files)}")
    logger.info(f"Всего записей в БД: {len(db_paths)}")
    
    if in_disk_not_in_db:
        logger.warning(f"\n⚠️  Файлы на диске, отсутствующие в БД ({len(in_disk_not_in_db)}):")
        for p in sorted(in_disk_not_in_db):
            logger.info(f"  - {p}")
            
    if in_db_not_in_disk:
        logger.error(f"\n❌ Записи в БД, файлы которых отсутствуют ({len(in_db_not_in_disk)}):")
        for p in sorted(in_db_not_in_disk):
            logger.info(f"  - {p}")
            
    if not in_disk_not_in_db and not in_db_not_in_disk:
        logger.success("\n✅ Медиатека в полном соответствии!")

    return 0

if __name__ == '__main__':
    sys.exit(main())
