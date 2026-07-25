import os
import subprocess
from pathlib import Path
from src.logger import logger

def get_connected_drives_string() -> str:
    """Сканирует подключенные диски и возвращает их в виде строки."""
    ps_cmd = "(Get-PSDrive -PSProvider FileSystem | Where-Object { $_.DisplayRoot -ne $null -or $_.Name -ne 'C' } | Select-Object -ExpandProperty Root) -join ','"
    try:
        result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Ошибка при сканировании дисков: {e}")
        return ""

def update_environment_drives():
    """Обновляет переменную окружения CONNECTED_DRIVES."""
    drives = get_connected_drives_string()
    os.environ['CONNECTED_DRIVES'] = drives
    logger.info(f"Актуальные диски обновлены в окружении: {drives}")
    return drives

if __name__ == '__main__':
    update_environment_drives()
