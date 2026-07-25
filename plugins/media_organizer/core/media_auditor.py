# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Аудит медиатеки и проверка целостности
# =============================================================================
# Описание:
#   Класс MediaAuditor для сверки данных БД с физическим наличием файлов
#   на диске.
#
# File: media_auditor.py
# Project: gemini-simplechat
# Package: plugins.media_organizer.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from src.logger import logger

from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core.media_scanner import MediaScanner


# =============================================================================
# MEDIA AUDITOR
# =============================================================================

INCOMPLETE_SUFFIXES = {'.part', '.!qb', '.crdownload', '.tmp'}
MIN_EPISODE_SIZE = 50 * 1024 * 1024  # 50 MB


class MediaAuditor:
    """Сверяет данные БД с физическим наличием файлов на диске.

    Attributes:
        db (MediaDatabase): Экземпляр базы данных.
        gemini: Экземпляр модели Gemini (опционально).
        SEASON_PATTERNS (re.Pattern): Паттерн для поиска сезонов.
    """

    SEASON_PATTERNS = re.compile(r'(?:season|\u0441езон)[\s._-]*(\d+)', re.IGNORECASE)

    def __init__(self, db: 'MediaDatabase', gemini=None) -> None:
        """Инициализация аудитора.

        Args:
            db (MediaDatabase): Экземпляр базы данных.
            gemini: Экземпляр модели Gemini (опционально).

        Examples:
            >>> auditor = MediaAuditor(db, gemini=gemini)
        """
        self.db = db
        self.gemini = gemini

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    # Поля, обязательные для полной записи
    # facts, similar, review — опциональные, не обязательные для полной записи
    _REQUIRED_FIELDS = ('plot', 'atmosphere', 'why_watch', 'mood', 'final_verdict', 'quote')

    async def audit(self, paths: list = None) -> List[Dict]:
        """Проведение полного аудита медиатеки.

        Проверяет:
        - Соответствие дисковой структуры и БД для сериалов
        - Полноту метаданных для всех записей

        Args:
            paths (list): Список путей для аудита (опционально).

        Returns:
            List[Dict]: Список найденных несовпадений (issues).

        Examples:
            >>> issues = await auditor.audit()
        """
        issues: List[Dict] = []
        total = skipped = checked = 0
        for record in self.db.export_all():
            # Фильтруем только сериалы (у них num_of_seasons > 0)
            if record.get('num_of_seasons', 0) <= 0:
                continue
            total += 1
            raw_path = record.get('path')
            if not raw_path:
                skipped += 1
                continue
            series_dir = Path(raw_path)
            if not series_dir.exists():
                skipped += 1
                continue
            # Проверяем, что это директория, а не файл
            if not series_dir.is_dir():
                print(f"  📁 **{record.get('title')}** — путь указывает на файл, а не на директорию: {raw_path}")
                skipped += 1
                continue
            checked += 1
            series_issues = self._audit_series(series_dir, record)
            title = record.get('title') or series_dir.name
            if series_issues:
                print(f"  ⚠️  {title}")
            else:
                print(f"  ✅ {title}")
            issues.extend(series_issues)

        print(f"📊 Сериалов в БД: {total} | Проверено: {checked} | Пропущено (диск недоступен): {skipped}")

        # Проверка полноты метаданных для всех записей
        print("\n🔎 Проверка полноты метаданных...")
        meta_issues = await self._audit_metadata()
        issues.extend(meta_issues)
        return issues

    async def _audit_metadata(self) -> List[Dict]:
        """Проверяет все записи БД на наличие обязательных полей метаданных.

        Упрощенная версия: не обогащает записи, только отмечает их как есть.

        Returns:
            List[Dict]: Список issues типа 'incomplete_metadata' для записей,
                       у которых нет даже базовых данных.
        """
        issues: List[Dict] = []
        for record in self.db.export_all():
            title = record.get('title', '')
            disk_name = record.get('disk_name', '')
            # Проверяем, есть ли хотя бы какие-то ключевые поля
            has_data = any(record.get(f) for f in ('title', 'main_category', 'plot', 'atmosphere', 'year'))
            if not has_data:
                print(f"  📋 {title} — нет базовых данных")
                issues.append({'type': 'incomplete_metadata', 'title': title,
                               'disk_name': disk_name, 'missing': 'no_data'})
            else:
                print(f"  ✅ {title} — есть в БД")
        return issues

    def _update_json(self, disk_name: str, media_type: str, record: dict) -> None:
        """Перегенерация JSON-отчёта диска после обновления записи в БД.

        Args:
            disk_name (str): Имя диска.
            media_type (str): 'movie' или 'series'.
            record (dict): Обновлённая запись (уже сохранена в БД до вызова).

        Examples:
            >>> auditor._update_json('ДИСК 1', 'series', record)
        """
        from plugins.media_organizer.core.report_generator import export_disk_json
        export_disk_json(self.db, disk_name, self.db.db_path.parent.parent / 'reports')

    # ------------------------------------------------------------------
    # PRIVATE
    # ------------------------------------------------------------------

    def _get_expected(self, record: Dict, title: str) -> tuple:
        """Эталон: сначала из БД, если нет — спрашиваем Gemini.

        Args:
            record (Dict): Запись из БД.
            title (str): Название медиа.

        Returns:
            tuple: (seasons, episodes) или (None, None).

        Examples:
            >>> seasons, episodes = auditor._get_expected(record, 'Фауда')
        """
        seasons = record.get('num_of_seasons')
        episodes = record.get('num_episodes_per_season')
        # Parse seasons - can be int, empty string, or numeric string
        if seasons is not None:
            if isinstance(seasons, str):
                seasons = seasons.strip()
                if seasons == '':
                    seasons = None
                else:
                    try:
                        seasons = int(seasons)
                    except ValueError:
                        seasons = None
        # Parse episodes - stored as JSON string or empty string
        if episodes is not None:
            if isinstance(episodes, str):
                episodes = episodes.strip()
                if episodes == '':
                    episodes = None
                else:
                    try:
                        episodes = json.loads(episodes)
                    except (json.JSONDecodeError, TypeError):
                        episodes = None
        if seasons and episodes:
            return seasons, episodes
        # Gemini не используется в синхронном методе _get_expected()
        # Для обогащения данных используйте другой механизм
        return seasons, episodes

    def _scan_season_dir(self, season_dir: Path) -> Dict:
        """Считает файлы в сезоне: полные, неполные, размер.

        Args:
            season_dir (Path): Путь к директории сезона.

        Returns:
            Dict: Статистика {'complete': int, 'incomplete': int, 'size_bytes': int}.

        Examples:
            >>> stats = auditor._scan_season_dir(Path('S:\\сериалы\\Фауда\\Season 1'))
        """
        complete = incomplete = 0
        total_size = 0
        for f in season_dir.iterdir():
            if not f.is_file():
                continue
            if f.suffix.lower() in INCOMPLETE_SUFFIXES:
                incomplete += 1
                continue
            if f.suffix.lower() not in MediaScanner.VIDEO_EXTENSIONS:
                continue
            size = f.stat().st_size
            total_size += size
            if size < MIN_EPISODE_SIZE:
                incomplete += 1
            else:
                complete += 1
        return {'complete': complete, 'incomplete': incomplete, 'size_bytes': total_size}

    def _find_season_dirs(self, series_dir: Path) -> Dict[int, Path]:
        """Находит все директории сезонов в директории сериала.

        Args:
            series_dir (Path): Путь к директории сериала.

        Returns:
            Dict[int, Path]: Словарь {season_num: path}.

        Examples:
            >>> seasons = auditor._find_season_dirs(Path('S:\\сериалы\\Фауда'))
        """
        result: Dict[int, Path] = {}
        for entry in series_dir.iterdir():
            if not entry.is_dir():
                continue
            m = self.SEASON_PATTERNS.search(entry.name)
            if m:
                result[int(m.group(1))] = entry
        return result

    def _audit_series(self, series_dir: Path, record: Dict) -> List[Dict]:
        """Проверка одного сериала на соответствие БД.

        Args:
            series_dir (Path): Путь к директории сериала.
            record (Dict): Запись из БД.

        Returns:
            List[Dict]: Список найденных несовпадений.

        Examples:
            >>> issues = auditor._audit_series(Path('S:\\сериалы\\Фауда'), record)
        """
        issues: List[Dict] = []
        title = record.get('title') or series_dir.name

        # Получаем эталон
        expected_seasons, expected_episodes = self._get_expected(record, title)

        # Физические сезоны
        physical_seasons = self._find_season_dirs(series_dir)
        actual_season_count = len(physical_seasons)
        # Проверка номера в имени папки
        expected_number = record.get('number')
        if expected_number is not None:
            m = re.match(r'^(\d+)\.', series_dir.name)
            actual_number = int(m.group(1)) if m else None
            if actual_number != expected_number:
                issues.append({'title': title, 'type': 'number',
                               'expected': expected_number, 'actual': actual_number,
                               'path': str(series_dir)})

        # Проверка количества сезонов
        if expected_seasons is not None and actual_season_count != expected_seasons:
            missing_seasons = [
                s for s in range(1, int(expected_seasons) + 1)
                if s not in physical_seasons
            ]
            for s in missing_seasons:
                issues.append({
                    'title': title, 'type': 'missing_season', 'season': s,
                    'path': str(series_dir),
                })

        # Проверка серий в каждом сезоне
        if expected_episodes:
            for season_num, season_dir in sorted(physical_seasons.items()):
                idx = season_num - 1
                if idx >= len(expected_episodes):
                    continue
                expected_ep = expected_episodes[idx]
                stats = self._scan_season_dir(season_dir)
                complete_ep = stats['complete']
                incomplete_ep = stats['incomplete']
                size_mb = stats['size_bytes'] / 1024 / 1024

                if complete_ep < expected_ep:
                    issues.append({
                        'title': title, 'type': 'episodes', 'season': season_num,
                        'expected': expected_ep, 'actual': complete_ep,
                        'incomplete': incomplete_ep, 'size_mb': round(size_mb, 1),
                        'path': str(season_dir),
                    })
                elif incomplete_ep > 0:
                    issues.append({
                        'title': title, 'type': 'incomplete_files', 'season': season_num,
                        'complete': complete_ep, 'incomplete': incomplete_ep,
                        'size_mb': round(size_mb, 1), 'path': str(season_dir),
                    })
        return issues
