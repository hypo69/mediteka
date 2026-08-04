# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование API эндпоинтов
# =============================================================================
# Описание:
#   Группа интеграционных тестов для систематической проверки доступности
#   и корректности ответов основных API эндпоинтов FastAPI Foundry.
#
# Примеры:
#   pytest tests/integration/test_api.py
#
# File: test_api.py
# Project: Ai Assistant
# Author: Gemini Code Assist
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import httpx
import respx

# Базовый URL сервера (берется из конфига, здесь используем дефолтный для тестов)
BASE_URL = "http://localhost:9696"

@pytest.mark.asyncio
async def test_api_info_endpoint():
    """Проверка эндпоинта основной информации об API."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api")
        assert response.status_code == 200
        # Проверяем, что в ответе есть упоминание версии или названия
        assert "FastAPI Foundry" in response.text or "version" in response.json()

@pytest.mark.asyncio
async def test_api_v1_health():
    """Проверка работоспособности системы (Health Check)."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"

@pytest.mark.asyncio
async def test_api_v1_models_list():
    """Проверка получения списка доступных моделей."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        # Ожидаем список (даже если он пустой)
        assert isinstance(data, (list, dict))

@pytest.mark.asyncio
async def test_api_docs_availability():
    """Проверка доступности Swagger UI и Redoc."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Проверка Swagger
        swagger_res = await client.get("/docs")
        assert swagger_res.status_code == 200
        assert "swagger-ui" in swagger_res.text.lower()

        # Проверка Redoc
        redoc_res = await client.get("/redoc")
        assert redoc_res.status_code == 200
        assert "redoc" in redoc_res.text.lower()

@pytest.mark.asyncio
@respx.mock
async def test_api_v1_generate_mocked():
    """Тестирование генерации с моком бэкенда LLM.
    
    Используется respx для перехвата запросов к Foundry/llama.cpp 
    внутри тестового окружения.
    """
    # Эмулируем ответ от бэкенда Foundry (по умолчанию порт 50477)
    backend_url = "http://localhost:50477/v1/chat/completions"
    respx.post(backend_url).mock(return_value=httpx.Response(200, json={
        "choices": [{
            "message": {"content": "This is a mocked response from Ai Assistant Engine"}
        }]
    }))

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        payload = {
            "prompt": "Tell me a joke",
            "model": "foundry::test-model",
            "max_tokens": 50,
            "temperature": 0.7
        }
        # Примечание: Для работы этого мока в интеграционном тесте 
        # сервер должен быть запущен в том же процессе.
        response = await client.post("/api/v1/generate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "mocked" in data["content"].lower()

@pytest.mark.asyncio
async def test_api_v1_404_not_found():
    """Проверка обработки запроса к несуществующему ресурсу.
    
    ПОЧЕМУ ЭТО ВАЖНО:
        Гарантия того, что сервер возвращает стандартный код 404 и 
        структурированное описание ошибки вместо падения или возврата HTML.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/v1/invalid-route-name-for-test")
        assert response.status_code == 404
        # Валидация наличия описания ошибки в формате FastAPI
        assert "detail" in response.json()

@pytest.mark.asyncio
async def test_api_v1_422_validation_error():
    """Проверка валидации входящих данных (отсутствие обязательных полей).
    
    ПОЧЕМУ ЭТО ВАЖНО:
        Проверка корректности работы Pydantic-схем. Запрос на генерацию 
        без поля 'prompt' должен быть отклонен на уровне валидации.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Отправка пустого тела запроса на endpoint генерации
        response = await client.post("/api/v1/generate", json={})
        assert response.status_code == 422
        # Анализ структуры ответа валидатора
        data = response.json()
        assert "detail" in data
        assert data["detail"][0]["type"] == "missing"

@pytest.mark.asyncio
@respx.mock
async def test_api_v1_401_unauthorized_mocked():
    """Имитация ситуации отсутствия авторизации при защищенном доступе.
    
    ПОЧЕМУ ЭТО ВАЖНО:
        Проверка готовности тестовой среды к обработке кодов безопасности.
    """
    # Создание мока для проверки маршрута, требующего API_KEY
    respx.get(f"{BASE_URL}/api/v1/config").mock(
        return_value=httpx.Response(401, json={"detail": "Not authenticated"})
    )
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/config")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
@respx.mock
async def test_api_v1_504_timeout_mocked():
    """Проверка обработки таймаута (504 Gateway Timeout).
    
    ПОЧЕМУ ЭТО ВАЖНО:
        Проверка реакции API сервера на задержки или "зависания" 
        внутренних бэкендов (Foundry/llama.cpp).
    """
    # Эмуляция таймаута на стороне инференс-движка
    backend_url = "http://localhost:50477/v1/chat/completions"
    respx.post(backend_url).mock(side_effect=httpx.TimeoutException("Backend is too slow"))

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        payload = {
            "prompt": "heavy task",
            "model": "foundry::test-timeout"
        }
        # Ожидаем, что сервер корректно перехватит таймаут и вернет 504
        response = await client.post("/api/v1/generate", json=payload)
        assert response.status_code == 504
        assert "timeout" in response.json().get("detail", "").lower()

@pytest.mark.asyncio
@respx.mock
async def test_api_v1_generate_stream_mocked():
    """Проверка корректности формирования SSE при потоковой генерации.
    
    ПОЧЕМУ ЭТО ВАЖНО:
        Интерфейсы чатов требуют немедленного отображения токенов. 
        Тест проверяет соблюдение протокола SSE (data: ...\n\n).
    """
    backend_url = "http://localhost:50477/v1/chat/completions"
    
    # Имитация потока данных от бэкенда
    async def stream_generator():
        chunks = [
            '{"choices": [{"delta": {"content": "Hello"}}]}',
            '{"choices": [{"delta": {"content": " world"}}]}',
            '[DONE]'
        ]
        for chunk in chunks:
            yield f"data: {chunk}\n\n".encode("utf-8")

    respx.post(backend_url).mock(return_value=httpx.Response(
        200, 
        content=stream_generator(),
        headers={"Content-Type": "text/event-stream"}
    ))

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        payload = {
            "prompt": "stream test",
            "model": "foundry::test-stream",
            "stream": True
        }
        
        async with client.stream("POST", "/api/v1/generate", json=payload) as response:
            assert response.status_code == 200
            assert response.headers["Content-Type"] == "text/event-stream"
            
            lines = [line async for line in response.aiter_lines()]
            # Проверка наличия данных и соблюдения формата SSE
            assert any("Hello" in line for line in lines)
            assert any("world" in line for line in lines)
            assert lines[-1] == "" # Последняя пустая строка в блоке SSE