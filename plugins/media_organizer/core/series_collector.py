# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Сбор и анализ эпизодов сериалов
# =============================================================================
# Описание:
#   Сканирование директорий: папка верхнего уровня = сериал, файлы = фильмы (игнор).
#   Извлечение номеров сезона и эпизода из имён файлов и папок.
#   Обнаружение дубликатов сезонов на разных путях.
#   Проверка целостности против эталона в таблице media.
#   Формирование Markdown-отчёта.
#
# File: series_collector.py
# Project: gemini-simplechat
# Package: plugins.media_organizer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from src.logger import logger
from src.utils.file import save_text_file
from plugins.media_organizer.core.database import MediaDatabase

VIDEO_EXTENSIONS: set = {
    '.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv',
    '.webm', '.m4v', '.mpg', '.mpeg', '.ts', '.m2ts',
}
IGNORE_DIRS: set = {'$RECYCLE.BIN', 'System Volume Information', '.git', '__pycache__', '@eaDir'}
_IGNORE_DIRS_UPPER = {d.upper() for d in IGNORE_DIRS}

def _should_ignore(name: str) -> bool:
    """Проверяет, нужно ли игнорировать директорию (регистронезависимо)."""
    return name.upper() in _IGNORE_DIRS_UPPER

_EP_PATTERNS: list = [
    re.compile(r'[Ss](\d{1,2})[Ee](\d{1,3})'),
    re.compile(r'(\d{1,2})x(\d{1,3})'),
    re.compile(r'[Сс]езон[\s._-]*(\d+).*?[Сс]ери[яи][\s._-]*(\d+)', re.IGNORECASE),
    re.compile(r'[Ss]eason[\s._-]*(\d+).*?[Ee]p(?:isode)?[\s._-]*(\d+)', re.IGNORECASE),
]
_SEASON_ONLY = re.compile(r'(?:[Ss]eason|[Сс]езон)[\s._-]*(\d+)', re.IGNORECASE)
_EP_ONLY     = re.compile(r'(?:[Ee]p(?:isode)?|[Сс]ери[яи])[\s._-]*(\d+)', re.IGNORECASE)
_TRAILING_NUM = re.compile(r'(?<![\d])\b(\d{1,2})\b[^\d]*(?:-[^\d].*)?$')  # «Title 3 - Source»


# ------------------------------------------------------------------
# Парсинг имён
# ------------------------------------------------------------------

def _parse_season_episode(name: str) -> Tuple[int, int]:
    """Извлечение номеров сезона и эпизода из строки имени файла.

    Args:
        name (str): Имя файла или папки.

    Returns:
        Tuple[int, int]: Номер сезона и эпизода; 0 если не найдено.

    Examples:
        >>> _parse_season_episode('Show.S02E05.mkv')
        (2, 5)
    """
    for pat in _EP_PATTERNS:
        m = pat.search(name)
        if m:
            return int(m.group(1)), int(m.group(2))
    s = _SEASON_ONLY.search(name)
    e = _EP_ONLY.search(name)
    return (int(s.group(1)) if s else 0, int(e.group(1)) if e else 0)


def _season_from_dir(dirname: str) -> int:
    """Извлечение номера сезона из имени директории.

    Args:
        dirname (str): Имя директории.

    Returns:
        int: Номер сезона или 0.

    Examples:
        >>> _season_from_dir('Season 3')
        3
        >>> _season_from_dir('The Blacklist 2 - LostFilm.TV [1080p]')
        2
    """
    m = _SEASON_ONLY.search(dirname)
    if m:
        return int(m.group(1))
    # Fallback: одиночное число в конце имени папки (до тире/скобки)
    # Например: «The Blacklist 2 - LostFilm.TV [1080p]» → 2
    stripped = re.sub(r'[\[\(].*', '', dirname).strip()  # убираем [1080p] и (год)
    m2 = re.search(r'\b(\d{1,2})\s*(?:-.*)?$', stripped)
    return int(m2.group(1)) if m2 else 0


