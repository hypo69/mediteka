import sqlite3
import json
import sys
from pathlib import Path

# Добавляем корень проекта для доступа к qBittorrent
sys.path.insert(0, str(Path(__file__).parent))
from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg

DB_PATH = Path(r"C:\mediateka\plugins\media_organizer\data\media.db")

def run_audit_and_update():
    print("--- 1. Загрузка данных из qBittorrent ---")
    cfg = _load_cfg()
    qbt_client = QBittorrentClient(
        host=cfg.host,
        port=int(cfg.port),
        username=cfg.username,
        password=cfg.password,
    )
    torrents = qbt_client.torrents()
    # Создаем карту: имя торрента -> размер
    torrent_map = {t['name']: t['size'] for t in torrents}
    
    print("--- 2. Сканирование файлов и обновление БД ---")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем все записи из БД
    cursor.execute("SELECT id, path FROM media")
    rows = cursor.fetchall()
    
    for row in rows:
        db_id, db_path = row
        file_path = Path(db_path)
        
        if file_path.exists():
            actual_size = file_path.stat().st_size
            
            # Попробуем найти соответствующий торрент (по имени папки или файла)
            # Это упрощенный поиск, так как в БД может быть путь к файлу, а в торренте - имя папки
            torrent_size = None
            for name, size in torrent_map.items():
                if name in str(file_path):
                    torrent_size = size
                    break
            
            size_delta = 0
            if torrent_size:
                size_delta = actual_size - torrent_size
            
            cursor.execute(
                "UPDATE media SET actual_size = ?, size_delta = ? WHERE id = ?",
                (actual_size, size_delta, db_id)
            )
    
    conn.commit()
    conn.close()
    print("--- Аудит и обновление БД завершены ---")

if __name__ == '__main__':
    run_audit_and_update()
