import json
from pathlib import Path
from plugins.media_organizer.core import MEDIA_DB
from plugins.media_organizer.core.database import MediaDatabase

def import_jsons(json_folder: str, disk_name: str = 'imported'):
    folder = Path(json_folder)
    if not folder.exists():
        print(f"Папка {folder} не найдена.")
        return

    db = MediaDatabase(MEDIA_DB)
    count = 0
    for file_path in folder.glob('*.json'):
        try:
            data = json.loads(file_path.read_text(encoding='utf-8'))
            title = data.get('title', file_path.stem)
            
            # Определяем тип медиа
            is_series = data.get('type', '').lower() == 'сериал' or data.get('num_of_seasons', 0) > 0
            media_type = 'series' if is_series else 'movie'
            
            # Если нет пути, указываем просто имя файла
            if 'path' not in data:
                data['path'] = f"imported/{file_path.name}"
            
            print(f"Importing: {title} ({media_type})")
            db.save_media(disk_name, media_type, data)
            count += 1
        except Exception as e:
            print(f"Error importing {file_path.name}: {e}")

    print(f"\n✅ Successfully imported {count} files to database.")
    print("To build the RAG index, run the `rebuild_rag` command.")
    print("NOTE: Building RAG search still requires GEMINI_API_KEY because it uses text-embedding model.")

if __name__ == "__main__":
    import_jsons(r"C:\mediteka\.files_for_rag")
