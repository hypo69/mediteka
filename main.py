# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Запуск веб-сервера AI Assistant
# =============================================================================
# Описание:
#   Инициализация FastAPI-приложения, подключение роутеров,
#   запуск uvicorn-сервера с поддержкой Telegram-бота.
#
# File: main.py
# Project: gemini-simplechat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
import os
import signal
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import header
from header import __root__
from src.ai import GoogleGenerativeAI
from src.fastapi import init_auth_router, init_chat_router, init_control_router, init_media_router, init_qbt_router, init_tts_router
from src.logger import logger
from src.utils.file import read_text_file
from src.utils.jjson import j_loads_ns
from plugins import load_plugins

load_dotenv(__root__ / '.env')
_cfg = j_loads_ns(__root__ / 'src' / 'fastapi' / 'config.json')

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Mount static files
app.mount('/webinterface', StaticFiles(directory=__root__ / 'webinterface'), name='webinterface')
app.mount('/html', StaticFiles(directory=__root__ / 'webinterface'), name='html')


_system_instruction: str = read_text_file(__root__ / '.ai_instructions' / 'prompts' / 'chat' / 'system_instruction.md') or ''
_api_key_names: list[str] = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]

use_foundry = os.getenv('USE_FOUNDRY', 'false').lower() in ('true', '1', 'yes')
foundry_model_id = os.getenv('FOUNDRY_MODEL_ID', 'qwen3-0.6b-generic-cpu:4')

if use_foundry:
    from src.ai.foundry_chat import FoundryChatBase
    model = FoundryChatBase(
        model_id=foundry_model_id,
        system_prompt=_system_instruction,
    )
else:
    model: GoogleGenerativeAI = GoogleGenerativeAI(
        api_key_names=_api_key_names,
        system_instruction=_system_instruction,
    )
plugins = load_plugins(model)

app.include_router(init_chat_router(model, plugins))
app.include_router(init_qbt_router())
app.include_router(init_media_router(prefix='/api/media-admin'))
app.include_router(init_media_router(prefix='/api/media'))
app.include_router(init_auth_router())
app.include_router(init_control_router())
app.include_router(init_tts_router())




