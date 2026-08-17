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
# Project: mediteka
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
        
        router = init_router(mock_model, mock_model, plugins)
        
        assert router is not None

    @pytest.mark.asyncio
    async def test_get_models_logging(self):
        """Тест логирования моделей agy."""
        from src.fastapi.router_chat import init_router
        
        mock_model = Mock()
        router = init_router(mock_model, mock_model, {})
        
        get_models_func = None
        for route in router.routes:
            if route.path in ('/models', '/api/chat/models'):
                get_models_func = route.endpoint
                break
        
        assert get_models_func is not None
        
        with patch('src.fastapi.router_chat.logger.info') as mock_log:
            await get_models_func()
            mock_log.assert_called()
            args, _ = mock_log.call_args
            assert "agy" in args[0].lower()


class TestRouterMedia:
    """Тесты router_media.py."""

    def test_init_router(self):
        """Тест инициализации media-роутера."""
        from src.fastapi.router_media import init_router
        
        router = init_router(prefix='/api/media')
        
        assert router
        assert router.prefix == '/api/media'

    @pytest.mark.asyncio
    async def test_search_rag_endpoint_with_body(self):
        """Тест поиска RAG с передачей параметров через тело запроса (JSON)."""
        from src.fastapi.router_media import init_router, RagSearchRequest
        router = init_router(prefix='/api/media')

        search_endpoint = next(r.endpoint for r in router.routes if r.path.endswith('/rag/search'))
        req = RagSearchRequest(query='топ ган', top_k=5, type='media')

        mock_rag = Mock()
        mock_rag.search.return_value = [
            {'id': '1', 'score': 0.85, 'text': 'Топ Ган фильм', 'meta': {'title': 'Топ Ган', 'type': 'movie', 'year': 1986, 'disk_name': 'диск 1'}}
        ]

        with patch('plugins.media_organizer.core.media_rag_functions._get_gemini_api_key', return_value='fake_key'), \
             patch('plugins.media_organizer.core.media_rag.get_media_rag', return_value=mock_rag):
            result = await search_endpoint(req=req)

        assert 'results' in result, "Результат поиска должен содержать ключ 'results'"
        assert len(result['results']) == 1, "Должен вернуться один найденный результат"
        assert result['results'][0]['title'] == 'Топ Ган', "Название фильма должно совпадать с моком"

    @pytest.mark.asyncio
    async def test_search_rag_endpoint_with_query_params(self):
        """Тест поиска RAG с передачей параметров через URL query string (без тела)."""
        from src.fastapi.router_media import init_router
        router = init_router(prefix='/api/media')

        search_endpoint = next(r.endpoint for r in router.routes if r.path.endswith('/rag/search'))

        mock_rag = Mock()
        mock_rag.search.return_value = [
            {'id': '2', 'score': 0.9, 'text': 'Топ Ган Мэверик', 'meta': {'title': 'Топ Ган: Мэверик', 'type': 'movie', 'year': 2022, 'disk_name': 'диск 2'}}
        ]

        with patch('plugins.media_organizer.core.media_rag_functions._get_gemini_api_key', return_value='fake_key'), \
             patch('plugins.media_organizer.core.media_rag.get_media_rag', return_value=mock_rag):
            result = await search_endpoint(query='топ ган мэверик', top_k=3, type='media')

        assert 'results' in result, "Результат поиска должен содержать ключ 'results'"
        assert len(result['results']) == 1, "Должен вернуться один найденный результат"
        assert result['results'][0]['title'] == 'Топ Ган: Мэверик', "Название фильма должно совпадать"

    @pytest.mark.asyncio
    async def test_search_rag_endpoint_empty_query_raises_400(self):
        """Тест раннего возврата ошибки 400 при пустом поисковом запросе."""
        from fastapi import HTTPException
        from src.fastapi.router_media import init_router
        router = init_router(prefix='/api/media')

        search_endpoint = next(r.endpoint for r in router.routes if r.path.endswith('/rag/search'))

        with pytest.raises(HTTPException) as exc_info:
            await search_endpoint(query='', type='media')

        assert exc_info.value.status_code == 400, "Пустой запрос должен вызывать HTTPException с кодом 400"


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
        assert len(manager.rooms) == 0
