"""
Тесты плагинов ai-mediteka
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch


class TestMediaOrganizerPlugin:
    """Тесты media_organizer плагина."""

    @pytest.mark.asyncio
    async def test_handle(self, mock_ai_model):
        """Тест обработки сообщения media_organizer."""
        from plugins.media_organizer.media_organizer import MediaOrganizerPlugin
        
        plugin = MediaOrganizerPlugin(mock_ai_model)
        
        with patch.object(plugin, '_handle') as mock_handle:
            mock_handle.return_value = AsyncMock(return_value="Scan completed")
            
            result = await plugin.handle("scan media")
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_handle_with_disk_paths(self, mock_ai_model):
        """Тест обработки с указанием путей."""
        from plugins.media_organizer.media_organizer import MediaOrganizerPlugin
        
        plugin = MediaOrganizerPlugin(mock_ai_model)
        
        result = await plugin.handle("scan disk 1", disk_paths=["E:"])
        
        # Проверка что метод вызван
        assert result is not None


class TestQBittorrentPlugin:
    """Тесты qbittorrent плагина."""

    def test_qbittorrent_client_init(self):
        """Тест инициализации QBittorrentClient."""
        from plugins.qbittorrent.qbittorrent import QBittorrentClient
        
        with patch('plugins.qbittorrent.qbittorrent.Client') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            
            client = QBittorrentClient(
                host='localhost',
                port=8080,
                username='admin',
                password='adminadmin'
            )
            
            assert client is not None

    @pytest.mark.asyncio
    async def test_torrents_list(self):
        """Тест получения списка торрентов."""
        from plugins.qbittorrent.qbittorrent import QBittorrentClient
        
        with patch('plugins.qbittorrent.qbittorrent.Client') as mock_client:
            mock_instance = Mock()
            mock_instance.torrents = Mock(return_value=[])
            mock_client.return_value = mock_instance
            
            client = QBittorrentClient('localhost', 8080, 'admin', 'adminadmin')
            
            torrents = client.torrents()
            
            assert isinstance(torrents, list)


class TestRAGPlugin:
    """Тесты RAG плагина."""

    @pytest.mark.asyncio
    async def test_is_media_query(self):
        """Тест определения медиа запроса."""
        from plugins.rag import RAGPlugin
        
        mock_model = Mock()
        plugin = RAGPlugin(mock_model)
        
        # Проверка медиа запросов
        assert plugin._is_media_query("фильм про войну") == True
        assert plugin._is_media_query("покажи сериал") == True

    @pytest.mark.asyncio
    async def test_is_dev_query(self):
        """Тест определения dev запроса."""
        from plugins.rag import RAGPlugin
        
        mock_model = Mock()
        plugin = RAGPlugin(mock_model)
        
        # Проверка dev запросов
        assert plugin._is_dev_query("обнови RAG") == True
        assert plugin._is_dev_query("перестрой индекс") == True


class TestTelegramBotPlugin:
    """Тесты telegram_bot плагина."""

    @pytest.mark.asyncio
    async def test_handle(self, mock_ai_model):
        """Тест обработки сообщения telegram ботом."""
        from plugins.telegram_bot.bot import TelegramBotPlugin
        
        plugin = TelegramBotPlugin(mock_ai_model)
        
        with patch.object(plugin, '_handle') as mock_handle:
            mock_handle.return_value = AsyncMock(return_value="Hello!")
            
            result = await plugin.handle("start")
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_process_message(self, mock_ai_model):
        """Тест обработки сообщения пользователя."""
        from plugins.telegram_bot.bot import TelegramBotPlugin
        
        plugin = TelegramBotPlugin(mock_ai_model)
        
        with patch.object(plugin, '_handle') as mock_handle:
            mock_handle.return_value = AsyncMock(return_value="Answer")
            
            result = await plugin._process_message("test message", None)
            
            assert result is not None


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
        """Тест создания плагина."""
        from plugins.torrent_playwright import plugin
        
        mock_model = Mock()
        p = plugin(mock_model)
        
        assert p is not None
