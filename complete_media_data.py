# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Принудительное дополнение данных медиатеки
# =============================================================================
# Описание:
#   Скрипт выполняет полное сканирование и классификацию контента для диска,
#   устраняя расхождения между файловой системой и базой данных.
#
# File: complete_media_data.py
# Project: gemini-simplechat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import sys
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Добавляем корень проекта в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from plugins.media_organizer.core.data_completer import complete_disk_data

load_dotenv()

async def main():
    parser = argparse.ArgumentParser(description='Принудительное заполнение БД медиатеки')
    parser.add_argument('disk_name', help='Имя диска для обработки')
    args = parser.parse_args()

    tmdb_key = os.getenv('TMDB_API_KEY', '')
    if not tmdb_key:
        print("❌ Не найден TMDB_API_KEY в .env")
        return 1

    success = await complete_disk_data(args.disk_name, tmdb_key)
    return 0 if success else 1

if __name__ == '__main__':
    asyncio.run(main())
