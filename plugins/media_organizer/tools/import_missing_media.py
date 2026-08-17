import sqlite3
import json
import asyncio
from pathlib import Path
from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core.media_organizer import INSTRUCTION, PersistentGenreClassifier
from src.ai import GoogleGenerativeAI
from src.secrets.api_key_state import load_api_keys

# Путь к БД
DB_PATH = '.\\plugins\\media_organizer\\data\\media.db'

# Список файлов, полученный ранее
with open('missing_files.json', 'r', encoding='utf-8') as f:
    MISSING_FILES = json.load(f)

async def import_media():
    _, key_names, _ = load_api_keys()
    if not key_names:
        print("❌ Нет доступных ключей.")
        return

    ai = GoogleGenerativeAI(api_key_names=[key_names[0]], system_instruction=INSTRUCTION)
    db = MediaDatabase(Path(DB_PATH))
    classifier = PersistentGenreClassifier(tmdb=None, gemini=ai, db=db, disk_name="UNKNOWN")

    print(f"🚀 Начало импорта {len(MISSING_FILES)} файлов.")

    for i, file_path in enumerate(MISSING_FILES):
        path = Path(file_path)
        print(f"[{i+1}/{len(MISSING_FILES)}] Обработка: {path.name}")
        
        try:
            # Используем классификатор для извлечения данных и вставки в БД
            # Предполагаем, что имя файла содержит достаточно информации
            await classifier._map_category(path.name, [path], 'series' if 'S0' in path.name else 'movie', path.name, 'S0' in path.name)
            print(f"✅ Успешно импортировано.")
        except Exception as e:
            print(f"❌ Ошибка при импорте {path.name}: {e}")
            await asyncio.sleep(5) # Пауза при ошибке

    print("🏁 Импорт завершен.")

if __name__ == '__main__':
    asyncio.run(import_media())
