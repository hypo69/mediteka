"""
Индексатор RAG для фильмотеки
"""

import os
import sqlite3
import sys

# Добавляем корневую директорию в sys.path для импорта логгера
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.logger import logger

import chromadb
from chromadb.utils import embedding_functions

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'media.db'))
CHROMA_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'chroma_db'))

def get_media_data():
    """Извлекает данные из базы данных SQLite."""
    logger.info("Подключение к базе данных %s", DB_PATH)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Извлекаем все фильмы/сериалы с нужными полями
        query = """
            SELECT id, title_ru, title_orig, year, genres, directors, 
                   "cast", plot, atmosphere, mood, why_watch, facts, review, path, disk_name
            FROM media
            WHERE media_type IN ('film', 'series') 
               OR main_category IS NOT NULL
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info("Извлечено %d записей", len(rows))
        return rows
    except Exception as e:
        logger.error("Ошибка при работе с БД: %s", e)
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def format_document(row):
    """Форматирует строку БД в текстовый документ для RAG."""
    parts = []
    
    title_ru = row['title_ru'] or ''
    title_orig = row['title_orig'] or ''
    year = row['year'] or ''
    
    title_line = f"Название: {title_ru}"
    if title_orig:
        title_line += f" / {title_orig}"
    if year:
        title_line += f" ({year})"
    parts.append(title_line)
    
    if row['genres']:
        parts.append(f"Жанры: {row['genres']}")
    if row['directors']:
        parts.append(f"Режиссер: {row['directors']}")
    if row['cast']:
        parts.append(f"В ролях: {row['cast']}")
    if row['plot']:
        parts.append(f"Сюжет: {row['plot']}")
    
    mood_atmos = []
    if row['mood']:
        mood_atmos.append(row['mood'])
    if row['atmosphere']:
        mood_atmos.append(row['atmosphere'])
    if mood_atmos:
        parts.append(f"Настроение/Атмосфера: {', '.join(mood_atmos)}")
        
    if row['why_watch']:
        parts.append(f"Зачем смотреть: {row['why_watch']}")
    if row['facts']:
        parts.append(f"Факты: {row['facts']}")
    if row['review']:
        parts.append(f"Отзыв: {row['review']}")
        
    return "\n".join(parts)

def build_index():
    """Создает ChromaDB коллекцию и индексирует все документы."""
    rows = get_media_data()
    if not rows:
        logger.warning("Нет данных для индексации.")
        return

    logger.info("Инициализация ChromaDB по пути: %s", CHROMA_DB_PATH)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    # Используем дефолтную функцию (all-MiniLM-L6-v2) или sentence-transformers
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    collection = client.get_or_create_collection(
        name="media_library", 
        embedding_function=sentence_transformer_ef
    )
    
    documents = []
    metadatas = []
    ids = []
    
    logger.info("Форматирование документов...")
    for row in rows:
        doc = format_document(row)
        if not doc.strip():
            continue
            
        documents.append(doc)
        
        meta = {
            "id": row['id'],
            "title_ru": row['title_ru'] or '',
            "year": row['year'] or 0,
            "path": row['path'] or '',
            "disk_name": row['disk_name'] or ''
        }
        # Убираем возможные None из меты, ChromaDB их не любит
        meta = {k: v for k, v in meta.items() if v is not None}
        
        metadatas.append(meta)
        ids.append(str(row['id']))

    logger.info("Добавление %d документов в векторную базу. Это может занять время...", len(documents))
    
    # Пакетное добавление (batching) чтобы не перегружать память
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        logger.info("Индексация батча %d-%d...", i, min(i + batch_size, len(documents)))
        collection.upsert(
            documents=documents[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
            ids=ids[i:i + batch_size]
        )
        
    logger.info("Индексация завершена успешно!")

if __name__ == "__main__":
    build_index()
