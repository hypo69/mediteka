import os
from pathlib import Path
from src.ai.gemini.rag import GeminiRAG
from plugins.media_organizer.core import MEDIA_RAG_DB
from dotenv import load_dotenv
from src.secrets.api_key_state import load_api_keys

def run():
    load_dotenv(Path("C:/mediteka/.env"))
    
    _api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
    api_keys, _, _ = load_api_keys(_api_key_names or None)
    if not api_keys:
        print("Error: No API keys found.")
        return
        
    api_key = api_keys[0]
    rag = GeminiRAG(api_key=api_key, db_path=MEDIA_RAG_DB)
    rag.clear()
    
    docs = []
    ragdata_dir = Path(r"C:\mediteka\RAGDATA\СВАТЫ")
    for idx, file_path in enumerate(ragdata_dir.glob("*.txt")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")
            continue
            
        docs.append({
            'id': f"svaty_doc_{idx}",
            'text': text,
            'meta': {
                'title': 'Сваты',
                'type': 'series',
                'disk_name': '',
                'main_category': 'Комедия',
                'year': '2008',
            }
        })
    
    print(f"Adding {len(docs)} documents to RAG...")
    rag.add_documents(docs)
    print("Done.")

if __name__ == "__main__":
    run()
