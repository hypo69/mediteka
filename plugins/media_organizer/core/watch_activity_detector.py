# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Детектор активности просмотра пользователя
# =============================================================================
# Описание:
#   Анализирует историю просмотров во всех профилях пользователей.
#   Определяет сериалы, которые пользователь начал активно смотреть.
#   Критерий: просмотрено не менее 3 серий первого сезона (прогресс > 50% или completed).
#
# File: watch_activity_detector.py
# Project: gemini-simplechat
# =============================================================================

import json
import re
import sqlite3
from pathlib import Path
from typing import Dict, Set
from src.logger import logger

PROFILES_DIR = Path(r'C:\mediateka\src\ai\gemini\user_rags')
DB_PATH = Path(r'C:\mediateka\plugins\media_organizer\data\media.db')

# Паттерны для поиска сезона и эпизода
_EP_PATTERNS = [
    re.compile(r'[Ss](\d{1,2})[Ee](\d{1,3})'),
    re.compile(r'(\d{1,2})x(\d{1,3})'),
    re.compile(r'[Сс]езон[\s._-]*(\d+).*?[Сс]ери[яи][\s._-]*(\d+)', re.IGNORECASE),
    re.compile(r'[Ss]eason[\s._-]*(\d+).*?[Ee]p(?:isode)?[\s._-]*(\d+)', re.IGNORECASE),
]

def parse_season_episode(name: str) -> tuple[int, int]:
    """Извлекает сезон и эпизод из имени файла."""
    for pat in _EP_PATTERNS:
        m = pat.search(name)
        if m:
            return int(m.group(1)), int(m.group(2))
    return 0, 0

class WatchActivityDetector:
    def __init__(self, profiles_dir: Path = PROFILES_DIR, db_path: Path = DB_PATH) -> None:
        self.profiles_dir = profiles_dir
        self.db_path = db_path

    def get_series_title_from_db(self, file_path: str) -> str | None:
        """Ищет название сериала по пути файла в базе данных."""
        if not self.db_path.exists():
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Сначала ищем точное совпадение пути файла
        cursor.execute("SELECT parent_id, title FROM media WHERE path = ? LIMIT 1", (file_path,))
        row = cursor.fetchone()
        
        # Если это дочерняя запись, ищем название родительского сериала
        if row and row[0]:
            parent_id = row[0]
            cursor.execute("SELECT title FROM media WHERE id = ? LIMIT 1", (parent_id,))
            parent_row = cursor.fetchone()
            conn.close()
            return parent_row[0] if parent_row else None
            
        # Если не нашли, пробуем по частичному пути (имени родительской папки)
        conn.close()
        path_obj = Path(file_path)
        # Для структуры: Сериалы / Имя Сериала / Сезон X / Серия.mkv
        # Имя Сериала обычно находится на 2 уровня выше
        if len(path_obj.parts) >= 3:
            return path_obj.parents[1].name
        return None

    def get_actively_watched_series(self) -> Set[str]:
        """Возвращает множество названий активно просматриваемых сериалов."""
        actively_watched = set()
        
        if not self.profiles_dir.exists():
            logger.warning(f"Директория профилей не найдена: {self.profiles_dir}")
            return actively_watched

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
                    profile_data = json.load(f)
                    
                watch_history = profile_data.get("watch_history", {})
                
                # Группировка просмотров по сериалам
                # { series_title: { episode_num } } (только для 1 сезона)
                series_progress: Dict[str, Set[int]] = {}
                
                for file_path, info in watch_history.items():
                    name = info.get("name", "")
                    last_pos = info.get("last_position", 0.0)
                    duration = info.get("duration", 0.0)
                    completed = info.get("completed", False)
                    
                    # Проверяем, просмотрена ли серия (минимум 50% или завершена)
                    is_watched = completed or (duration > 0 and (last_pos / duration) >= 0.50)
                    if not is_watched:
                        continue
                        
                    season, episode = parse_season_episode(name)
                    if not season:
                        # Попробуем распарсить из пути
                        season, episode = parse_season_episode(file_path)
                        
                    # Нас интересует только 1-й сезон для детекта начала просмотра
                    if season == 1 and episode > 0:
                        series_title = self.get_series_title_from_db(file_path)
                        if series_title:
                            series_progress.setdefault(series_title, set()).add(episode)
                            
                for series_title, episodes in series_progress.items():
                    if len(episodes) >= 3:
                        logger.info(f"Сериал '{series_title}' определен как активно просматриваемый (просмотрено {len(episodes)} сер. 1-го сезона)")
                        actively_watched.add(series_title)
            except Exception as e:
                logger.error(f"Ошибка при анализе профиля {profile_path}: {e}")
                
        return actively_watched
