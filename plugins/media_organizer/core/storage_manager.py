# -*- coding: utf-8 -*-
import json
import os
from pathlib import Path
from src.logger import logger

STORAGE_CONFIG = Path(__file__).parent.parent / 'data' / 'storage_config.json'
ACTIVE_STORAGE_FILE = Path(__file__).parent.parent / 'data' / 'active_storage.json'


def scan_and_save_active_storage() -> list:
    """Сканирует диски из конфига и сохраняет доступные пути в JSON.

    Returns:
        list: Список путей к доступным хранилищам.
    """
    if not STORAGE_CONFIG.exists():
        logger.error(f"Файл конфигурации хранилищ не найден: {STORAGE_CONFIG}")
        return []

    with open(STORAGE_CONFIG, 'r', encoding='utf-8') as f:
        disk_map = json.load(f)

    active_paths = []
    for disk_name, path in disk_map.items():
        if os.path.exists(path):
            active_paths.append(path)
            logger.info(f"Хранилище доступно: {disk_name} -> {path}")
        else:
            logger.warning(f"Хранилище недоступно: {disk_name} -> {path}")

    with open(ACTIVE_STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(active_paths, f, ensure_ascii=False, indent=2)

    # Также обновляем переменную окружения для совместимости
    os.environ['CONNECTED_DRIVES'] = ','.join(p.rstrip('\\') for p in active_paths)

    logger.info(f"Активных хранилищ: {len(active_paths)} из {len(disk_map)}: {active_paths}")
    return active_paths


def load_active_storage() -> list:
    """Загружает список путей доступных хранилищ.

    Returns:
        list: Список путей к доступным хранилищам.
    """
    if not ACTIVE_STORAGE_FILE.exists():
        return []

    with open(ACTIVE_STORAGE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
