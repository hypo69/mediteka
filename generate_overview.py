# -*- coding: utf-8 -*-
import asyncio
import json
import sqlite3
import sys
from pathlib import Path
from src.ai import GoogleGenerativeAI
from src.logger import logger

DB_PATH = Path('plugins/media_organizer/data/media.db')
JSON_PATH = Path('plugins/media_organizer/data/media_overview_data.json')
OUTPUT_PATH = Path('Media_Library_Overview.md')
API_PAUSE_SECONDS = 5

def load_data():
    if JSON_PATH.exists():
        try:
            return json.loads(JSON_PATH.read_text(encoding='utf-8'))
        except Exception as e:
            logger.error(f"Error loading JSON data: {e}")
    return {}

def save_data(data):
    try:
        JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception as e:
        logger.error(f"Error saving JSON data: {e}")

async def generate_or_expand_plot(ai, title, year, country, genres, existing_plot=None):
    if existing_plot:
        prompt = f"""Перепиши и расширь следующий сюжет для фильма/сериала '{title}' ({year}, {country}, жанры: {genres}) так, чтобы его длина составляла строго от 120 до 150 слов.
Текст должен быть цельным, увлекательным, написанным грамотным русским языком. Не используй никаких заголовков (например, 'Сюжет:' или 'Описание:'), списков или жирного шрифта. Текст должен быть просто в виде одного или двух связных абзацев.

Существующий сюжет:
{existing_plot}
"""
    else:
        prompt = f"""Напиши подробный сюжет для фильма/сериала '{title}' ({year}, {country}, жанры: {genres}) так, чтобы его длина составляла строго от 120 до 150 слов.
Текст должен быть цельным, увлекательным, написанным грамотным русским языком. Не используй никаких заголовков (например, 'Сюжет:' или 'Описание:'), списков или жирного шрифта. Текст должен быть просто в виде одного или двух связных абзацев.
"""
    
    for attempt in range(3):
        try:
            response = await ai.ask(prompt)
            if response:
                text = response.strip()
                # Clean up header styling
                for header in ('**Сюжет:**', '**Описание:**', 'Сюжет:', 'Описание:'):
                    text = text.replace(header, '').strip()
                words = text.split()
                word_count = len(words)
                if 110 <= word_count <= 165:
                    return text
                logger.warning(f"Plot word count for '{title}' was {word_count}, retrying (attempt {attempt + 1})...")
        except Exception as e:
            logger.error(f"Error calling AI for plot generation of '{title}': {e}")
            await asyncio.sleep(2)
            
    return response.strip() if response else (existing_plot or "Описание сюжета отсутствует.")

def clean_list_field(val):
    if not val:
        return "—"
    try:
        parsed = json.loads(val)
        if isinstance(parsed, list):
            return ", ".join(parsed) if parsed else "—"
        return str(parsed)
    except:
        return str(val)

def clean_rating_field(val):
    if not val:
        return "—"
    try:
        parsed = json.loads(val)
        if isinstance(parsed, dict):
            parts = []
            if parsed.get('imdb'):
                parts.append(f"IMDb: {parsed['imdb']}")
            if parsed.get('tmdb'):
                parts.append(f"TMDB: {parsed['tmdb']}")
            if parsed.get('kp') or parsed.get('kinopoisk'):
                parts.append(f"КП: {parsed.get('kp') or parsed.get('kinopoisk')}")
            return " | ".join(parts) if parts else "—"
        return str(parsed)
    except:
        return str(val)

def clean_review_field(val):
    if not val:
        return ""
    try:
        parsed = json.loads(val)
        if isinstance(parsed, dict):
            liked = parsed.get('liked', '').strip()
            disliked = parsed.get('disliked', '').strip()
            parts = []
            if liked:
                parts.append(f"Понравилось: {liked}")
            if disliked:
                parts.append(f"Не понравилось: {disliked}")
            return " — ".join(parts) if parts else ""
        return str(parsed)
    except:
        return str(val)

async def process_item_sequentially(ai, item, data_store):
    item_id = str(item['id'])
    
    title = item['title_ru'] or item['title'] or "Без названия"
    year = item['year'] or "—"
    country = item['country'] or "—"
    
    try:
        genres_list = json.loads(item['genres'] or '[]')
        genres_str = ", ".join(genres_list) if isinstance(genres_list, list) else str(item['genres'])
    except Exception:
        genres_str = str(item['genres'] or "—")
        
    awards_str = clean_list_field(item['awards'])
    rating_str = clean_rating_field(item['rating'])
    directors_str = clean_list_field(item['directors'])
    cast_str = clean_list_field(item['cast'])
    
    # Check if we already have a valid plot in the store
    existing_entry = data_store.get(item_id)
    if existing_entry and existing_entry.get('plot'):
        plot_len = len(existing_entry['plot'].split())
        if 110 <= plot_len <= 165:
            # Re-update other metadata in case they changed, but reuse the plot
            data_store[item_id].update({
                "title_ru": title,
                "year": year,
                "country": country,
                "genres": genres_str,
                "awards": awards_str,
                "rating": rating_str,
                "directors": directors_str,
                "cast": cast_str,
                "review": clean_review_field(item['review']),
                "why_watch": (item['why_watch'] or "").strip(),
                "main_category": item['main_category'] or "Другое",
                "media_type": item['media_type']
            })
            save_data(data_store)
            return False  # No API call made

    # Check if DB plot is already valid
    db_plot = item['plot']
    db_plot_len = len(db_plot.split()) if db_plot else 0
    if 120 <= db_plot_len <= 150:
        new_plot = db_plot
        api_called = False
    else:
        logger.info(f"Generating/Expanding plot for: {title} (ID: {item['id']})")
        new_plot = await generate_or_expand_plot(ai, title, year, country, genres_str, db_plot)
        api_called = True
            
    data_store[item_id] = {
        "id": item['id'],
        "title_ru": title,
        "year": year,
        "country": country,
        "genres": genres_str,
        "awards": awards_str,
        "rating": rating_str,
        "directors": directors_str,
        "cast": cast_str,
        "plot": new_plot,
        "review": clean_review_field(item['review']),
        "why_watch": (item['why_watch'] or "").strip(),
        "main_category": item['main_category'] or "Другое",
        "media_type": item['media_type']
    }
    save_data(data_store)
    return api_called

