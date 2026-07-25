# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: RAG на базе Gemini Embedding API и SQLite
# =============================================================================
# Описание:
#   Векторизация документов через Gemini text-embedding-004,
#   хранение эмбеддингов в SQLite, cosine similarity поиск через numpy.
#   Не требует внешних векторных БД — только google-genai и numpy.
#
# File: rag.py
# Project: ai-mediteka
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import sqlite3
from pathlib import Path
from typing import List

import numpy as np
from google import genai
from google.genai import types

from src.logger import logger

_EMBED_MODEL = 'models/gemini-embedding-2'
_EMBED_DIM = 3072


class GeminiRAG:
    """RAG-индекс на базе Gemini Embedding API и SQLite.

    Векторизация произвольных текстовых документов, хранение в SQLite,
    семантический поиск ближайших соседей через cosine similarity.

    Attributes:
        db_path (Path): Путь к SQLite-файлу индекса.
        client: Клиент google.genai.

    Examples:
        >>> rag = GeminiRAG(api_key='...', db_path=Path('rag.db'))
        >>> rag.add_documents([{'id': '1', 'text': 'Титаник — фильм 1997 года', 'meta': {}}])
        >>> results = rag.search('фильм про корабль', top_k=3)
    """

    def __init__(self, api_key: str, db_path: Path) -> None:
        """Инициализация RAG-индекса.

        Args:
            api_key (str): Ключ Gemini API.
            db_path (Path): Путь к файлу SQLite для хранения эмбеддингов.

        Examples:
            >>> rag = GeminiRAG(api_key='key', db_path=Path('index.db'))
        """
        self.db_path = db_path
        self.client = genai.Client(api_key=api_key)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    # Инициализация схемы
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        """Создание таблицы rag_index если не существует."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rag_index (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    meta TEXT NOT NULL DEFAULT '{}',
                    embedding BLOB NOT NULL
                )
            """)

    # ------------------------------------------------------------------
    # Векторизация
    # ------------------------------------------------------------------

    def _embed(self, texts: List[str], task_type: str = 'RETRIEVAL_DOCUMENT') -> List[List[float]]:
        """Получение эмбеддингов для списка текстов через Gemini API с обработкой 429 и ротацией ключей.

        Args:
            texts (List[str]): Список текстов для векторизации.
            task_type (str): Тип задачи: 'RETRIEVAL_DOCUMENT' или 'RETRIEVAL_QUERY'.

        Returns:
            List[List[float]]: Список векторов.
        """
        import time
        from google.genai.errors import APIError
        from src.secrets.api_key_state import load_api_keys, mark_exhausted
        
        import random
        # Выбираем случайную стартовую позицию для ротации
        start_idx = random.randint(0, 100)
        max_retries = 10
        base_delay = 1.0
        
        for attempt in range(max_retries):
            # Загружаем доступные ключи
            api_keys, key_names, _ = load_api_keys()
            if not api_keys:
                raise RuntimeError("Нет доступных ключей API Gemini")
            
            # Ротируем ключи со случайным стартом
            key_idx = (start_idx + attempt) % len(api_keys)
            current_key = api_keys[key_idx]
            current_name = key_names[key_idx]
            
            # Пересоздаем клиент с новым ключом
            client = genai.Client(api_key=current_key)
            try:
                response = client.models.embed_content(
                    model=_EMBED_MODEL,
                    contents=[types.Content(parts=[types.Part.from_text(text=t)]) for t in texts],
                    config=types.EmbedContentConfig(task_type=task_type),
                )
                return [e.values for e in response.embeddings]
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    delay = 5.0 + attempt * 2
                    logger.warning(f"Превышен лимит (429) для ключа {current_name}. Переключаемся и ждем {delay} сек...")
                    time.sleep(delay)
                    continue
                raise e
                
        raise RuntimeError("Превышено количество попыток запроса эмбеддингов из-за ограничений скорости (429)")

    # ------------------------------------------------------------------
    # Запись
    # ------------------------------------------------------------------

    def add_documents(self, docs: List[dict], batch_size: int = 50) -> int:
        """Векторизация и сохранение документов в индекс.

        Документы с существующим id перезаписываются.

        Args:
            docs (List[dict]): Список документов вида {'id': str, 'text': str, 'meta': dict}.
            batch_size (int): Размер пакета документов для одного запроса векторизации.

        Returns:
            int: Количество добавленных/обновлённых документов.

        Examples:
            >>> rag.add_documents([{'id': 'titanic', 'text': 'Титаник 1997', 'meta': {'disk': 'ДИСК 1'}}])
        """
        if not docs:
            return 0
        
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i + batch_size]
            texts = [d['text'] for d in batch]
            try:
                vectors = self._embed(texts, task_type='RETRIEVAL_DOCUMENT')
            except Exception as e:
                logger.error(f"Ошибка получения эмбеддингов для батча {i}-{i+len(batch)}: {e}")
                raise e
            with sqlite3.connect(self.db_path) as conn:
                for doc, vec in zip(batch, vectors):
                    conn.execute(
                        'INSERT OR REPLACE INTO rag_index (id, text, meta, embedding) VALUES (?, ?, ?, ?)',
                        (
                            doc['id'],
                            doc['text'],
                            json.dumps(doc.get('meta', {}), ensure_ascii=False),
                            np.array(vec, dtype=np.float32).tobytes(),
                        )
                    )
            import time
            time.sleep(1.0)
        return len(docs)

    def delete_document(self, doc_id: str) -> None:
        """Удаление документа из индекса по id.

        Args:
            doc_id (str): Идентификатор документа.

        Examples:
            >>> rag.delete_document('titanic')
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM rag_index WHERE id = ?', (doc_id,))

    def clear(self) -> None:
        """Полная очистка индекса.

        Examples:
            >>> rag.clear()
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM rag_index')

    # ------------------------------------------------------------------
    # Поиск
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 5, threshold: float = 0.0) -> List[dict]:
        """Семантический поиск ближайших документов по cosine similarity.

        Args:
            query (str): Поисковый запрос.
            top_k (int): Максимальное количество результатов.
            threshold (float): Минимальный порог схожести (0.0–1.0).

        Returns:
            List[dict]: Список {'id', 'text', 'meta', 'score'} отсортированный по убыванию score.

        Examples:
            >>> results = rag.search('фильм про любовь на корабле', top_k=3)
        """
        query_vec = np.array(self._embed([query], task_type='RETRIEVAL_QUERY')[0], dtype=np.float32)
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute('SELECT id, text, meta, embedding FROM rag_index').fetchall()

        if not rows:
            return []

        ids, texts, metas, scores = [], [], [], []
        for row_id, text, meta_str, emb_bytes in rows:
            vec = np.frombuffer(emb_bytes, dtype=np.float32)
            norm = vec / (np.linalg.norm(vec) + 1e-10)
            score = float(np.dot(query_norm, norm))
            if score >= threshold:
                ids.append(row_id)
                texts.append(text)
                metas.append(json.loads(meta_str))
                scores.append(score)

        # Сортировка по убыванию score, обрезка до top_k
        order = np.argsort(scores)[::-1][:top_k]
        return [
            {'id': ids[i], 'text': texts[i], 'meta': metas[i], 'score': round(scores[i], 4)}
            for i in order
        ]

    def count(self) -> int:
        """Количество документов в индексе.

        Returns:
            int: Число записей в rag_index.

        Examples:
            >>> n = rag.count()
        """
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute('SELECT COUNT(*) FROM rag_index').fetchone()[0]
