# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Модуль отслеживания медиа-файлов и путей
# =============================================================================
# Описание:
#   Модуль для работы с путями к медиа, загрузки путей из конфига,
#   фильтрации путей по дискам и нормализации имён дисков.
#
# File: media_tracker.py
# Project: gemini-simplechat
# Package: plugins.media_organizer.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from pathlib import Path
from typing import List, Optional
from header import __root__


def load_media_paths(filepath: Optional[Path] = None) -> List[Path]:
    """Возвращает пути к медиа-дискам (сериалы и фильмы в корне проекта).
    
    Args:
        filepath: Не используется, сохранено для обратной совместимости.
        
    Returns:
        List[Path]: Список путей к папкам медиа.
    """
    return [__root__ / 'сериалы', __root__ / 'фильмы']


def _filter_paths_by_disk(paths: List[Path], disk_name: str) -> List[Path]:
    """Фильтрует пути по имени диска.
    
    Args:
        paths: Список путей к медиа.
        disk_name: Имя диска для фильтрации (например, "1", "2", "FILMS").
        
    Returns:
        List[Path]: Отфильтрованный список путей.
    """
    normalized_disk = disk_name.lower().strip()
    
    import re
    suffix_match = re.match(r'(?:диск|disk)\s+(.+)', normalized_disk)
    clean_suffix = suffix_match.group(1).strip() if suffix_match else normalized_disk
    
    result = []
    
    for path in paths:
        path_str = str(path).lower()
        # Проверяем, содержит ли путь имя диска, его нормализованную форму или очищенный суффикс
        if normalized_disk in path_str or str(disk_name) in str(path) or clean_suffix in path_str:
            result.append(path)
    
    # Если не найдено совпадений, возвращаем первый путь (если есть)
    # Это позволяет использовать один путь для нескольких дисков при необходимости
    if not result and paths:
        result = paths[:1]
    
    return result


def _normalize_disk_name(name: str) -> str:
    """Нормализует имя диска для консистентного использования.
    
    Args:
        name: Исходное имя диска (например, "диск 1", "Disk 2", "FILMS").
        
    Returns:
        str: Нормализованное имя диска (например, "ДИСК 1").
    """
    # Нормализуем регистр и убираем лишние пробелы
    normalized = name.strip()
    # Если начинается с "диск" или "disk", сохраняем суффикс
    import re
    match = re.match(r'(?:диск|disk)\s*(.+)', normalized, re.IGNORECASE)
    if match:
        val = match.group(1).strip()
        return f"ДИСК {val}"
    return normalized
