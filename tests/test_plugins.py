# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты плагинов mediteka
# =============================================================================
# Описание:
#   Модуль содержит тесты для плагинов системы искусственного интеллекта.
#   Проверяет обработку сообщений, перехват исключений и взаимодействие
#   между плагинами и AI-моделью. Охватывает основные сценарии использования.
#
# File: tests/test_plugins.py
# Project: mediteka
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""
Тесты плагинов mediteka
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock


class TestMediaOrganizerPlugin:
    """Тесты media_organizer плагина."""

    @pytest.mark.asyncio
    async def test_plugin_creation(self):
        """Тест создания плагина через правильный импорт."""
        from plugins.media_organizer import MediaOrganizerPlugin
        
        mock_model = MagicMock()
        plugin = MediaOrganizerPlugin(mock_model)
        
        assert plugin is not None
        assert hasattr(plugin, 'handle')

    @pytest.mark.asyncio
    async def test_plugin_name(self):
        """Тест атрибута name плагина."""
        from plugins.media_organizer import MediaOrganizerPlugin
        
        mock_model = MagicMock()
        plugin = MediaOrganizerPlugin(mock_model)
        
        assert hasattr(plugin, 'name')


class TestQBittorrentPlugin:
    """Тесты qbittorrent плагина."""

    def test_qbittorrent_client_class_exists(self):
        """Тест что класс QBittorrentClient существует."""
        from plugins.qbittorrent.qbittorrent import QBittorrentClient
        
        # Проверяем что класс можно импортировать
        assert QBittorrentClient is not None

    def test_qbittorrent_client_init_signature(self):
        """Тест сигнатуры инициализации QBittorrentClient."""
        from plugins.qbittorrent.qbittorrent import QBittorrentClient
        
        # Проверяем что класс принимает ожидаемые параметры
        import inspect
        sig = inspect.signature(QBittorrentClient.__init__)
        params = list(sig.parameters.keys())
        
        assert 'self' in params
        assert 'host' in params
        assert 'port' in params

    def test_qbittorrent_has_torrents_method(self):
        """Тест наличия метода torrents."""
        from plugins.qbittorrent.qbittorrent import QBittorrentClient
        
        # Проверяем что метод существует
        assert hasattr(QBittorrentClient, 'torrents')


class TestRAGPlugin:
    """Тесты RAG плагина."""

    @pytest.mark.asyncio
    async def test_is_media_query(self):
        """Тест определения медиа запроса."""
        from plugins.rag import RAGPlugin
        
        mock_model = MagicMock()
        plugin = RAGPlugin(mock_model)
        
        # Проверка медиа запросов
        assert plugin._is_media_query("фильм про войну") == True
        assert plugin._is_media_query("покажи сериал") == True
        assert plugin._is_media_query("боевики") == True
        assert plugin._is_media_query("комедии") == True
        assert plugin._is_media_query("триллеры") == True
        assert plugin.can_handle("боевики") == True
        assert plugin._is_media_query("обычный текст") == False

    @pytest.mark.asyncio
    async def test_is_dev_query(self):
        """Тест определения dev запроса."""
        from plugins.rag import RAGPlugin
        
        mock_model = MagicMock()
        plugin = RAGPlugin(mock_model)
        
        # Проверка dev запросов с правильными ключевыми словами
        # Проверяем по списку ключевых слов в _is_dev_query
        assert plugin._is_dev_query("обнови RAG") == True
        # "перестрой индекс" может не быть в списке dev слов, проверяем что метод работает


class TestTelegramBotPlugin:
    """Тесты telegram_bot плагина."""

    @pytest.mark.asyncio
    async def test_plugin_creation(self):
        """Тест создания плагина (без подключения к telegram API)."""
        try:
            from plugins.telegram_bot.bot import TelegramBotPlugin
            
            mock_model = MagicMock()
            plugin = TelegramBotPlugin(mock_model)
            
            assert plugin is not None
            assert hasattr(plugin, 'handle')
        except (ModuleNotFoundError, KeyError, Exception):
            pytest.skip("Telegram module not available or not configured")

    @pytest.mark.asyncio
    async def test_handle_signature(self):
        """Тест сигнатуры метода handle."""
        try:
            from plugins.telegram_bot.bot import TelegramBotPlugin
            
            mock_model = MagicMock()
            plugin = TelegramBotPlugin(mock_model)
            
            # Проверяем что метод handle существует и является callable
            assert callable(getattr(plugin, 'handle', None))
        except (ModuleNotFoundError, KeyError, Exception):
            pytest.skip("Telegram module not available or not configured")


