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
        
        # Обновляем модель в памяти без перезагрузки
        if data.mode == 'chat' and hasattr(request.app.state, 'chat_model'):
            request.app.state.chat_model.update_system_instruction(data.content)
        elif data.mode == 'narrator' and hasattr(request.app.state, 'narrator_model'):
            request.app.state.narrator_model.update_system_instruction(data.content)
            
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
        
        # Обновляем модель в памяти без перезагрузки
        if data.mode == 'chat' and hasattr(request.app.state, 'chat_model'):
            request.app.state.chat_model.update_system_instruction(content)
        elif data.mode == 'narrator' and hasattr(request.app.state, 'narrator_model'):
            request.app.state.narrator_model.update_system_instruction(content)
            
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
# RAG Endpoints
# ============================================================================

class RagConfigRequest(BaseModel):
    mode: str

@router.get('/rag/config')
async def get_rag_config(request: Request):
    """Получение режима RAG."""
    _check_admin(request)
    config_path = __root__ / 'config.json'
    mode = "rag+model"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                mode = cfg.get("rag", {}).get("mode", "rag+model")
        except Exception as e:
            logger.error("Ошибка чтения config.json", e)
    return {"mode": mode}

@router.post('/rag/config')
async def set_rag_config(request: Request, data: RagConfigRequest):
    """Установка режима RAG."""
    _check_admin(request)
    config_path = __root__ / 'config.json'
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        else:
            cfg = {}
            
        if "rag" not in cfg:
            cfg["rag"] = {}
            
        cfg["rag"]["mode"] = data.mode
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            
        return {"status": "ok", "mode": data.mode}
    except Exception as e:
        logger.error("Ошибка записи config.json", e)
        raise HTTPException(status_code=500, detail="Ошибка сохранения конфигурации RAG")


class WebSearchConfigRequest(BaseModel):
    engine: str
    gemini_model: str = "gemini-2.5-flash"
    agy_model: str = "agy-flash"

@router.get('/web-search/config')
async def get_web_search_config(request: Request):
    """Получение конфигурации сервера веб-поиска."""
    _check_admin(request)
    config_path = __root__ / 'config.json'
    engine = "playwright"
    gemini_model = "gemini-2.5-flash"
    agy_model = "agy-flash"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                ws = cfg.get("web_search", {})
                engine = ws.get("engine", "playwright")
                gemini_model = ws.get("gemini_model", "gemini-2.5-flash")
                agy_model = ws.get("agy_model", "agy-flash")
        except Exception as e:
            logger.error("Ошибка чтения config.json для web_search", e)
    return {
        "engine": engine,
        "gemini_model": gemini_model,
        "agy_model": agy_model
    }

@router.post('/web-search/config')
async def set_web_search_config(request: Request, data: WebSearchConfigRequest):
    """Установка сервера веб-поиска (playwright / langchain / gemini / agy)."""
    _check_admin(request)
    config_path = __root__ / 'config.json'
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        else:
            cfg = {}
            
        if "web_search" not in cfg:
            cfg["web_search"] = {}
            
        cfg["web_search"]["engine"] = data.engine
        cfg["web_search"]["gemini_model"] = data.gemini_model
        cfg["web_search"]["agy_model"] = data.agy_model
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            
        return {
            "status": "ok",
            "engine": data.engine,
            "gemini_model": data.gemini_model,
            "agy_model": data.agy_model
        }
    except Exception as e:
        logger.error("Ошибка записи config.json для web_search", e)
        raise HTTPException(status_code=500, detail="Ошибка сохранения конфигурации веб-поиска")


class WebSearchTestRequest(BaseModel):
    query: str
    engine: str = ""

@router.post('/web-search/test')
async def test_web_search(request: Request, data: WebSearchTestRequest):
    """Тестовое выполнение поиска через выбранный поисковый движок."""
    _check_admin(request)
    query = data.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Поисковый запрос не может быть пустым")

    engine = data.engine
    gemini_model = "gemini-2.5-flash"
    agy_model = "agy-flash"
    config_path = __root__ / 'config.json'
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                ws = cfg.get("web_search", {})
                if not engine:
                    engine = ws.get("engine", "playwright")
                gemini_model = ws.get("gemini_model", "gemini-2.5-flash")
                agy_model = ws.get("agy_model", "agy-flash")
        except Exception as e:
            logger.error("Ошибка чтения config.json для web_search", e)

    if not engine:
        engine = "playwright"

    try:
        if engine == "gemini":
            from plugins.web_search.gemini_searcher import GeminiWebSearcher
            searcher = GeminiWebSearcher()
            res = await searcher.search_and_extract(query, model=gemini_model)
            return {"status": "ok", "engine": engine, "result": res}
        elif engine == "agy":
            from plugins.web_search.agy_searcher import AgyWebSearcher
            searcher = AgyWebSearcher()
            res = await searcher.search_and_extract(query, model=agy_model)
            return {"status": "ok", "engine": engine, "result": res}
        elif engine == "langchain":
            from src.ai.langchain_agent import MediaSearchAgent
            agent = MediaSearchAgent(config_path=config_path)
            search_res = await agent.search(query)
            return {"status": "ok", "engine": engine, "result": json.dumps(search_res, ensure_ascii=False, indent=2)}
        else:
            from plugins.web_search.playwright_searcher import PlaywrightWebSearcher
            searcher = PlaywrightWebSearcher()
            res = await searcher.search_and_extract(query)
            return {"status": "ok", "engine": engine, "result": res}
    except Exception as e:
        logger.error(f"Ошибка тестового поиска {engine}", e)
        return {"status": "error", "engine": engine, "message": str(e)}




# ============================================================================
# Initialization
# ============================================================================

def init_router() -> APIRouter:
    """Инициализация роутера управления системными инструкциями и источниками."""
    return router
