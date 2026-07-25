import json
import os
from pathlib import Path
from src.logger import logger

STORAGE_CONFIG = Path(__file__).parent.parent / 'data' / 'storage_config.json'
ACTIVE_STORAGE_FILE = Path(__file__).parent.parent / 'data' / 'active_storage.json'

def scan_and_save_active_storage():
    """Сканирует диски из конфига и сохраняет доступные в JSON."""
    if not STORAGE_CONFIG.exists():
        logger.error(f"Файл конфигурации хранилищ не найден: {STORAGE_CONFIG}")
        return

    with open(STORAGE_CONFIG, 'r', encoding='utf-8') as f:
        disk_map = json.load(f)

    active_disks = []
    for disk_name, path in disk_map.items():
        if os.path.exists(path):
            active_disks.append(disk_name)
    
    with open(ACTIVE_STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(active_disks, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Актуальные хранилища сохранены: {active_disks}")

def load_active_storage():
    """Загружает список доступных дисков."""
    if not ACTIVE_STORAGE_FILE.exists():
        return []
    
    with open(ACTIVE_STORAGE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
