# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Автономный запуск Telegram-бота
# =============================================================================
# Описание:
#   Запускает Telegram-бота в отдельном процессе, независимо от uvicorn.
#   Использует те же плагины и AI-модель, что и основной сервер.
#   Запускается через Run-Unicorn.ps1 параллельно с uvicorn --workers.
#
# File: bot_runner.py
# Project: gemini-simplechat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
import os
import sys
import signal
from pathlib import Path

from dotenv import load_dotenv

import header
from header import __root__

load_dotenv(__root__ / '.env')

from src.utils.jjson import j_loads_ns
from src.logger import logger

_cfg = j_loads_ns(__root__ / 'src' / 'fastapi' / 'config.json')


async def _run_bot() -> None:
    """Запуск Telegram-бота с полным набором плагинов и AI-модели."""
    from src.ai import GoogleGenerativeAI
    from src.utils.file import read_text_file
    from plugins import load_plugins

    _system_instruction = read_text_file(__root__ / '.ai_instructions' / 'prompts' / 'chat' / 'system_instruction.md') or ''
    _api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]

    use_foundry = os.getenv('USE_FOUNDRY', 'false').lower() in ('true', '1', 'yes')
    foundry_model_id = os.getenv('FOUNDRY_MODEL_ID', 'qwen3-0.6b-generic-cpu:4')

    if use_foundry:
        from src.ai.foundry_chat import FoundryChatBase
        model = FoundryChatBase(model_id=foundry_model_id, system_prompt=_system_instruction)
    else:
        model = GoogleGenerativeAI(api_key_names=_api_key_names, system_instruction=_system_instruction)

    plugins = load_plugins(model)
    tg_plugin = plugins.get('telegram_bot')

    if not tg_plugin:
        logger.warning('Telegram-бот плагин не найден — bot_runner завершается.')
        return

    if hasattr(tg_plugin, 'set_plugins'):
        tg_plugin.set_plugins(plugins)

    loop = asyncio.get_event_loop()

    stop_event = asyncio.Event()

    def _handle_exit(*_):
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_exit)
        except (NotImplementedError, AttributeError):
            signal.signal(sig, _handle_exit)

    logger.info('Telegram-бот запущен (отдельный процесс)')
    try:
        await tg_plugin.start()
        await stop_event.wait()
    finally:
        await tg_plugin.stop()
        logger.info('Telegram-бот остановлен')


if __name__ == '__main__':
    asyncio.run(_run_bot())
