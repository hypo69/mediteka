# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: API управления Foundry
# =============================================================================
# Описание:
#   Контроль жизненного цикла службы Foundry (статус, запуск, остановка).
#
# File: src/api/endpoints/foundry_management.py
# Project: Ai Assistant (Docker)
# Package: FastApiFoundry
# Module: api.endpoints.foundry_management
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# Date: 2025
# =============================================================================

import asyncio
import subprocess
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Any, Dict
from ...utils.command_agent import CommandAgent
from ...utils.api_utils import api_response_handler

# Попытка импорта WebSocket менеджера для уведомлений в реальном времени
try:
    from ..websocket_manager import manager
except ImportError:
    manager = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/foundry", tags=["foundry"])

class FoundryStatus(BaseModel):
    running: bool
    success: bool = True
    port: Optional[int] = None
    url: Optional[str] = None

async def _poll_foundry_status_task(max_attempts: int = 12, interval: int = 5):
    """Фоновая задача для периодического опроса статуса Foundry после запуска.
    
    Обоснование:
      - Уведомление в логах о фактической готовности сервиса.
      - Предоставление актуальной информации без необходимости ручного обновления.
    """
    agent: CommandAgent = CommandAgent()
    last_status_str: str = "unknown"

    for i in range(1, max_attempts + 1):
        # Ожидание перед следующей проверкой
        await asyncio.sleep(interval)
        status = await agent.parse_foundry_status()
        current_status_str = status.get("status", "unknown")
        
        # Отправка уведомления через WebSocket при изменении статуса
        # Sending WebSocket notification on status change
        if manager and current_status_str != last_status_str:
            try:
                await manager.broadcast({
                    "type": "foundry_status_update",
                    "status": current_status_str,
                    "port": status.get("port"),
                    "attempt": i,
                    "timestamp": asyncio.get_event_loop().time()
                })
            except Exception as e:
                logger.debug(f"Ошибка WebSocket уведомления: {e}")
            
            last_status_str = current_status_str

        if current_status_str in ["running", "degraded"]:
            logger.info(f"Foundry Polling: Сервис успешно запущен и отвечает (Попытка {i})")
            return
        
        # Оповещение в Telegram при неудаче последней попытки
        if i == max_attempts:
            from src.utils.telegram_bot import system_bot
            await system_bot.send_message("❌ *Ошибка старта:* Foundry не ответил за 60 секунд после команды запуска.")
            
        logger.debug(f"Foundry Polling: Ожидание готовности... ({i}/{max_attempts})")
    
    logger.warning(f"Foundry Polling: Сервис не перешел в рабочий статус за {max_attempts * interval} сек")

@router.get("/status", response_model=FoundryStatus)
@api_response_handler
async def get_foundry_status() -> FoundryStatus:
    """Получение статуса службы Foundry через системный агент.

    Returns:
        FoundryStatus: Объект со статусом работы, портом и URL.
    """
    agent: CommandAgent = CommandAgent()
    # Получение структурированного статуса через CommandAgent
    # Retrieval of structured status via CommandAgent
    status: Dict[str, Any] = await agent.parse_foundry_status()
    
    is_running: bool = status.get("status") in ["running", "degraded"]
    port: Optional[int] = status.get("port")
    
    return FoundryStatus(
        running=is_running,
        success=status.get("status") != "failed",
        port=port,
        url=f"http://localhost:{port}/v1/" if port else None
    )

@router.post("/start")
@api_response_handler
async def start_foundry(background_tasks: BackgroundTasks) -> dict:
    """Запуск службы Foundry через системный агент.

    Args:
        background_tasks (BackgroundTasks): Фоновые задачи FastAPI.

    Returns:
        dict: Статус выполнения и сообщение.
    """
    agent: CommandAgent = CommandAgent()
    
    # Проверка доступности команды перед запуском
    # Command availability verification before execution
    if not await agent.test_command_available("foundry"):
        return {"success": False, "error": "foundry CLI not found — is Foundry Local installed?"}

    try:
        # Выполнение команды запуска через агент (с учетом предохранителя)
        # Execution of the start command via agent (considering the circuit breaker)
        result = await agent.run("foundry", ["service", "start"])
        
        if result.get("exit_code") == 0:
            # Добавление фоновой задачи для опроса готовности
            # Adding a background task for readiness polling
            background_tasks.add_task(_poll_foundry_status_task)
            
            logger.info("Запущена команда старта Foundry, добавлен фоновый опрос статуса")
            return {"success": True, "message": "Foundry start command executed"}
            
        return {"success": False, "error": result.get("error") or "Failed to start Foundry"}
    except Exception as e:
        logger.error(f"❌ Failed to start Foundry: {e}")
        return {"success": False, "error": str(e)}

@router.post("/stop")
@api_response_handler
async def stop_foundry() -> dict:
    """Остановка службы Foundry через системный агент.

    Returns:
        dict: Сообщение о результате операции.
    """
    agent: CommandAgent = CommandAgent()

    if not await agent.test_command_available("foundry"):
        return {"success": False, "error": "foundry CLI not found"}

    try:
        result = await agent.run("foundry", ["service", "stop"])
        if result.get("exit_code") == 0:
            return {"success": True, "message": "Foundry stop command executed"}
        return {"success": False, "error": result.get("error") or "Failed to stop Foundry"}
    except Exception as e:
        logger.error(f"❌ Failed to stop Foundry: {e}")
        return {"success": False, "error": str(e)}

@router.post("/reset-breaker")
@api_response_handler
async def reset_foundry_breaker() -> dict:
    """Ручной сброс предохранителя для команд Foundry.
    """
    agent: CommandAgent = CommandAgent()
    agent.reset_circuit_breaker("foundry")
    return {"success": True, "message": "Circuit breaker for 'foundry' reset"}