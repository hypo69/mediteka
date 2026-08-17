import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
root_dir = Path(r'C:\mediateka')
sys.path.append(str(root_dir))

from plugins.qbittorrent.qbittorrent import QBittorrentClient

def analyze_torrents_and_db():
    # Настройки подключения
    client = QBittorrentClient(host='127.0.0.1', port=9000, username='', password='')
    
    try:
        torrents = client.torrents()
        print(f"Найдено торрентов: {len(torrents)}")
        
        # Вывод краткой информации для анализа
        for t in torrents[:10]: # Ограничим вывод 10 торрентами для наглядности
            print(f"Hash: {t['hash']} | Name: {t['name']} | Path: {t['save_path']}")
            
    except Exception as e:
        print(f"Ошибка при подключении к qBittorrent: {e}")

if __name__ == '__main__':
    analyze_torrents_and_db()
