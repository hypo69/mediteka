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
from google import genai
from google.genai import types

from src.logger import logger

class FaissEngine:
    """Движок для управления FAISS-индексом.

    Хранение векторов в FAISS и метаданных в JSON-файлах.
    Без использования СУБД.

    Attributes:
        index_dir (Path): Директория хранения индекса.
        dimension (int): Размерность векторов (Gemini-embedding-2).
    """

    def __init__(self, index_dir: Path) -> None:
        """Инициализация FAISS-движка.

        Args:
            index_dir (Path): Директория для файлов индекса.
        """
        self.index_dir: Path = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_file: Path = self.index_dir / "index.faiss"
        self.meta_file: Path = self.index_dir / "index.json"
        self.dimension: int = 3072
        self.index = self._load_or_create_index()
        self.metadatas: List[Dict] = self._load_metadatas()

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

    def _embed(self, api_key: str, texts: List[str], task_type: str = 'RETRIEVAL_DOCUMENT') -> np.ndarray:
        """Получение эмбеддингов для списка текстов через Gemini API.

        Args:
            api_key (str): API-ключ Gemini.
            texts (List[str]): Список текстов для векторизации.
            task_type (str): Тип задачи.

        Returns:
            np.ndarray: Векторы эмбеддингов.
        """
        client = genai.Client(api_key=api_key)
        response = client.models.embed_content(
            model='models/gemini-embedding-2',
            contents=[types.Content(parts=[types.Part.from_text(text=t)]) for t in texts],
            config=types.EmbedContentConfig(task_type=task_type),
        )
        return np.array([e.values for e in response.embeddings], dtype=np.float32)

    def add_documents(self, docs: List[Dict], api_key: str) -> bool:
        """Векторизация и добавление документов в индекс FAISS.

        Args:
            docs (List[Dict]): Список документов.
            api_key (str): API-ключ для Gemini.

        Returns:
            bool: Успешность операции.
        """
        texts = [d['text'] for d in docs]
        vectors = self._embed(api_key, texts, task_type='RETRIEVAL_DOCUMENT')
        
        self.index.add(vectors)
        self.metadatas.extend([{'meta': d.get('meta', {}), 'text': d['text']} for d in docs])
        return self.save()

    def search(self, query: str, api_key: str, top_k: int = 5) -> List[Dict]:
        """Поиск по индексу FAISS.

        Args:
            query (str): Запрос пользователя.
            api_key (str): API-ключ Gemini.
            top_k (int): Количество результатов.

        Returns:
            List[Dict]: Список результатов поиска.
        """
        query_vec = self._embed(api_key, [query], task_type='RETRIEVAL_QUERY')
        
        scores, indices = self.index.search(query_vec, top_k)
        
        results: List[Dict] = []
        for i in range(top_k):
            idx = int(indices[0][i])
            if idx >= 0:
                results.append({
                    'data': self.metadatas[idx],
                    'score': float(scores[0][i])
                })
        return results
