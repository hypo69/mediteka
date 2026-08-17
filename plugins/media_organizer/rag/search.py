"""
Скрипт поиска (Retrieval) по RAG-индексу фильмотеки
"""

import os
import sys

# Force UTF-8 encoding for standard output
sys.stdout.reconfigure(encoding='utf-8')

# Добавляем корневую директорию в sys.path для импорта логгера
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.logger import logger

import chromadb
from chromadb.utils import embedding_functions

CHROMA_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'chroma_db'))

def search_media(query: str, n_results: int = 5):
    """Выполняет семантический поиск по векторной базе данных."""
    logger.info("Подключение к ChromaDB по пути: %s", CHROMA_DB_PATH)
    
    if not os.path.exists(CHROMA_DB_PATH):
        logger.error("База данных ChromaDB не найдена! Сначала запустите indexer.py.")
        return []
        
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    try:
        collection = client.get_collection(
            name="media_library",
            embedding_function=sentence_transformer_ef
        )
    except ValueError:
        logger.error("Коллекция 'media_library' не найдена. Сначала запустите indexer.py.")
        return []
        
    logger.info("Выполнение поиска для запроса: '%s'", query)
    
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    # Форматирование результатов
    found_items = []
    
    if not results['documents'] or not results['documents'][0]:
        logger.info("Ничего не найдено.")
        return found_items
        
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        dist = results['distances'][0][i]
        
        found_items.append({
            'document': doc,
            'metadata': meta,
            'distance': dist
        })
        
    return found_items

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        user_query = "Смешная комедия на вечер с хорошим настроением"
        
    print(f"\n--- ПОИСК: {user_query} ---\n")
    
    results = search_media(user_query)
    
    for i, res in enumerate(results, 1):
        meta = res['metadata']
        print(f"[{i}] {meta.get('title_ru')} ({meta.get('year')}) - Оценка совпадения: {res['distance']:.4f}")
        print(f"    Путь: {meta.get('path')}")
        print(f"    Сниппет: {res['document'][:150]}...\n")
