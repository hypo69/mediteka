# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Пользовательский RAG на основе истории чата
# =============================================================================
# Описание:
#   Каждый запрос пользователя (вопрос + ответ модели) индексируется
#   в персональную SQLite-базу с Gemini-эмбеддингами.
#   Позволяет модели «помнить» предпочтения и прошлые запросы пользователя.
#
# File: user_query_rag.py
# Project: ai-mediteka
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Optional

from src.ai.gemini.rag import GeminiRAG
from src.logger import logger

# Директория для хранения пользовательских RAG-баз
_USER_RAGS_DIR = Path(__file__).parent / "user_rags"
_USER_RAGS_DIR.mkdir(exist_ok=True)

# Максимальное количество документов в одной базе (старые вытесняются)
_MAX_DOCS_PER_USER = 500

# Минимальная длина запроса для индексации (исключаем "да", "нет" и т.п.)
_MIN_QUERY_LEN = 10


def _get_user_rag_path(user_id) -> Path:
    """Возвращает путь к RAG-базе конкретного пользователя."""
    safe_id = str(user_id).replace(".", "_").replace("/", "_").replace("\\", "_")
    return _USER_RAGS_DIR / f"user_rag_{safe_id}.db"


def _make_doc_id(user_id, query: str) -> str:
    """Генерирует стабильный уникальный ID документа (дедупликация по запросу)."""
    key = f"{user_id}_{query.strip().lower()}"
    return f"{user_id}_{hashlib.md5(key.encode('utf-8')).hexdigest()}"


def get_user_rag(user_id, api_key: str) -> GeminiRAG:
    """Возвращает RAG-индекс для конкретного пользователя.

    Создаёт базу если её нет. Не перестраивает существующую.

    Args:
        user_id: ID пользователя (int из БД или строка "anon_<IP>").
        api_key: Ключ Gemini API для эмбеддингов.

    Returns:
        GeminiRAG: Экземпляр пользовательского RAG-индекса.
    """
    db_path = _get_user_rag_path(user_id)
    return GeminiRAG(api_key=api_key, db_path=db_path)


def index_user_query(
    user_id,
    api_key: str,
    query: str,
    response: str,
) -> bool:
    """Индексирует пару (запрос пользователя + ответ модели) в персональный RAG.

    Пропускает слишком короткие запросы и дубликаты (по хешу).
    При переполнении (> _MAX_DOCS_PER_USER) удаляет старейшие записи.

    Args:
        user_id: ID пользователя или строка "anon_<IP>".
        api_key: Ключ Gemini API.
        query: Текст запроса пользователя.
        response: Ответ модели.

    Returns:
        bool: True если документ был добавлен/обновлён, False если пропущен.
    """
    if not query or not response:
        return False

    # Не индексируем очень короткие запросы (да / нет / ок)
    if len(query.strip()) < _MIN_QUERY_LEN:
        return False

    try:
        rag = get_user_rag(user_id, api_key)

        # Прореживание при переполнении — удаляем старейшие записи
        _prune_if_needed(rag, user_id)

        doc_id = _make_doc_id(user_id, query)
        doc_text = f"Пользователь спросил: {query}\nОтвет модели: {response}"

        rag.add_documents([{
            "id": doc_id,
            "text": doc_text,
            "meta": {
                "user_id": str(user_id),
                "timestamp": time.time(),
                "q": query[:500],
                "response": response[:1000],
            },
        }])
        return True

    except Exception as ex:
        logger.error(f"Ошибка индексации запроса пользователя {user_id}", ex, False)
        return False


def search_user_context(
    user_id,
    api_key: str,
    query: str,
    top_k: int = 3,
    threshold: float = 0.4,
) -> list:
    """Семантический поиск по истории запросов пользователя.

    Args:
        user_id: ID пользователя.
        api_key: Ключ Gemini API.
        query: Текущий запрос для поиска похожего контекста.
        top_k: Количество результатов.
        threshold: Минимальный порог схожести (0.0-1.0).

    Returns:
        list[dict]: Список {"id", "text", "meta", "score"} по убыванию score.
    """
    try:
        rag = get_user_rag(user_id, api_key)
        if rag.count() == 0:
            return []
        return rag.search(query, top_k=top_k, threshold=threshold)
    except Exception as ex:
        logger.error(f"Ошибка поиска по RAG пользователя {user_id}", ex, False)
        return []


def get_user_rag_stats(user_id, api_key: str) -> dict:
    """Возвращает статистику RAG-индекса пользователя.

    Args:
        user_id: ID пользователя.
        api_key: Ключ Gemini API.

    Returns:
        dict: Поля count, db_path, db_size_kb.
    """
    db_path = _get_user_rag_path(user_id)
    try:
        rag = get_user_rag(user_id, api_key)
        count = rag.count()
    except Exception:
        count = 0

    size_kb = round(db_path.stat().st_size / 1024, 1) if db_path.exists() else 0
    return {
        "user_id": str(user_id),
        "count": count,
        "db_path": str(db_path),
        "db_size_kb": size_kb,
    }


def clear_user_rag(user_id, api_key: str) -> bool:
    """Полная очистка персонального RAG-индекса пользователя.

    Args:
        user_id: ID пользователя.
        api_key: Ключ Gemini API.

    Returns:
        bool: True при успехе.
    """
    try:
        rag = get_user_rag(user_id, api_key)
        rag.clear()
        return True
    except Exception as ex:
        logger.error(f"Ошибка очистки RAG пользователя {user_id}", ex, False)
        return False


# =============================================================================
# Internal helpers
# =============================================================================

def _prune_if_needed(rag: GeminiRAG, user_id) -> None:
    """Удаляет старейшие документы если индекс превысил _MAX_DOCS_PER_USER.

    Стратегия: читаем meta.timestamp из всех документов, удаляем 10% старейших.
    """
    count = rag.count()
    if count < _MAX_DOCS_PER_USER:
        return

    try:
        import sqlite3
        import json

        with sqlite3.connect(rag.db_path) as conn:
            rows = conn.execute("SELECT id, meta FROM rag_index").fetchall()

        parsed = []
        for row_id, meta_str in rows:
            try:
                meta = json.loads(meta_str)
                ts = float(meta.get("timestamp", 0))
            except Exception:
                ts = 0
            parsed.append((row_id, ts))

        parsed.sort(key=lambda x: x[1])
        to_delete = parsed[:max(1, count // 10)]

        for doc_id, _ in to_delete:
            rag.delete_document(doc_id)

        logger.info(f"UserRAG [{user_id}]: удалено {len(to_delete)} старых записей (было {count})")

    except Exception as ex:
        logger.error(f"Ошибка прореживания RAG пользователя {user_id}", ex, False)
