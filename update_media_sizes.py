# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Обновление размеров медиафайлов и статистики хранилищ
# =============================================================================
# Описание:
#   1. Обновляет media_size в таблице media для всех файлов.
#   2. Обновляет таблицу storage для указанных дисков (или найденных).
#
# Использование:
#   python update_media_sizes.py [Drives...]
#   Пример: python update_media_sizes.py E: L:
#
# File: update_media_sizes.py
# Project: ai-mediteka
# =============================================================================

import sqlite3
import shutil
import subprocess
import argparse
from pathlib import Path
from src.logger import logger

DB_PATH = Path(r'C:\mediateka\plugins\media_organizer\data\media.db')

def get_dir_size(path: Path) -> int:
    """Рекурсивный расчет размера директории."""
    total_size = 0
    try:
        for p in path.rglob('*'):
            if p.is_file():
                total_size += p.stat().st_size
    except Exception as e:
        logger.warning(f"Ошибка при расчете размера директории {path}: {e}")
    return total_size

def get_volume_labels():
    """Получает маппинг букв дисков к их меткам томов через PowerShell."""
    cmd = "powershell -Command \"Get-Volume | Select-Object DriveLetter, FileSystemLabel | Where-Object {$_.DriveLetter -ne $null} | ForEach-Object { $_.DriveLetter + ':' + $_.FileSystemLabel }\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    mapping = {}
    if result.returncode == 0:
        for line in result.stdout.strip().split('\n'):
            parts = line.strip().split(':')
            if len(parts) >= 2:
                mapping[parts[0].upper() + ':'] = parts[1]
    return mapping

def update_media_sizes_and_storage(target_disks=None):
    if not DB_PATH.exists():
        logger.error(f"База данных не найдена: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Обновление размеров медиафайлов и директорий
    print("Обновление размеров медиафайлов и директорий...")
    cursor.execute("SELECT id, path FROM media WHERE path IS NOT NULL AND path != ''")
    records = cursor.fetchall()
    
    updated_count = 0
    
    # Инициализация статистики
    storage_stats = {d.upper() + ('' if d.endswith(':') else ':'): {'root': Path(d)} for d in (target_disks or [])}

    for record_id, file_path_str in records:
        path = Path(file_path_str)
        if path.exists():
            try:
                if path.is_file():
                    size = path.stat().st_size
                elif path.is_dir():
                    size = get_dir_size(path)
                else:
                    continue
                    
                cursor.execute("UPDATE media SET media_size = ? WHERE id = ?", (size, record_id))
                updated_count += 1
                
                # Собираем статистику по диску
                letter = path.drive.upper()
                if not target_disks or letter in storage_stats:
                    if letter not in storage_stats:
                        storage_stats[letter] = {'root': Path(letter)}
            except Exception as e:
                logger.warning(f"Ошибка обновления размера для {file_path_str}: {e}")

    # 2. Обновление таблицы storage
    print("Обновление статистики хранилищ (автоматическое получение имен)...")
    volume_labels = get_volume_labels()
    
    for letter, stats in storage_stats.items():
        root = stats['root']
        try:
            if root.exists():
                total, used, free = shutil.disk_usage(root)
                label = volume_labels.get(letter, f"Disk {letter}")
                
                cursor.execute("""
                    INSERT OR REPLACE INTO storage (storage_name, storage_letter, storage_size, free_size)
                    VALUES (?, ?, ?, ?)
                """, (label, letter, total, free))
                print(f"Обновлено хранилище {label} ({letter}): Свободно {free // (1024**3)} GB")
            else:
                print(f"Хранилище {letter} недоступно.")
        except Exception as e:
            logger.warning(f"Ошибка получения статистики для {letter}: {e}")

    conn.commit()
    conn.close()
    print(f"Готово. Обновлено медиа-записей: {updated_count}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Обновление размеров медиафайлов и статистики хранилищ.')
    parser.add_argument('disks', nargs='*', help='Список букв дисков для обработки (например, E: L:)')
    args = parser.parse_args()
    
    update_media_sizes_and_storage(args.disks)
