# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование декораторов API
# =============================================================================
# Описание:
#   Модульные тесты для проверки логики декораторов, управляющих 
#   структурой HTTP ответов.
#
# Примеры:
#   pytest tests/unit/test_decorators.py
#
# File: test_decorators.py
# Project: Ai Assistant
# Author: Gemini Code Assist
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from src.api.utils import api_response_handler

# ПОЧЕМУ ТЕСТ ВАЖЕН:
#   Декоратор @api_response_handler обеспечивает консистентность API. 
#   Клиенты ожидают поле 'success' в каждом успешном ответе.

@pytest.mark.asyncio
async def test_api_response_handler_success_injection():
    """Проверка автоматической вставки поля success: true в словарь ответа."""
    
    @api_response_handler
    async def mock_endpoint():
        return {"data": "payload"}

    response = await mock_endpoint()
    
    # Проверка модификации ответа
    assert "success" in response
    assert response["success"] is True
    assert response["data"] == "payload"