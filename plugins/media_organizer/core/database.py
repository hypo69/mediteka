# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Управление базой данных медиатеки
# =============================================================================
# Описание:
#   Инициализация схемы SQLite, сохранение и извлечение записей о медиафайлах,
#   эпизодах сериалов, дубликатах и сводных данных.
#
# File: media_database.py
# Project: gemini-simplechat
# Package: plugins.media_organizer.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import re
import sqlite3
from pathlib import Path
from typing import Dict, List

from src.logger import logger

_JSON_FIELDS = (
    'genres', 'directors', 'cast',
    'facts', 'similar',
)
_JSON_INTEGER_FIELDS = {'num_of_seasons', 'year', 'parent_id'}
_JSON_FIELDS_STRING = {'media_type'}  # Строковое поле, не JSON


def normalize_disk_name(name: str) -> str:
    """Нормализация имени диска для сравнения, убирает префикс до первой точки.
    
    Например: '01. movie' -> 'movie', '02.Series.Name' -> 'Series.Name'
    
    Args:
        name (str): Исходное имя диска.
        
    Returns:
        str: Нормализованное имя.
    """
    if not name:
        return name
    # Ищем первую точку и возвращаем часть после неё, убирая ведущие пробелы
    dot_pos = name.find('.')
    if dot_pos > 0:
        return name[dot_pos + 1:].lstrip()
    return name


