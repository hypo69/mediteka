#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Назначение категорий торрентам из БД
# =============================================================================
# Описание:
#   Скрипт сопоставляет торренты с медиа-записями из БД по названию
#   и устанавливает соответствующие категории в qBittorrent.
#
# File: assign_categories.py
# Project: gemini-simplechat
# =============================================================================

import sys
from pathlib import Path

# Добавляем корень проекта в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from plugins.media_organizer.core.database import MediaDatabase
from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg, _token_overlap

MEDIA_DB = Path(__file__).parent / 'plugins' / 'media_organizer' / 'data' / 'media.db'

def main():
    print("=== Назначение категорий торрентам ===")
    
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
    try:
        db = MediaDatabase(MEDIA_DB)
        records = db.export_all()
        # Фильтруем записи, у которых есть категория
        media_with_cats = [r for r in records if r.get('main_category')]
        print(f"✅ Загружено {len(media_with_cats)} записей с категориями из БД")
    except Exception as e:
        print(f"❌ Ошибка загрузки БД: {e}")
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
    print("Запуск назначения категорий...")
    
    assigned_count = 0
    error_count = 0
    threshold = 0.5  # Порог уверенности для fuzzy-матчинга
    
    for t in torrents:
        tid = t['hash']
        name = t['name']
        
        # Поиск лучшего совпадения в БД
        best_score = 0.0
        best_cat = None
        
        for rec in media_with_cats:
            score = _token_overlap(name, rec['title'])
            if score > best_score:
                best_score = score
                best_cat = rec['main_category']
        
        if best_score >= threshold and best_cat:
            try:
                qbt_client.create_category(best_cat)
                qbt_client.set_category(tid, best_cat)
                print(f"   ✅ {name} -> {best_cat} (score={best_score:.2f})")
                assigned_count += 1
            except Exception as e:
                print(f"   ❌ Ошибка для {name}: {e}")
                error_count += 1
        else:
            print(f"   ❓ {name} (нет совпадений, score={best_score:.2f})")
            
    print(f"\n=== Итоги ===")
    print(f"Назначено категорий: {assigned_count}")
    print(f"Ошибок: {error_count}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
