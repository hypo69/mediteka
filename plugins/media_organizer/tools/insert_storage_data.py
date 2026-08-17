# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Занесение данных о хранилищах в БД
# =============================================================================
# Описание:
#   Скрипт выполняет вставку или обновление записей о дисковых носителях в таблицу
#   storage базы данных медиатеки. Запрашивает реальные статистики размеров дисков
#   через shutil.disk_usage и сохраняет общий размер, свободное место и букву диска.
#
# File: insert_storage_data.py
# Project: gemini-simplechat
# Package: MediaOrganizer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sqlite3
import shutil
from pathlib import Path
from src.logger import logger

DB_PATH = Path(r'C:\mediateka\plugins\media_organizer\data\media.db')

def insert_storage_data(data: list[dict[str, str]]) -> bool:
    """
    Вставка данных о хранилищах в таблицу storage с реальными размерами.
    """
    if not DB_PATH.exists():
        logger.error('База данных не найдена.')
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        for entry in data:
            name = f"Диск {entry['number']}"
            
            # Получение данных о диске
            try:
                # Используем строку пути для shutil
                total, used, free = shutil.disk_usage(entry['letter'])
            except Exception:
                total, free = 0, 0
                logger.warning(f"Не удалось получить статистику для {entry['letter']}")

            # Вставляем/обновляем
            cursor.execute("""
                INSERT OR REPLACE INTO storage (storage_name, storage_letter, storage_size, free_size)
                VALUES (?, ?, ?, ?)
            """, (name, entry['letter'], total, free))
            print(f"Обновлено: {name} ({entry['letter']})")
        
        conn.commit()
        print('Данные успешно обновлены.')
        return True
    except Exception as ex:
        logger.error('Ошибка при обновлении данных в таблице storage', ex)
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    # Данные из запроса пользователя
    storage_data = [
        {'number': '3', 'letter': 'N:'},
        {'number': '4', 'letter': 'M:'},
        {'number': '6', 'letter': 'I:'},
        {'number': '7', 'letter': 'V:'},
        {'number': '9', 'letter': 'G:'}
    ]
    insert_storage_data(storage_data)
