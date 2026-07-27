# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Модульное тестирование FAISS RAG движка
# =============================================================================
# Описание:
#   Тестирование функциональности FaissEngine: индексация, поиск, сохранение.
#
# File: test_code_helper_rag.py
# Project: gemini-simplechat
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import numpy as np
from pathlib import Path
from plugins.code_helper.rag.engine import FaissEngine
import shutil
import os

# Фикстура для создания временной директории индекса
@pytest.fixture
def rag_dir(tmp_path):
    d = tmp_path / "rag_index"
    d.mkdir()
    yield d
    shutil.rmtree(d)

def test_faiss_engine_init(rag_dir):
    """Проверка инициализации движка."""
    engine = FaissEngine(rag_dir)
    assert engine.index_dir == rag_dir
    assert engine.dimension == 768
    assert len(engine.metadatas) == 0

@pytest.mark.anyio
async def test_faiss_engine_add_and_search(rag_dir):
    """Проверка индексации и поиска (мокируем API-ключ)."""
    # ВНИМАНИЕ: Для реального теста нужен API-ключ Gemini,
    # который не должен храниться в коде. Предполагаем, что он есть в ENV.
    api_key = os.getenv('GEMINI_API_KEY') or ''
    if not api_key:
        pytest.skip("API-ключ не найден")
        
    engine = FaissEngine(rag_dir)
    
    docs = [
        {'text': 'Hello world', 'meta': {'path': 'test1.txt'}},
        {'text': 'Gemini RAG testing', 'meta': {'path': 'test2.txt'}}
    ]
    
    success = await engine.add_documents(docs, api_key=api_key)
    assert success is True
    assert len(engine.metadatas) == 2
    
    # Поиск
    results = await engine.search('Hello', api_key=api_key, top_k=1)
    assert len(results) == 1
    assert results[0]['data']['text'] == 'Hello world'
    assert results[0]['score'] >= 0.0

@pytest.mark.anyio
async def test_faiss_engine_save_load(rag_dir):
    """Проверка сохранения и загрузки индекса."""
    api_key = os.getenv('GEMINI_API_KEY') or ''
    if not api_key:
        pytest.skip("API-ключ не найден")

    # Создаем и сохраняем
    engine1 = FaissEngine(rag_dir)
    docs = [{'text': 'Persistent data', 'meta': {'path': 'pers.txt'}}]
    await engine1.add_documents(docs, api_key=api_key)
    
    # Загружаем новый экземпляр
    engine2 = FaissEngine(rag_dir)
    assert len(engine2.metadatas) == 1
    assert engine2.metadatas[0]['text'] == 'Persistent data'
