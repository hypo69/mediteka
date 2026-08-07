# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI-роутер управления системными инструкциями и источниками
# =============================================================================
# Описание:
#   CRUD для файлов системных инструкций.
#   Файловое версионирование: активные файлы хранятся в prompts/{mode}/,
#   история версий — в prompts/{mode}/versions/.
#
# File: router_admin.py
# Project: mediteka
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from header import __root__
from src.logger import logger

router = APIRouter(prefix='/api/admin', tags=['admin'])

# ============================================================================
# Пути к файлам инструкций
# ============================================================================

_INSTRUCTION_FILES: Dict[str, Path] = {
    'chat': __root__ / 'prompts' / 'chat' / 'system_instruction.md',
    'narrator': __root__ / 'prompts' / 'narrator' / 'narrator_style.md',
}

_VERSIONS_DIRS: Dict[str, Path] = {
    'chat': __root__ / 'prompts' / 'chat' / 'versions',
    'narrator': __root__ / 'prompts' / 'narrator' / 'versions',
}

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


def _get_active_file(mode: str) -> Path:
    """Возвращает путь к активному файлу инструкции по режиму."""
    path = _INSTRUCTION_FILES.get(mode)
    if not path:
        raise HTTPException(status_code=400, detail=f'Неизвестный режим: {mode}. Допустимые: chat, narrator')
    return path


def _get_versions_dir(mode: str) -> Path:
    """Возвращает путь к папке версий и создаёт её если нет."""
    path = _VERSIONS_DIRS.get(mode)
    if not path:
        raise HTTPException(status_code=400, detail=f'Неизвестный режим: {mode}')
    path.mkdir(parents=True, exist_ok=True)
    return path


def _next_version_number(versions_dir: Path) -> int:
    """Вычисляет следующий номер версии на основе файлов в папке."""
    existing = list(versions_dir.glob('v*.md'))
    numbers = []
    for f in existing:
        m = re.match(r'^v(\d+)_', f.name)
        if m:
            numbers.append(int(m.group(1)))
    return max(numbers, default=0) + 1


def _load_sources_raw() -> str:
    """Загружает сырой текст из sources.json."""
    if _SOURCES_FILE.exists():
        try:
            return _SOURCES_FILE.read_text(encoding='utf-8')
        except Exception as ex:
            logger.error('Ошибка чтения sources.json', ex)
    return '{}'


def _save_sources_raw(content: str) -> None:
    """Сохраняет сырой текст в sources.json."""
    try:
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


class InstructionRoleUpdate(BaseModel):
    mode: str   # 'chat' | 'narrator'
    content: str


class InstructionActivateRequest(BaseModel):
    mode: str       # 'chat' | 'narrator'
    filename: str   # имя файла из папки versions/, например 'v2_2026-08-07.md'


# ============================================================================
# Legacy System Instruction Endpoints (backward compat)
# ============================================================================

@router.get('/system_instruction')
async def get_system_instruction(request: Request) -> Dict[str, str]:
    """Получение текста системной инструкции чата (legacy endpoint)."""
    _check_admin(request)
    active_file = _get_active_file('chat')
    try:
        content = active_file.read_text(encoding='utf-8') if active_file.exists() else ''
        return {'content': content}
    except Exception as ex:
        logger.error('Ошибка чтения system_instruction', ex)
        raise HTTPException(status_code=500, detail='Не удалось прочитать системную инструкцию')


@router.post('/system_instruction')
async def update_system_instruction(request: Request, data: SystemInstructionUpdate) -> Dict[str, str]:
    """Обновление текста системной инструкции чата (legacy endpoint)."""
    _check_admin(request)
    active_file = _get_active_file('chat')
    try:
        active_file.parent.mkdir(parents=True, exist_ok=True)
        active_file.write_text(data.content, encoding='utf-8')
        logger.info('System instruction updated via admin panel (legacy endpoint)')
        return {'status': 'ok', 'message': 'Системная инструкция успешно сохранена'}
    except Exception as ex:
        logger.error('Ошибка записи system_instruction', ex)
        raise HTTPException(status_code=500, detail='Не удалось сохранить системную инструкцию')


# ============================================================================
# Instructions Endpoints (файловое версионирование)
# ============================================================================

@router.get('/instructions')
async def get_instruction(request: Request, mode: str = 'chat') -> Dict[str, str]:
    """Получение активной инструкции по режиму из файла."""
    _check_admin(request)
    active_file = _get_active_file(mode)
    try:
        content = active_file.read_text(encoding='utf-8') if active_file.exists() else ''
        return {'content': content, 'mode': mode, 'file': str(active_file.name)}
    except Exception as ex:
        logger.error(f'Ошибка чтения инструкции mode={mode}', ex)
        raise HTTPException(status_code=500, detail='Не удалось прочитать инструкцию')


