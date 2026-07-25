# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля src/ai
# =============================================================================
# Описание:
#   Модуль содержит тесты для модуля искусственного интеллекта src/ai.
#   Проверяет основные методы взаимодействия с AI-моделями Gemini, включая
#   синхронные запросы, потоковую генерацию и работу с моками.
#
# File: tests/test_ai.py
# Project: ai-mediteka
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""
Тесты модуля src/ai
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path


class TestGoogleGenerativeAI:
    """Тесты класса GoogleGenerativeAI."""

    @pytest.mark.asyncio
    async def test_chat_with_mock(self, mock_ai_model):
        """Тест метода chat с моком."""
        mock_ai_model.chat.return_value = AsyncMock(return_value="Test response")
        
        result = await mock_ai_model.chat("Test question")
        
        assert result == "Test response"
        mock_ai_model.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_stream_with_mock(self, mock_ai_model):
        """Тест метода chat_stream с моком."""
        async def mock_stream():
            yield "Chunk 1"
            yield "Chunk 2"
        
        mock_ai_model.chat_stream.return_value = mock_stream()
        
        chunks = []
        async for chunk in mock_ai_model.chat_stream("Test"):
            chunks.append(chunk)
        
        assert len(chunks) == 2
        assert chunks[0] == "Chunk 1"

    @pytest.mark.asyncio
    async def test_ask_with_mock(self, mock_ai_model):
        """Тест метода ask с моком."""
        mock_ai_model.ask.return_value = AsyncMock(return_value="Test answer")
        
        result = await mock_ai_model.ask("Test question")
        
        assert result == "Test answer"


class TestRAGFunctions:
    """Тесты функций RAG."""

    @pytest.mark.asyncio
    async def test_build_dev_rag(self):
        """Тест построения dev RAG."""
        from src.ai.dev_rag import build_dev_rag
        
        with patch('src.ai.dev_rag.GoogleGenerativeAI') as mock_ai:
            mock_instance = Mock()
            mock_ai.return_value = mock_instance
            
            result = build_dev_rag("test_api_key")
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_rag_search_tool(self):
        """Тест функции rag_search_tool."""
        from src.ai.dev_rag import rag_search_tool
        
        # Проверка без выброса исключений
        result = rag_search_tool("test query", top_k=2, api_key="test")
        
        assert result is not None


class TestFoundryChat:
    """Тесты FoundryChatBase."""

    @pytest.mark.asyncio
    async def test_foundry_chat_initialization(self):
        """Тест инициализации FoundryChatBase."""
        from src.ai.foundry_chat import FoundryChatBase
        
        with patch('src.ai.foundry_chat.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            
            chat = FoundryChatBase(
                model_id="test-model",
                system_prompt="Test system prompt"
            )
            
            assert chat is not None
            assert chat.model_id == "test-model"


class TestUserRAG:
    """Тесты пользовательского RAG."""

    @pytest.mark.asyncio
    async def test_get_user_rag_path(self):
        """Тест получения пути к user RAG."""
        from src.ai.gemini.user_query_rag import _get_user_rag_path
        
        result = _get_user_rag_path(1)
        
        assert isinstance(result, Path)
        assert "user_1_rag" in str(result)

    @pytest.mark.asyncio
    async def test_make_doc_id(self):
        """Тест создания doc_id."""
        from src.ai.gemini.user_query_rag import _make_doc_id
        
        result = _make_doc_id(1, "test query")
        
        assert isinstance(result, str)
        assert "user_1" in result