# ------------------------------------------------------------------
# Сканирование
# ------------------------------------------------------------------

def _collect_episodes(series_dir: Path, series_title: str, scan_path: str) -> List[Dict]:
    """Рекурсивный сбор видеофайлов внутри папки сериала.

    Args:
        series_dir (Path): Корневая папка сериала.
        series_title (str): Название сериала (имя папки).
        scan_path (str): Путь сканирования верхнего уровня.

    Returns:
        List[Dict]: Список словарей с данными эпизодов.

    Examples:
        >>> eps = _collect_episodes(Path('D:/Series/Fauda'), 'Fauda', 'D:/Series')
    """
    episodes: List[Dict] = []
    for filepath in series_dir.rglob('*'):
        if not filepath.is_file() or filepath.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        season, episode = _parse_season_episode(filepath.name)
        if not season:
            season = _season_from_dir(filepath.parent.name)
        episodes.append({
            'series_title': series_title,
            'season': season or 0,
            'episode': episode or 0,
            'episode_title': '',
            'filepath': str(filepath),
            'filename': filepath.name,
            'size_mb': round(filepath.stat().st_size / 1_048_576, 2),
            'scan_path': scan_path,
        })
    return episodes


def scan(paths: List[Path]) -> List[Dict]:
    """Сканирование путей: папки верхнего уровня = сериалы, файлы = фильмы (игнор).

    Args:
        paths (List[Path]): Список корневых директорий для сканирования.

    Returns:
        List[Dict]: Список всех найденных эпизодов.

    Examples:
        >>> episodes = scan([Path('D:/Series'), Path('E:/Backup')])
    """
    all_episodes: List[Dict] = []
    for root in paths:
        if not root.exists():
            logger.warning(f'Путь не существует: {root}')
            continue
        logger.info(f'Сканирование: {root}')
        for entry in sorted(root.iterdir()):
            if _should_ignore(entry.name) or not entry.is_dir():
                continue
            episodes = _collect_episodes(entry, entry.name, str(root))
            logger.info(f'  {entry.name}: {len(episodes)} эп.')
            all_episodes.extend(episodes)
    return all_episodes


# ------------------------------------------------------------------
# Проверка дубликатов
# ------------------------------------------------------------------

