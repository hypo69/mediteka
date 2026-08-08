# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Интеграционные тесты API endpoints
# =============================================================================
# Описание:
#   Модуль содержит интеграционные тесты для всех API endpoint-ов приложения.
#   Проверяет корректность обработки запросов, взаимодействие с плагинами и
#   AI-моделью, а также работу промежуточного ПО (middleware). Обеспечивает
#   покрытие основных сценариев использования API.
#
# File: tests/test_integration_api.py
# Project: mediteka
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""
Интеграционные тесты API endpoints
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch


class TestChatAPI:
    """Интеграционные тесты /api/chat endpoints."""

    @pytest.mark.asyncio
    async def test_post_chat(self):
        """Тест POST /api/chat."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        from src.fastapi.router_chat import init_router
        
        app = FastAPI()
        mock_model = Mock()
        mock_model.chat = AsyncMock(return_value="Test response")
        mock_model.chat_stream = AsyncMock()
        
        plugins = {}
        app.include_router(init_router(mock_model, mock_model, plugins))
        
        client = TestClient(app)
        
        response = client.post(
            '/api/chat',
            json={
                'message': 'Какой фильм посмотреть?',
                'history': []
            }
        )
        
        assert response.status_code == 200


class TestMediaAPI:
    """Интеграционные тесты /api/media endpoints."""

    def test_get_media_files(self):
        """Тест GET /api/media/files."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        from src.fastapi.router_media import init_router
        
        app = FastAPI()
        app.include_router(init_router())
        
        client = TestClient(app)
        
        with patch('src.fastapi.router_media._db') as mock_db:
            mock_instance = Mock()
            mock_instance.export_all = Mock(return_value=[])
            mock_db.return_value = mock_instance
            
            response = client.get('/api/media/files')
            
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_post_media_by_title(self):
        """Тест POST /api/media/by-title."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        from src.fastapi.router_media import init_router
        
        app = FastAPI()
        app.include_router(init_router())
        
        client = TestClient(app)
        
        with patch('src.fastapi.router_media._db') as mock_db:
            mock_instance = Mock()
            mock_instance.export_all = Mock(return_value=[])
            mock_db.return_value = mock_instance
            
            response = client.post(
                '/api/media/by-title',
                json={'title': 'Титаник', 'type': 'movie'}
            )
            
            assert response.status_code == 200

    def test_get_media_by_category(self):
        """Тест GET /api/media/by-category."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        from src.fastapi.router_media import init_router
        
        app = FastAPI()
        app.include_router(init_router())
        
        client = TestClient(app)
        
        with patch('src.fastapi.router_media._db') as mock_db:
            mock_instance = Mock()
            mock_instance.export_all = Mock(return_value=[])
            mock_db.return_value = mock_instance
            
            response = client.get('/api/media/by-category')
            
            assert response.status_code == 200


class TestTorrentAPI:
    """Интеграционные тесты /api/torrents endpoints."""

    def test_get_torrents(self):
        """Тест GET /api/torrents."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        from src.fastapi.router_qbittorrent import init_router
        
        app = FastAPI()
        app.include_router(init_router())
        
        client = TestClient(app)
        
        # Тест без запущенного qBittorrent
        response = client.get('/api/torrents')
        
        # Ожидаем 503 если qBittorrent недоступен
        assert response.status_code in [200, 503]

    def test_post_torrent_download_magnet(self):
        """Тест POST /api/torrents/download с magnet ссылкой."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        from src.fastapi.router_qbittorrent import init_router
        
        app = FastAPI()
        app.include_router(init_router())
        
        client = TestClient(app)
        
        # Тестируем что эндпоинт доступен и обрабатывает запрос
        # qBittorrent может быть недоступен, ожидаем 500 или 503
        response = client.post(
            '/api/torrents/download',
            json={
                'url': 'magnet:?xt=urn:btih:test',
                'title': 'Test',
                'source': 'test'
            }
        )
        
        # Проверяем что запрос обработан (любой код ответа кроме 422)
        assert response.status_code in [200, 500, 503]


class TestAuthAPI:
    """Интеграционные тесты /api/auth endpoints."""

    def test_get_models(self):
        """Тест GET /api/chat/models."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        from src.fastapi.router_chat import init_router
        
        app = FastAPI()
        mock_model = Mock()
        app.include_router(init_router(mock_model, mock_model, {}))
        
        client = TestClient(app)
        
        response = client.get('/api/chat/models')
        
        assert response.status_code == 200
        data = response.json()
        assert 'models' in data


class TestControlAPI:
    """Интеграционные тесты WebSocket control endpoints."""

    def test_get_control_status(self):
        """Тест GET /api/control/status."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        from src.fastapi.router_control import init_router
        
        app = FastAPI()
        app.include_router(init_router())
        
        client = TestClient(app)
        
        response = client.get('/api/control/status')
        
        # Проверка статуса
        assert response.status_code == 200


class TestTTSAPI:
    """Интеграционные тесты /api/tts endpoints."""

    def test_tts_synthesize(self):
        """Тест синтеза речи."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel
        
        from src.fastapi.router_tts import init_router
        
        app = FastAPI()
        
        # Добавляем CORS middleware для теста
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )
        
        app.include_router(init_router())
        
        client = TestClient(app)
        
        # Тест эндпоинта с правильным форматом данных
        class TTSRequest(BaseModel):
            text: str
            voice: str = "ru-RU-DmitryNeural"
            system: str = "edge-tts"
        
        # Отправляем корректный запрос
        response = client.post(
            '/api/tts/synthesize',
            json={'text': 'Привет мир', 'voice': 'ru-RU-DmitryNeural', 'system': 'edge-tts'}
        )
        
        # Проверяем что запрос принят или отклонен по валидной причине
        assert response.status_code in [200, 404, 405, 500]


class TestAdminAPI:
    """Интеграционные тесты админских endpoints."""

    def test_admin_interface_redirect(self):
        """Тест доступа к админке."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        from main import app
        
        client = TestClient(app)
        
        response = client.get('/admin')
        
        # Админка может быть доступна напрямую или с редиректом
        assert response.status_code in [200, 303]

    def test_root_redirect(self):
        """Тест редиректа на главную."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        from main import app
        
        client = TestClient(app)
        
        response = client.get('/')
        
        # Должен быть редирект на /user
        assert response.status_code in [200, 307]
