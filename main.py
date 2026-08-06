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
from src.fastapi import init_auth_router, init_chat_router, init_control_router, init_media_router, init_qbt_router, init_tts_router, init_logs_router, init_keys_router, init_admin_router
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


# Auto login local user to user_id=1
@app.middleware("http")
async def auto_login_local_user(request: Request, call_next):
    # Check if host is local loopback (127.0.0.1 or localhost)
    if request.url.hostname in ('127.0.0.1', 'localhost'):
        token = request.cookies.get('auth_token', '')
        from src.fastapi.router_auth import verify_jwt_token
        is_token_valid = False
        if token:
            try:
                is_token_valid = verify_jwt_token(token) is not None
            except Exception:
                pass

        if not token or not is_token_valid:
            from src.user_manager import user_manager
            try:
                db_user = user_manager.get_user_by_id(1)
                if db_user:
                    from src.fastapi.router_auth import TokenData, create_jwt_token
                    token_data = TokenData(
                        email=db_user['email'],
                        name=db_user['name'],
                        picture=db_user.get('picture', ''),
                        id=db_user['id']
                    )
                    token = create_jwt_token(token_data)
                    response = await call_next(request)
                    response.set_cookie(
                        'auth_token',
                        token,
                        httponly=True,
                        secure=False,
                        samesite='lax',
                        max_age=3600 * 24 * 30  # 30 days
                    )
                    return response
            except Exception as e:
                logger.error(f"Error in auto_login_local_user middleware: {e}")
    return await call_next(request)


# Mount static files
webinterface_dir = __root__ / 'webinterface'
webinterface_dir.mkdir(parents=True, exist_ok=True)
app.mount('/webinterface', StaticFiles(directory=webinterface_dir), name='webinterface')
app.mount('/html', StaticFiles(directory=webinterface_dir), name='html')


_system_instruction: str = read_text_file(__root__ / 'prompts' / 'chat' / 'system_instruction.md') or ''
_api_key_names: list[str] = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]

use_foundry = os.getenv('USE_FOUNDRY', 'false').lower() in ('true', '1', 'yes')
foundry_model_id = os.getenv('FOUNDRY_MODEL_ID', 'qwen3-0.6b-generic-cpu:4')

from src.ai import UnifiedChatModel
model = UnifiedChatModel(
    api_key_names=_api_key_names,
    system_instruction=_system_instruction,
    foundry_model_id=foundry_model_id,
    use_foundry=use_foundry,
)
plugins = load_plugins(model)

app.include_router(init_chat_router(model, plugins))
app.include_router(init_qbt_router(model))
app.include_router(init_media_router(prefix='/api/media-admin'))
app.include_router(init_media_router(prefix='/api/media'))
app.include_router(init_auth_router())
app.include_router(init_control_router())
app.include_router(init_tts_router())
app.include_router(init_logs_router())
app.include_router(init_keys_router())
app.include_router(init_admin_router())


@app.on_event("startup")
async def startup_event():
    # Сканируем подключённые диски ОС и обновляем CONNECTED_DRIVES
    from plugins.media_organizer.core.drive_scanner import update_environment_drives
    update_environment_drives()

    from src.logger.log_analyzer import start_log_analyzer
    start_log_analyzer()
    
    if os.getenv('PRELOAD_SILERO', 'false').lower() in ('true', '1', 'yes'):
        from src.tts.silero import get_silero_model
        logger.info("Pre-loading Silero TTS model...")
        try:
            get_silero_model()
            logger.info("Silero TTS model pre-loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to pre-load Silero TTS model: {e}")




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



