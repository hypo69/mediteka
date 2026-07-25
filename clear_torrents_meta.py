#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Очистка метаданных торрентов (Категории и Метки)
# =============================================================================
# Описание:
#   Скрипт удаляет категории и все метки у всех торрентов в qBittorrent.
#
# File: clear_torrents_meta.py
# Project: gemini-simplechat
# =============================================================================

import sys
from pathlib import Path

# Добавляем корень проекта в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg

def main():
    print("=== Очистка метаданных торрентов ===")
    
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

    # Получение списка торрентов
    try:
        torrents = qbt_client.torrents()
    except Exception as e:
        print(f"❌ Ошибка получения списка торрентов: {e}")
        return 1
    
    if not torrents:
        print("ℹ Торренты не найдены.")
        return 0
    
    print(f"Найдено торрентов: {len(torrents)}")
    print("Запуск очистки категорий и меток...")
    
    cleared_count = 0
    error_count = 0
    
    for t in torrents:
        tid = t['hash']
        name = t['name']
        
        try:
            # Очистка категории
            if t.get('category'):
                qbt_client.set_category(tid, "")
            
            # Очистка меток
            tags_str = t.get('tags', '')
            if tags_str:
                # Метки в qBittorrent приходят строкой через запятую
                tags_list = [tag.strip() for tag in tags_str.split(',')]
                if tags_list:
                    qbt_client.remove_tags(tid, ",".join(tags_list))
            
            print(f"   ✅ Очищено: {name}")
            cleared_count += 1
        except Exception as e:
            print(f"   ❌ Ошибка для {name}: {e}")
            error_count += 1
    
    print(f"\n=== Итоги ===")
    print(f"Очищено торрентов: {cleared_count}")
    print(f"Ошибок: {error_count}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
