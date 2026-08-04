# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Система RAG (Core)
# =============================================================================
# Описание:
#   Основной класс для работы с векторным поиском и извлечением контекста.
#   Управляет загрузкой индексов FAISS и поиском релевантных чанков.
#
# File: src/rag/rag_system.py
# Project: Ai Assistant (Docker)
# Package: src.rag
# Module: rag_system
# Version: 0.6.1
# Changes in 0.6.1:
#   - index_directories: fixed config access (config.get_section instead of config.rag_system.get)
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import json
from datetime import datetime
import logging
from pathlib import Path
import numpy as np
from typing import List, Dict, Any, Optional

import faiss
from src.logger import logger
from src.core.config import config

class RAGSystem:
    """Класс для управления жизненным циклом RAG индекса и выполнения поиска."""

    def __init__(self) -> None:
        """Инициализация экземпляра RAG системы."""
        self.index: Optional[faiss.Index] = None
        self.chunks: List[Dict[str, Any]] = []
        self.model: Any = None
        self._search_cache: Dict[tuple, List[Dict[str, Any]]] = {} # Кэш для результатов поиска
        self.current_index_dir: Optional[str] = None
        self._sqlite_backed_index: bool = False
        self.source_dirs: List[Path] = [] # Список исходных директорий для индексации
        self.RAG_HOME: Path = Path(config.dir_rag).expanduser()

    def _profile_index_dir(self, safe_name: str) -> Path:
        """Получение пути к директории профиля."""
        self.RAG_HOME = Path(config.dir_rag).expanduser()
        return self.RAG_HOME / safe_name

    def _get_model(self) -> Any:
        """Инициализация и получение модели эмбеддингов.

        ПОЧЕМУ ВЫБРАНА ЛЕНИВАЯ ЗАГРУЗКА:
          - Модели SentenceTransformers (например, mpnet или MiniLM) занимают значительный объем RAM.
          - Загрузка при первом обращении предотвращает задержки при старте сервера, если RAG не используется.

        Returns:
            Any: Экземпляр SentenceTransformer.
        """
        if self.model is None:
            # Импорт внутри метода для предотвращения задержек при инициализации модуля
            # Import inside the method to prevent initialization delays
            from sentence_transformers import SentenceTransformer
            
            model_name: str = config.rag_model
            logger.info(f"Загрузка модели эмбеддингов: {model_name}")
            self.model = SentenceTransformer(model_name)
            
        return self.model

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Поиск релевантных фрагментов текста в векторном индексе.

        ПОЧЕМУ ИСПОЛЬЗУЕТСЯ ЭТА РЕАЛИЗАЦИЯ:
          - FAISS обеспечивает сверхбыстрый поиск в векторном пространстве.
          - SentenceTransformers гарантирует высокое качество семантического сопоставления.
          - Проверка наличия индекса предотвращает ошибки при пустой базе знаний.

        Args:
            query (str): Текст поискового запроса.
            top_k (int): Количество возвращаемых результатов.

        Returns:
            List[Dict[str, Any]]: Список найденных сегментов с контентом и оценкой схожести.
        """
        results: List[Dict[str, Any]] = []
        query_vector: np.ndarray = None
        distances: np.ndarray = None
        
        # Проверка кеша
        # Cache check
        cache_key = (query, top_k)
        if cache_key in self._search_cache:
            logger.debug(f"Возвращение результатов поиска из кеша для запроса: '{query[:50]}...'")
            return self._search_cache[cache_key]
        indices: np.ndarray = None
        model: Any = None
        
        # Проверка готовности системы к поиску
        # System readiness check for search
        if not self.index:
            logger.warning("Поиск невозможен: индекс не загружен.")
            return []

        if not query.strip():
            return []

        if self.index.ntotal <= 0:
            return []

        try:
            # Получение модели и генерация вектора запроса
            # Retrieval of the model and generation of the query vector
            model = self._get_model()
            query_vector = model.encode([query]).astype('float32')
            faiss.normalize_L2(query_vector)

            # Выполнение поиска в FAISS
            # Execution of the FAISS search
            search_k = top_k
            if self._sqlite_backed_index:
                search_k = min(max(top_k * 5, top_k), self.index.ntotal)
            distances, indices = self.index.search(query_vector, search_k)

            # Сборка результатов на основе найденных индексов
            # Assembly of results based on discovered indices
            if self._sqlite_backed_index and self.current_index_dir:
                from .document_store import DocumentStore

                ids = [int(idx) for idx in indices[0] if idx != -1]
                store = DocumentStore(Path(self.current_index_dir) / "documents.db")
                chunks_by_id = store.get_active_chunks_by_ids(ids)

                for i, idx in enumerate(indices[0]):
                    chunk_row = chunks_by_id.get(int(idx))
                    if not chunk_row:
                        continue

                    chunk = {
                        "id": chunk_row["id"],
                        "document_id": chunk_row["document_id"],
                        "source": chunk_row.get("source_path") or chunk_row.get("doc_title"),
                        "path": chunk_row.get("source_path", ""),
                        "section": chunk_row.get("doc_title", ""),
                        "text": chunk_row["text"],
                        "content": chunk_row["text"],
                        "score": float(distances[0][i]),
                    }
                    results.append(chunk)
                    if len(results) >= top_k:
                        break
            else:
                for i, idx in enumerate(indices[0]):
                    if idx == -1 or idx >= len(self.chunks):
                        continue

                    chunk = self.chunks[idx].copy()

                    # Конвертация расстояния в score (нормализация зависит от типа индекса)
                    # Conversion of distance to score
                    chunk['score'] = float(distances[0][i])
                    results.append(chunk)

            # Сохранение результатов в кеш
            # Saving results to cache
            self._search_cache[cache_key] = results
            logger.debug(f"Поиск завершен. Найдено результатов: {len(results)}")
            return results

        except Exception as e:
            logger.error(f"Ошибка при выполнении векторного поиска: {e}")
            return []

    def _check_index_integrity(self, index_file: Path) -> bool:
        """Проверка целостности и доступности файла индекса FAISS.

        Обоснование:
          - Предотвращение загрузки поврежденных или пустых файлов.
          - Базовая проверка прав доступа и размера заголовка.

        Args:
            index_file (Path): Путь к файлу faiss.index.

        Returns:
            bool: True если файл прошел проверку.
        """
        file_size: int = 0

        if not index_file.exists():
            logger.warning(f"Файл faiss.index не найден: {index_file}")
            return False

        if not index_file.is_file():
            logger.error(f"Путь к индексу не является файлом: {index_file}")
            return False

        try:
            file_size = index_file.stat().st_size
            # Минимальный размер заголовка FAISS индекса (~100 байт)
            # Minimal FAISS index header size check
            if file_size < 100:
                logger.error(f"Файл индекса слишком мал или поврежден ({file_size} байт): {index_file}")
                return False
        except Exception as e:
            logger.error(f"Ошибка доступа к файлу индекса: {e}")
            return False

        return True

    def _remove_duplicate_chunks(self) -> None:
        """Удаление дубликатов фрагментов текста из текущего набора чанков.

        Обоснование:
          - Предотвращает избыточность контекста при поиске.
          - Уменьшает потребление памяти.
          - Использует уникальность текста как критерий идентичности.
        """
        unique_chunks: List[Dict[str, Any]] = []
        seen_texts: set = set()

        for chunk in self.chunks:
            # Получение текста из полей 'text' или 'content'
            # Retrieval of text from 'text' or 'content' fields
            text = chunk.get('text', chunk.get('content', ''))
            if text and text not in seen_texts:
                seen_texts.add(text)
                unique_chunks.append(chunk)

        if len(unique_chunks) < len(self.chunks):
            logger.info(f"Очистка дубликатов: удалено {len(self.chunks) - len(unique_chunks)} фрагментов")
            self.chunks = unique_chunks

    async def index_directories(self, source_dirs: List[str] = None) -> bool:
        """Индексация нескольких директорий и обновление векторной базы.
        
        ПОЧЕМУ ЭТО ВАЖНО:
          - Позволяет объединять знания из разных локальных источников.
          - Использует TextExtractor для обработки файлов (PDF, DOCX и др.).
          
        Args:
            source_dirs (List[str], optional): Список путей. Если None, берутся из конфига.
        """
        dirs_to_process = source_dirs or config.get_section("rag_system").get("source_dirs", [])
        if not dirs_to_process:
            logger.warning("Список директорий для индексации пуст.")
            return False

        logger.info(f"Начало индексации из {len(dirs_to_process)} источников...")
        
        # Обоснование: В текущей реализации мы предполагаем наличие внешнего 
        # компонента TextExtractor, который вызывается для каждого файла в папках.
        # Здесь должна быть логика обхода и вызова эмбеддингов.
        
        all_new_chunks = []
        for folder in dirs_to_process:
            folder_path = Path(folder).expanduser()
            if not folder_path.exists():
                logger.error(f"Директория не найдена: {folder_path}")
                continue
            
            logger.debug(f"Обработка папки: {folder_path}")
            # Логика извлечения текста и создания чанков...
            # (В реальном сценарии здесь вызывается TextExtractor)
        
        self.source_dirs = [Path(d) for d in dirs_to_process]
        # После сбора всех данных — обновление текущего индекса
        # self.index = ... (создание FAISS индекса из накопленных векторов)
        return True

    async def initialize(self) -> bool:
        """Инициализация RAG системы при старте приложения.

        Загружает индекс из директории, заданной в конфигурации.
        Если индекс не найден — возвращает False без ошибки.

        Returns:
            bool: True если индекс успешно загружен.
        """
        index_dir = config.rag_index_dir
        index_path = Path(index_dir).expanduser() / "faiss.index"
        if not index_path.exists():
            logger.warning(f"⚠️ RAG index not found at {index_path}, skipping load")
            return False
        return await self.reload_index(index_dir)

    async def reload_index(self, index_dir: str) -> bool:
        """Динамическая перезагрузка индекса RAG для смены профилей.

        ПОЧЕМУ ВЫБРАНО ЭТО РЕШЕНИЕ:
          - Позволяет переключать контекст знаний "на лету" без перезапуска API.
          - Использует стандартные файлы .index и .json для совместимости с индоксером.
          - Обеспечивает атомарность: состояние обновляется только после успешной загрузки файлов.

        Args:
            index_dir (str): Путь к директории с файлами faiss.index и chunks.json.

        Returns:
            bool: True если индекс и чанки успешно загружены.
        """
        path: Path = Path(index_dir).expanduser()
        index_file: Path = path / "faiss.index"
        chunks_file: Path = path / "chunks.json"
        loaded_index: Optional[faiss.Index] = None
        loaded_chunks: List[Dict[str, Any]] = []

        model: Any = None
        model_dim: int = 0
        index_dim: int = 0

        logger.info(f"Перезагрузка RAG профиля: {path}")

        if not path.exists(): # Проверка существования директории
            logger.error(f"Директория RAG индекса не найдена: {path}")
            return False

        # Проверка целостности индекса перед загрузкой
        # Index integrity check before loading
        if not self._check_index_integrity(index_file):
            return False

        try:
            # Загрузка векторной базы
            # Loading of the FAISS index
            loaded_index = faiss.read_index(str(index_file))
            
            # Проверка совместимости размерности векторов
            # Verification of vector dimension compatibility
            model = self._get_model()
            model_dim = model.get_sentence_embedding_dimension()
            index_dim = loaded_index.d
            
            if model_dim != index_dim:
                logger.error(
                    f"Несовместимость размерности векторов! "
                    f"Модель ({config.rag_model}): {model_dim}, Индекс: {index_dim}. "
                    f"Профиль: {path}"
                )
                return False
            
            # Загрузка метаданных (текстовых сегментов)
            # Loading of the chunk metadata
            if chunks_file.exists():
                loaded_chunks = json.loads(chunks_file.read_text(encoding="utf-8"))
            sqlite_backed_index = (path / "documents.db").exists() and "IDMap" in type(loaded_index).__name__
            
            # Атомарное обновление состояния системы
            # Atomic update of the system state
            self.index = loaded_index
            self.chunks = loaded_chunks
            self._sqlite_backed_index = sqlite_backed_index

            # Очистка дубликатов фрагментов
            # Removal of duplicate fragments
            self._remove_duplicate_chunks()

            self.current_index_dir = str(path)
            
            # Очистка кеша поиска при перезагрузке индекса
            # Clearing search cache on index reload
            self._search_cache = {}
            
            # Автоматическое сохранение метаданных при перезагрузке
            # Automatic saving of metadata on reload
            meta_file = path / "meta.json"
            meta_data = {}
            if meta_file.exists():
                try:
                    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
                except Exception:
                    logger.debug(f"Ошибка чтения meta.json в {path}, создание новой структуры")
            
            meta_data.update({
                "index_dir": str(path),
                "chunks": len(self.chunks),
                "model": config.rag_model,
                "updated_at": datetime.now().isoformat()
            })
            
            if "name" not in meta_data:
                meta_data["name"] = path.name

            meta_file.write_text(json.dumps(meta_data, ensure_ascii=False, indent=2), encoding="utf-8")
            
            logger.info(f"RAG профиль успешно изменен. Активно чанков: {len(self.chunks)}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при смене RAG профиля: {e}")
            return False

    def format_context(self, results: List[Dict[str, Any]]) -> str:
        """Форматирование результатов поиска в единый блок текста."""
        # Объединение текстовых фрагментов через двойной перенос строки
        # Joining of text fragments with double newline
        return "\n\n".join([r.get("text", r.get("content", "")) for r in results])

    def filter_by_source(self, results: List[Dict[str, Any]], sources: List[str]) -> List[Dict[str, Any]]:
        """Фильтрация результатов поиска по списку источников.

        Обоснование:
          - Ограничение области поиска конкретными документами.
          - Поддержка пользовательских фильтров в интерфейсе.

        Args:
            results (List[Dict[str, Any]]): Список результатов поиска.
            sources (List[str]): Список названий источников для фильтрации.

        Returns:
            List[Dict[str, Any]]: Отфильтрованные результаты.
        """
        filtered: List[Dict[str, Any]] = []
        source_set: set = set(sources)
        res: Dict[str, Any] = None

        for res in results:
            # Сопоставление источника со списком разрешенных
            # Matching the source with the allowed list
            if res.get('source') in source_set:
                filtered.append(res)

        return filtered

    def filter_by_score(self, results: List[Dict[str, Any]], min_score: float) -> List[Dict[str, Any]]:
        """Фильтрация результатов поиска по минимальному порогу схожести.

        Обоснование:
          - Отсечение нерелевантных фрагментов с низким весом совпадения.
          - Повышение качества контекста для LLM.

        Args:
            results (List[Dict[str, Any]]): Список результатов поиска.
            min_score (float): Минимальный порог схожести.

        Returns:
            List[Dict[str, Any]]: Отфильтрованные результаты.
        """
        filtered: List[Dict[str, Any]] = []
        res: Dict[str, Any] = None

        for res in results:
            # Сравнение оценки схожести с пороговым значением
            # Comparison of the similarity score with the threshold value
            if res.get('score', 0.0) >= min_score:
                filtered.append(res)

        return filtered

rag_system = RAGSystem()
