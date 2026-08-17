import sys
import sqlite3
from pathlib import Path

# Добавляем корень проекта в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg

DB_PATH = Path(r"C:\mediateka\plugins\media_organizer\data\media.db")

def force_update_torrents():
    print("=== Принудительное обновление путей торрентов ===")
    
    # Инициализация qBittorrent
    try:
        cfg = _load_cfg()
        qbt_client = QBittorrentClient(
            host=cfg.host,
            port=int(cfg.port),
            username=cfg.username,
            password=cfg.password,
        )
        print("✅ Клиент qBittorrent подключен")
    except Exception as e:
        print(f"❌ Ошибка подключения к qBittorrent: {e}")
        return

    # Загрузка базы данных
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Берем уникальные пути для сериалов, перенесенных в Y:\сериалы
    cursor.execute("SELECT path FROM media WHERE path LIKE 'Y:\сериалы\%' GROUP BY path")
    rows = cursor.fetchall()
    
    # Получение списка торрентов из qBittorrent
    torrents = qbt_client.torrents()
    
    for row in rows:
        db_path = row[0]
        series_name = Path(db_path).name
        print(f"\nПроверка: {series_name} -> {db_path}")
        
        # Ищем торрент
        for t in torrents:
            if t['name'] == series_name:
                print(f"   Нашел торрент: {t['name']} (Hash: {t['hash'][:10]}...)")
                if t['save_path'] != db_path:
                    print(f"   Обновляю путь: {t['save_path']} -> {db_path}")
                    qbt_client.set_location(t['hash'], str(db_path))
                else:
                    print(f"   Путь уже корректен.")
                break
    
    conn.close()
    print("\n=== Обновление завершено ===")

if __name__ == '__main__':
    force_update_torrents()
