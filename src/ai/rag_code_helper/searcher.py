# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Поиск документов в RAG
# =============================================================================
# Описание:
#   Поиск ближайших чанков в индексе FAISS.
#
# Examples:
#   >>> searcher = Searcher('src/ai/rag_code_helper/config.json')
#   >>> results = searcher.search(query_embedding, top_k=5)
#
# File: searcher.py
# Package: AI.RAG_CODE_HELPER
# Class: Searcher
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import faiss
import numpy as np
from src.logger import logger
from src.utils.jjson import j_loads
from typing import List

class Searcher:
    """Поиск документов в индексе FAISS.
    
    Attributes:
        config (dict): Конфигурация поисковика.
    """

    def __init__(self, config_path: str) -> None:
        """Инициализация поисковика.
        
        Args:
            config_path (str): Путь к файлу конфигурации.
        """
        self.config: dict = j_loads(config_path) or {}
        index_path = self.config.get('index_path', 'code_index.faiss')
        self.index = faiss.read_index(index_path)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[int]:
        """Поиск ближайших соседей.
        
        Args:
            query_embedding (np.ndarray): Вектор запроса.
            top_k (int): Количество результатов.
            
        Returns:
            List[int]: Список индексов чанков.
        """
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        return indices[0].tolist()
