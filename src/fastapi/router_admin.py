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

class SystemInstructionUpdate(BaseModel):
    content: str


class InstructionVersion(BaseModel):
    id: int
    role: str  # 'chat' | 'narrator'
    content: str
    is_active: bool
    created_at: str


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
# System Instruction Versions Endpoints
# ============================================================================

from plugins.media_organizer.core import MEDIA_DB as DATABASE_PATH


class InstructionRoleUpdate(BaseModel):
    mode: str  # 'chat' | 'narrator'
    content: str


class InstructionActivateRequest(BaseModel):
    id: int


@router.get('/instructions')
async def get_instruction(request: Request, mode: str = 'chat') -> Dict[str, str]:
    """Получение активной инструкции по режиму."""
    _check_admin(request)
    try:
        import sqlite3
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT content FROM system_instructions WHERE role = ? AND is_active = 1 ORDER BY created_at DESC LIMIT 1",
                (mode,)
            ).fetchone()
            if row:
                return {'content': row['content']}
            # Fallback to file
            content = _SYSTEM_INSTRUCTION_FILE.read_text(encoding='utf-8') if _SYSTEM_INSTRUCTION_FILE.exists() else ''
            return {'content': content}
    except Exception as ex:
        logger.error('Ошибка чтения system_instruction', ex)
        raise HTTPException(status_code=500, detail='Не удалось прочитать системную инструкцию')


@router.post('/instructions/save')
async def save_instruction(request: Request, data: InstructionRoleUpdate) -> Dict[str, str]:
    """Сохранение новой версии инструкции."""
    _check_admin(request)
    try:
        import sqlite3
        from datetime import datetime
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            # Вставка новой версии
            conn.execute(
                "INSERT INTO system_instructions (role, content, is_active, created_at) VALUES (?, ?, 1, ?)",
                (data.mode, data.content, datetime.now().isoformat())
            )
            
            # Деактивация старых версий
            conn.execute(
                "UPDATE system_instructions SET is_active = 0 WHERE role = ?",
                (data.mode,)
            )
            
            conn.commit()
        
        # Обновляем файл
        _SYSTEM_INSTRUCTION_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SYSTEM_INSTRUCTION_FILE.write_text(data.content, encoding='utf-8')
        
        logger.info(f'Instruction saved for mode={data.mode} via admin panel')
        return {'status': 'ok', 'message': 'Инструкция успешно сохранена'}
    except Exception as ex:
        logger.error('Ошибка записи system_instruction', ex)
        raise HTTPException(status_code=500, detail='Не удалось сохранить инструкцию')


@router.get('/instructions/versions')
async def get_instruction_versions(request: Request) -> Dict[str, List[Dict]]:
    """Получение истории версий инструкций."""
    _check_admin(request)
    try:
        import sqlite3
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, role, content, is_active, created_at FROM system_instructions ORDER BY created_at DESC"
            ).fetchall()
            
            versions = []
            for row in rows:
                versions.append({
                    'id': row['id'],
                    'role': row['role'],
                    'content': row['content'],
                    'is_active': bool(row['is_active']),
                    'created_at': row['created_at']
                })
            
            return {'versions': versions}
    except Exception as ex:
        logger.error('Ошибка чтения версий инструкций', ex)
        raise HTTPException(status_code=500, detail='Не удалось прочитать версии инструкций')


@router.post('/instructions/activate')
async def activate_instruction(request: Request, data: InstructionActivateRequest) -> Dict[str, str]:
    """Активация выбранной версии инструкции."""
    _check_admin(request)
    try:
        import sqlite3
        with sqlite3.connect(DATABASE_PATH) as conn:
            # Деактивация всех
            conn.execute("UPDATE system_instructions SET is_active = 0 WHERE id != ?", (data.id,))
            # Активация выбранной
            conn.execute("UPDATE system_instructions SET is_active = 1 WHERE id = ?", (data.id,))
            conn.commit()
        
        # Обновляем файл
        row = conn.execute(
            "SELECT content FROM system_instructions WHERE id = ?",
            (data.id,)
        ).fetchone()
        if row:
            _SYSTEM_INSTRUCTION_FILE.write_text(row['content'], encoding='utf-8')
        
        logger.info(f'Instruction v{data.id} activated via admin panel')
        return {'status': 'ok', 'message': 'Версия активирована'}
    except Exception as ex:
        logger.error('Ошибка активации инструкции', ex)
        raise HTTPException(status_code=500, detail='Не удалось активировать версию')


@router.post('/instructions/check')
async def check_instruction_in_model(request: Request, data: Dict[str, Any]) -> Dict[str, Any]:
    """Проверка инструкции в модели."""
    _check_admin(request)
    try:
        from src.ai import UnifiedChatModel
        from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
        
        api_key = _get_gemini_api_key()
        if not api_key:
            raise HTTPException(status_code=500, detail='API ключ не настроен')
        
        system_instruction = data.get('instruction', '')
        prompt = data.get('prompt', 'Привет!')
        
        # Создаем модель с инструкцией
        model = UnifiedChatModel(
            api_key_names=[n.strip() for n in api_key.split(',') if n.strip()],
            system_instruction=system_instruction,
            foundry_model_id='qwen3-0.6b-generic-cpu:4',
            use_foundry=False,
        )
        
        response = await model.chat(prompt)
        
        # Подсчет токенов (грубая оценка)
        total_tokens = len(system_instruction) // 3 + len(prompt) // 3 + len(response) // 3
        
        return {
            'status': 'ok',
            'response': response,
            'token_count': total_tokens
        }
    except Exception as ex:
        logger.error('Ошибка проверки инструкции в модели', ex)
        raise HTTPException(status_code=500, detail=f'Ошибка проверки: {ex}')


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
