# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Интеллектуальное сопоставление медиа-файлов с торрентами
# =============================================================================
# Описание:
#   Модуль для точного сопоставления медиа-файлов из БД с торрентами в qBittorrent.
#   
#   Алгоритм:
#   1. Загружает список торрентов (из torrents_data.json)
#   2. Получает список медиа-файлов из базы данных (фильмы, сериалы)
#   3. Разбивает медиа-файлы на батчи и отправляет в AI
#   4. AI возвращает JSON сопоставления: медиа -> торрент
#   5. Обновляет torrent_id в базе и пути в qBittorrent
#
# File: assign_torrents_ids.py
# Project: gemini-simplechat
# Package: plugins.media_organizer.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from src.logger import logger
from plugins.media_organizer.core.database import MediaDatabase
from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg

# Пути к файлам
TORRENTS_DATA_FILE = Path(__file__).parent.parent / 'config' / 'torrents_data.json'
MEDIA_DB = Path(__file__).parent.parent / 'data' / 'media.db'
BATCH_SIZE = 10  # Оптимальный размер батча для контекста

# =============================================================================
# DATA FETCHING
# =============================================================================

def fetch_media_from_db(db_path: Path) -> Dict:
    """Получает медиа-файлы из базы данных."""
    db = MediaDatabase(db_path)
    all_media = db.export_all()
    
    result = {'movies': [], 'series': []}
    
    for item in all_media:
        if item.get('num_of_seasons', 0) > 0:
            result['series'].append(item)
        else:
            result['movies'].append(item)
            
    return result

# =============================================================================
# JSON CONSTRUCTION
# =============================================================================

def build_media_json(media_files: Dict) -> List[Dict]:
    """Строит компактную JSON-структуру для медиа-файлов."""
    result = []
    
    for item in media_files.get('movies', []) + media_files.get('series', []):
        result.append({
            'type': 'series' if item.get('num_of_seasons', 0) > 0 else 'movie',
            'name': item.get('title', 'Unknown'),
            'path': item.get('path', ''),
            'size': item.get('media_size', 0),
        })
    return result

def build_torrents_json(torrents_data: Dict) -> List[Dict]:
    """Строит компактную JSON-структуру для торрентов."""
    result = []
    # Исправленное регулярное выражение: флаг (?i) в начале
    pattern = re.compile(r'(?i)[Ss]\d{2}|[Ee]\d{2,3}|season|серия')
    
    for t in torrents_data.get('torrents', []):
        name = t.get('name', '')
        result.append({
            'type': 'series' if pattern.search(name) else 'movie',
            'name': name,
            'size': t.get('size', 0),
        })
    return result

# =============================================================================
# AI INTEGRATION (Оптимизированная)
# =============================================================================

async def ask_ai_for_matching(ai_model, torrents_json: List[Dict], media_chunk: List[Dict]) -> Dict:
    """Отправляет в AI запрос на сопоставление батча медиа-файлов."""
    
    # Компактный JSON для экономии токенов
    prompt = f"""Сопоставь медиа-файлы (из БД) с торрентами.
Верни ТОЛЬКО JSON: {{"matches": [{{"media_path": "...", "torrent_hash": "..."}}]}}

Торренты: {json.dumps(torrents_json, separators=(',', ':'))}
Медиа (Батч): {json.dumps(media_chunk, separators=(',', ':'))}
"""
    response = await ai_model.ask(prompt)
    
    # Парсинг ответа
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return {'matches': [], 'mismatches': [], 'series_redirects': [], 'incomplete_episodes': []}

# =============================================================================
# DATABASE UPDATES
# =============================================================================

def update_database(db: MediaDatabase, matching_result: Dict, qbt_client=None, torrents_sources: Dict = {}) -> Dict:
    """Обновляет базу данных и qBittorrent."""
    results = {'matched': 0, 'redirected': 0, 'started_downloads': 0, 'errors': []}
    
    for match in matching_result.get('matches', []):
        try:
            torrent_hash = match['torrent_hash']
            torrent_src = torrents_sources.get(torrent_hash, "")
            db.update_torrent_id(match['media_path'], torrent_hash, torrent_src)
            results['matched'] += 1
            
            if qbt_client:
                # Определяем новую папку как родительскую папку медиа-файла
                new_location = str(Path(match['media_path']).parent)
                qbt_client.set_location(torrent_hash, new_location)
                results['redirected'] += 1
                
        except Exception as e:
            results['errors'].append(str(e))
    
    return results

# =============================================================================
# MAIN FUNCTION
# =============================================================================

async def assign_torrent_ids(ai_model, disk_paths: List[Path], db_path: Path = MEDIA_DB, torrents_file: Path = TORRENTS_DATA_FILE) -> Dict:
    """Основная функция с батчингом."""
    with open(torrents_file, 'r', encoding='utf-8') as f:
        torrents_data = json.load(f)
    
    # Инициализация qBittorrent
    qbt_client = ""
    try:
        cfg = _load_cfg()
        qbt_client = QBittorrentClient(
            host=cfg.host,
            port=int(cfg.port),
            username=cfg.username,
            password=cfg.password,
        )
    except Exception as e:
        logger.error(f"Не удалось инициализировать qBittorrent: {e}")
    
    # Собираем информацию об источниках торрентов
    torrents_sources = {}
    if qbt_client:
        try:
            for t in qbt_client.torrents():
                h = t.get("hash", "")
                if h:
                    src = t.get("comment", "")
                    if not src:
                        src = t.get("tracker", "")
                    torrents_sources[h] = src
        except Exception as e:
            logger.error(f"Не удалось получить информацию об источниках торрентов: {e}")
    
    media_files = fetch_media_from_db(db_path)
    torrents_json = build_torrents_json(torrents_data)
    media_json = build_media_json(media_files)
    
    final_results = {'matched': 0, 'redirected': 0, 'started_downloads': 0, 'errors': []}
    db = MediaDatabase(db_path)
    
    # Батчинг
    for i in range(0, len(media_json), BATCH_SIZE):
        batch = media_json[i:i + BATCH_SIZE]
        matching_result = await ask_ai_for_matching(ai_model, torrents_json, batch)
        
        # Обновление результатов
        results = update_database(db, matching_result, qbt_client=qbt_client, torrents_sources=torrents_sources)
        
        for k in ['matched', 'redirected', 'started_downloads']:
            final_results[k] += results[k]
        final_results['errors'].extend(results['errors'])
        
        logger.info(f"Обработано {i+len(batch)}/{len(media_json)} медиа-файлов")
        
    return final_results
