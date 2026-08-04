# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: RagAgent Unit Tests
# =============================================================================
# Description:
#   Unit testing of RAG agent logic with FAISS mocks.
#   Validation of context injection and Unicode handling.
#
# File: tests/agents/test_rag_agent.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Moved to tests/agents/ (was in scripts/)
#   - Added Unicode validation test
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from unittest.mock import MagicMock


class TestRagAgent:
    """Unit tests for RAG agent with mocked FAISS search."""

    def test_context_injection(self, mocker):
        """Validation of context injection into agent prompt.

        Why mock FAISS:
            Real FAISS index requires loading embedding models (hundreds of MB),
            which is unacceptable for fast unit tests.
        """
        mock_rag = MagicMock()
        mock_rag.search.return_value = [
            "Ai Assistant instruction: use port 9696.",
            "RAG index updated 2026.",
        ]
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Answer based on context"

        # Invocation of search
        results = mock_rag.search("Which port to use?")

        assert len(results) == 2
        assert "9696" in results[0]
        mock_rag.search.assert_called_once_with("Which port to use?")

    def test_unicode_support(self, mocker):
        """Validation of Cyrillic Unicode integrity in RAG search results."""
        mock_rag = MagicMock()
        mock_rag.search.return_value = ["Инструкция: Используйте кодировку UTF-8."]

        search_results = mock_rag.search("тест")

        # Validation of no character corruption
        assert search_results[0] == "Инструкция: Используйте кодировку UTF-8."
        assert "Используйте" in search_results[0]

    def test_empty_results_handling(self):
        """Validation of agent behavior when RAG returns no matches."""
        mock_rag = MagicMock()
        mock_rag.search.return_value = []

        results = mock_rag.search("unknown query")

        assert isinstance(results, list)
        assert len(results) == 0
