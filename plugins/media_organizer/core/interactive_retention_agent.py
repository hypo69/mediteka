# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Интерактивный агент очистки медиатеки
# =============================================================================
# Описание:
#   Анализирует профили пользователей и находит кандидатов на очистку:
#     - Сериалы и фильмы, которые полностью просмотрены (completed).
#     - Сериалы и фильмы, которые не просматривались более 30 дней.
#   Предоставляет функции для их удаления с диска с сохранением
#   метаданных в БД и изменением статуса торрентов в qBittorrent на "Do Not Download".
#
# File: interactive_retention_agent.py
# Project: gemini-simplechat
# =============================================================================

import os
import time
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple
from src.logger import logger
from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg
from plugins.media_organizer.core.watch_activity_detector import parse_season_episode

DB_PATH = Path(r'C:\mediateka\plugins\media_organizer\data\media.db')
PROFILES_DIR = Path(r'C:\mediateka\src\ai\gemini\user_rags')

class InteractiveRetentionAgent:
    def __init__(self, db_path: Path = DB_PATH, profiles_dir: Path = PROFILES_DIR, inactivity_days: int = 30) -> None:
        self.db_path = db_path
        self.profiles_dir = profiles_dir
        self.inactivity_seconds = inactivity_days * 24 * 60 * 60
        
        # Инициализация qBittorrent
        qbt_cfg = _load_cfg()
        self.qbt = QBittorrentClient(
            host=getattr(qbt_cfg, "host", "localhost"),
            port=getattr(qbt_cfg, "port", 8080),
            username=getattr(qbt_cfg, "username", "admin"),
            password=getattr(qbt_cfg, "password", "adminadmin")
        )

    def get_cleanup_candidates(self) -> List[Dict]:
        """Находит сериалы и фильмы, которые можно очистить.
        
        Returns:
            List[Dict]: Список кандидатов с информацией о названии, типе,
                        размере и причине рекомендации к удалению.
        """
        candidates = []
        if not self.profiles_dir.exists():
            return candidates

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        current_time = time.time()

        try:
            from src.user_manager import user_manager
            admins = [u for u in user_manager.get_all_users(active_only=False) if u.get("is_admin") == 1 or u.get("role") == "admin"]
            admin_ids = {str(u["id"]) for u in admins}
        except Exception as e:
            logger.warning(f"Не удалось получить список администраторов: {e}")
            admin_ids = set()

        for profile_path in self.profiles_dir.glob("user_profile_*.json"):
            filename = profile_path.stem
            user_id = filename.replace("user_profile_", "")
            if user_id not in admin_ids:
                continue

            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    import json
                    profile_data = json.load(f)
                    
                watch_history = profile_data.get("watch_history", {})
                
                # Группируем просмотры по названиям медиа
                # { title: { "last_watched": float, "all_completed": bool, "paths": [str], "episodes_count": int } }
                media_groups = {}
                
                for file_path, info in watch_history.items():
                    name = info.get("name", "")
                    updated_at = info.get("updated_at", 0.0)
                    completed = info.get("completed", False)
                    
                    # Ищем название сериала или фильма в БД
                    cursor.execute("SELECT title, media_type, torrent_id, media_size FROM media WHERE path = ? LIMIT 1", (file_path,))
                    row = cursor.fetchone()
                    
                    # Если это эпизод сериала, ищем родителя
                    title = None
                    media_type = "movie"
                    torrent_id = None
                    media_size = 0
                    
                    if row:
                        title = row["title"]
                        media_type = row["media_type"]
                        torrent_id = row["torrent_id"]
                        media_size = row["media_size"] or 0
                    else:
                        # Fallback по родительской папке
                        path_obj = Path(file_path)
                        if len(path_obj.parts) >= 2:
                            title = path_obj.parent.name
                        else:
                            title = name
                            
                    if not title:
                        continue
                        
                    grp = media_groups.setdefault(title, {
                        "last_watched": 0.0,
                        "all_completed": True,
                        "paths": [],
                        "media_type": media_type,
                        "torrent_id": torrent_id,
                        "media_size": 0
                    })
                    
                    grp["last_watched"] = max(grp["last_watched"], updated_at)
                    if not completed:
                        grp["all_completed"] = False
                    grp["paths"].append(file_path)
                    grp["media_size"] += media_size

                # Фильтруем группы по критериям «устаревания»
                for title, info in media_groups.items():
                    reason = None
                    days_inactive = int((current_time - info["last_watched"]) / (24*60*60))
                    
                    if info["all_completed"]:
                        reason = "Полностью просмотрен"
                    elif (current_time - info["last_watched"]) > self.inactivity_seconds:
                        reason = f"Брошено на середине (неактивно {days_inactive} дн.)"
                        
                    if reason:
                        candidates.append({
                            "title": title,
                            "media_type": info["media_type"],
                            "torrent_id": info["torrent_id"],
                            "size_mb": round(info["media_size"] / 1_048_576, 2),
                            "reason": reason,
                            "paths": info["paths"],
                            "last_watched_days_ago": days_inactive
                        })
            except Exception as e:
                logger.error(f"Ошибка при поиске кандидатов в {profile_path}: {e}")

        conn.close()
        # Возвращаем уникальный список кандидатов
        unique_candidates = {}
        for c in candidates:
            unique_candidates[c["title"]] = c
        return list(unique_candidates.values())

    def delete_candidate(self, title: str, dry_run: bool = True) -> Tuple[bool, int]:
        """Удаляет файлы кандидата с диска и отключает их загрузку в qBittorrent.
        
        Returns:
            Tuple[bool, int]: (Успешно ли, объем освобожденного места в байтах)
        """
        candidates = self.get_cleanup_candidates()
        target = None
        for c in candidates:
            if c["title"].lower() == title.lower():
                target = c
                break
                
        if not target:
            logger.warning(f"Кандидат '{title}' не найден или не подходит под критерии очистки")
            return False, 0
            
        torrent_hash = target.get("torrent_id")
        freed_bytes = 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Если есть torrent_id, отключаем файлы в qBittorrent
        if torrent_hash:
            try:
                files = self.qbt.files(torrent_hash)
                file_ids_to_disable = []
                for file_id, file_info in enumerate(files):
                    # Проверяем, совпадает ли путь файла из торрента с удаляемыми путях
                    # или просто отключаем все файлы торрента
                    file_ids_to_disable.append(file_id)
                    
                if file_ids_to_disable and not dry_run:
                    self.qbt.set_file_priority(torrent_hash, file_ids_to_disable, 0)
                    logger.info(f"В qBittorrent отключена загрузка для всех файлов торрента {title}")
            except Exception as e:
                logger.warning(f"Ошибка при работе с qBittorrent для {title}: {e}")

        # 2. Физическое удаление файлов с диска
        for path_str in target["paths"]:
            path = Path(path_str)
            if path.exists():
                try:
                    freed_bytes += path.stat().st_size
                    if not dry_run:
                        os.remove(path)
                        logger.info(f"Удален файл: {path}")
                        cursor.execute("DELETE FROM media WHERE path = ?", (path_str,))
                except Exception as e:
                    logger.error(f"Ошибка при удалении файла {path}: {e}")
                    
        conn.commit()
        conn.close()
        
        logger.info(f"Очистка '{title}' завершена. Освобождено {freed_bytes // 1_048_576} MB (Dry Run = {dry_run})")
        return True, freed_bytes