def build_markdown(data_store):
    logger.info("Building Markdown file from JSON data...")
    items = list(data_store.values())
    
    series_items = [r for r in items if r.get('media_type') == 'series']
    movie_items = [r for r in items if r.get('media_type') == 'movie']
    
    def group_by_category(item_list):
        groups = {}
        for item in item_list:
            cat = item.get('main_category') or "Другое"
            groups.setdefault(cat, []).append(item)
        for cat in groups:
            groups[cat].sort(key=lambda x: (x.get('title_ru') or '').lower())
        return groups
        
    series_grouped = group_by_category(series_items)
    movies_grouped = group_by_category(movie_items)
    
    md_lines = []
    TAB = "\t\t"
    
    md_lines.append("# Сериалы:\n")
    for category in sorted(series_grouped.keys()):
        md_lines.append(f"## {category}:\n")
        for item in series_grouped[category]:
            md_lines.append(f" ### [{item.get('id')}] {item.get('title_ru')}")
            md_lines.append(f"{TAB}- {item.get('year')}, {item.get('country')}, {item.get('genres')}")
            md_lines.append(f"{TAB}- Премии: {item.get('awards')}, Индекс: {item.get('rating')}")
            md_lines.append(f"{TAB}- Режиссер: {item.get('directors')}")
            md_lines.append(f"{TAB}- Актеры: {item.get('cast')}")
            md_lines.append("")
            
            # plot paragraph/s
            plot_val = item.get('plot') or ""
            for p in plot_val.splitlines():
                if p.strip():
                    md_lines.append(f"{TAB}{p.strip()}")
            md_lines.append("")
            
            review_val = item.get('review')
            if review_val:
                md_lines.append(f"{TAB}{review_val}")
                md_lines.append("")
                
            why_watch_val = item.get('why_watch')
            if why_watch_val:
                md_lines.append(f"{TAB}{why_watch_val}")
                md_lines.append("")
            
            md_lines.append("---\n")
            
    md_lines.append("\n# Фильмы:\n")
    for category in sorted(movies_grouped.keys()):
        md_lines.append(f"## {category}:\n")
        for item in movies_grouped[category]:
            md_lines.append(f" ### [{item.get('id')}] {item.get('title_ru')}")
            md_lines.append(f"{TAB}- {item.get('year')}, {item.get('country')}, {item.get('genres')}")
            md_lines.append(f"{TAB}- Премии: {item.get('awards')}, Индекс: {item.get('rating')}")
            md_lines.append(f"{TAB}- Режиссер: {item.get('directors')}")
            md_lines.append(f"{TAB}- Актеры: {item.get('cast')}")
            md_lines.append("")
            
            plot_val = item.get('plot') or ""
            for p in plot_val.splitlines():
                if p.strip():
                    md_lines.append(f"{TAB}{p.strip()}")
            md_lines.append("")
            
            review_val = item.get('review')
            if review_val:
                md_lines.append(f"{TAB}{review_val}")
                md_lines.append("")
                
            why_watch_val = item.get('why_watch')
            if why_watch_val:
                md_lines.append(f"{TAB}{why_watch_val}")
                md_lines.append("")
            
            md_lines.append("---\n")
            
    OUTPUT_PATH.write_text("\n".join(md_lines), encoding='utf-8')
    logger.info(f"Markdown overview generated at {OUTPUT_PATH}")

async def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--convert-only':
        data_store = load_data()
        build_markdown(data_store)
        return
        
    logger.info("Starting media library overview generation with sequential execution and pauses...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, title_ru, year, country, genres, directors, "cast", 
               rating, awards, plot, why_watch, review, main_category, media_type 
        FROM media 
        WHERE media_type IN ('series', 'movie')
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    logger.info(f"Loaded {len(rows)} media items from database.")
    
    # Load existing progress JSON
    data_store = load_data()
    
    ai = GoogleGenerativeAI()
    
    processed_count = 0
    api_calls_count = 0
    
    for item in rows:
        api_called = await process_item_sequentially(ai, item, data_store)
        processed_count += 1
        
        if api_called:
            api_calls_count += 1
            # Add pause to avoid rate limits
            await asyncio.sleep(API_PAUSE_SECONDS)
            
    logger.info(f"Processed {processed_count} items. Made {api_calls_count} API calls.")
    
    # Build final markdown
    build_markdown(data_store)

if __name__ == "__main__":
    asyncio.run(main())