@router.post('/instructions/save')
async def save_instruction(request: Request, data: InstructionRoleUpdate) -> Dict[str, str]:
    """Сохранение новой версии инструкции в файл и обновление активного файла."""
    _check_admin(request)
    active_file = _get_active_file(data.mode)
    versions_dir = _get_versions_dir(data.mode)

    try:
        # 1. Вычисляем номер следующей версии
        version_num = _next_version_number(versions_dir)
        date_str = datetime.now().strftime('%Y-%m-%d')
        version_filename = f'v{version_num}_{date_str}.md'
        version_path = versions_dir / version_filename

        # 2. Сохраняем файл версии
        version_path.write_text(data.content, encoding='utf-8')
        logger.info(f'Saved instruction version: {version_path}')

        # 3. Перезаписываем активный файл
        active_file.parent.mkdir(parents=True, exist_ok=True)
        active_file.write_text(data.content, encoding='utf-8')
        logger.info(f'Updated active instruction file: {active_file} (mode={data.mode})')

        return {
            'status': 'ok',
            'message': f'Инструкция сохранена как версия {version_filename}',
            'version': version_filename
        }
    except Exception as ex:
        logger.error(f'Ошибка сохранения инструкции mode={data.mode}', ex)
        raise HTTPException(status_code=500, detail='Не удалось сохранить инструкцию')


@router.get('/instructions/versions')
async def get_instruction_versions(request: Request, mode: str = 'chat') -> Dict[str, Any]:
    """Получение списка версий инструкций из папки versions/."""
    _check_admin(request)
    versions_dir = _get_versions_dir(mode)
    active_file = _get_active_file(mode)

    try:
        # Читаем содержимое активного файла для сравнения
        active_content = active_file.read_text(encoding='utf-8') if active_file.exists() else ''

        version_files = sorted(versions_dir.glob('v*.md'), key=lambda f: f.stat().st_mtime, reverse=True)

        versions = []
        for vf in version_files:
            try:
                file_content = vf.read_text(encoding='utf-8')
                stat = vf.stat()
                created_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
                is_active = (file_content.strip() == active_content.strip())
                versions.append({
                    'filename': vf.name,
                    'mode': mode,
                    'is_active': is_active,
                    'created_at': created_at,
                    'size': stat.st_size,
                    'preview': file_content[:120] + '...' if len(file_content) > 120 else file_content,
                })
            except Exception as read_ex:
                logger.warning(f'Не удалось прочитать файл версии {vf}: {read_ex}')

        return {'versions': versions, 'mode': mode}
    except Exception as ex:
        logger.error(f'Ошибка чтения версий mode={mode}', ex)
        raise HTTPException(status_code=500, detail='Не удалось прочитать версии')


@router.post('/instructions/activate')
async def activate_instruction(request: Request, data: InstructionActivateRequest) -> Dict[str, str]:
    """Активация выбранной версии инструкции — копирует файл версии в активный."""
    _check_admin(request)
    versions_dir = _get_versions_dir(data.mode)
    active_file = _get_active_file(data.mode)

    # Безопасность: только имя файла, без path traversal
    safe_filename = Path(data.filename).name
    version_path = versions_dir / safe_filename

    if not version_path.exists():
        raise HTTPException(status_code=404, detail=f'Версия {safe_filename} не найдена')

    try:
        content = version_path.read_text(encoding='utf-8')
        active_file.parent.mkdir(parents=True, exist_ok=True)
        active_file.write_text(content, encoding='utf-8')
        logger.info(f'Activated instruction version {safe_filename} for mode={data.mode}')
        return {'status': 'ok', 'message': f'Версия {safe_filename} активирована', 'version': safe_filename}
    except Exception as ex:
        logger.error(f'Ошибка активации версии {safe_filename}', ex)
        raise HTTPException(status_code=500, detail='Не удалось активировать версию')


@router.post('/instructions/check')
async def check_instruction_in_model(request: Request, data: Dict[str, Any]) -> Dict[str, Any]:
    """Временная проверка инструкции в модели без сохранения."""
    _check_admin(request)
    try:
        from src.ai.unified_chat import UnifiedChatModel
        import os

        api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
        if not api_key_names:
            raise HTTPException(status_code=500, detail='GEMINI_API_KEY_NAMES не настроен')

        system_instruction = data.get('instruction', '')
        prompt = data.get('prompt', 'Привет!')
        foundry_model_id = os.getenv('FOUNDRY_MODEL_ID', 'qwen3-0.6b-generic-cpu:4')

        # Создаём временный инстанс модели для теста
        temp_model = UnifiedChatModel(
            api_key_names=api_key_names,
            system_instruction=system_instruction,
            foundry_model_id=foundry_model_id,
            use_foundry=False,
        )

        response = await temp_model.chat(prompt)

        total_tokens = len(system_instruction) // 3 + len(prompt) // 3 + len(response or '') // 3

        return {
            'status': 'ok',
            'response': response or '',
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
    logger.info(f'Plugin {plugin_name} enabled state changed to {data.enabled}')
    return {'name': plugin_name, 'enabled': plugin.enabled}


# ============================================================================
# Initialization
# ============================================================================

def init_router() -> APIRouter:
    """Инициализация роутера управления системными инструкциями и источниками."""
    return router