ADMIN_LOGIN_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход в панель управления</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Plus+Jakarta+Sans:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(255, 255, 255, 0.03);
            --card-border: rgba(255, 255, 255, 0.08);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.4);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
        }

        /* Ambient background glow */
        body::before {
            content: '';
            position: absolute;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, var(--primary-glow) 0%, transparent 70%);
            top: 20%;
            left: 30%;
            z-index: 0;
            filter: blur(40px);
            animation: float-slow 12s infinite alternate ease-in-out;
        }
        body::after {
            content: '';
            position: absolute;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(168, 85, 247, 0.2) 0%, transparent 70%);
            bottom: 15%;
            right: 25%;
            z-index: 0;
            filter: blur(50px);
            animation: float-slow 15s infinite alternate-reverse ease-in-out;
        }

        @keyframes float-slow {
            0% { transform: translate(0, 0) scale(1); }
            100% { transform: translate(50px, 30px) scale(1.1); }
        }

        .login-container {
            position: relative;
            z-index: 10;
            width: 100%;
            max-width: 400px;
            padding: 40px;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .logo {
            text-align: center;
            margin-bottom: 30px;
        }

        .logo h1 {
            font-size: 28px;
            font-weight: 600;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #fff 0%, var(--text-muted) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo p {
            font-size: 14px;
            color: var(--text-muted);
            margin-top: 8px;
        }

        .input-group {
            position: relative;
            margin-bottom: 24px;
        }

        .input-group input {
            width: 100%;
            padding: 16px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: #fff;
            font-size: 16px;
            outline: none;
            transition: all 0.3s ease;
            font-family: inherit;
        }

        .input-group input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 4px var(--primary-glow);
            background: rgba(255, 255, 255, 0.08);
        }

        .btn-submit {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, var(--primary) 0%, #4f46e5 100%);
            border: none;
            border-radius: 12px;
            color: #fff;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px var(--primary-glow);
            font-family: inherit;
        }

        .btn-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px var(--primary-glow);
        }

        .btn-submit:active {
            transform: translateY(0);
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>Панель управления</h1>
            <p>Введите пароль администратора для доступа</p>
        </div>
        <form method="POST" action="/admin">
            <div class="input-group">
                <input type="password" name="password" placeholder="Пароль" required autofocus autocomplete="current-password">
            </div>
            <button type="submit" class="btn-submit">Войти</button>
        </form>
    </div>
</body>
</html>
"""


def check_admin_auth(request: Request):
    from fastapi.responses import RedirectResponse, HTMLResponse
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
        
    # User is admin. Now check password "onela" using cookie check.
    if request.cookies.get('admin_password_verified') == 'true':
        return False
        
    if request.url.path != '/admin':
        return RedirectResponse(url='/admin', status_code=303)
        
    return HTMLResponse(content=ADMIN_LOGIN_HTML)


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


@app.post('/admin')
async def admin_interface_post(request: Request):
    """Verify password and set admin verification cookie or redirect to main page."""
    from fastapi.responses import RedirectResponse
    # First ensure user has valid auth token and role
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

    form = await request.form()
    password = form.get('password')
    if password == 'onela':
        response = RedirectResponse(url='/admin', status_code=303)
        response.set_cookie(key='admin_password_verified', value='true', max_age=86400 * 30, httponly=True)
        return response
    else:
        return RedirectResponse(url='/', status_code=303)



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


@app.get('/logs')
async def logs_interface():
    """Redirect to admin dashboard logs tab."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url='/admin#tab-logs', status_code=303)


from pydantic import BaseModel

class FoundryConfigRequest(BaseModel):
    enabled: bool
    url: str
    key: str
    model: str

@app.get('/api/foundry/config')
async def get_foundry_config():
    import os
    return {
        "enabled": os.getenv("USE_FOUNDRY", "false").lower() in ("true", "1", "yes"),
        "url": os.getenv("FOUNDRY_BASE_URL", "http://localhost:3000"),
        "key": os.getenv("FOUNDRY_API_KEY", ""),
        "model": os.getenv("FOUNDRY_MODEL_ID", "qwen3-0.6b-generic-cpu:4")
    }

@app.post('/api/foundry/config')
async def save_foundry_config(data: FoundryConfigRequest):
    from dotenv import set_key
    import os
    env_path = str(__root__ / '.env')
    
    set_key(env_path, "USE_FOUNDRY", "true" if data.enabled else "false")
    set_key(env_path, "FOUNDRY_BASE_URL", data.url)
    set_key(env_path, "FOUNDRY_API_KEY", data.key)
    set_key(env_path, "FOUNDRY_MODEL_ID", data.model)
    
    # Update current process environment
    os.environ["USE_FOUNDRY"] = "true" if data.enabled else "false"
    os.environ["FOUNDRY_BASE_URL"] = data.url
    os.environ["FOUNDRY_API_KEY"] = data.key
    os.environ["FOUNDRY_MODEL_ID"] = data.model
    
    return {"status": "ok"}



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