class MediaDatabase:
    """Управление SQLite-базой данных медиатеки.

    Хранение записей о фильмах, сериалах, эпизодах и дубликатах.

    Attributes:
        db_path (Path): Путь к файлу базы данных.
    """

    def __init__(self, db_path: Path) -> None:
        """Инициализация подключения и схемы базы данных.

        Args:
            db_path (Path): Путь к файлу SQLite.

        Examples:
            >>> db = MediaDatabase(Path('media.db'))
        """
        self.db_path: Path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _normalize_disk_name_sql(self, name: str) -> str:
        """Обертка для normalize_disk_name, используемая в SQLite.
        
        Args:
            name (str): Исходное имя диска.
            
        Returns:
            str: Нормализованное имя.
        """
        return normalize_disk_name(name)

    # ------------------------------------------------------------------
    # Инициализация схемы
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        """Создание и миграция таблиц базы данных."""
        with sqlite3.connect(self.db_path) as conn:
            # Регистрируем пользовательскую функцию для SQLite
            conn.create_function('normalize_disk_name', 1, self._normalize_disk_name_sql)
            
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            cols = {row[1] for row in conn.execute('PRAGMA table_info(media)').fetchall()} if 'media' in tables else set()

            # Миграция устаревшей схемы
            if cols and ('raw_name' in cols or 'title' not in cols):
                conn.execute('DROP TABLE IF EXISTS media')
                conn.execute('DROP TABLE IF EXISTS duplicates')
                conn.execute('DROP TRIGGER IF EXISTS trg_check_duplicates')
                logger.info('Миграция БД: удалена устаревшая колонка raw_name')
            elif cols and 'path' not in cols:
                conn.execute('ALTER TABLE media ADD COLUMN path TEXT')
            if cols and 'number' in cols:
                logger.warning('Миграция БД: столбец number больше не используется и будет удалён при следующем полном сканировании')
            if cols and 'seasons' in cols:
                logger.warning('Миграция БД: столбец seasons больше не используется и будет удалён при следующем полном сканировании')
            if cols and 'review' not in cols:
                conn.execute('ALTER TABLE media ADD COLUMN review TEXT')
            if cols and 'episodes_detail' in cols:
                conn.execute('ALTER TABLE media DROP COLUMN episodes_detail')
            if cols and 'title_orig' not in cols:
                conn.execute('ALTER TABLE media ADD COLUMN title_orig TEXT')
            if cols and 'title_ru' not in cols:
                conn.execute('ALTER TABLE media ADD COLUMN title_ru TEXT')
            if cols and 'torrent_id' not in cols:
                conn.execute('ALTER TABLE media ADD COLUMN torrent_id TEXT')
            if cols and 'media_size' not in cols:
                conn.execute('ALTER TABLE media ADD COLUMN media_size INTEGER')
            if cols and 'media_type' not in cols:
                conn.execute('ALTER TABLE media ADD COLUMN media_type TEXT')
            if cols and 'episode_scan_skipped' not in cols:
                conn.execute('ALTER TABLE media ADD COLUMN episode_scan_skipped INTEGER')
            if cols and 'plot_granularity' not in cols:
                conn.execute('ALTER TABLE media ADD COLUMN plot_granularity TEXT')
            if cols and 'torrent_source' not in cols:
                conn.execute('ALTER TABLE media ADD COLUMN torrent_source TEXT')

            conn.execute("""
                CREATE TABLE IF NOT EXISTS media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    disk_name TEXT NOT NULL,
                    path TEXT,
                    review TEXT,
                    title TEXT NOT NULL,
                    title_orig TEXT,
                    title_ru TEXT,
                    year INTEGER,
                    main_category TEXT,
                    country TEXT,
                    genres TEXT,
                    directors TEXT,
                    cast TEXT,
                    num_of_seasons INTEGER,
                    num_episodes_per_season TEXT,
                    status TEXT,
                    rating TEXT,
                    awards TEXT,
                    plot TEXT,
                    atmosphere TEXT,
                    why_watch TEXT,
                    mood TEXT,
                    final_verdict TEXT,
                    can_stop_at TEXT,
                    quote TEXT,
                    facts TEXT,
                    similar TEXT,
                    parent_id INTEGER,
                    media_size INTEGER,
                    media_type TEXT,
                    episode_scan_skipped INTEGER,
                    plot_granularity TEXT,
                    torrent_source TEXT,
                    UNIQUE(path)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS duplicates (
                    title TEXT NOT NULL,
                    disk_name TEXT NOT NULL,
                    PRIMARY KEY (title, disk_name)
                )
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_check_duplicates
                AFTER INSERT ON media
                BEGIN
                    INSERT OR IGNORE INTO duplicates (title, disk_name)
                    SELECT m.title, m.disk_name
                    FROM media m
                    WHERE EXISTS (
                        SELECT 1 FROM media m2
                        WHERE m2.title = NEW.title
                          AND m2.disk_name != NEW.disk_name
                    );
                END
            """)

    def get_media_by_path(self, path: str) -> Dict:
        """Поиск записи по пути (используется для проверки обработанных элементов).
        
        Путь используется ТОЧНО как есть, без преобразований.

        Args:
            path (str): Полный путь к медиа.

        Returns:
            Dict: Найденная запись или пустой словарь.

        Examples:
            >>> rec = db.get_media_by_path('S:\\фильмы\\Вертикаль.mkv')
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM media WHERE path = ? LIMIT 1',
                (path,)
            ).fetchone()
            return self._parse_row(row) if row else {}

    def get_media_by_torrent_id(self, torrent_id: str) -> Dict:
        """Поиск записи по torrent_id.

        Args:
            torrent_id (str): Hash торрента.

        Returns:
            Dict: Найденная запись или пустой словарь.

        Examples:
            >>> rec = db.get_media_by_torrent_id('abc123...')
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM media WHERE torrent_id = ? LIMIT 1',
                (torrent_id,)
            ).fetchone()
            return self._parse_row(row) if row else {}

    def update_torrent_id(self, path: str, torrent_id: str, torrent_source: str = "") -> bool:
        """Обновление torrent_id и torrent_source для записи по пути.

        Args:
            path (str): Путь к медиа.
            torrent_id (str): Hash торрента.
            torrent_source (str): Источник торрента (URL или комментарий).

        Returns:
            bool: True если обновление успешно.

        Examples:
            >>> success = db.update_torrent_id('/path/to/file', 'abc123...', 'http://tracker...')
        """
        with sqlite3.connect(self.db_path) as conn:
            if torrent_source:
                result = conn.execute(
                    'UPDATE media SET torrent_id = ?, torrent_source = ? WHERE path = ?',
                    (torrent_id, torrent_source, path)
                ).rowcount
            else:
                result = conn.execute(
                    'UPDATE media SET torrent_id = ? WHERE path = ?',
                    (torrent_id, path)
                ).rowcount
            return result > 0

    def _parse_row(self, row: sqlite3.Row) -> Dict:
        """Преобразование строки таблицы media в словарь.

        Args:
            row (sqlite3.Row): Строка результата запроса.

        Returns:
            Dict: Словарь с полями.

        Examples:
            >>> data = db._parse_row(row)
        """
        if not row:
            return {}
        data = dict(row)
        # JSON-поля (TEXT → list/dict)
        for field in ('genres', 'directors', 'cast', 'facts', 'similar'):
            raw = data.get(field)
            if raw and isinstance(raw, str):
                try:
                    data[field] = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    data[field] = []
            else:
                data[field] = []
        for field in ('rating', 'review'):
            raw = data.get(field)
            if raw and isinstance(raw, str):
                try:
                    data[field] = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    data[field] = {}
            else:
                data[field] = {}
        # Integer fields
        for field in _JSON_INTEGER_FIELDS:
            raw = data.get(field)
            data[field] = raw if raw is not None else 0
        
        # parent_id should be None if not set
        if 'parent_id' in data and data['parent_id'] == 0:
            data['parent_id'] = None
        
        # media_size
        data['media_size'] = data.get('media_size') or 0
        
        # episode_scan_skipped (INTEGER -> bool)
        episode_scan_skipped = data.get('episode_scan_skipped')
        data['episode_scan_skipped'] = bool(episode_scan_skipped) if episode_scan_skipped is not None else False
        
        # plot_granularity
        data['plot_granularity'] = data.get('plot_granularity') or ''
        
        # Keep 'id' in data so that child records can query parent_id.
        return data

    def save_media(self, disk_name: str, media_type: str, data: Dict) -> None:
        """Сохранение записи в базу данных.

        Args:
            disk_name (str): Имя диска.
            media_type (str): Тип: 'movie' или 'series'.
            data (Dict): Данные для сохранения.

        Examples:
            >>> db.save_media('ДИСК 1', 'movie', {'title': 'Film', ...})
        """
        # Конвертация JSON-полей в строку
        save_data = data.copy()
        # Списки и словари конвертируем в строку
        for field in ('genres', 'directors', 'cast', 'facts', 'similar', 'awards', 'num_episodes_per_season'):
            value = save_data.get(field)
            if value is not None:
                if isinstance(value, (list, dict)):
                    save_data[field] = json.dumps(value, ensure_ascii=False)
                    print(f"DEBUG save_media: converting {field} -> {save_data[field]}")
        # num_of_seasons должен быть числом, даже если Gemini вернул список
        ns_value = save_data.get('num_of_seasons')
        if ns_value is not None:
            if isinstance(ns_value, list):
                save_data['num_of_seasons'] = ns_value[0] if ns_value else 0
                print(f"DEBUG save_media: num_of_seasons list -> {save_data['num_of_seasons']}")
            elif isinstance(ns_value, dict):
                save_data['num_of_seasons'] = 0
                print(f"DEBUG save_media: num_of_seasons dict -> 0")
        # Словари rating, review конвертируем в строку
        for field in ('rating', 'review'):
            value = save_data.get(field)
            if value is not None:
                if isinstance(value, dict):
                    print(f"DEBUG save_media: converting {field} = {value} ({type(value).__name__})")
                    save_data[field] = json.dumps(value, ensure_ascii=False)

        # Check if 'id' is in data (for parent_id tracking)
        has_id = 'id' in data and data['id'] is not None

        fields_list = [
            'disk_name', 'path', 'media_type', 'review', 'title', 'title_orig', 'title_ru', 
            'year', 'main_category', 'country', 'genres', 'directors', 'cast', 
            'num_of_seasons', 'num_episodes_per_season', 'status', 'rating', 'awards', 
            'plot', 'atmosphere', 'why_watch', 'mood', 'final_verdict', 'can_stop_at', 
            'quote', 'facts', 'similar', 'parent_id', 'media_size', 
            'episode_scan_skipped', 'plot_granularity', 'torrent_id', 'torrent_source'
        ]
        if has_id:
            fields_list.append('id')

        columns_str = ", ".join(fields_list)
        values_str = ", ".join([f":{f}" for f in fields_list])

        params = {
            'disk_name': disk_name,
            'path': data.get('path'),
            'media_type': media_type,
            'review': save_data.get('review'),
            'title': data.get('title', ''),
            'title_orig': data.get('title_orig'),
            'year': data.get('year', 0),
            'title_ru': data.get('title_ru'),
            'main_category': data.get('main_category'),
            'country': data.get('country'),
            'genres': save_data.get('genres'),
            'directors': save_data.get('directors'),
            'cast': save_data.get('cast'),
            'num_of_seasons': save_data.get('num_of_seasons', 0),
            'num_episodes_per_season': save_data.get('num_episodes_per_season'),
            'status': data.get('status'),
            'rating': save_data.get('rating'),
            'awards': save_data.get('awards'),
            'plot': data.get('plot'),
            'atmosphere': data.get('atmosphere'),
            'why_watch': data.get('why_watch'),
            'mood': data.get('mood'),
            'final_verdict': data.get('final_verdict'),
            'can_stop_at': data.get('can_stop_at'),
            'quote': data.get('quote'),
            'facts': save_data.get('facts'),
            'similar': save_data.get('similar'),
            'parent_id': data.get('parent_id'),
            'media_size': data.get('media_size', 0),
            'episode_scan_skipped': 1 if save_data.get('episode_scan_skipped') else 0,
            'plot_granularity': save_data.get('plot_granularity'),
            'torrent_id': data.get('torrent_id', ''),
            'torrent_source': data.get('torrent_source', ''),
        }
        if has_id:
            params['id'] = data['id']

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                INSERT OR REPLACE INTO media 
                ({columns_str})
                VALUES ({values_str})
            """, params)

    _COMPLETE_FIELDS = ('title', 'main_category', 'plot', 'atmosphere', 'why_watch', 'mood', 'final_verdict', 'quote')
    # facts, similar, review — опциональные поля, не обязательные для полной записи

    def is_complete(self, record: Dict) -> bool:
        """Проверка полноты записи по обязательным полям.

        Поля facts, similar, review — опциональные, проверяются только если заполнены.

        Args:
            record (Dict): Запись из БД.

        Returns:
            bool: True если все обязательные поля заполнены.

        Examples:
            >>> db.is_complete({'title': 'Fargo', 'main_category': 'Драмы', 'plot': '...', ...})
        """
        return all(record.get(f) for f in self._COMPLETE_FIELDS)

    def get_media(self, disk_name: str, title: str) -> Dict:
        """Поиск записи по диску и названию.

        Args:
            disk_name (str): Имя диска.
            title (str): Название медиа.

        Returns:
            Dict: Найденная запись или пустой словарь.

        Examples:
            >>> rec = db.get_media('ДИСК 1', 'Фауда')
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM media WHERE disk_name = ? AND title = ?',
                (disk_name, title)
            ).fetchone()
            return self._parse_row(row) if row else {}

    def find_any_disk(self, title: str) -> Dict:
        """Поиск записи по всей БД независимо от диска.

        Args:
            title (str): Название медиа.

        Returns:
            Dict: Найденная запись или пустой словарь.

        Examples:
            >>> rec = db.find_any_disk('Breaking Bad')
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM media WHERE title = ? LIMIT 1',
                (title,)
            ).fetchone()
            return self._parse_row(row) if row else {}

    def find_duplicates(self) -> Dict[str, List[Dict]]:
        """Чтение дублей из таблицы duplicates.

        Returns:
            Dict[str, List[Dict]]: Словарь {ключ: список записей по дискам}.

        Examples:
            >>> dups = db.find_duplicates()
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT title, disk_name FROM duplicates ORDER BY title'
            ).fetchall()
            result: Dict[str, List[Dict]] = {}
            for row in rows:
                key = row['title']
                result.setdefault(key, []).append({'disk_name': row['disk_name']})
            return result

    def update_duplicates(self) -> int:
        """Обновление таблицы duplicates на основе всех записей в БД.
        
        Находит дубликаты по (title) между разными дисками, сравнивая
        нормализованные имена файлов (без префикса до точки).
        
        Returns:
            int: Количество уникальных дубликатов найдено.
        """
        with sqlite3.connect(self.db_path) as conn:
            # Регистрируем пользовательскую функцию для SQLite
            conn.create_function('normalize_disk_name', 1, self._normalize_disk_name_sql)
            
            # Очищаем старые дубликаты
            conn.execute('DELETE FROM duplicates')
            
            # Находим новые дубликаты
            conn.execute("""
                INSERT OR IGNORE INTO duplicates (title, disk_name)
                SELECT m.title, m.disk_name
                FROM media m
                WHERE EXISTS (
                    SELECT 1 FROM media m2
                    WHERE m2.title = m.title
                      AND m2.disk_name != m.disk_name
                )
            """)
            
            # Возвращаем количество уникальных дубликатов
            count = conn.execute('SELECT COUNT(DISTINCT title) FROM duplicates').fetchone()[0]
            return count if count else 0

    def export_all(self) -> List[Dict]:
        """Экспорт всех записей таблицы media.

        Returns:
            List[Dict]: Список всех записей.

        Examples:
            >>> records = db.export_all()
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('SELECT * FROM media ORDER BY disk_name, title').fetchall()
            return [self._parse_row(row) for row in rows]

    def export_disk(self, disk_name: str) -> List[Dict]:
        """Экспорт всех записей одного диска.

        Args:
            disk_name (str): Имя диска.

        Returns:
            List[Dict]: Список записей диска.

        Examples:
            >>> records = db.export_disk('ДИСК 5')
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM media WHERE disk_name = ? ORDER BY main_category, title',
                (disk_name,)
            ).fetchall()
            return [self._parse_row(row) for row in rows]

    def assign_numbers(self, disk_name: str) -> int:
        """Сквозная нумерация записей диска: сериалы и фильмы раздельно,
        сортировка по категории → названию.

        Порядок категорий и названий определяет итоговый номер.
        Счётчик сериалов и фильмов начинается с 1 независимо.

        Args:
            disk_name (str): Имя диска.

        Returns:
            int: Количество обработанных записей.

        Examples:
            >>> count = db.assign_numbers('ДИСК 5')
        """
        records = self.export_disk(disk_name)
        # Делим на сериалы и фильмы по наличию поля num_of_seasons (у сериалов оно > 0)
        series = sorted(
            [r for r in records if r.get('num_of_seasons', 0) > 0],
            key=lambda r: (r.get('main_category', ''), r.get('title', ''))
        )
        movies = sorted(
            [r for r in records if r.get('num_of_seasons', 0) == 0],
            key=lambda r: (r.get('main_category', ''), r.get('title', ''))
        )
        # Numbering is no longer stored in DB
        return len(records)

    def get_series_summary(self) -> List[Dict]:
        """Агрегированная сводка по сериалам из series_episodes.

        Returns:
            List[Dict]: Список сводок: название, сезоны, эпизоды, размер.

        Examples:
            >>> summary = db.get_series_summary()
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT series_title,
                       COUNT(*) as total_episodes,
                       COUNT(DISTINCT season) as total_seasons,
                       MIN(season) as first_season,
                       MAX(season) as last_season,
                       SUM(size_mb) as total_size_mb
                FROM series_episodes
                GROUP BY series_title
                ORDER BY series_title
            """).fetchall()
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Консолидация дублей
    # ------------------------------------------------------------------

    def consolidate_duplicates(self) -> int:
        """Консолидация дублирующихся записей одного диска с одинаковым path.

        Дубли возникают когда raw_name (транслит) и нормализованный title от Gemini
        сохраняются как отдельные строки. Метод объединяет поля (побеждает непустое
        значение из более полной записи), удаляет лишние строки.

        Returns:
            int: Количество удалённых дублей.

        Examples:
            >>> removed = db.consolidate_duplicates()
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Группы строк одного диска с одинаковым path (path не пустой)
            rows = conn.execute("""
                SELECT id, disk_name, path, title
                FROM media
                WHERE path != '' AND path IS NOT NULL
                ORDER BY disk_name, path, id
            """).fetchall()

        # Группировка по (disk_name, path)
        groups: dict = {}
        for row in rows:
            key = (row['disk_name'], row['path'])
            groups.setdefault(key, []).append(dict(row))

        removed = 0
        for key, group in groups.items():
            if len(group) < 2:
                continue
            disk_name, _ = key
            # Загрузка полных записей
            full_records = [
                self.get_media(disk_name, g['title'])
                for g in group
            ]
            # Выбор наиболее полной записи как базовой (максимум заполненных полей)
            base = max(full_records, key=lambda r: sum(1 for v in r.values() if v))
            # Дополнение базовой непустыми полями из остальных
            for rec in full_records:
                if rec is base:
                    continue
                for field, value in rec.items():
                    if value and not base.get(field):
                        base[field] = value
            # Удаление дублей будет реализовано позже
            # for g in group:
            #     if g['title'] != base.get('title'):
            #         self.delete_media(disk_name, g['title'])
            #         removed += 1
            # Сохранение объединённой записи
            # media_type определяется по num_of_seasons: если > 0, то serial, иначе movie
            media_type = 'c' if base.get('num_of_seasons', 0) > 0 else 'movie'
            self.save_media(disk_name, media_type, base)

        return removed

    def delete_disk(self, disk_name: str) -> int:
        """Удаляет все записи медиа для указанного диска.
        
        Args:
            disk_name (str): Имя диска.
            
        Returns:
            int: Количество удаленных записей.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM media WHERE disk_name = ?", (disk_name,))
            conn.commit()
            return cursor.rowcount

    # ------------------------------------------------------------------
    # Консолидация дублей
    # ------------------------------------------------------------------