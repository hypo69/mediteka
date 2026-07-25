# -*- coding: utf-8 -*-
import asyncio
import json
from src.ai import GoogleGenerativeAI
from plugins.media_organizer.core import SYSTEM_INSTRUCTION
from pathlib import Path

async def get_series_info(ai, title):
    print(f"--- Получение общей информации для: {title} ---")
    prompt = f"Напиши общую информацию о сериале '{title}': название, жанры, страна, год, краткий сюжет (plot_summary_total), общее количество сезонов."
    response = await ai.ask(prompt)
    # Очистка и парсинг
    return json.loads(response.replace('```json', '').replace('```', '').strip())

async def get_season_info(ai, title, season_number):
    print(f"--- Получение данных для сезона {season_number} ---")
    prompt = f"""Напиши максимально подробную карточку для {season_number}-го сезона сериала '{title}'.
Для КАЖДОГО эпизода напиши длинное, детализированное описание (не менее 100 слов), глубокий анализ сюжетной арки, раскрытие характера персонажей, ключевые диалоги и последствия.
Формат JSON:
{{
    "season_number": {season_number},
    "season_plot_summary": "...",
    "final_verdict": "...",
    "episodes": [
        {{ 
            "episode_number": 1, 
            "title": "...", 
            "detailed_description": "...", 
            "character_arcs": "...",
            "final_verdict": "..." 
        }},
        ...
    ]
}}
"""
    response = await ai.ask(prompt)
    return json.loads(response.replace('```json', '').replace('```', '').strip())

async def generate_complete_card(title: str):
    ai = GoogleGenerativeAI(system_instruction=SYSTEM_INSTRUCTION)
    
    # 1. Общая инфа
    series_card = await get_series_info(ai, title)
    num_seasons = series_card.get('num_of_seasons', 6)
    
    series_card['seasons'] = []
    
    # 2. Итеративно по сезонам
    for i in range(1, num_seasons + 1):
        season_data = await get_season_info(ai, title, i)
        series_card['seasons'].append(season_data)
        
    print(json.dumps(series_card, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(generate_complete_card("Острые козырьки"))
