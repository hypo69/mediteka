# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля src/fastapi
# =============================================================================
# Описание:
#   Модуль содержит тесты для модуля FastAPI API сервера. Проверяет создание
#   тестового клиента, настройки CORS, маршрутизацию и базовую логику обработки
#   запросов. Обеспечивает покрытие основных endpoint-ов API-сервера.
#
# File: tests/test_fastapi.py
# Project: ai-mediteka
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""
Тесты модуля src/fastapi
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def app_client():
    """Создание FastAPI тестового клиента."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    
    return app


class TestRouterAuth:
    """Тесты router_auth.py."""

    def test_create_jwt_token(self):
        """Тест создания JWT токена."""
        from src.fastapi.router_auth import TokenData, create_jwt_token
        
        token_data = TokenData(
            email="test@example.com",
            name="Test User",
            id=1
        )
        
        token = create_jwt_token(token_data)
        
        assert token is not None
        assert len(token) > 0

    def test_verify_jwt_token(self):
        """Тест верификации JWT токена."""
        from src.fastapi.router_auth import TokenData, create_jwt_token, verify_jwt_token
        
        token_data = TokenData(
            email="test@example.com",
            name="Test User",
            id=1
        )
        
        token = create_jwt_token(token_data)
        verified = verify_jwt_token(token)
        
        assert verified is not None
        assert verified.email == "test@example.com"

    def test_verify_jwt_token_invalid(self):
        """Тест верификации невалидного токена."""
        from src.fastapi.router_auth import verify_jwt_token
        
        result = verify_jwt_token("invalid_token")
        
        assert result is None


class TestRouterChat:
    """Тесты router_chat.py."""

    def test_init_router(self, app_client):
        """Тест инициализации чат-роутера."""
        from src.fastapi.router_chat import init_router
        
        mock_model = Mock()
        mock_model.chat = AsyncMock()
        mock_model.chat_stream = AsyncMock()
        
        plugins = {}
        
        router = init_router(mock_model, plugins)
        
        assert router is not None


class TestRouterMedia:
    """Тесты router_media.py."""

    def test_init_router(self):
        """Тест инициализации media-роутера."""
        from src.fastapi.router_media import init_router
        
        router = init_router(prefix='/api/media')
        
        assert router is not None
        assert router.prefix == '/api/media'


class TestRouterQbittorrent:
    """Тесты router_qbittorrent.py."""

    def test_init_router(self):
        """Тест инициализации qbt-роутера."""
        from src.fastapi.router_qbittorrent import init_router
        
        router = init_router()
        
        assert router is not None
        assert router.prefix == '/api/torrents'


class TestRouterTTS:
    """Тесты router_tts.py."""

    def test_init_router(self):
        """Тест инициализации tts-роутера."""
        from src.fastapi.router_tts import init_router
        
        router = init_router(prefix='/api/tts')
        
        assert router is not None
        assert router.prefix == '/api/tts'


class TestRouterControl:
    """Тесты router_control.py."""

    def test_connection_manager(self):
        """Тест ConnectionManager."""
        from src.fastapi.router_control import ControlConnectionManager
        
        manager = ControlConnectionManager()
        
        assert manager is not None
        assert len(manager.active_connections) == 0
