import sqlite3
import sys
from pathlib import Path

# Добавляем корень проекта для доступа к qBittorrent
sys.path.insert(0, str(Path(__file__).parent))
from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg

DB_PATH = Path(r"C:\mediateka\plugins\media_organizer\data\media.db")

def analyze_completed_torrents():
    print("--- Анализ 100% загруженных торрентов ---")
    
    cfg = _load_cfg()
    qbt_client = QBittorrentClient(
        host=cfg.host,
        port=int(cfg.port),
        username=cfg.username,
        password=cfg.password,
    )
    
    # Получаем торренты
    torrents = qbt_client.torrents()
    # Фильтруем завершенные (progress == 1.0)
    completed_torrents = [t for t in torrents if t.get('progress', 0) == 1.0]
    torrent_map = {t['name']: t for t in completed_torrents}
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Найдено {len(completed_torrents)} завершенных торрентов.")
    
    problematic_files = []
    
    for name, t in torrent_map.items():
        # Ищем записи в БД для этого торрента
        cursor.execute("SELECT path, actual_size, size_delta FROM media WHERE path LIKE ?", (f"%{name}%",))
        rows = cursor.fetchall()
        
        for path, actual_size, delta in rows:
            if actual_size is None:
                problematic_files.append((name, path, "Файл не найден на диске"))
            elif delta != 0:
                problematic_files.append((name, path, f"Дельта размера: {delta} байт"))
    
    conn.close()
    
    if problematic_files:
        print(f"\nНайдено {len(problematic_files)} проблемных файлов для 100% торрентов:")
        for name, path, issue in problematic_files[:20]: # Выведем первые 20
            print(f"  [{name}] {path} -> {issue}")
        
        # Сохраним полный список
        with open("completed_torrent_issues.txt", "w", encoding="utf-8") as f:
            for item in problematic_files:
                f.write(f"{item[0]} | {item[1]} | {item[2]}\n")
        print("\nПолный список сохранен в completed_torrent_issues.txt")
    else:
        print("\nПроблемных файлов для 100% торрентов не найдено.")

if __name__ == '__main__':
    analyze_completed_torrents()
