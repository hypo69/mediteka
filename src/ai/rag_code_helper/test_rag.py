# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование RAG
# =============================================================================
# Описание:
#   Тест индексации и поиска в RAG.
#
# File: test_rag.py
# Author: hypo69
# =============================================================================

import asyncio
from pathlib import Path
import numpy as np
from src.ai.rag_code_helper.indexer import Indexer
from src.ai.rag_code_helper.searcher import Searcher
from src.ai.gemini.generative_ai import GoogleGenerativeAI
from src.logger.logger import logger

async def test_rag():
    # Инициализация
    ai = GoogleGenerativeAI()
    indexer = Indexer('src/ai/rag_code_helper/config.json', ai)
    
    # Тестовые данные
    test_files = [Path('src/ai/rag_code_helper/indexer.py')]
    
    # Индексация
    success = await indexer.process_files(test_files)
    if not success:
        logger.error("Индексация провалилась")
        return

    # Поиск
    searcher = Searcher('src/ai/rag_code_helper/config.json')
    query = "FAISS index creation"
    query_embedding = await ai.embed(query)
    
    if query_embedding is not None:
        results = searcher.search(query_embedding.reshape(1, -1), top_k=1)
        print(f"Результаты поиска (индексы чанков): {results}")
    else:
        logger.error("Не удалось сгенерировать эмбеддинг запроса")

if __name__ == "__main__":
    asyncio.run(test_rag())
