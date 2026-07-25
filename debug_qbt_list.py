import sys
from pathlib import Path

# Добавляем корень проекта в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg

def list_torrents():
    try:
        cfg = _load_cfg()
        qbt_client = QBittorrentClient(
            host=cfg.host,
            port=int(cfg.port),
            username=cfg.username,
            password=cfg.password,
        )
        torrents = qbt_client.torrents()
        print(f"Всего торрентов: {len(torrents)}")
        for t in torrents[:10]: # Выведем первые 10 для примера
            print(f"Имя: {t['name']}, Путь: {t['save_path']}, Hash: {t['hash'][:10]}...")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    list_torrents()
