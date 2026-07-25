# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Запуск сопоставления торрентов с медиа
# =============================================================================
# Описание:
#   Скрипт для запуска процесса интеллектуального сопоставления медиа-файлов
#   из базы данных с торрентами в qBittorrent.
#
# File: run_assign_torrents.py
# Project: gemini-simplechat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from src.ai import GoogleGenerativeAI
from plugins.media_organizer.core.assign_torrents_ids import assign_torrent_ids
from plugins.media_organizer.core import SYSTEM_INSTRUCTION

async def main():
    print("=== Запуск сопоставления медиа с торрентами ===")
    
    # Инициализация модели ИИ
    ai = GoogleGenerativeAI(system_instruction=SYSTEM_INSTRUCTION)
    
    # Запуск процесса
    results = await assign_torrent_ids(ai_model=ai, disk_paths=[])
    
    print("\n=== Результаты сопоставления ===")
    print(f"Сопоставлено: {results['matched']}")
    print(f"Перемещено путей: {results['redirected']}")
    if results['errors']:
        print(f"Ошибок: {len(results['errors'])}")
        for err in results['errors']:
            print(f" - {err}")
    print("=== Процесс завершен ===")

if __name__ == '__main__':
    asyncio.run(main())