@app.get('/', response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serving of main HTML page - redirects to user interface."""
    content = read_text_file(__root__ / 'webinterface' / 'tv' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read user index page')
    return HTMLResponse(content=content)


@app.get('/user', response_class=HTMLResponse)
async def user_interface() -> HTMLResponse:
    """Serving of user HTML page (player + chat)."""
    content = read_text_file(__root__ / 'webinterface' / 'tv' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read user index page')
    return HTMLResponse(content=content)


@app.get('/user/{full_path:path}', response_class=HTMLResponse)
async def user_static(full_path: str) -> HTMLResponse:
    """Serving user static files."""
    content = read_text_file(__root__ / 'webinterface' / 'user' / full_path)
    if not content:
        raise HTTPException(status_code=404, detail='File not found')
    return HTMLResponse(content=content)


@app.get('/tgmini', response_class=HTMLResponse)
async def tgmini_interface() -> HTMLResponse:
    """Serving of Telegram Mini App HTML page."""
    content = read_text_file(__root__ / 'webinterface' / 'tgmini' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read Telegram Mini App index page')
    return HTMLResponse(content=content)


@app.get('/tgmini/{full_path:path}', response_class=HTMLResponse)
async def tgmini_static(full_path: str) -> HTMLResponse:
    """Serving Telegram Mini App static files."""
    content = read_text_file(__root__ / 'webinterface' / 'tgmini' / full_path)
    if not content:
        raise HTTPException(status_code=404, detail='File not found')
    return HTMLResponse(content=content)


@app.get('/rc', response_class=HTMLResponse)
async def rc_interface() -> HTMLResponse:
    """Serving of Remote Control HTML page."""
    content = read_text_file(__root__ / 'webinterface' / 'rc' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read Remote Control page')
    return HTMLResponse(content=content)


@app.get('/rc/{full_path:path}', response_class=HTMLResponse)
async def rc_static(full_path: str) -> HTMLResponse:
    """Serving Remote Control static files."""
    content = read_text_file(__root__ / 'webinterface' / 'rc' / full_path)
    if not content:
        raise HTTPException(status_code=404, detail='File not found')
    return HTMLResponse(content=content)


@app.get('/user_tts', response_class=HTMLResponse)
async def user_tts_interface() -> HTMLResponse:
    """Serving of User TTS experimental page."""
    content = read_text_file(__root__ / 'webinterface' / 'user_tts' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read User TTS page')
    return HTMLResponse(content=content)


@app.get('/user_tts/{full_path:path}', response_class=HTMLResponse)
async def user_tts_static(full_path: str) -> HTMLResponse:
    """Serving User TTS static files."""
    content = read_text_file(__root__ / 'webinterface' / 'user_tts' / full_path)
    if not content:
        raise HTTPException(status_code=404, detail='File not found')
    return HTMLResponse(content=content)



def check_admin_auth(request: Request):
    import base64
    from fastapi import Response
    from fastapi.responses import RedirectResponse
    token = request.cookies.get('auth_token')
    if not token:
        return RedirectResponse(url='/', status_code=303)
        
    from src.fastapi.router_auth import verify_jwt_token
    user_data = verify_jwt_token(token)
    if not user_data:
        return RedirectResponse(url='/', status_code=303)
        
    from src.user_manager import user_manager
    db_user = user_manager.get_user_by_email(user_data.email)
    if not db_user or (not db_user.get('is_admin', 0) and db_user.get('role') != 'admin'):
        return RedirectResponse(url='/', status_code=303)
        
    # User is admin. Now check password "onela" using Basic Auth.
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Admin Login"'}
        )
        
    try:
        encoded = auth_header.split(" ")[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":", 1)
        if password != "onela":
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Admin Login"'}
            )
    except Exception:
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Admin Login"'}
        )
        
    return None


@app.get('/admin')
async def admin_interface(request: Request):
    """Serving of admin HTML page with security verification."""
    auth_response = check_admin_auth(request)
    if auth_response:
        return auth_response
    content = read_text_file(__root__ / 'webinterface' / 'admin' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read admin index page')
    return HTMLResponse(content=content)


@app.get('/admin/{full_path:path}')
async def admin_static(full_path: str, request: Request):
    """Serving admin static files with security verification."""
    auth_response = check_admin_auth(request)
    if auth_response:
        return auth_response
    content = read_text_file(__root__ / 'webinterface' / 'admin' / full_path)
    if not content:
        raise HTTPException(status_code=404, detail='File not found')
    return HTMLResponse(content=content)


@app.get('/tv', response_class=HTMLResponse)
async def tv_interface() -> HTMLResponse:
    """Serving of TV Player HTML page."""
    content = read_text_file(__root__ / 'webinterface' / 'tv' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read TV index page')
    return HTMLResponse(content=content)


@app.get('/tv/{full_path:path}', response_class=HTMLResponse)
async def tv_static(full_path: str) -> HTMLResponse:
    """Serving TV static files."""
    content = read_text_file(__root__ / 'webinterface' / 'tv' / full_path)
    if not content:
        raise HTTPException(status_code=404, detail='File not found')
    return HTMLResponse(content=content)



if __name__ == '__main__':
    # Для разработки: однопроцессный запуск без --workers
    # В продакшене используйте Run-Unicorn.ps1, который запускает:
    #   uvicorn main:app --workers N  (без Telegram-бота)
    #   python bot_runner.py           (Telegram-бот отдельно)
    port: int = int(_cfg.port)
    if not port:
        logger.error('Порт не задан в конфигурации')
        sys.exit(1)

    cert_file = Path(r'C:\Users\onela\.certs\localhost+2.pem')
    key_file = Path(r'C:\Users\onela\.certs\localhost+2-key.pem')

    ssl_kwargs = {}
    use_ssl = os.getenv('USE_SSL', 'true').lower() in ('true', '1', 'yes')
    if use_ssl and cert_file.exists() and key_file.exists():
        ssl_kwargs = {'ssl_certfile': str(cert_file), 'ssl_keyfile': str(key_file)}
        logger.info(f'Запуск сервера https://{_cfg.host}:{port} (SSL включен)')
    else:
        logger.warning('Запуск без HTTPS (SSL выключен или сертификаты не найдены)')
        logger.info(f'Запуск сервера http://{_cfg.host}:{port}')

    uvicorn.run('main:app', host=_cfg.host, port=port, **ssl_kwargs)
