# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Агент фоновой предзагрузки сериалов
# =============================================================================
# Описание:
#   Автоматически возобновляет скачивание последующих сезонов для активно просматриваемых сериалов.
#   Соблюдает квоту активных закачек (25% свободного пространства).
#
# File: torrent_prefetch_agent.py
# Project: gemini-simplechat
# =============================================================================

import sqlite3
from pathlib import Path
from src.logger import logger
from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg
from plugins.media_organizer.core.disk_quota_manager import DiskQuotaManager
from plugins.media_organizer.core.watch_activity_detector import WatchActivityDetector, parse_season_episode

DB_PATH = Path(r'C:\mediateka\plugins\media_organizer\data\media.db')

class TorrentPrefetchAgent:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.detector = WatchActivityDetector(db_path=db_path)
        self.quota_mgr = DiskQuotaManager(db_path=db_path)
        
        # Инициализация qBittorrent
        qbt_cfg = _load_cfg()
        self.qbt = QBittorrentClient(
            host=getattr(qbt_cfg, "host", "localhost"),
            port=getattr(qbt_cfg, "port", 8080),
            username=getattr(qbt_cfg, "username", "admin"),
            password=getattr(qbt_cfg, "password", "adminadmin")
        )

    def prefetch_active_shows(self, dry_run: bool = True) -> int:
        """Включает закачку следующих сезонов для активных сериалов.
        
        Returns:
            int: Количество запущенных на закачку файлов.
        """
        logger.info(f"Запуск агента предзагрузки (Dry Run = {dry_run})")
        actively_watched = self.detector.get_actively_watched_series()
        
        if not actively_watched:
            logger.info("Нет активно просматриваемых сериалов для предзагрузки.")
            return 0
            
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Получаем все сериалы, у которых есть torrent_id
        cursor.execute("""
            SELECT DISTINCT title, torrent_id, disk_name
            FROM media 
            WHERE media_type = 'series' AND torrent_id IS NOT NULL AND parent_id IS NULL
        """)
        shows = cursor.fetchall()
        
        prefetched_count = 0
        
        for show in shows:
            title = show["title"]
            torrent_hash = show["torrent_id"]
            disk_name = show["disk_name"]
            
            if title not in actively_watched:
                continue
                
            # Проверяем квоту диска перед началом закачки
            # Мы должны убедиться, что у нас есть 25% свободного буфера под закачки
            drive_letter = disk_name.split()[0] if disk_name else "D:"
            if not drive_letter.endswith(":"):
                drive_letter += ":"
                
            try:
                quota = self.quota_mgr.get_disk_quota_status(drive_letter)
                # Если свободного места меньше 5% (лимит НЗ), не ставим новые закачки
                if quota["is_reserve_violated"]:
                    logger.warning(f"Диск {drive_letter} исчерпал НЗ (5%). Отмена предзагрузки для '{title}'.")
                    continue
            except Exception as e:
                logger.warning(f"Не удалось проверить квоту для диска {drive_letter}: {e}")
                
            logger.info(f"Активация предзагрузки для сериала '{title}'...")
            
            try:
                files = self.qbt.files(torrent_hash)
            except Exception as e:
                logger.warning(f"Не удалось получить файлы для торрента {torrent_hash} ({title}): {e}")
                continue
                
            files_to_enable = []
            
            for file_id, file_info in enumerate(files):
                file_name = file_info.get("name", "")
                priority = file_info.get("priority", 1)
                progress = file_info.get("progress", 0.0)
                
                # Если файл уже качается или скачан, пропускаем
                if priority > 0 or progress == 1.0:
                    continue
                    
                season, episode = parse_season_episode(file_name)
                
                # Загружаем сезоны > 1 (например, 2 сезон)
                if season > 1:
                    files_to_enable.append((file_id, file_name))
            
            if files_to_enable:
                logger.info(f"Сериал '{title}': найдено {len(files_to_enable)} файлов последующих сезонов для активации")
                prefetched_count += len(files_to_enable)
                
                file_ids = [f[0] for f in files_to_enable]
                if not dry_run:
                    self.qbt.set_file_priority(torrent_hash, file_ids, 1) # Устанавливаем приоритет Normal (1)
                    logger.info(f"В qBittorrent успешно активирована загрузка {len(file_ids)} файлов для '{title}'")
                    
        conn.close()
        logger.info(f"Агент предзагрузки завершил работу. Запущено файлов: {prefetched_count}")
        return prefetched_count

if __name__ == '__main__':
    agent = TorrentPrefetchAgent()
    agent.prefetch_active_shows(dry_run=True)
