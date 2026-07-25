#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Запуск сопоставления медиа-файлов с торрентами
# =============================================================================
# Описание:
#   Скрипт для запуска интеллектуального сопоставления медиа-файлов на диске
#   с торрентами в qBittorrent через AI-модель.
#
# File: assign_torrents_ids.py
# Project: gemini-simplechat
# Package: plugins.media_organizer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Добавляем корень проекта в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from src.logger import logger

from plugins.media_organizer.core import MEDIA_DB
from plugins.media_organizer.core import SYSTEM_INSTRUCTION
from plugins.media_organizer.core.assign_torrents_ids import assign_torrent_ids
from plugins.media_organizer.core.media_tracker import load_media_paths, _filter_paths_by_disk

from src.ai import GoogleGenerativeAI


def main():
    parser = argparse.ArgumentParser(
        description='Сопоставление медиа-файлов с торрентами через AI'
    )
    parser.add_argument(
        '--disk', '-d',
        type=str,
        help='Имя диска для обработки (например: ДИСК 1). Если не указан - все диски'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Подробный вывод'
    )
    parser.add_argument(
        '--dry-run', '--dry',
        action='store_true',
        help='Не сохранять изменения в базу (только отображение)'
    )
    
    args = parser.parse_args()
    
    # Загрузка путей к дискам
    media_paths = load_media_paths()
    
    if not media_paths:
        logger.warning("❌ Не заданы пути для сканирования. Заполните plugins/media_organizer/config/media_paths.txt")
        return 1
    
    if args.disk:
        # Фильтруем только указанный диск
        disk_paths = _filter_paths_by_disk(media_paths, args.disk)
        if not disk_paths:
            logger.warning(f"❌ Не найден путь для диска '{args.disk}'")
            return 1
    else:
        disk_paths = media_paths
    
    logger.info("=== Сопоставление медиа-файлов с торрентами ===")
    logger.info(f"Путь к базе данных: {MEDIA_DB}")
    logger.info("Диски для обработки:")
    for p in disk_paths:
        logger.info(f"  - {p}")
    logger.info("")
    
    # Подготовка AI-модели
    logger.info("Подготовка AI-модели...")
    try:
        from src.secrets.api_key_state import load_api_keys
        _, key_names, _ = load_api_keys()
        
        if not key_names:
            logger.warning("❌ Нет доступных активных ключей.")
            return 1
        
        ai = GoogleGenerativeAI(api_key_names=[key_names[0]], system_instruction=SYSTEM_INSTRUCTION)
        logger.success("✅ AI-модель подготовлена")
    except Exception as e:
        logger.error(f"❌ Ошибка подготовки AI-модели: {e}")
        return 1
    
    # Запуск сопоставления
    logger.info("")
    results = asyncio.run(assign_torrent_ids(ai, disk_paths, MEDIA_DB))
    
    # Вывод результатов
    logger.info("")
    logger.info("=== Результаты ===")
    if 'error' in results:
        logger.error(f"❌ {results['error']}")
        return 1
    
    logger.info(f"Совпадений: {results.get('matched', 0)}")
    logger.info(f"Перенаправлений: {results.get('redirected', 0)}")
    logger.info(f"Запущено загрузок: {results.get('started_downloads', 0)}")
    
    if results.get('errors'):
        logger.warning(f"Ошибок: {len(results['errors'])}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
