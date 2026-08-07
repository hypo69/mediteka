# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Перестройка Chat RAG из JSON-хранилища одобренных ответов
# =============================================================================
# Описание:
#   Читает все одобренные ответы из data/chat_responses/*.json и строит
#   FAISS-индекс, который используется для поиска релевантного контекста в чате.
#   Запускается вручную: python rebuild_chat_rag.py
#
# File: rebuild_chat_rag.py
# Project: mediteka
# Package: <root>
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import json
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from src.logger import logger

STORE_DIR = Path(__file__).parent / 'plugins' / 'media_organizer' / 'data' / 'chat_responses'
RAG_DIR = Path(__file__).parent / 'plugins' / 'media_organizer' / 'data'
RAG_FAISS = RAG_DIR / 'chat_rag.faiss'
RAG_META = RAG_DIR / 'chat_rag.json'


def load_all_responses() -> list[dict]:
    """Загружает все JSON-файлы из хранилища одобренных ответов."""
    entries = []
    if not STORE_DIR.exists():
        logger.warning(f'[rebuild_chat_rag] Директория хранилища не найдена: {STORE_DIR}')
        return entries
    for fp in sorted(STORE_DIR.glob('*.json')):
        try:
            entry = json.loads(fp.read_text(encoding='utf-8'))
            entries.append(entry)
        except Exception as ex:
            logger.error(f'[rebuild_chat_rag] Ошибка чтения {fp.name}', ex)
    return entries


def build_rag_index(entries: list[dict]) -> bool:
    """Строит FAISS-индекс из загруженных записей.

    Args:
        entries: Список одобренных ответов из JSON-хранилища.

    Returns:
        True при успехе, False при ошибке.
    """
    if not entries:
        logger.warning('[rebuild_chat_rag] Нет записей для индексации — хранилище пусто.')
        return False

    try:
        from src.ai.gemini.user_query_rag import index_user_query

        api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
        if not api_key_names:
            logger.error('[rebuild_chat_rag] Не заданы GEMINI_API_KEY_NAMES в окружении.')
            return False

        # Для перестройки используем первый доступный ключ
        from src.ai.gemini.generative_ai import GoogleGenerativeAI
        temp_model = GoogleGenerativeAI(api_key_names=api_key_names, sleep_on_exhausted=False)
        api_key = getattr(temp_model, 'api_key', '') or ''

        if not api_key:
            logger.error('[rebuild_chat_rag] Не удалось получить API-ключ.')
            return False

        indexed = 0
        for entry in entries:
            user_id = entry.get('user_id', 'unknown')
            query = entry.get('query', '')
            chat_text = entry.get('chat_text', '')
            voice_text = entry.get('voice_text', '')
            combined = f"Текст для чата:\n{chat_text}\n\nТекст для диктора:\n{voice_text}"

            success = index_user_query(user_id, api_key, query, combined)
            if success:
                indexed += 1

        logger.info(f'[rebuild_chat_rag] Проиндексировано {indexed}/{len(entries)} записей.')
        return True

    except Exception as ex:
        logger.error('[rebuild_chat_rag] Ошибка построения RAG-индекса', ex)
        return False


if __name__ == '__main__':
    print('=' * 60)
    print('  Перестройка Chat RAG из JSON-хранилища одобренных ответов')
    print('=' * 60)

    entries = load_all_responses()
    print(f'  Найдено записей: {len(entries)}')

    if not entries:
        print('  Хранилище пусто. Добавьте одобренные ответы через кнопку 💾 в чате.')
        sys.exit(0)

    success = build_rag_index(entries)
    if success:
        print('  ✅ RAG-индекс успешно перестроен.')
    else:
        print('  ❌ Ошибка при перестройке RAG-индекса. Смотрите логи.')
        sys.exit(1)
