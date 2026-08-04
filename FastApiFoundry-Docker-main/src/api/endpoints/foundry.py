# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Foundry Endpoints (Refactored)
# =============================================================================
# Описание:
#   Упрощенные endpoints для работы с Foundry сервисом
#
# File: foundry.py
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from fastapi import APIRouter
from ...models.foundry_client import foundry_client

router = APIRouter()

@router.get("/foundry/status")
async def foundry_status():
    """Получить статус сервиса Foundry"""
    try:
        health = await foundry_client.health_check()
        
        # Определяем статус работы
        is_running = health.get("status") == "healthy"
        port = health.get("port")
        url = health.get("url")
        
        return {
            "success": True,
            "running": is_running,
            "status": health.get("status", "unknown"),
            "port": port if port and port != "Unknown" else None,
            "url": url if url else None,
            "error": health.get("error") if not is_running else None
        }
    except Exception as e:
        return {
            "success": False, 
            "running": False,
            "status": "error",
            "port": None,
            "url": None,
            "error": str(e)
        }

@router.get("/foundry/models/list")
async def list_foundry_models():
    """Получить список всех доступных моделей"""
    try:
        models = await foundry_client.list_available_models()
        return models
    except Exception as e:
        return {"success": False, "error": str(e), "models": []}