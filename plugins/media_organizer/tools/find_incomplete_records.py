# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Поиск записей с незаполненными полями
# =============================================================================
# Описание:
#   Скрипт проверяет таблицу `media` на наличие записей, где ключевые поля
#   (title, plot, main_category) пустые или отсутствуют.
#
# File: find_incomplete_records.py
# Project: gemini-simplechat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from pathlib import Path
from plugins.media_organizer.core import MEDIA_DB
from plugins.media_organizer.core.database import MediaDatabase
from src.utils.printer import pprint

def find_incomplete():
    db = MediaDatabase(MEDIA_DB)
    records = db.export_all()
    
    incomplete = []
    
    # Поля, которые считаем обязательными для полноты (согласно database.py)
    required_fields = ('title', 'plot', 'main_category')
    
    for rec in records:
        is_missing = False
        missing_fields = []
        for field in required_fields:
            if not rec.get(field):
                is_missing = True
                missing_fields.append(field)
        
        if is_missing:
            incomplete.append({
                'id': rec.get('id'),
                'title': rec.get('title'),
                'disk_name': rec.get('disk_name'),
                'missing': missing_fields
            })
            
    print(f"Найдено записей с незаполненными полями: {len(incomplete)}")
    pprint(incomplete[:10]) # Выведем первые 10 для примера
    
    return incomplete

if __name__ == '__main__':
    find_incomplete()
