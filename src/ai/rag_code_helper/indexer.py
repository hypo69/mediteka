# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Индексация документов для RAG
# =============================================================================
# Описание:
#   Индексация кода и создание векторного индекса FAISS.
#
# Examples:
#   >>> indexer = Indexer('src/ai/rag_code_helper/config.json')
#   >>> indexer.index_documents(documents)
#
# File: indexer.py
# Package: AI.RAG_CODE_HELPER
# Class: Indexer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from pathlib import Path
from typing import List, Dict
import faiss
import numpy as np
from src.logger import logger
from src.utils.jjson import j_loads
from src.ai.gemini.generative_ai import GoogleGenerativeAI

class Indexer:
    """Индексация документов и создание векторного индекса FAISS.
    
    Attributes:
        config (dict): Конфигурация индексатора.
        ai (GoogleGenerativeAI): Экземпляр модели AI.
    """

    def __init__(self, config_path: str, ai: GoogleGenerativeAI) -> None:
        """Инициализация индексатора.
        
        Args:
            config_path (str): Путь к файлу конфигурации.
            ai (GoogleGenerativeAI): Экземпляр модели AI.
        """
        self.config: dict = j_loads(config_path) or {}
        self.ai = ai

    def chunk_text(self, text: str) -> List[str]:
        """Разбиение текста на чанки."""
        chunk_size = self.config.get('chunk_size', 1000)
        overlap = self.config.get('chunk_overlap', 200)
        
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i : i + chunk_size])
        return chunks

    async def process_files(self, file_paths: List[Path]) -> bool:
        """Чанкинг, эмбеддинг и индексация файлов."""
        all_chunks = []
        all_embeddings = []
        
        for file_path in file_paths:
            content = file_path.read_text(encoding='utf-8')
            chunks = self.chunk_text(content)
            for chunk in chunks:
                embedding = await self.ai.embed(chunk)
                if embedding is not None:
                    all_chunks.append(chunk)
                    all_embeddings.append(embedding)
        
        if not all_embeddings:
            return False
            
        embeddings_np = np.array(all_embeddings)
        return self.index_documents(all_chunks, embeddings_np)

    def index_documents(self, chunks: List[str], embeddings: np.ndarray) -> bool:
        """Создание и сохранение индекса FAISS.
        
        Args:
            chunks (List[str]): Список чанков текста.
            embeddings (np.ndarray): Векторные представления чанков.
            
        Returns:
            bool: True если индекс успешно создан и сохранен, иначе False.
        """
        if not chunks or embeddings.size == 0:
            logger.error("Нет данных для индексации")
            return False

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings.astype('float32'))
        
        index_path = self.config.get('index_path', 'code_index.faiss')
        faiss.write_index(index, index_path)
        
        logger.info(f"Индекс успешно сохранен в {index_path}")
        return True
