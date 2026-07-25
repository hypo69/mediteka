# -*- coding: utf-8 -*-
import sqlite3
import os
import shutil
import json
from plugins.plugin import BasePlugin
from src.logger import logger

class RemoveMediaPlugin(BasePlugin):
    """Плагин для безопасного удаления медиа-контента."""

    name = 'remove_media'

    def __init__(self, ai_model) -> None:
        super().__init__(ai_model)
        self.db_path = r'plugins\media_organizer\data\media.db'
        self.config_path = r'plugins\media_organizer\config\torrents_names.json.md'

    async def _handle(self, message: str) -> str:
        if not message.startswith('удалить медиа'):
            return ''
        
        # Пример команды: "удалить медиа [id или путь]"
        parts = message.split(maxsplit=2)
        if len(parts) < 3:
            return 'Укажите ID или путь к медиа для удаления.'
        
        target = parts[2]
        
        # 1. Поиск
        media_records = self._find_media(target)
        if not media_records:
            return f'Медиа не найдено: {target}'
        
        # 2. Dry-run (для безопасности можно требовать подтверждение в будущем)
        # В этой версии выполняем удаление сразу после поиска
        
        # 3. Удаление
        return self._perform_deletion(media_records)

    def _find_media(self, target: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ищем по ID (число) или по пути
        if target.isdigit():
            cursor.execute('SELECT id, title, path FROM media WHERE id = ?', (target,))
        else:
            cursor.execute('SELECT id, title, path FROM media WHERE path = ?', (target,))
            
        records = cursor.fetchall()
        conn.close()
        return records

    def _perform_deletion(self, records):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        results = []
        for media_id, title, path in records:
            # Удаление физических файлов
            if path and os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            
            # Удаление записей (включая связанные)
            cursor.execute('DELETE FROM media WHERE id = ?', (media_id,))
            cursor.execute('DELETE FROM media WHERE parent_id = ?', (media_id,))
            
            results.append(f'Удалено: {title} (ID: {media_id})')
            
        conn.commit()
        conn.close()
        
        return '\n'.join(results)
