# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI-роутер управления системными инструкциями и источниками
# =============================================================================
# Описание:
#   CRUD для файла системных инструкций (.ai_instructions/prompts/chat/system_instruction.md)
#   и для реестра источников (source.json) в корне проекта.
#
# File: router_admin.py
# Project: mediteka
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from header import __root__
from src.logger import logger

router = APIRouter(prefix='/api/admin', tags=['admin'])

_SYSTEM_INSTRUCTION_FILE = __root__ / 'prompts' / 'chat' / 'system_instruction.md'
_SOURCES_FILE = __root__ / 'plugins' / 'movie_search_sources' / 'sources.json'


# ============================================================================
# Helper functions
# ============================================================================

def _check_admin(request: Request) -> None:
    """Проверка прав администратора. Бросает HTTPException если нет доступа."""
    from src.fastapi.router_auth import verify_jwt_token
    token = request.cookies.get('auth_token')
    if not token:
        raise HTTPException(status_code=401, detail='Не авторизован')
    user_data = verify_jwt_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail='Неверный сессионный токен')
    from src.user_manager import user_manager
    db_user = user_manager.get_user_by_email(user_data.email)
    if not db_user or (not db_user.get('is_admin', 0) and db_user.get('role') != 'admin'):
        raise HTTPException(status_code=403, detail='Только администраторы имеют доступ')


def _load_sources_raw() -> str:
    """Загружает сырой текст из sources.json."""
    if _SOURCES_FILE.exists():
        try:
            return _SOURCES_FILE.read_text(encoding='utf-8')
        except Exception as ex:
            logger.error('Ошибка чтения sources.json', ex)
    return "{}"


def _save_sources_raw(content: str) -> None:
    """Сохраняет сырой текст в sources.json."""
    try:
        # Валидация JSON перед сохранением
        json.loads(content)
        _SOURCES_FILE.write_text(content, encoding='utf-8')
    except json.JSONDecodeError as ex:
        raise HTTPException(status_code=400, detail=f'Неверный формат JSON: {ex}')
    except Exception as ex:
        logger.error('Ошибка записи sources.json', ex)
        raise HTTPException(status_code=500, detail='Не удалось сохранить источники')


# ============================================================================
# Pydantic Models
# ============================================================================

class SystemInstructionUpdate(BaseModel):
    content: str


class RawSourcesUpdate(BaseModel):
    content: str


# ============================================================================
# System Instruction Endpoints
# ============================================================================

@router.get('/system_instruction')
async def get_system_instruction(request: Request) -> Dict[str, str]:
    """Получение текста системной инструкции."""
    _check_admin(request)
    try:
        content = _SYSTEM_INSTRUCTION_FILE.read_text(encoding='utf-8') if _SYSTEM_INSTRUCTION_FILE.exists() else ''
        return {'content': content}
    except Exception as ex:
        logger.error('Ошибка чтения system_instruction', ex)
        raise HTTPException(status_code=500, detail='Не удалось прочитать системную инструкцию')


@router.post('/system_instruction')
async def update_system_instruction(request: Request, data: SystemInstructionUpdate) -> Dict[str, str]:
    """Обновление текста системной инструкции."""
    _check_admin(request)
    try:
        _SYSTEM_INSTRUCTION_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SYSTEM_INSTRUCTION_FILE.write_text(data.content, encoding='utf-8')
        logger.info('System instruction updated via admin panel')
        return {'status': 'ok', 'message': 'Системная инструкция успешно сохранена'}
    except Exception as ex:
        logger.error('Ошибка записи system_instruction', ex)
        raise HTTPException(status_code=500, detail='Не удалось сохранить системную инструкцию')


# ============================================================================
# Sources Endpoints
# ============================================================================

@router.get('/sources/raw')
async def get_sources_raw(request: Request) -> Dict[str, str]:
    """Получение сырого JSON-текста источников."""
    _check_admin(request)
    content = _load_sources_raw()
    return {'content': content}


@router.post('/sources/raw')
async def update_sources_raw(request: Request, data: RawSourcesUpdate) -> Dict[str, str]:
    """Обновление сырого JSON-текста источников."""
    _check_admin(request)
    _save_sources_raw(data.content)
    logger.info('Sources JSON updated via admin panel')
    return {'status': 'ok'}


# ============================================================================
# Plugin Endpoints
# ============================================================================

class PluginStateUpdate(BaseModel):
    enabled: bool

@router.get('/plugin/{plugin_name}/status')
async def get_plugin_status(plugin_name: str, request: Request):
    """Получение статуса плагина."""
    _check_admin(request)
    plugin = request.app.state.plugins.get(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail='Плагин не найден')
    enabled = getattr(plugin, 'enabled', True)
    return {'name': plugin_name, 'enabled': enabled}

@router.post('/plugin/{plugin_name}/status')
async def update_plugin_status(plugin_name: str, data: PluginStateUpdate, request: Request):
    """Обновление статуса плагина."""
    _check_admin(request)
    plugin = request.app.state.plugins.get(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail='Плагин не найден')
    plugin.enabled = data.enabled
    logger.info(f"Plugin {plugin_name} enabled state changed to {data.enabled}")
    return {'name': plugin_name, 'enabled': plugin.enabled}

# ============================================================================
# Initialization
# ============================================================================

def init_router() -> APIRouter:
    """Инициализация роутера управления системными инструкциями и источниками."""
    return router