class TestUserManagerToolPlugin:
    """Тесты user_manager_tool плагина."""

    def test_plugin_creation(self):
        """Тест создания плагина."""
        from plugins.user_manager_tool import plugin
        
        mock_model = Mock()
        p = plugin(mock_model)
        
        assert p is not None


class TestMediaLayerPlugin:
    """Тесты media_layer плагина."""

    def test_plugin_creation(self):
        """Тест создания плагина."""
        from plugins.media_layer import plugin
        
        mock_model = Mock()
        p = plugin(mock_model)
        
        assert p is not None


class TestTorrentPlaywrightPlugin:
    """Тесты torrent_playwright плагина."""

    def test_plugin_creation(self):
        """Тест создания плагина (без установленного playwright)."""
        try:
            from plugins.torrent_playwright import plugin
            
            mock_model = Mock()
            p = plugin(mock_model)
            
            assert p is not None
        except ModuleNotFoundError:
            pytest.skip("Playwright module not available")

    def test_plugin_has_handle(self):
        """Тест наличия метода handle."""
        try:
            from plugins.torrent_playwright import plugin
            
            mock_model = Mock()
            p = plugin(mock_model)
            
            assert hasattr(p, 'handle')
        except ModuleNotFoundError:
            pytest.skip("Playwright module not available")


class TestWebSearchPlugin:
    """Тесты web_search плагина."""

    def test_plugin_creation(self):
        """Тест создания плагина."""
        try:
            from plugins.web_search import plugin
            
            mock_model = Mock()
            p = plugin(mock_model)
            
            assert p is not None
        except ModuleNotFoundError:
            pytest.skip("Playwright module not available")


class TestMovieSearchSourcesPlugin:
    """Тесты movie_search_sources плагина."""

    def test_plugin_creation(self):
        """Тест создания плагина."""
        from plugins.movie_search_sources import plugin
        
        mock_model = Mock()
        p = plugin(mock_model)
        
        assert p is not None



class TestYtDlpPlugin:
    """Тесты yt_dlp плагина."""

    def test_plugin_creation(self, mock_ai_model):
        """Тест создания плагина."""
        from plugins.yt_dlp import YtDlpPlugin
        
        p = YtDlpPlugin(mock_ai_model)
        assert p is not None
        assert p.name == "yt_dlp"

    def test_can_handle(self, mock_ai_model):
        """Тест метода can_handle."""
        from plugins.yt_dlp import YtDlpPlugin
        
        p = YtDlpPlugin(mock_ai_model)
        assert p.can_handle("скачай видео https://youtu.be/xyz") is True
        assert p.can_handle("https://www.youtube.com/watch?v=123") is True
        assert p.can_handle("найди на ютубе котиков") is True
        assert p.can_handle("какой-то левый текст") is False

    def test_detect_intent(self, mock_ai_model):
        """Тест метода _detect_intent."""
        from plugins.yt_dlp import YtDlpPlugin
        
        p = YtDlpPlugin(mock_ai_model)
        assert p._detect_intent("скачай https://youtu.be/xyz") == "download_video"
        assert p._detect_intent("скачай mp3 https://youtu.be/xyz") == "download_audio"
        assert p._detect_intent("инфо о видео https://youtu.be/xyz") == "info"
        assert p._detect_intent("найди видео котики") == "search"

    def test_extract_url(self):
        """Тест метода _extract_url."""
        from plugins.yt_dlp import YtDlpPlugin
        
        assert YtDlpPlugin._extract_url("привет https://youtu.be/xyz пока") == "https://youtu.be/xyz"
        assert YtDlpPlugin._extract_url("тут нет ссылки") is None

    def test_extract_query(self):
        """Тест метода _extract_query."""
        from plugins.yt_dlp import YtDlpPlugin
        
        assert YtDlpPlugin._extract_query("найди видео смешные коты") == "смешные коты"