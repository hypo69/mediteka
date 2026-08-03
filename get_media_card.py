# -*- coding: utf-8 -*-
import asyncio
import json
import sys
import sqlite3
import ssl
from pathlib import Path
from src.ai import GoogleGenerativeAI
from plugins.media_organizer.core import SYSTEM_INSTRUCTION, MEDIA_DB
from plugins.media_organizer.core.database import MediaDatabase

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import certifi
import httpx
try:
    os.environ['SSL_CERT_FILE'] = certifi.where()
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # Monkey-patch httpx to bypass certificate verification
    orig_client_init = httpx.Client.__init__
    httpx.Client.__init__ = lambda self, *a, **k: orig_client_init(self, *a, **{**k, 'verify': False})
    
    orig_async_client_init = httpx.AsyncClient.__init__
    httpx.AsyncClient.__init__ = lambda self, *a, **k: orig_async_client_init(self, *a, **{**k, 'verify': False})
except Exception:
    pass

db = MediaDatabase(MEDIA_DB)

def find_local_media(title: str):
    """Поиск записи в локальной БД по названию."""
    if not MEDIA_DB.exists():
        return None
    with sqlite3.connect(MEDIA_DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """SELECT * FROM media 
               WHERE (LOWER(title) = ? OR LOWER(title_ru) = ? OR LOWER(title_orig) = ?) 
               AND media_type IN ('movie', 'series', 'serial', 'Фильм', 'Сериал') 
               LIMIT 1""",
            (title.lower(), title.lower(), title.lower())
        ).fetchone()
        if row:
            return db._parse_row(row)
    return None

def get_seasons_and_episodes_from_db(series_id: int):
    """Получение сезонов и эпизодов из локальной БД по ID сериала."""
    seasons_list = []
    if not MEDIA_DB.exists():
        return seasons_list
    with sqlite3.connect(MEDIA_DB) as conn:
        conn.row_factory = sqlite3.Row
        season_rows = conn.execute(
            "SELECT * FROM media WHERE media_type = 'season' AND parent_id = ? ORDER BY id ASC",
            (series_id,)
        ).fetchall()
        for s_row in season_rows:
            s_record = db._parse_row(s_row)
            s_id = s_record.get('id')
            
            episode_rows = conn.execute(
                "SELECT * FROM media WHERE media_type = 'episode' AND parent_id = ? ORDER BY id ASC",
                (s_id,)
            ).fetchall()
            episodes = []
            for ep_row in episode_rows:
                ep_record = db._parse_row(ep_row)
                plot_str = ep_record.get('plot', '')
                # Пытаемся разделить на начало и конец, если есть разделитель, или пишем в begins
                begins = plot_str
                ends = ""
                episodes.append({
                    "episode_number": len(episodes) + 1,
                    "begins": begins,
                    "ends": ends,
                    "final_verdict": ep_record.get('final_verdict') or ""
                })
            
            seasons_list.append({
                "season_number": len(seasons_list) + 1,
                "rating": s_record.get('rating') or {},
                "description": s_record.get('plot') or '',
                "episodes": episodes,
                "final_verdict": s_record.get('final_verdict') or ''
            })
    return seasons_list

async def get_media_type_from_gemini(ai, title):
    """Определение типа медиа через Gemini (фильм или сериал)."""
    prompt = f"Определи тип медиа для '{title}'. Верни JSON с единственным полем 'type', значение должно быть строго 'movie' или 'series'."
    try:
        response = await ai.ask(prompt)
        data = json.loads(response.replace('```json', '').replace('```', '').strip())
        return data.get('type', 'movie')
    except Exception:
        return 'movie'

async def get_movie_info(ai, title):
    """Получение полной информации о фильме через Gemini по шаблону."""
    prompt = f"""Напиши полную карточку для фильма '{title}' по шаблону для фильма из системной инструкции.
Верни строго в формате JSON (без markdown обертки ```json).
Шаблон полей:
{{
  "title": "Название (Оригинальное Название, Год)",
  "title_ru": "Русское название",
  "title_orig": "Оригинальное название",
  "type": "Фильм",
  "main_category": "Категория",
  "country": "Страна",
  "genres": ["Жанр1"],
  "directors": ["Режиссёр"],
  "cast": ["Актёр1"],
  "num_of_seasons": null,
  "status": null,
  "rating": {{"imdb": float, "tmdb": float, "кинопоиск": float}},
  "awards": ["Награда"],
  "why_watch": "...",
  "why_watch_tts": "...",
  "mood": "...",
  "plot": "...",
  "plot_tts": "...",
  "atmosphere": "...",
  "seasons": null,
  "final_verdict": "...",
  "can_stop_at": null,
  "quote": "...",
  "facts": ["Факт1"],
  "similar": ["Похожее1"],
  "review": {{
    "rating": "отличный",
    "liked": "...",
    "disliked": "..."
  }}
}}"""
    response = await ai.ask(prompt)
    return json.loads(response.replace('```json', '').replace('```', '').strip())

