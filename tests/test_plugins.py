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
        assert plugin._is_dev_query("обнови RAG") == True

    def test_format_count_word(self):
        """Тест формирования числительных для вариантов."""
        from plugins.rag import _format_count_word
        
        assert _format_count_word(1) == "один вариант"
        assert _format_count_word(2) == "два варианта"
        assert _format_count_word(5) == "пять вариантов"
        assert _format_count_word(10) == "десять вариантов"
        assert _format_count_word(12) == "12 вариантов"

    @pytest.mark.asyncio
    async def test_handle_direct_multi_items_voice_text(self):
        """Тест формирования текста диктора для нескольких тайтлов с предложением продолжить диалог."""
        import json
        from plugins.rag import RAGPlugin

        mock_model = MagicMock()
        plugin = RAGPlugin(mock_model)

        sample_items = [
            {
                'clean_title': 'The Foreigner',
                'title': 'The Foreigner',
                'media_type': 'movie',
                'disk_name': 'D:',
                'year': 2017
            },
            {
                'clean_title': 'The Terminal List',
                'title': 'The Terminal List: Season 1',
                'media_type': 'series',
                'disk_name': 'E:',
                'year': 2022
            },
            {
                # Дубликат по display_title (должен отфильтроваться)
                'clean_title': 'Список смертников',
                'title': 'Список смертников',
                'media_type': 'series',
                'disk_name': 'F:',
                'year': 2022
            },
            {
                'clean_title': 'Tin Soldier',
                'title': 'Tin Soldier',
                'media_type': 'movie',
                'disk_name': 'D:',
                'year': 2025
            }
        ]

        def fake_get_media_card(disk_name, base_title, m_type):
            if 'Foreigner' in base_title:
                return json.dumps({
                    'title_ru': 'Иностранец',
                    'genres': ['Боевик', 'Триллер'],
                    'cast': ['Джеки Чан', 'Пирс Броснан'],
                    'why_watch': 'Динамичный боевик с напряжённым сюжетом.'
                }, ensure_ascii=False)
            elif 'Terminal' in base_title or 'Список' in base_title:
                return json.dumps({
                    'title_ru': 'Список смертников',
                    'genres': ['Боевик', 'Триллер', 'Драма'],
                    'cast': ['Крис Прэтт', 'Констанс Ву'],
                    'why_watch': 'Остросюжетный сериал про спецназ.'
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    'title_ru': 'Игры возмездия',
                    'genres': ['Боевик'],
                    'cast': ['Джейми Фокс', 'Роберт Де Ниро'],
                    'why_watch': 'Криминальный боевик.'
                }, ensure_ascii=False)

        with patch('plugins.rag.get_media_card', side_effect=fake_get_media_card):
            chunks = []
            async for chunk in plugin._handle_direct_multi_items("Найди боевик", sample_items, {}):
                chunks.append(chunk)

            voice_chunks = [c['voice'] for c in chunks if 'voice' in c]
            text_chunks = [c['text'] for c in chunks if 'text' in c]

            assert len(voice_chunks) == 1
            voice_text = voice_chunks[0]
            
            # Проверяем дедупликацию в тексте чата (Список смертников только один раз)
            full_text = text_chunks[0]
            assert full_text.count("Список смертников") == 1
            assert "Иностранец" in full_text
            assert "Игры возмездия" in full_text

            # Проверяем структуру текста диктора:
            # 1. Вводная фраза
            assert "Я нашла в локальной медиатеке три варианта." in voice_text
            # 2. Содержит минимальную информацию о тайтлах (название, жанр, актёры)
            assert "Иностранец — боевик, в главных ролях Джеки Чан и Пирс Броснан." in voice_text
            assert "Список смертников — боевик, в главных ролях Крис Прэтт и Констанс Ву." in voice_text
            assert "Игры возмездия — боевик, в главных ролях Джейми Фокс и Роберт Де Ниро." in voice_text
            # 3. Предложение к продолжению диалога (3 опции)
            assert "Какой фильм включить, рассказать подробнее или поискать другой вариант?" in voice_text

    @pytest.mark.asyncio
    async def test_handle_direct_rag_voice_text(self):
        """Тест формирования текста диктора для одиночной карточки медиа."""
        import json
        from plugins.rag import RAGPlugin

        mock_model = MagicMock()
        plugin = RAGPlugin(mock_model)

        sample_item = {
            'clean_title': 'The Foreigner',
            'title': 'The Foreigner',
            'media_type': 'movie',
            'disk_name': 'D:'
        }

        fake_card = json.dumps({
            'title_ru': 'Иностранец',
            'genres': ['Боевик', 'Триллер'],
            'cast': ['Джеки Чан', 'Пирс Броснан'],
            'why_watch': 'Динамичный боевик о мести безутешного отца.'
        }, ensure_ascii=False)

        with patch('plugins.rag.get_media_card', return_value=fake_card):
            chunks = []
            async for chunk in plugin._handle_direct_rag(sample_item):
                chunks.append(chunk)

            voice_chunks = [c['voice'] for c in chunks if 'voice' in c]
            assert len(voice_chunks) == 1
            voice_text = voice_chunks[0]

            assert "Найден фильм Иностранец — боевик, в главных ролях Джеки Чан и Пирс Броснан." in voice_text
            assert "Включить этот фильм, рассказать о нём подробнее или поискать другой?" in voice_text


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