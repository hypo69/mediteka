# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Сканирование медиатеки и TMDB API клиент
# =============================================================================
# Описание:
#   Класс TMDBClient для взаимодействия с API The Movie Database.
#   Класс MediaScanner для базового сканирования файловой структуры медиа.
#
# File: media_scanner.py
# Project: gemini-simplechat
# Package: plugins.media_organizer.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import requests

from src.logger import logger


# =============================================================================
# TMDB API CLIENT
# =============================================================================

class TMDBClient:
    """Клиент для работы с API The Movie Database (TMDB).

    Предоставляет методы для поиска фильмов, сериалов и получения их деталей.

    Attributes:
        BASE_URL (str): Базовый URL TMDB API.
        session: Сессия requests с автоматической авторизацией.
    """

    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self, api_key: str) -> None:
        """Инициализация клиента с API ключом.

        Args:
            api_key (str): API ключ для TMDB.

        Examples:
            >>> client = TMDBClient('your_api_key_here')
        """
        self.session = requests.Session()
        self.session.params = {'api_key': api_key, 'language': 'ru-RU'}

    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """Поиск фильма по названию и году.

        Args:
            title (str): Название фильма.
            year (Optional[int]): Год выпуска (опционально).

        Returns:
            Optional[Dict]: Информация о фильме или None если не найдено.

        Examples:
            >>> client.search_movie('Титаник', 1997)
        """
        try:
            results = self.session.get(
                f"{self.BASE_URL}/search/movie",
                params={'query': title}
            ).json().get('results', [])
            if year:
                for r in results:
                    if r.get('release_date', '').startswith(str(year)):
                        return r
            return results[0] if results else None
        except Exception as e:
            logger.warning(f"TMDB search_movie '{title}': {e}")
            return None

    def search_tv_series(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """Поиск сериала по названию и году.

        Args:
            title (str): Название сериала.
            year (Optional[int]): Год выпуска (опционально).

        Returns:
            Optional[Dict]: Информация о сериале или None если не найдено.

        Examples:
            >>> client.search_tv_series('Фауда', 2015)
        """
        try:
            results = self.session.get(
                f"{self.BASE_URL}/search/tv",
                params={'query': title}
            ).json().get('results', [])
            if year:
                for r in results:
                    if r.get('first_air_date', '').startswith(str(year)):
                        return r
            return results[0] if results else None
        except Exception as e:
            logger.warning(f"TMDB search_tv '{title}': {e}")
            return None

    def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """Получение детальной информации о фильме.

        Args:
            movie_id (int): ID фильма в TMDB.

        Returns:
            Optional[Dict]: Детальная информация о фильме.

        Examples:
            >>> details = client.get_movie_details(278)
        """
        try:
            return self.session.get(f"{self.BASE_URL}/movie/{movie_id}").json()
        except Exception as e:
            logger.warning(f"TMDB movie details {movie_id}: {e}")
            return None

    def get_tv_details(self, tv_id: int) -> Optional[Dict]:
        """Получение детальной информации о сериале.

        Args:
            tv_id (int): ID сериала в TMDB.

        Returns:
            Optional[Dict]: Детальная информация о сериале.

        Examples:
            >>> details = client.get_tv_details(1396)
        """
        try:
            return self.session.get(f"{self.BASE_URL}/tv/{tv_id}").json()
        except Exception as e:
            logger.warning(f"TMDB tv details {tv_id}: {e}")
            return None

    def get_genres(self, media_type: str = 'movie') -> Dict[int, str]:
        """Получение списка жанров для медиа.

        Args:
            media_type (str): Тип медиа: 'movie' или 'tv'.

        Returns:
            Dict[int, str]: Словарь {id: название_жанра}.

        Examples:
            >>> genres = client.get_genres('movie')
        """
        try:
            genres = self.session.get(
                f"{self.BASE_URL}/genre/{media_type}/list"
            ).json().get('genres', [])
            return {g['id']: g['name'] for g in genres}
        except Exception as e:
            logger.warning(f"TMDB genres: {e}")
            return {}


# =============================================================================
# MEDIA SCANNER
# =============================================================================

class MediaScanner:
    """Сканирование файловой структуры медиатеки.

    Определяет фильмы и сериалы по структуре директорий и файлов.
    Поддерживает глубокое сканирование сезонов и эпизодов.

    Attributes:
        VIDEO_EXTENSIONS (set): Расширения видеофайлов.
        IGNORE_DIRS (set): Директории для игнорирования.
        SEASON_PATTERNS (re.Pattern): Паттерн для поиска сезонов.
    """

    VIDEO_EXTENSIONS = {
        '.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv',
        '.webm', '.m4v', '.mpg', '.mpeg', '.ts', '.m2ts', '.iso'
    }
    IGNORE_DIRS = {'$RECYCLE.BIN', 'System Volume Information', '.git', 'node_modules', '__pycache__', '@eaDir'}
    # Предварительно создаем множество имен для игнорирования в верхнем регистре
    _IGNORE_DIRS_UPPER = {d.upper() for d in IGNORE_DIRS}
    SEASON_PATTERNS = re.compile(r'(?:season|\u0441езон)[\s._-]*(\d+)', re.IGNORECASE)

    def __init__(self) -> None:
        """Инициализация сканера медиа.

        Creates empty containers for movies, series and seasons.
        """
        self.movies: List[Dict] = []
        self.series: Dict[str, Dict] = {}
        self.seasons: Dict = {}

    def _should_ignore(self, name: str) -> bool:
        """Проверяет, нужно ли игнорировать директорию (регистронезависимо)."""
        return name.upper() in self._IGNORE_DIRS_UPPER

    def scan_paths(self, paths: List[Path]) -> None:
        """Этап 1: Базовое сканирование - фильмы, сериалы, сезоны (без эпизодов).

        Каждый диск содержит:
        - "сериалы" — для сериалов
        - "фильмы" — для фильмов

        Args:
            paths (List[Path]): Список путей для сканирования (может быть корень диска или папка films/series).

        Examples:
            >>> scanner.scan_paths([Path('S:\\'), Path('T:\\')])
            >>> scanner.scan_paths([Path('S:\\фильмы'), Path('S:\\сериалы')])
        """
        for path in paths:
            # Нормализуем путь (S: -> S:\\)
            path_str = str(path)
            normalized = Path(os.path.normpath(path_str))
            # Гарантируем завершающий \\ для корня диска (S: -> S:\\)
            if len(normalized.parts) == 1 and normalized.drive:
                normalized = Path(str(normalized) + '\\')
            if not normalized.exists():
                continue

            # Если это папка films или series, сканируем её напрямую
            name_lower = normalized.name.lower()
            if name_lower == "фильмы" or "фильмы" in name_lower:
                self._scan_directory(normalized, is_series=False)
                continue
            if name_lower == "сериалы" or "сериалы" in name_lower:
                self._scan_directory(normalized, is_series=True)
                continue

            # Иначе ищем поддиректории: сериалы и фильмы (регистронезависимо)
            has_standard_subdirs = False
            for entry in normalized.iterdir():
                try:
                    if entry.is_dir():
                        entry_name_lower = entry.name.lower()
                        if entry_name_lower == "сериалы":
                            self._scan_directory(entry, is_series=True)
                            has_standard_subdirs = True
                        elif entry_name_lower == "фильмы":
                            self._scan_directory(entry, is_series=False)
                            has_standard_subdirs = True
                except Exception as e:
                    logger.warning(f"Ошибка при сканировании поддиректории {entry}: {e}")

            # Если не нашли стандартных поддиректорий и директория не была отсканирована напрямую,
            # сканируем ее саму как директорию с медиа (считая по умолчанию сериалы)
            if not has_standard_subdirs:
                self._scan_directory(normalized, is_series=True)
    def _scan_directory(self, root_path: Path, is_series: bool = False) -> None:
        """Сканирует директорию и добавляет найденные медиа.

        Args:
            root_path (Path): Корневая директория для сканирования.
            is_series (bool): True если это директория сериалов, False - фильмов.

        Examples:
            >>> scanner._scan_directory(Path('S:\\сериалы'), is_series=True)
        """
        for entry in root_path.iterdir():
            if self._should_ignore(entry.name):
                continue
            if entry.is_dir():
                # Директория = сериал
                self._process_series_dir(entry)
            elif entry.is_file() and entry.suffix.lower() in self.VIDEO_EXTENSIONS:
                # Файл в корне = фильм
                self._process_movie_file(entry, is_series=is_series)

    def _process_series_dir(self, dirpath: Path) -> None:
        """Этап 1: Директория сериала - берем имя папки как есть, считаем сезоны.

        Args:
            dirpath (Path): Путь к директории сериала.

        Examples:
            >>> scanner._process_series_dir(Path('S:\\сериалы\\Фауда'))
        """
        seasons: Dict = {}
        total_size = 0
        for entry in dirpath.iterdir():
            if entry.is_dir():
                # Это сезон
                m = self.SEASON_PATTERNS.search(entry.name)
                if m:
                    season_num = int(m.group(1))
                    # Размер директории сезона
                    season_size = self._get_directory_size(entry)
                    seasons[season_num] = {
                        'path': str(entry),
                        'size': season_size,
                        'episode_count': 0,  # Будет заполнено в этапе 3
                        'episodes': []
                    }
                    total_size += season_size
        self.series[dirpath.name] = {
            'raw_name': dirpath.name,
            'title': dirpath.name,
            'path': str(dirpath),
            'season_count': len(seasons),
            'seasons': seasons,
            'total_size': total_size,
        }

    def _process_movie_file(self, filepath: Path, is_series: bool = False) -> None:
        """Этап 1: Файл в корне директории - берем имя файла как есть.

        Args:
            filepath (Path): Полный путь к файлу.
            is_series (bool): Для совместимости (не используется).

        Examples:
            >>> scanner._process_movie_file(Path('S:\\фильмы\\Титаник.mkv'))
        """
        self.movies.append({
            'raw_name': filepath.stem,
            'title': filepath.stem,
            'path': str(filepath),  # Используем 'path' для всех типов
            'size': filepath.stat().st_size,
        })

    def _get_directory_size(self, dirpath: Path) -> int:
        """Получить суммарный размер всех файлов в директории.

        Args:
            dirpath (Path): Путь к директории.

        Returns:
            int: Общий размер в байтах.

        Examples:
            >>> size = scanner._get_directory_size(Path('S:\\сериалы\\Фауда\\Season 1'))
        """
        total = 0
        for f in dirpath.rglob('*'):
            if f.is_file():
                total += f.stat().st_size
        return total

    def deep_scan_series(self) -> None:
        """Этап 3: Глубокое сканирование - содержимое эпизодов сериала.

        Заполняет информацию об эпизодах в каждом сезоне.

        Examples:
            >>> scanner.deep_scan_series()
        """
        for series_title, series_data in self.series.items():
            seasons = series_data.get('seasons', {})
            for season_num, season_data in seasons.items():
                season_dir = Path(season_data['path'])
                episodes: List[Dict] = []
                for f in season_dir.iterdir():
                    if f.is_file() and f.suffix.lower() in self.VIDEO_EXTENSIONS:
                        episodes.append({
                            'filename': f.name,
                            'path': str(f),  # Используем 'path' для всех типов
                            'size': f.stat().st_size
                        })
                season_data['episode_count'] = len(episodes)
                season_data['episodes'] = episodes