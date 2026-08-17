#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Принудительная проверка торрентов (Force Recheck)
# =============================================================================
# Описание:
#   Скрипт запускает "принудительную проверку" (Force Recheck) для всех
#   торрентов, у которых установлен torrent_id в базе данных медиатеки.
#
# File: update_torrent_state.py
# Project: mediteka
# =============================================================================

import sys
from pathlib import Path

# Добавляем корень проекта в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from plugins.media_organizer.core.database import MediaDatabase
from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg

MEDIA_DB = Path(__file__).parent / 'plugins' / 'media_organizer' / 'data' / 'media.db'

def main():
    print("=== Принудительная проверка торрентов (Force Recheck) ===")
    
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
    
    # Сбор всех уникальных torrent_id
    torrent_ids = {r.get('torrent_id') for r in records if r.get('torrent_id')}
    
    if not torrent_ids:
        print("ℹ В базе данных нет торрентов с привязанными ID.")
        return 0
    
    print(f"Найдено торрентов в БД: {len(torrent_ids)}")
    print("Запуск принудительной проверки...")
    
    success_count = 0
    error_count = 0
    
    for tid in torrent_ids:
        try:
            qbt_client.recheck(tid)
            print(f"   ✅ Запущено: {tid}")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Ошибка для {tid}: {e}")
            error_count += 1
    
    print(f"\n=== Итоги ===")
    print(f"Запущено проверок: {success_count}")
    print(f"Ошибок: {error_count}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
