import asyncio
import json
import sqlite3
import sys
from pathlib import Path
from dotenv import load_dotenv

import header
from header import __root__
from src.ai import GoogleGenerativeAI
from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core import MEDIA_DB

load_dotenv()

async def reprocess_db():
    print("🚀 Starting reprocessing of SQLite database media records for TTS fields...")
    db = MediaDatabase(MEDIA_DB)
    processed_file = __root__ / 'processed_ids.json'
    
    processed_ids = set()
    if processed_file.exists():
        try:
            with open(processed_file, 'r', encoding='utf-8') as f:
                processed_ids = set(json.load(f))
        except Exception:
            pass
            
    # Get all movie and series records
    with sqlite3.connect(MEDIA_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM media WHERE (media_type = 'movie' OR media_type = 'series' OR media_type = 'c')"
        ).fetchall()
        
    records = [db._parse_row(r) for r in rows]
    pending_records = [r for r in records if r['id'] not in processed_ids]
    
    completed = len(records) - len(pending_records)
    total = len(records) or 1
    
    print(f"📊 Progress: {completed} / {total} records completed ({(completed / total) * 100:.1f}%).")
    print(f"📋 Found {len(pending_records)} pending records that need TTS rewriting.")
    
    if not pending_records:
        print("✅ All records already have TTS fields populated!")
        return

    # Load API keys
    from src.secrets.api_key_state import load_api_keys
    _, key_names, _ = load_api_keys()
    if not key_names:
        print("❌ No API keys found! Aborting.")
        return
        
    ai = GoogleGenerativeAI(api_key_names=key_names)
    
    tts_system_instruction = (
        "Ты — профессиональный редактор дикторских текстов для умного домашнего кинотеатра.\n"
        "Твоя задача — адаптировать ВСЕ текстовые поля в предоставленных данных фильма/сериала для озвучивания диктором (TTS).\n\n"
        "Верни ответ строго в формате JSON, повторив структуру исходных полей, но переписав значения согласно правилам:\n"
        "1. Русский язык: Все английские названия или имена должны быть записаны русской транскрипцией.\n"
        "2. Числа словами: Все числа и годы должны быть написаны прописью (например, 'две тысячи шестом' вместо '2006').\n"
        "3. Никакой разметки: Без использования Markdown, списков, кавычек и спецсимволов.\n"
        "4. Объем текста:\n"
        "   - Поле 'plot' (сюжет) должно содержать СТРОГО от 120 до 150 слов.\n"
        "   - Поле 'final_verdict' должно содержать СТРОГО от 70 до 80 слов.\n\n"
        "Пример JSON на выходе:\n"
        "{\n"
        "  \"title_ru\": \"Русское название\",\n"
        "  \"main_category\": \"Категория\",\n"
        "  \"country\": \"Страна\",\n"
        "  \"plot\": \"Адаптированный сюжет (120-150 слов)\",\n"
        "  \"atmosphere\": \"Атмосфера (около 15 слов)\",\n"
        "  \"why_watch\": \"Почему стоит смотреть\",\n"
        "  \"mood\": \"Настроение\",\n"
        "  \"quote\": \"Цитата\",\n"
        "  \"can_stop_at\": \"Можно остановиться после\",\n"
        "  \"facts\": [\"Факт 1\", \"Факт 2\"],\n"
        "  \"similar\": [\"Похожее 1\", \"Похожее 2\"],\n"
        "  \"final_verdict\": \"Финальный вердикт (70-80 слов)\",\n"
        "  \"review\": {\"rating\": \"оценка\", \"liked\": \"что понравилось\", \"disliked\": \"что не понравилось\"}\n"
        "}"
    )

    for i, record in enumerate(pending_records, 1):
        title = record.get('title')
        print(f"[{i}/{len(pending_records)}] Reprocessing: {title} ({record.get('media_type')})")
        
        # Prepare content to send to Gemini
        input_data = {
            "title_ru": record.get("title_ru"),
            "main_category": record.get("main_category"),
            "country": record.get("country"),
            "plot": record.get("plot"),
            "atmosphere": record.get("atmosphere"),
            "why_watch": record.get("why_watch"),
            "mood": record.get("mood"),
            "quote": record.get("quote"),
            "can_stop_at": record.get("can_stop_at"),
            "facts": record.get("facts"),
            "similar": record.get("similar"),
            "final_verdict": record.get("final_verdict"),
            "review": record.get("review")
        }
        
        prompt = (
            f"Данные по медиа для перевода в дикторский формат:\n"
            f"{json.dumps(input_data, ensure_ascii=False, indent=2)}"
        )
        
        try:
            response_text = await ai.ask(
                q=prompt,
                generation_config={
                    "system_instruction": tts_system_instruction,
                    "response_mime_type": "application/json"
                }
            )
            
            if not response_text:
                print(f"⚠️ Empty response for {title}")
                continue
                
            res_data = json.loads(response_text)
            
            # Update values in record dict
            for key in input_data.keys():
                if key in res_data:
                    record[key] = res_data[key]

            # Save the modified record back to SQLite database using db.save_media
            db.save_media(record['disk_name'], record['media_type'], record)
            
            # Save ID to processed list
            processed_ids.add(record['id'])
            with open(processed_file, 'w', encoding='utf-8') as f:
                json.dump(list(processed_ids), f, ensure_ascii=False)
                
            print(f"   Успешно переписано: {title}")
            
        except Exception as e:
            print(f"❌ Ошибка обработки {title}: {e}")
            
    print("🎉 Reprocessing complete!")

if __name__ == "__main__":
    asyncio.run(reprocess_db())
