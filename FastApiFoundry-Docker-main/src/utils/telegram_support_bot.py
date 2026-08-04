# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telegram Support Bot
# =============================================================================
# Description:
#   Customer-facing Telegram bot. Receives user questions, searches the
#   configured RAG profile for context, generates an answer via the active
#   AI model, and returns it to the user.
#   Operator can view conversations via the web UI /api/v1/support/dialogs.
#
# File: src/utils/telegram_support_bot.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from telebot.async_telebot import AsyncTeleBot

from ..core.config import config

logger = logging.getLogger(__name__)

# Dialogs storage file
_DIALOGS_FILE = Path("logs/support_dialogs.jsonl")


def _save_message(chat_id: int, username: str, role: str, text: str) -> None:
    """Append a message to the dialogs log.

    Args:
        chat_id (int): Telegram chat id.
        username (str): Telegram username or first name.
        role (str): 'user' or 'assistant'.
        text (str): Message text.
    """
    _DIALOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "chat_id": chat_id,
        "username": username,
        "role": role,
        "text": text,
        "ts": datetime.now().isoformat(),
    }
    with open(_DIALOGS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


async def _ask_model(question: str, rag_profile: str) -> str:
    """Search RAG profile and generate answer via active model.

    Args:
        question (str): User question.
        rag_profile (str): RAG profile name to search.

    Returns:
        str: Generated answer text.
    """
    import aiohttp

    base = f"http://localhost:{config.api_port}/api/v1"

    # RAG search
    context = ""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base}/rag/search",
                json={"query": question, "top_k": 5, "profile": rag_profile},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                results = data.get("results") or []
                context = "\n\n".join(r.get("text", "") for r in results[:3])
    except Exception as e:
        logger.warning(f"RAG search failed: {e}")

    # Build prompt
    system_prompt = (
        "You are a helpful support assistant for FastAPI Foundry. "
        "Answer the user's question based on the provided documentation context. "
        "Be concise and accurate. If the context doesn't contain the answer, say so."
    )
    user_content = f"Context:\n{context}\n\nQuestion: {question}" if context else question

    # Generate via active model
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base}/ai/generate",
                json={
                    "prompt": user_content,
                    "system_prompt": system_prompt,
                    "use_rag": False,  # Already injected context manually
                    "max_tokens": 1024,
                    "temperature": 0.5,
                },
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                data = await resp.json()
                return data.get("content") or data.get("error") or "No response from model."
    except Exception as e:
        logger.error(f"Model generation failed: {e}")
        return "Sorry, the AI model is currently unavailable. Please try again later."


class TelegramSupportBot:
    """Customer-facing support bot powered by RAG + local AI model."""

    def __init__(self) -> None:
        self.bot: Optional[AsyncTeleBot] = None
        self._rag_profile: str = config.telegram_support_rag_profile

    async def start(self) -> None:
        """Start polling. Exits silently if support bot is disabled."""
        token = config.telegram_support_token
        if not token:
            logger.info("Telegram support bot disabled (no token).")
            return

        self.bot = AsyncTeleBot(token)
        logger.info("✅ Telegram support bot started.")

        @self.bot.message_handler(commands=["start", "help"])
        async def on_start(message):
            await self.bot.reply_to(
                message,
                "👋 Hello! I'm the FastAPI Foundry support assistant.\n"
                "Ask me anything about the system and I'll do my best to help.",
            )

        @self.bot.message_handler(func=lambda m: True, content_types=["text"])
        async def on_message(message):
            chat_id = message.chat.id
            username = message.from_user.username or message.from_user.first_name or str(chat_id)
            text = message.text.strip()

            _save_message(chat_id, username, "user", text)

            # Typing indicator
            await self.bot.send_chat_action(chat_id, "typing")

            answer = await _ask_model(text, self._rag_profile)
            _save_message(chat_id, username, "assistant", answer)

            await self.bot.reply_to(message, answer)

        await self.bot.infinity_polling(skip_pending=True)


support_bot = TelegramSupportBot()
