# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Вспомогательные утилиты API
# =============================================================================
# Описание:
#   Общие инструменты для обработки запросов и форматирования ответов.
#
# File: utils.py
# Project: Ai Assistant
# Author: Gemini Code Assist
# =============================================================================

import logging
import os
import time
from functools import wraps
from typing import Any, Dict
import httpx
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

async def _send_telegram_alert(message: str):
    """Отправка уведомления в Telegram о критической задержке.
    
    ОБОСНОВАНИЕ:
      Оперативное реагирование на деградацию производительности LLM-бэкенда.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": chat_id, "text": message}, timeout=5.0)
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")

def api_response_handler(func):
    """Декоратор для автоматической инъекции статуса успеха и времени выполнения в JSON ответы."""
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time
            
            if execution_time > 10.0:
                logger.error(f"🚨 CRITICAL SLOWDOWN in {func.__name__}: {execution_time:.4f}s")
                alert_text = f"🚨 Ai Assistant Critical Slowdown!\nEndpoint: {func.__name__}\nTime: {execution_time:.2f}s"
                await _send_telegram_alert(alert_text)
            elif execution_time > 2.0:
                logger.warning(f"🐢 Slow request detected in {func.__name__}: {execution_time:.4f}s")
                
            if isinstance(result, dict):
                if "success" not in result:
                    result["success"] = True
                result["execution_time"] = f"{execution_time:.4f}s"
            return result
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Internal Server Error",
                    "detail": str(e),
                    "execution_time": f"{execution_time:.4f}s"
                }
            )
    return wrapper