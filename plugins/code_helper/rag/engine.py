# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: RAG-движок на базе FAISS для ассистента кода
# =============================================================================
# Описание:
#   Реализация семантического поиска по кодовой базе с использованием
#   библиотеки FAISS. Обеспечивает векторизацию документов и поиск
#   ближайших соседей без использования СУБД.
#
# Примеры:
#   >>> from plugins.code_helper.rag.engine import FaissEngine
#   >>> engine = FaissEngine(Path('index_dir'))
#   >>> engine.add_documents(docs, api_key='...')
#
# File: engine.py
# Project: gemini-simplechat
# Package: plugins.code_helper.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import faiss
import json
import numpy as np
from pathlib import Path
from typing import List, Dict

from src.logger import logger
from src.ai.gemini.generative_ai import GoogleGenerativeAI

class FaissEngine:
    """Движок для управления FAISS-индексом.

    Хранение векторов в FAISS и метаданных в JSON-файлах.
    Без использования СУБД.

    Attributes:
        index_dir (Path): Директория хранения индекса.
        dimension (int): Размерность векторов (Gemini-embedding-2).
    """

    def __init__(self, index_dir: Path) -> None:
        """Инициализация FAISS-движка."""
        self.index_dir: Path = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_file: Path = self.index_dir / "index.faiss"
        self.meta_file: Path = self.index_dir / "index.json"
        self.dimension: int = 768  # text-embedding-004 dimensionality
        self.index = self._load_or_create_index()
        self.metadatas: List[Dict] = self._load_metadatas()
        
        # Инициализация нашего проверенного оберточного класса
        self.ai_model = GoogleGenerativeAI(api_key_names=['fmashulia'])

    def _load_or_create_index(self):
        """Загрузка или создание нового индекса FAISS."""
        if self.index_file.exists():
            return faiss.read_index(str(self.index_file))
        return faiss.IndexFlatL2(self.dimension)

    def _load_metadatas(self) -> List[Dict]:
        """Загрузка метаданных из JSON-файла."""
        if self.meta_file.exists():
            try:
                with open(self.meta_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Ошибка чтения метаданных", e)
                return []
        return []

    def save(self) -> bool:
        """Сохранение индекса и метаданных."""
        try:
            faiss.write_index(self.index, str(self.index_file))
            with open(self.meta_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadatas, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error("Ошибка сохранения индекса", e)
            return False

    async def _embed_batch(self, texts: List[str]) -> np.ndarray:
        """Генерация эмбеддингов с автоматической обработкой квот."""
        vectors = []
        for text in texts:
            # Используем встроенный метод эмбеддинга из GoogleGenerativeAI, он асинхронный
            vec = await self.ai_model.embed(text)
            if vec is not None:
                vectors.append(vec)
            else:
                # В случае неудачи заполняем заглушкой
                vectors.append(np.zeros(self.dimension, dtype=np.float32))
        return np.array(vectors, dtype=np.float32)

    async def add_documents(self, docs: List[Dict], api_key: str = None) -> bool:
        """Векторизация и добавление документов в индекс FAISS."""
        texts = [d['text'] for d in docs]
        vectors = await self._embed_batch(texts)
        
        self.index.add(vectors)
        self.metadatas.extend([{'meta': d.get('meta', {}), 'text': d['text']} for d in docs])
        return self.save()

    async def search(self, query: str, api_key: str = None, top_k: int = 5) -> List[Dict]:
        """Поиск по индексу FAISS."""
        query_vec = await self.ai_model.embed(query)
        if query_vec is None:
            return []
            
        scores, indices = self.index.search(query_vec.reshape(1, -1), top_k)
        
        results: List[Dict] = []
        for i in range(top_k):
            idx = int(indices[0][i])
            if idx >= 0:
                results.append({
                    'data': self.metadatas[idx],
                    'score': float(scores[0][i])
                })
        return results