def find_season_duplicates(db: MediaDatabase) -> List[Dict]:
    """Поиск сезонов одного сериала на нескольких разных путях сканирования.

    Args:
        db (MediaDatabase): Экземпляр базы данных.

    Returns:
        List[Dict]: Список дублей: series_title, season, locations.

    Examples:
        >>> dups = find_season_duplicates(db)
    """
    with sqlite3.connect(db.db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT series_title, season, scan_path, COUNT(*) as ep_count
            FROM series_episodes
            WHERE season > 0
            GROUP BY series_title, season, scan_path
            ORDER BY series_title, season
        """).fetchall()

    groups: Dict[Tuple, List[Dict]] = {}
    for r in rows:
        key = (r['series_title'], r['season'])
        groups.setdefault(key, []).append({'scan_path': r['scan_path'], 'ep_count': r['ep_count']})

    return [
        {'series_title': t, 'season': s, 'locations': locs}
        for (t, s), locs in groups.items()
        if len(locs) > 1
    ]


# ------------------------------------------------------------------
# Проверка целостности
# ------------------------------------------------------------------

def check_integrity(db: MediaDatabase) -> List[Dict]:
    """Сверка фактических данных series_episodes с эталоном из таблицы media.

    Проверка количества сезонов и серий в каждом сезоне.

    Args:
        db (MediaDatabase): Экземпляр базы данных.

    Returns:
        List[Dict]: Список несовпадений с полями type, series, season, expected, actual.

    Examples:
        >>> issues = check_integrity(db)
    """
    issues: List[Dict] = []
    with sqlite3.connect(db.db_path) as conn:
        conn.row_factory = sqlite3.Row
        media_rows = conn.execute("""
            SELECT title, количество_сезонов, количество_серий_в_каждом_сезоне
            FROM media
            WHERE type = 'series'
              AND (количество_сезонов IS NOT NULL OR количество_серий_в_каждом_сезоне IS NOT NULL)
        """).fetchall()

        for rec in media_rows:
            title: str = rec['title']
            expected_seasons: int = rec['количество_сезонов'] or 0
            raw_eps: str = rec['количество_серий_в_каждом_сезоне'] or ''
            expected_eps: List[int] = json.loads(raw_eps) if raw_eps else []

            actual = conn.execute("""
                SELECT season, COUNT(*) as ep_count
                FROM series_episodes
                WHERE series_title = ? AND season > 0
                GROUP BY season ORDER BY season
            """, (title,)).fetchall()

            if not actual:
                continue

            actual_seasons: int = len(actual)
            actual_map: Dict[int, int] = {r['season']: r['ep_count'] for r in actual}

            if expected_seasons and actual_seasons != expected_seasons:
                issues.append({
                    'type': 'seasons', 'series': title,
                    'expected': expected_seasons, 'actual': actual_seasons,
                })

            for idx, exp_ep in enumerate(expected_eps, start=1):
                act_ep: int = actual_map.get(idx, 0)
                if not act_ep:
                    issues.append({
                        'type': 'missing_season', 'series': title,
                        'season': idx, 'expected': exp_ep,
                    })
                elif act_ep != exp_ep:
                    issues.append({
                        'type': 'episodes', 'series': title,
                        'season': idx, 'expected': exp_ep, 'actual': act_ep,
                    })
    return issues


# ------------------------------------------------------------------
# Формирование отчёта
# ------------------------------------------------------------------

def build_report(duplicates: List[Dict], integrity_issues: List[Dict], output_path: Path) -> Path:
    """Формирование Markdown-отчёта по дубликатам и целостности.

    Args:
        duplicates (List[Dict]): Список дублей сезонов.
        integrity_issues (List[Dict]): Список нарушений целостности.
        output_path (Path): Путь для сохранения отчёта.

    Returns:
        Path: Путь к сохранённому файлу отчёта.

    Examples:
        >>> path = build_report(dups, issues, Path('reports/series_report.md'))
    """
    lines: List[str] = [
        '# Series Collector Report',
        f'_{datetime.now().strftime("%d.%m.%Y %H:%M")}_',
        '',
        f'## Season Duplicates ({len(duplicates)})',
    ]

    if duplicates:
        for d in duplicates:
            lines.append(f"\n### {d['series_title']} — Season {d['season']}")
            for loc in d['locations']:
                lines.append(f"- `{loc['scan_path']}` — {loc['ep_count']} ep.")
    else:
        lines.append('_No duplicates found._')

    lines.append(f'\n## Integrity Issues ({len(integrity_issues)})')
    if integrity_issues:
        for iss in integrity_issues:
            if iss['type'] == 'seasons':
                lines.append(f"- **{iss['series']}**: expected {iss['expected']} seasons, found {iss['actual']}")
            elif iss['type'] == 'missing_season':
                lines.append(f"- **{iss['series']}** Season {iss['season']}: missing (expected {iss['expected']} ep.)")
            else:
                lines.append(f"- **{iss['series']}** Season {iss['season']}: expected {iss['expected']} ep., found {iss['actual']}")
    else:
        lines.append('_No integrity issues found._')

    save_text_file('\n'.join(lines), output_path)
    return output_path


# ------------------------------------------------------------------
# Точка входа
# ------------------------------------------------------------------

def collect(paths: List[Path], db: MediaDatabase) -> int:
    """Сканирование путей и сохранение эпизодов в базу данных.

    Args:
        paths (List[Path]): Список директорий для сканирования.
        db (MediaDatabase): Экземпляр базы данных.

    Returns:
        int: Количество сохранённых эпизодов.

    Examples:
        >>> total = collect([Path('D:/Series')], db)
    """
    db.init_series_episodes()
    episodes = scan(paths)
    for ep in episodes:
        db.save_episode(ep)
    return len(episodes)
