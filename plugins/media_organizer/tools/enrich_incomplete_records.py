# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Автоматическое дополнение данных для неполных записей
# =============================================================================
# Описание:
#   Скрипт находит записи в БД с незаполненными полями, запрашивает недостающую
#   информацию у Gemini и обновляет запись в базе.
#
# File: enrich_incomplete_records.py
# Project: gemini-simplechat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
from pathlib import Path

from src.ai import GoogleGenerativeAI
from plugins.media_organizer.core import MEDIA_DB, SYSTEM_INSTRUCTION
from plugins.media_organizer.core.database import MediaDatabase

async def enrich_record(db, ai, record):
    """Обогащение одной записи через Gemini."""
    title = record.get('title')
    media_type = record.get('media_type', 'movie')
    
    print(f"Обогащение: {title} ({media_type})...")
    
    prompt = f"Напиши подробную карточку (JSON) для {media_type}: '{title}'. Заполни все поля: plot, genres, atmosphere, rating, facts, similar, etc."
    
    # Запрос к Gemini
    response = await ai.ask(prompt)
    
    # Пытаемся извлечь JSON из ответа
    try:
        # Очистка от markdown блоков если есть
        content = response.replace('```json', '').replace('```', '').strip()
        data = json.loads(content)
        
        # Обновляем поля записи
        record.update(data)
        
        # Сохраняем в БД
        db.save_media(record['disk_name'], media_type, record)
        print(f"✅ Успешно обновлено: {title}")
        return True
    except Exception as e:
        print(f"❌ Ошибка обработки {title}: {e}")
        return False

async def main():
    db = MediaDatabase(MEDIA_DB)
    ai = GoogleGenerativeAI(system_instruction=SYSTEM_INSTRUCTION)
    
    # Получаем все записи
    records = db.export_all()
    
    # Критерии неполноты
    required_fields = ('plot', 'main_category')
    
    incomplete = [r for r in records if not all(r.get(f) for f in required_fields)]
    
    print(f"Всего записей: {len(records)}, Неполных: {len(incomplete)}")
    
    # Обработаем все неполные записи
    to_process = incomplete
    
    for rec in to_process:
        await enrich_record(db, ai, rec)
        # Небольшая пауза между запросами
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
