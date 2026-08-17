# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Агент очистки и удержания дискового пространства
# =============================================================================
# Описание:
#   Удаляет сезоны > 1 для неактивных сериалов.
#   Сохраняет пилотную серию (даже если она в сезоне 0/спецвыпусках) и весь 1-й сезон.
#   Устанавливает приоритет удаленных файлов в qBittorrent в "Do Not Download" (0).
#
# File: torrent_retention_agent.py
# Project: gemini-simplechat
# =============================================================================

import os
import sqlite3
from pathlib import Path
from src.logger import logger
from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg
from plugins.media_organizer.core.watch_activity_detector import WatchActivityDetector, parse_season_episode

DB_PATH = Path(r'C:\mediateka\plugins\media_organizer\data\media.db')

class TorrentRetentionAgent:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.detector = WatchActivityDetector(db_path=db_path)
        
        # Инициализация клиента qBittorrent
        qbt_cfg = _load_cfg()
        self.qbt = QBittorrentClient(
            host=getattr(qbt_cfg, "host", "localhost"),
            port=getattr(qbt_cfg, "port", 8080),
            username=getattr(qbt_cfg, "username", "admin"),
            password=getattr(qbt_cfg, "password", "adminadmin")
        )

    def enforce_retention(self, dry_run: bool = True) -> int:
        """Очищает неактивные сезоны сериалов.
        
        Args:
            dry_run (bool): Если True, то файлы не удаляются физически.
            
        Returns:
            int: Объем освобожденного пространства в байтах.
        """
        logger.info(f"Запуск агента очистки (Dry Run = {dry_run})")
        actively_watched = self.detector.get_actively_watched_series()
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Получаем все сериалы, у которых есть torrent_id
        cursor.execute("""
            SELECT DISTINCT parent.title, parent.torrent_id 
            FROM media parent
            WHERE parent.media_type = 'series' AND parent.torrent_id IS NOT NULL AND parent.parent_id IS NULL
        """)
        shows = cursor.fetchall()
        
        freed_bytes = 0
        
        for show in shows:
            title = show["title"]
            torrent_hash = show["torrent_id"]
            
            # Если пользователь активно смотрит этот сериал, пропускаем его очистку
            if title in actively_watched:
                logger.info(f"Пропуск очистки для активно просматриваемого сериала: '{title}'")
                continue
                
            logger.info(f"Анализ сериала '{title}' на наличие лишних сезонов...")
            
            # Получаем список файлов этого торрента из qBittorrent
            try:
                files = self.qbt.files(torrent_hash)
            except Exception as e:
                logger.warning(f"Не удалось получить файлы для торрента {torrent_hash} ({title}): {e}")
                continue
                
            files_to_disable = []
            
            for file_id, file_info in enumerate(files):
                file_name = file_info.get("name", "")
                file_size = file_info.get("size", 0)
                
                # Проверяем, загружен ли файл (progress > 0)
                progress = file_info.get("progress", 0.0)
                if progress == 0:
                    continue
                    
                season, episode = parse_season_episode(file_name)
                
                # Логика сохранения пилота и первого сезона:
                # 1. Если это пилот (обычно в имени файла есть слово "pilot" или сезон 1 серия 1/сезон 0)
                is_pilot = "pilot" in file_name.lower() or "пайлот" in file_name.lower()
                
                # Оставляем только season 1 и пилоты. Все остальное (> 1) помечаем на удаление.
                if season > 1 and not is_pilot:
                    files_to_disable.append((file_id, file_name, file_size))
            
            if files_to_disable:
                logger.info(f"Сериал '{title}': найдено {len(files_to_disable)} файлов для очистки")
                
                # Отключаем загрузку в qBittorrent
                file_ids = [f[0] for f in files_to_disable]
                if not dry_run:
                    self.qbt.set_file_priority(torrent_hash, file_ids, 0)
                    logger.info(f"В qBittorrent отключена загрузка для {len(file_ids)} файлов сериала '{title}'")
                
                # Физическое удаление файлов с диска
                # Сначала получаем путь сохранения торрента
                try:
                    torrents = self.qbt.torrents()
                    save_path = None
                    for t in torrents:
                        if t.get("hash") == torrent_hash:
                            save_path = t.get("save_path")
                            break
                            
                    if save_path:
                        for _, file_name, file_size in files_to_disable:
                            full_path = Path(save_path) / file_name
                            if full_path.exists():
                                logger.info(f"Удаление файла: {full_path} ({file_size // 1048576} MB)")
                                freed_bytes += file_size
                                if not dry_run:
                                    os.remove(full_path)
                                    # Также удалим запись о конкретном эпизоде из БД media, если она там есть
                                    cursor.execute("DELETE FROM media WHERE path = ?", (str(full_path),))
                except Exception as e:
                    logger.error(f"Ошибка при удалении файлов для сериала '{title}': {e}")
                    
        conn.commit()
        conn.close()
        
        logger.info(f"Агент очистки завершил работу. Освобождено: {freed_bytes // 1048576} MB")
        return freed_bytes

if __name__ == '__main__':
    agent = TorrentRetentionAgent()
    agent.enforce_retention(dry_run=True)
