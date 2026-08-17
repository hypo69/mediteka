# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты LangChain Media Plugin и компонентов
# =============================================================================
# Описание:
#   Тесты для модуля langchain_tools, langchain_prompts, mcp_client,
#   langchain_agent и плагина langchain_media.
#
# File: tests/test_langchain_media.py
# Project: mediteka
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from src.ai.langchain_prompts import (
    MEDIA_SEARCH_SYSTEM_PROMPT,
    TOOL_SELECTION_GUIDELINES,
    RESULT_FORMAT_INSTRUCTIONS,
)
from src.ai.langchain_tools import (
    get_streaming_sources,
    build_player_url,
)
from plugins.langchain_media.langchain_media import LangChainMediaPlugin


class TestLangChainPrompts:
    """Тесты системных промптов LangChain Media Agent."""

    def test_prompts_exist_and_non_empty(self):
        """Проверка наличия и непустоты системных промптов."""
        assert len(MEDIA_SEARCH_SYSTEM_PROMPT) > 0
        assert len(TOOL_SELECTION_GUIDELINES) > 0
        assert len(RESULT_FORMAT_INSTRUCTIONS) > 0
        assert "Mediteka" in MEDIA_SEARCH_SYSTEM_PROMPT
        assert "action" in RESULT_FORMAT_INSTRUCTIONS


class TestLangChainTools:
    """Тесты нативных инструментов LangChain."""

    def test_get_streaming_sources(self):
        """Тест получения стриминговых источников из каталога."""
        raw_result = get_streaming_sources.invoke("Matrix")
        data = json.loads(raw_result)
        assert isinstance(data, dict)
        assert "iframe_players" in data
        assert len(data["iframe_players"]) > 0

    def test_build_player_url_youtube(self):
        """Тест формирования URL для YouTube."""
        raw_result = build_player_url.invoke({
            "url": "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
            "provider": "youtube",
        })
        data = json.loads(raw_result)
        assert data.get("provider") == "youtube"
        assert "embed/aqz-KE-bpKQ" in data.get("embed_url", "")

    def test_build_player_url_vidsrc(self):
        """Тест формирования URL для VidSrc по ID."""
        raw_result = build_player_url.invoke({
            "url": "603",
            "provider": "vidsrc",
        })
        data = json.loads(raw_result)
        assert data.get("provider") == "vidsrc"
        assert "vidsrc.cc/v2/embed/movie/603" in data.get("embed_url", "")


class TestLangChainMediaPlugin:
    """Тесты плагина langchain_media."""

    def test_plugin_creation(self):
        """Тест инициализации плагина."""
        mock_model = MagicMock()
        plugin = LangChainMediaPlugin(mock_model)
        assert plugin.name == "langchain_media"
        assert hasattr(plugin, "can_handle")
        assert hasattr(plugin, "handle")

    def test_can_handle_positive(self):
        """Тест распознавания медиа-запросов."""
        mock_model = MagicMock()
        plugin = LangChainMediaPlugin(mock_model)
        assert plugin.can_handle("найди фильм Интерстеллар")
        assert plugin.can_handle("Где посмотреть сериал?")
        assert plugin.can_handle("скачать фильм 1080p")
        assert plugin.can_handle("найди торрент Дюна")

    def test_can_handle_negative(self):
        """Тест отсечения нерелевантных запросов."""
        mock_model = MagicMock()
        plugin = LangChainMediaPlugin(mock_model)
        assert not plugin.can_handle("Какая погода сегодня?")
        assert not plugin.can_handle("Привет, как дела?")
        assert not plugin.can_handle("")

    def test_format_response_player(self):
        """Тест форматирования ответа для плеера."""
        mock_model = MagicMock()
        plugin = LangChainMediaPlugin(mock_model)
        result_dict = {
            "action": "player",
            "title": "Матрица",
            "source": "hdrezka",
            "url": "https://rezka.ag/matrix",
        }
        html = plugin._format_response(result_dict)
        assert "Матрица" in html
        assert "CosmicPlayer.play" in html

    def test_format_response_torrent(self):
        """Тест форматирования ответа для торрентов."""
        mock_model = MagicMock()
        plugin = LangChainMediaPlugin(mock_model)
        result_dict = {
            "action": "torrent",
            "title": "Интерстеллар",
            "torrents": [
                {
                    "title": "Interstellar 1080p BDRip",
                    "url": "magnet:?xt=urn:btih:123",
                    "source": "rutracker",
                    "size": "14 GB",
                    "seeds": "150",
                }
            ],
        }
        html = plugin._format_response(result_dict)
        assert "Интерстеллар" in html
        assert "download-torrent-btn" in html
        assert "rutracker" in html
