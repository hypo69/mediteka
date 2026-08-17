# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование провайдеров веб-поиска и MCP-серверов
# =============================================================================

import os
import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

import importlib.util
from pathlib import Path

from plugins.web_search.gemini_searcher import GeminiKeyPool, GeminiWebSearcher
from plugins.web_search.agy_searcher import AgyWebSearcher
from plugins.web_search import WebSearchPlugin

_mcp_dir = Path(__file__).resolve().parent.parent / ".mcp"

def _load_mcp_module(filename: str):
    spec = importlib.util.spec_from_file_location(filename, _mcp_dir / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_gemini_mcp = _load_mcp_module("gemini_search_mcp_server.py")
gemini_web_search = _gemini_mcp.gemini_web_search
gemini_key_pool_status = _gemini_mcp.gemini_key_pool_status

_agy_mcp = _load_mcp_module("agy_search_mcp_server.py")
agy_web_search = _agy_mcp.agy_web_search



class TestGeminiKeyPool:
    """Тесты пула ротации API-ключей Gemini."""

    def test_init_with_valid_keys(self):
        """Тест инициализации с валидным списком ключей."""
        keys = ["AIzaSyKey1_test", "AIzaSyKey2_test"]
        pool = GeminiKeyPool(keys)
        assert len(pool.api_keys) == 2
        assert pool._current_key == "AIzaSyKey1_test"

    def test_rotate_key(self):
        """Тест ротации ключей по кругу."""
        keys = ["KeyA_123456", "KeyB_123456", "KeyC_123456"]
        pool = GeminiKeyPool(keys)
        assert pool._current_key == "KeyA_123456"

        k2 = pool._rotate_key()
        assert k2 == "KeyB_123456"
        assert pool._current_key == "KeyB_123456"

        k3 = pool._rotate_key()
        assert k3 == "KeyC_123456"

        # Проверка закольцованности (Round-Robin)
        k1_again = pool._rotate_key()
        assert k1_again == "KeyA_123456"

    def test_generate_with_search_success(self):
        """Тест успешной генерации с поиском."""
        keys = ["Key1_123456"]
        pool = GeminiKeyPool(keys)

        mock_resp = MagicMock()
        mock_resp.text = "Результаты поиска FastAPI 2026"
        mock_candidate = MagicMock()
        
        mock_chunk = MagicMock()
        mock_chunk.web.title = "FastAPI Docs"
        mock_chunk.web.uri = "https://fastapi.tiangolo.com"
        mock_chunk.web.domain = "fastapi.tiangolo.com"

        mock_grounding = MagicMock()
        mock_grounding.web_search_queries = ["FastAPI 2026 releases"]
        mock_grounding.grounding_chunks = [mock_chunk]

        mock_candidate.grounding_metadata = mock_grounding
        mock_resp.candidates = [mock_candidate]

        pool._client.models.generate_content = MagicMock(return_value=mock_resp)

        res = pool.generate_with_search("FastAPI 2026")
        assert res["text"] == "Результаты поиска FastAPI 2026"
        assert len(res["sources"]) == 1
        assert res["sources"][0]["url"] == "https://fastapi.tiangolo.com"
        assert res["search_queries"] == ["FastAPI 2026 releases"]


class TestGeminiWebSearcher:
    """Тесты обертки GeminiWebSearcher."""

    @pytest.mark.asyncio
    async def test_search_and_extract(self):
        """Тест формирования итогового контекста с источниками."""
        searcher = GeminiWebSearcher(api_keys=["Key1_123456"])
        mock_pool = MagicMock()
        mock_pool.generate_with_search.return_value = {
            "text": "Найдены свежие факты о фильме.",
            "sources": [
                {"title": "Кинопоиск", "url": "https://kinopoisk.ru/item/1"}
            ],
            "search_queries": ["сюжет фильма"]
        }
        searcher._pool_instance = mock_pool

        result = await searcher.search_and_extract("фильм Начало")
        assert "Найдены свежие факты о фильме." in result
        assert "[Кинопоиск](https://kinopoisk.ru/item/1)" in result


class TestAgyWebSearcher:
    """Тесты поисковика Antigravity (AGY)."""

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """Тест обработки пустого запроса."""
        searcher = AgyWebSearcher()
        res = await searcher.search_and_extract("")
        assert "Пустой" in res

    @pytest.mark.asyncio
    async def test_search_via_sdk_mock(self):
        """Тест вызова поиска через мок SDK."""
        searcher = AgyWebSearcher(model_id="agy-flash")
        with patch.object(searcher, "_search_via_sdk", new_callable=AsyncMock) as mock_sdk:
            mock_sdk.return_value = "Результат поиска от Antigravity Agent"
            res = await searcher.search_and_extract("новинки кино 2026")
            assert "Результат поиска от Antigravity Agent" in res


class TestWebSearchPluginEngines:
    """Тесты маршрутизации движков в WebSearchPlugin."""

    @pytest.mark.asyncio
    async def test_handle_gemini_engine(self):
        """Тест выполнения поиска с движком gemini."""
        mock_ai = MagicMock()
        mock_ai.chat = AsyncMock(return_value="Суммаризированный ответ")

        p = WebSearchPlugin(mock_ai)
        p._get_engine = MagicMock(return_value="gemini")
        
        mock_searcher = MagicMock()
        mock_searcher.search_and_extract = AsyncMock(return_value="Контекст поиска Gemini")
        p._gemini_searcher = mock_searcher

        statuses = []
        async for item in p._handle("поищи в интернете информацию про квантовые компьютеры"):
            if "status" in item:
                statuses.append(item["status"])
            if "text" in item:
                assert item["text"] == "Суммаризированный ответ"

        assert any("Gemini (Grounding)" in s for s in statuses)

    @pytest.mark.asyncio
    async def test_handle_agy_engine(self):
        """Тест выполнения поиска с движком agy."""
        mock_ai = MagicMock()
        mock_ai.chat = AsyncMock(return_value="Суммаризированный ответ")

        p = WebSearchPlugin(mock_ai)
        p._get_engine = MagicMock(return_value="agy")
        
        mock_searcher = MagicMock()
        mock_searcher.search_and_extract = AsyncMock(return_value="Контекст поиска AGY")
        p._agy_searcher = mock_searcher

        statuses = []
        async for item in p._handle("поищи в интернете последние космические миссии"):
            if "status" in item:
                statuses.append(item["status"])
            if "text" in item:
                assert item["text"] == "Суммаризированный ответ"

        assert any("Antigravity (AGY)" in s for s in statuses)


class TestMcpServers:
    """Тесты инструментов FastMCP серверов."""

    @pytest.mark.asyncio
    async def test_gemini_mcp_tool(self):
        """Тест gemini_web_search инструмента."""
        with patch("plugins.web_search.gemini_searcher.GeminiWebSearcher.search_and_extract", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = "MCP Gemini search result"
            res = await gemini_web_search("тестовый запрос")
            assert res == "MCP Gemini search result"

    @pytest.mark.asyncio
    async def test_agy_mcp_tool(self):
        """Тест agy_web_search инструмента."""
        with patch("plugins.web_search.agy_searcher.AgyWebSearcher.search_and_extract", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = "MCP AGY search result"
            res = await agy_web_search("тестовый запрос")
            assert res == "MCP AGY search result"
