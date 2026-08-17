import json
import os
from pathlib import Path
from src.logger import logger

STORAGE_CONFIG = Path(r'plugins/media_organizer/data/storage_config.json')
ACTIVE_STORAGE_FILE = Path(r'plugins/media_organizer/data/active_storage.json')

def sync_active_storage():
    """Синхронизирует конфиг хранилищ с фактически подключенными дисками."""
    if not STORAGE_CONFIG.exists():
        logger.error(f"Файл конфигурации хранилищ не найден: {STORAGE_CONFIG}")
        return

    # Получаем список подключенных дисков из переменной окружения
    connected_drives_str = os.environ.get('CONNECTED_DRIVES', '')
    connected_drives = [d.strip().rstrip('\\') for d in connected_drives_str.split(',') if d.strip()]
    
    with open(STORAGE_CONFIG, 'r', encoding='utf-8') as f:
        disk_map = json.load(f)

    active_disks = []
    for disk_name, path in disk_map.items():
        # Сравниваем пути без завершающего слэша (например, 'S:' == 'S:')
        drive_letter = path.strip().rstrip('\\')
        if drive_letter in connected_drives:
            active_disks.append(disk_name)
    
    with open(ACTIVE_STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(active_disks, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Актуальные хранилища синхронизированы: {active_disks}")
    return active_disks

if __name__ == '__main__':
    # Для теста/запуска через командную строку
    # Имитация переменной окружения для отладки, если не задана
    if 'CONNECTED_DRIVES' not in os.environ:
        import subprocess
        # Получаем диски через powershell, если переменная не задана
        ps_cmd = "(Get-PSDrive -PSProvider FileSystem | Where-Object { $_.DisplayRoot -ne $null -or $_.Name -ne 'C' } | Select-Object -ExpandProperty Root) -join ','"
        result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True)
        os.environ['CONNECTED_DRIVES'] = result.stdout.strip()
        
    sync_active_storage()
