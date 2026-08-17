import os
import json
import sys
from pathlib import Path

# Добавляем корень проекта для доступа к qBittorrent
sys.path.insert(0, str(Path(__file__).parent))
from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg

def get_disk_files(drives):
    file_sizes = {}
    for drive in drives:
        root = Path(f"{drive}:\\")
        if not root.exists():
            print(f"Диск {drive} не найден, пропускаю.")
            continue
        print(f"Сканирование диска {drive}...")
        for path in root.rglob('*'):
            if path.is_file() and path.suffix.lower() in ['.mkv', '.avi', '.mp4', '.mov']:
                file_sizes[str(path)] = path.stat().st_size
    return file_sizes

def get_torrent_files():
    cfg = _load_cfg()
    qbt_client = QBittorrentClient(
        host=cfg.host,
        port=int(cfg.port),
        username=cfg.username,
        password=cfg.password,
    )
    torrents = qbt_client.torrents()
    torrent_data = {}
    for t in torrents:
        # Для простоты берем имя и общий размер, 
        # полноценная сверка по файлам внутри торрента требует вызова get_torrent_files(hash)
        torrent_data[t['name']] = t['size']
    return torrent_data

def run_audit():
    drives = ['R', 'Y', 'T', 'X']
    
    print("--- Сбор данных о файлах на дисках ---")
    file_map = get_disk_files(drives)
    
    print("--- Сбор данных из qBittorrent ---")
    torrent_map = get_torrent_files()
    
    # Здесь логика сравнения. 
    # ВАЖНО: Прямое сравнение размера файла на диске с размером ВСЕГО торрента некорректно,
    # если в торренте много файлов.
    # Для глубокого аудита нужно сопоставлять файлы внутри торрента.
    
    print(f"\nВсего найдено файлов медиа: {len(file_map)}")
    print(f"Всего торрентов в клиенте: {len(torrent_map)}")
    
    # Сохраним в JSON для дальнейшего анализа
    with open('audit_results.json', 'w', encoding='utf-8') as f:
        json.dump({'files': file_map, 'torrents': torrent_map}, f, indent=2, ensure_ascii=False)
    print("\nРезультаты сохранены в audit_results.json")

if __name__ == '__main__':
    run_audit()
