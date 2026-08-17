# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Управление квотами дискового пространства
# =============================================================================
# Описание:
#   Анализирует свободное и занятое пространство на дисках медиатеки.
#   Рассчитывает квоты:
#     - 70% для постоянного хранилища (фильмы, сериалы)
#     - 25% для буфера закачек
#     - 5% неприкосновенный запас (НЗ)
#
# File: disk_quota_manager.py
# Project: gemini-simplechat
# =============================================================================

import shutil
import sqlite3
from pathlib import Path
from typing import Dict, List
from src.logger import logger

DB_PATH = Path(r'C:\mediateka\plugins\media_organizer\data\media.db')

class DiskQuotaManager:
    """Управление квотами и лимитами дисков."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path

    def get_disk_quota_status(self, drive_letter: str) -> Dict[str, float]:
        """Возвращает квоты и текущее использование для конкретного диска.
        
        Args:
            drive_letter (str): Буква диска, например 'D:' или 'E:'
            
        Returns:
            Dict[str, float]: Словарь с размерами в байтах.
        """
        path = Path(drive_letter + '\\' if not drive_letter.endswith('\\') else drive_letter)
        if not path.exists():
            raise FileNotFoundError(f"Диск {drive_letter} недоступен")

        total, used, free = shutil.disk_usage(path)
        
        # Квоты
        storage_limit = total * 0.70
        download_buffer = total * 0.25
        reserve = total * 0.05
        
        return {
            "total": float(total),
            "used": float(used),
            "free": float(free),
            "storage_limit_70": float(storage_limit),
            "download_buffer_25": float(download_buffer),
            "reserve_5": float(reserve),
            "is_storage_exceeded": float(used) > float(storage_limit),
            "is_reserve_violated": float(free) < float(reserve)
        }

    def update_storage_table(self, drive_letter: str, label: str) -> None:
        """Обновляет информацию в таблице storage базы данных."""
        status = self.get_disk_quota_status(drive_letter)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Убедимся, что таблица содержит нужные колонки или создадим/обновим ее
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS storage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                storage_name TEXT,
                storage_letter TEXT UNIQUE,
                storage_size INTEGER,
                free_size INTEGER,
                storage_limit_70 INTEGER,
                download_buffer_25 INTEGER,
                reserve_5 INTEGER
            )
        """)
        
        cursor.execute("""
            INSERT OR REPLACE INTO storage 
            (storage_name, storage_letter, storage_size, free_size, storage_limit_70, download_buffer_25, reserve_5)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            label, 
            drive_letter.upper().rstrip('\\'), 
            int(status["total"]), 
            int(status["free"]), 
            int(status["storage_limit_70"]), 
            int(status["download_buffer_25"]), 
            int(status["reserve_5"])
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Обновлены квоты для диска {drive_letter} ({label}): Свободно {status['free'] // (1024**3)} GB")

    def get_all_managed_disks(self) -> List[Dict]:
        """Возвращает список всех дисков, зарегистрированных в БД."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM storage")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            return []
        finally:
            conn.close()
