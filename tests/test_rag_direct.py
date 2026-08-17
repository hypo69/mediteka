# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты прямого RAG ответа
# =============================================================================
# Описание:
#   Тестирование прямого возврата карточек и списков тайтлов из RAG плагина
#   без обращения к языковой модели.
#
# File: tests/test_rag_direct.py
# Project: gemini-simplechat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from unittest.mock import MagicMock
from plugins.rag import RAGPlugin


class TestRAGDirect:
    """Тестирование прямого возврата данных из RAG."""

    @pytest.mark.asyncio
    async def test_rag_multi_items_direct(self):
        """Тест запроса жанра/подборки (возврат списка без LLM)."""
        mock_model = MagicMock()
        plugin = RAGPlugin(mock_model)

        chunks = []
        res = await plugin.handle("боевики")
        async for chunk in res:
            chunks.append(chunk)

        # Модель не должна вызываться
        mock_model.chat.assert_not_called()
        mock_model.chat_stream.assert_not_called()
        mock_model.ask.assert_not_called()

        text_chunks = [c for c in chunks if "text" in c]
        assert len(text_chunks) > 0
        text = text_chunks[0]["text"]
        assert "<film>" in text
        assert "Игры возмездия" in text or "Список смертников" in text or "Самаритянин" in text

    @pytest.mark.asyncio
    async def test_rag_single_item_direct(self):
        """Тест запроса конкретного фильма (возврат JSON карточки без LLM)."""
        mock_model = MagicMock()
        plugin = RAGPlugin(mock_model)

        chunks = []
        res = await plugin.handle("Самаритянин")
        async for chunk in res:
            chunks.append(chunk)

        # Модель не должна вызываться
        mock_model.chat.assert_not_called()
        mock_model.chat_stream.assert_not_called()
        mock_model.ask.assert_not_called()

        text_chunks = [c for c in chunks if "text" in c]
        assert len(text_chunks) > 0
        text = text_chunks[0]["text"]
        assert "Самаритянин" in text
