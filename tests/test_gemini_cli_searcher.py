# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование провайдера веб-поиска Gemini CLI
# =============================================================================
# Описание:
#   Модульные тесты для GeminiCliWebSearcher, интеграции в WebSearchPlugin,
#   административных эндпоинтов и MCP-сервера поиска Gemini CLI.
#
# File: test_gemini_cli_searcher.py
# Project: mediteka
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from plugins.web_search.gemini_cli_searcher import GeminiCliWebSearcher
from plugins.web_search import WebSearchPlugin


class TestGeminiCliWebSearcher:
    """Тесты поискового адаптера Gemini CLI."""

    def test_init_default_model(self):
        """Тест инициализации с моделью по умолчанию."""
        searcher = GeminiCliWebSearcher()
        assert searcher.model_id in ("gemini-3.1-flash-lite", "gemini-2.5-flash") or "gemini" in searcher.model_id

    def test_init_explicit_model(self):
        """Тест инициализации с явно переданной моделью."""
        searcher = GeminiCliWebSearcher(model_id="gemini-3.1-pro-preview")
        assert searcher.model_id == "gemini-3.1-pro-preview"

    def test_model_setter_normalization(self):
        """Тест сеттера модели с нормализацией префиксов."""
        searcher = GeminiCliWebSearcher()
        searcher.model_id = "gemini_cli:gemini-3.1-flash-lite"
        assert searcher.model_id == "gemini-3.1-flash-lite"

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """Тест обработки пустого запроса."""
        searcher = GeminiCliWebSearcher()
        res = await searcher.search_and_extract("   ")
        assert "Пустой" in res

    @pytest.mark.asyncio
    async def test_search_and_extract_success(self):
        """Тест успешного извлечения данных через мок CLI клиента."""
        searcher = GeminiCliWebSearcher(model_id="gemini-3.1-flash-lite")
        mock_response = (
            "YOLO mode is enabled. All tool calls will be automatically approved.\n"
            "## Результаты поиска\n"
            "1. Марсоход Perseverance обнаружил новые образцы.\n"
            "Источники:\n"
            "- https://nasa.gov/perseverance"
        )

        with patch.object(searcher._chat_client, "ask", new_callable=AsyncMock) as mock_ask:
            mock_ask.return_value = mock_response
            res = await searcher.search_and_extract("новости марсохода 2026")
            assert "Марсоход Perseverance" in res
            assert "YOLO mode is enabled" not in res
            assert "https://nasa.gov/perseverance" in res


class TestWebSearchPluginGeminiCliEngine:
    """Тесты маршрутизации WebSearchPlugin для движка gemini_cli."""

    @pytest.mark.asyncio
    async def test_handle_gemini_cli_engine(self):
        """Тест вызова поиска через Gemini CLI в WebSearchPlugin."""
        mock_ai = MagicMock()
        mock_ai.chat = AsyncMock(return_value="Итоговый ответ нейросети")

        p = WebSearchPlugin(mock_ai)
        p._get_config = MagicMock(return_value={
            "engine": "gemini_cli",
            "gemini_cli_model": "gemini-3.1-flash-lite"
        })

        mock_searcher = MagicMock()
        mock_searcher.search_and_extract = AsyncMock(return_value="Контекст поиска через Gemini CLI")
        p._gemini_cli_searcher = mock_searcher

        statuses = []
        async for item in p._handle("поищи в интернете погоду в Тель-Авиве"):
            if "status" in item:
                statuses.append(item["status"])
            if "text" in item:
                assert item["text"] == "Итоговый ответ нейросети"

        assert any("Gemini CLI" in s for s in statuses)
        mock_searcher.search_and_extract.assert_awaited_once()


class TestRouterAdminGeminiCliEndpoints:
    """Тесты эндпоинтов FastAPI для конфигурации поиска Gemini CLI."""

    @pytest.mark.asyncio
    async def test_web_search_config_get_and_set(self):
        """Тест получения и сохранения настроек через router_admin."""
        from src.fastapi.router_admin import WebSearchConfigRequest, set_web_search_config, get_web_search_config
        from starlette.requests import Request

        mock_request = MagicMock(spec=Request)
        mock_request.session = {"user": {"username": "admin", "is_admin": True}}

        # Тест POST
        post_data = WebSearchConfigRequest(
            engine="gemini_cli",
            gemini_model="gemini-2.5-flash",
            gemini_cli_model="gemini-3.1-flash-lite",
            agy_model="agy-flash"
        )
        set_res = await set_web_search_config(mock_request, post_data)
        assert set_res["status"] == "ok"
        assert set_res["engine"] == "gemini_cli"
        assert set_res["gemini_cli_model"] == "gemini-3.1-flash-lite"

        # Тест GET
        get_res = await get_web_search_config(mock_request)
        assert get_res["engine"] == "gemini_cli"
        assert get_res["gemini_cli_model"] == "gemini-3.1-flash-lite"

    @pytest.mark.asyncio
    async def test_web_search_test_endpoint_gemini_cli(self):
        """Тест тестового выполнения поиска через эндпоинт /web-search/test."""
        from src.fastapi.router_admin import WebSearchTestRequest, test_web_search
        from starlette.requests import Request

        mock_request = MagicMock(spec=Request)
        mock_request.session = {"user": {"username": "admin", "is_admin": True}}

        test_data = WebSearchTestRequest(
            query="тестовый запрос",
            engine="gemini_cli"
        )

        with patch("plugins.web_search.gemini_cli_searcher.GeminiCliWebSearcher.search_and_extract", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = "Тестовая выдача Gemini CLI"
            res = await test_web_search(mock_request, test_data)
            assert res["status"] == "ok"
            assert res["engine"] == "gemini_cli"
            assert res["result"] == "Тестовая выдача Gemini CLI"
