#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Синхронизация путей торрентов с БД
# =============================================================================
# Описание:
#   Скрипт обновляет пути сохранения торрентов в qBittorrent, основываясь
#   на путях, указанных в базе данных медиатеки.
#
# File: update_torrents_path.py
# Project: mediteka
# =============================================================================

import sys
import sqlite3
from pathlib import Path

# Добавляем корень проекта в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from plugins.media_organizer.core.database import MediaDatabase
from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg

MEDIA_DB = Path(__file__).parent / 'plugins' / 'media_organizer' / 'data' / 'media.db'

def main():
    print("=== Синхронизация путей торрентов ===")
    
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
        return 1

    # Загрузка базы данных
    db = MediaDatabase(MEDIA_DB)
    records = db.export_all()
    
    # Получение списка торрентов из qBittorrent
    try:
        torrents = qbt_client.torrents()
        torrents_map = {t['hash']: t for t in torrents}
    except Exception as e:
        print(f"❌ Ошибка получения списка торрентов: {e}")
        return 1

    updated = 0
    errors = 0

    print("Начинаю проверку путей...")
    for rec in records:
        torrent_id = rec.get('torrent_id')
        db_path = rec.get('path')
        
        if not torrent_id or not db_path:
            continue
        
        if torrent_id not in torrents_map:
            continue
            
        torrent = torrents_map[torrent_id]
        current_save_path = torrent.get('save_path', '')
        # Ожидаемый путь сохранения — родительская папка медиа-файла
        expected_save_path = str(Path(db_path).parent)
        
        # Сравниваем пути (с учетом возможных различий в слешах)
        if Path(current_save_path) != Path(expected_save_path):
            print(f"🔄 Обновление пути: {torrent['name']}")
            print(f"   Было: {current_save_path}")
            print(f"   Стало: {expected_save_path}")
            try:
                qbt_client.set_location(torrent_id, expected_save_path)
                updated += 1
            except Exception as e:
                print(f"   ❌ Ошибка обновления: {e}")
                errors += 1
    
    print(f"\n=== Итоги ===")
    print(f"Обновлено путей: {updated}")
    print(f"Ошибок: {errors}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
