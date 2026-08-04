# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telegram Listener Bot
# =============================================================================
# Description:
#   Passive Telegram bot that only listens and logs all incoming messages.
#   Does NOT send any replies. Useful for monitoring, data collection,
#   and building training datasets from real conversations.
#
#   Token: TELEGRAM_LISTENER_TOKEN in .env
#
# File: telegram/listener_bot.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Changes in 0.8.0:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from telebot.async_telebot import AsyncTeleBot

sys.path.insert(0, str(Path(__file__).parent.parent))
from config_manager import config

logger = logging.getLogger(__name__)

_LOG_FILE = Path(config.dir_dialogs) / "listener_log.jsonl"


def _log(message) -> None:
    """Append incoming message to JSONL log file.

    Args:
        message: Telebot Message object.
    """
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now().isoformat(),
        "chat_id": message.chat.id,
        "chat_type": message.chat.type,
        "user_id": message.from_user.id if message.from_user else None,
        "username": (message.from_user.username or message.from_user.first_name) if message.from_user else None,
        "content_type": message.content_type,
        "text": message.text or "",
    }
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.debug(f"📥 [{entry['chat_id']}] {entry['username']}: {entry['text'][:80]}")


class ListenerBot:
    """Passive Telegram bot — listens and logs, never replies."""

    def __init__(self) -> None:
        self.bot: Optional[AsyncTeleBot] = None

    async def start(self) -> None:
        """Start polling. Exits silently if TELEGRAM_LISTENER_TOKEN is not set."""
        token = config.telegram_listener_token
        if not token:
            logger.info("Listener bot disabled (TELEGRAM_LISTENER_TOKEN not set).")
            return

        self.bot = AsyncTeleBot(token)
        logger.info("✅ Listener bot started.")
        self._register_handlers()

        try:
            await self.bot.infinity_polling(skip_pending=True)
        except Exception as e:
            logger.error(f"Listener bot polling error: {e}")

    def _register_handlers(self) -> None:
        bot = self.bot

        @bot.message_handler(func=lambda m: True, content_types=[
            "text", "photo", "document", "voice", "video",
            "sticker", "location", "contact", "audio",
        ])
        async def on_any(message):
            _log(message)


listener_bot = ListenerBot()
