#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Аудит диска (Файлы vs БД)
# =============================================================================
# Описание:
#   Скрипт сканирует указанную директорию, сверяет дерево файлов с БД.
#   Новые файлы обрабатываются через MediaOrganizerPlugin для наполнения метаданными.
#
# File: audit_disk.py
# =============================================================================

import sys
import argparse
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Добавляем корень проекта в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from src.logger import logger
from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core.media_organizer import MediaOrganizerPlugin
from src.ai import GoogleGenerativeAI
from plugins.media_organizer.core.media_organizer import INSTRUCTION
from plugins.media_organizer.core.data_completer import complete_disk_data

load_dotenv()

# КОНФИГУРАЦИЯ: Укажите пути к вашим дискам здесь
DISK_MAP = {
    "Диск 2": "E:\\", 
    "Диск 8": "L:\\", 
    "Диск 1": "S:\\", 
    "Диск 5": "Z:\\", 
}

MEDIA_DB = Path(__file__).parent / 'plugins' / 'media_organizer' / 'data' / 'media.db'
MEDIA_EXT = {".mkv", ".mp4", ".avi", ".m4v", ".mov", ".ts", ".wmv"}

async def process_new_files(disk_name, missing_files):
    logger.info(f"\nЗапуск MediaOrganizer для {len(missing_files)} файлов...")
    # Инициализация ИИ
    ai = GoogleGenerativeAI(system_instruction=INSTRUCTION)
    plugin = MediaOrganizerPlugin(ai)
    
    # Обработка файлов
    # Предполагаем, что plugin.handle может принять список путей
    # Адаптируйте под API вашего плагина
    result = await plugin.handle(f'скан медиатеки {disk_name}', disk_paths=[Path(str(p)) for p in missing_files])
    logger.info(result)

async def main():
    parser = argparse.ArgumentParser(description='Аудит файлов на дисках vs БД')
    parser.add_argument('disk_names', nargs='+', help='Имена дисков')
    parser.add_argument('--yes', '-y', action='store_true', help='Автоматически обновить БД')
    parser.add_argument('--auto-fix', action='store_true', help='Автоматически исправить данные при обнаружении расхождений')
    args = parser.parse_args()

    tmdb_key = os.getenv('TMDB_API_KEY', '')
    db = MediaDatabase(MEDIA_DB)
    
    for disk_name in args.disk_names:
        if disk_name not in DISK_MAP:
            logger.warning(f"❌ Диск '{disk_name}' не найден в конфигурации. Пропускаем.")
            continue

        root_path = Path(DISK_MAP[disk_name])
        if not root_path.exists():
            logger.warning(f"❌ Путь '{root_path}' для диска '{disk_name}' не существует.")
            continue

        logger.info(f"\n=== Аудит диска: {disk_name} ({root_path}) ===")
        
        # 1. Загрузка данных из БД
        db_records = db.export_disk(disk_name)
        db_paths = {Path(r['path']).resolve(): r for r in db_records if r.get('path')}
        
        # 2. Сканирование диска
        logger.info("Сканирование диска...")
        disk_files = set()
        for path in root_path.rglob('*'):
            if path.is_file() and path.suffix.lower() in MEDIA_EXT:
                disk_files.add(path.resolve())

        # 3. Сравнение
        missing_in_db = sorted(list(disk_files - db_paths.keys()))
        
        if not missing_in_db:
            logger.success("✅ Все файлы найдены в БД!")
            continue

        logger.warning(f"⚠️  Найдено {len(missing_in_db)} файлов, отсутствующих в БД.")
        
        if args.auto_fix:
            logger.info(f"🔄 Запуск автоматического исправления для '{disk_name}'...")
            await complete_disk_data(disk_name, tmdb_key)
            continue

        if not args.yes:
            choice = input(f"Обработать их через MediaOrganizer? (y/n): ")
            if choice.lower() != 'y':
                logger.info("Пропущено.")
                continue
        
        await process_new_files(disk_name, missing_in_db)
    
    return 0

if __name__ == '__main__':
    asyncio.run(main())