async def get_series_info(ai, title):
    """Получение общей информации о сериале через Gemini по шаблону."""
    prompt = f"""Напиши общую информацию о сериале '{title}' по шаблону сериала.
Верни строго в формате JSON (без markdown обертки ```json).
Шаблон полей:
{{
  "title": "Название (Оригинальное Название) (1-N сезоны)",
  "title_ru": "Русское название",
  "title_orig": "Оригинальное название",
  "type": "Сериал",
  "main_category": "Категория",
  "country": "Страна",
  "genres": ["Жанр1"],
  "directors": ["Режиссёр"],
  "cast": ["Актёр1"],
  "num_of_seasons": int,
  "status": "завершён"/"продолжается",
  "rating": {{"imdb": float, "tmdb": float, "кинопоиск": float}},
  "awards": ["Награда"],
  "why_watch": "...",
  "why_watch_tts": "...",
  "mood": "...",
  "plot": "...",
  "plot_tts": "...",
  "atmosphere": "...",
  "seasons": [],
  "final_verdict": null,
  "can_stop_at": null,
  "quote": "...",
  "facts": ["Факт1"],
  "similar": ["Похожее1"],
  "review": {{
    "rating": "отличный",
    "liked": "...",
    "disliked": "..."
  }}
}}"""
    response = await ai.ask(prompt)
    return json.loads(response.replace('```json', '').replace('```', '').strip())

async def get_season_info(ai, title, season_number):
    """Получение данных для конкретного сезона сериала."""
    prompt = f"""Напиши подробную информацию для {season_number}-го сезона сериала '{title}'.
Верни строго в формате JSON (без markdown обертки ```json).
Формат JSON:
{{
    "season_number": {season_number},
    "rating": {{"imdb": 8.5, "tmdb": 8.2, "кинопоиск": 8.6}},
    "description": "Описание происходящего в сезоне...",
    "episodes": [
        {{ 
            "episode_number": 1, 
            "begins": "С чего начинается...", 
            "ends": "Чем заканчивается...",
            "final_verdict": "Вердикт по эпизоду..."
        }}
    ],
    "final_verdict": "Итоговый вердикт по сезону..."
}}"""
    response = await ai.ask(prompt)
    return json.loads(response.replace('```json', '').replace('```', '').strip())

async def generate_complete_card(title: str):
    # 1. Сначала ищем в локальной БД
    local_rec = find_local_media(title)
    if local_rec:
        print(f"--- Найдено в локальной медиатеке: {title} ---")
        media_type = local_rec.get('media_type', '').lower()
        
        # Строим карточку на основе полей БД
        card = {
            "title": local_rec.get("title"),
            "title_ru": local_rec.get("title_ru"),
            "title_orig": local_rec.get("title_orig"),
            "type": "Сериал" if media_type in ('series', 'serial', 'сериал') else "Фильм",
            "main_category": local_rec.get("main_category"),
            "country": local_rec.get("country"),
            "genres": local_rec.get("genres"),
            "directors": local_rec.get("directors"),
            "cast": local_rec.get("cast"),
            "num_of_seasons": local_rec.get("num_of_seasons"),
            "status": local_rec.get("status"),
            "rating": local_rec.get("rating"),
            "awards": local_rec.get("awards"),
            "why_watch": local_rec.get("why_watch"),
            "why_watch_tts": None,
            "mood": local_rec.get("mood"),
            "plot": local_rec.get("plot"),
            "plot_tts": None,
            "atmosphere": local_rec.get("atmosphere"),
            "seasons": None,
            "final_verdict": local_rec.get("final_verdict"),
            "can_stop_at": local_rec.get("can_stop_at"),
            "quote": local_rec.get("quote"),
            "facts": local_rec.get("facts"),
            "similar": local_rec.get("similar"),
            "review": local_rec.get("review")
        }
        
        if card["type"] == "Сериал":
            card["seasons"] = get_seasons_and_episodes_from_db(local_rec.get("id"))
        
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return

    # 2. Если в локальной медиатеке нет — ищем в интернете через Gemini
    print(f"--- Не найдено в медиатеке. Поиск в интернете для: {title} ---")
    ai = GoogleGenerativeAI(system_instruction=SYSTEM_INSTRUCTION)
    
    media_type = await get_media_type_from_gemini(ai, title)
    
    if media_type == 'series':
        series_card = await get_series_info(ai, title)
        num_seasons = series_card.get('num_of_seasons', 1)
        if not num_seasons:
            num_seasons = 1
            
        series_card['seasons'] = []
        for i in range(1, num_seasons + 1):
            try:
                season_data = await get_season_info(ai, title, i)
                series_card['seasons'].append(season_data)
            except Exception as e:
                print(f"Ошибка при получении данных сезона {i}: {e}", file=sys.stderr)
                
        print(json.dumps(series_card, ensure_ascii=False, indent=2))
    else:
        movie_card = await get_movie_info(ai, title)
        print(json.dumps(movie_card, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    title_arg = sys.argv[1] if len(sys.argv) > 1 else "Острые козырьки"
    asyncio.run(generate_complete_card(title_arg))

