# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telegram HelpDesk Bot
# =============================================================================
# Description:
#   Customer-facing support bot for FastAPI Foundry.
#   Flow:
#     1. User sends a question in Telegram
#     2. Bot searches the configured RAG profile for relevant context
#     3. Context + question are sent to the active AI model via /api/v1/ai/generate
#     4. Answer is returned to the user
#     5. Full dialog is saved to logs/helpdesk_dialogs.jsonl
#
#   Token:      TELEGRAM_HELPDESK_TOKEN in .env
#   RAG profile: config.json → telegram_helpdesk.rag_profile  (default: "support")
#   No access restriction — any Telegram user can write to the bot.
#
# File: telegram/helpdesk_bot.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiohttp
from telebot.async_telebot import AsyncTeleBot
from telebot import types

sys.path.insert(0, str(Path(__file__).parent.parent))
from config_manager import config

logger = logging.getLogger(__name__)

_DIALOGS_FILE = Path(config.dir_dialogs) / "helpdesk_dialogs.jsonl"

# Per-user conversation history (in-memory, keyed by chat_id)
# Stores last N turns for multi-turn context
_MAX_HISTORY_TURNS = 6
_history: dict[int, list[dict]] = {}


# ── Dialog persistence ────────────────────────────────────────────────────────

def _save(chat_id: int, username: str, role: str, text: str) -> None:
    """Append one message to the JSONL dialog log.

    Args:
        chat_id (int): Telegram chat id.
        username (str): Display name of the user.
        role (str): 'user' or 'assistant'.
        text (str): Message content.
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


# ── RAG search ────────────────────────────────────────────────────────────────

async def _rag_search(query: str, profile: str) -> str:
    """Search the RAG profile and return concatenated top-3 chunks.

    Args:
        query (str): User question.
        profile (str): RAG profile name (subdirectory under ~/.rag/).

    Returns:
        str: Concatenated context text, or empty string on failure.
    """
    base = f"http://localhost:{config.api_port}/api/v1"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base}/rag/search",
                json={"query": query, "top_k": 5, "profile": profile},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                data = await resp.json()
                results = data.get("results") or []
                return "\n\n".join(r.get("text", "") for r in results[:3])
    except Exception as e:
        logger.warning(f"RAG search failed: {e}")
        return ""


# ── AI generation ─────────────────────────────────────────────────────────────

async def _generate(chat_id: int, question: str, context: str) -> str:
    """Generate an answer using the active AI model.

    Builds a system prompt with documentation context and sends the
    conversation history for multi-turn support.

    Args:
        chat_id (int): Used to retrieve per-user history.
        question (str): Current user question.
        context (str): RAG context text (may be empty).

    Returns:
        str: Model answer or error message.
    """
    base = f"http://localhost:{config.api_port}/api/v1"

    system_prompt = (
        "You are a helpful support assistant for FastAPI Foundry — "
        "a local AI model server. Answer the user's question based on "
        "the provided documentation context. Be concise and accurate. "
        "If the context does not contain the answer, say so honestly."
    )

    # Inject RAG context into the user turn
    user_content = f"Documentation context:\n{context}\n\nQuestion: {question}" if context else question

    # Build history for multi-turn
    history = _history.get(chat_id, [])
    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_content})

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base}/ai/generate",
                json={
                    "prompt": user_content,
                    "system_prompt": system_prompt,
                    "messages": messages,
                    "use_rag": False,
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


def _update_history(chat_id: int, question: str, answer: str) -> None:
    """Add the latest turn to in-memory history, capped at _MAX_HISTORY_TURNS.

    Args:
        chat_id (int): Telegram chat id.
        question (str): User message.
        answer (str): Assistant reply.
    """
    turns = _history.setdefault(chat_id, [])
    turns.append({"role": "user",      "content": question})
    turns.append({"role": "assistant", "content": answer})
    # Keep only the last N turns (2 messages per turn)
    if len(turns) > _MAX_HISTORY_TURNS * 2:
        _history[chat_id] = turns[-(  _MAX_HISTORY_TURNS * 2):]


# ── Bot class ─────────────────────────────────────────────────────────────────

class HelpdeskBot:
    """Customer-facing helpdesk bot powered by RAG + local AI model."""

    def __init__(self) -> None:
        self.bot: Optional[AsyncTeleBot] = None
        self._rag_profile: str = config.telegram_helpdesk_rag_profile

    async def start(self) -> None:
        """Start polling. Exits silently if TELEGRAM_HELPDESK_TOKEN is not set."""
        token = config.telegram_helpdesk_token
        if not token:
            logger.info("HelpDesk bot disabled (TELEGRAM_HELPDESK_TOKEN not set).")
            return

        self.bot = AsyncTeleBot(token)
        logger.info("✅ HelpDesk bot started.")
        self._register_handlers()

        try:
            await self.bot.infinity_polling(skip_pending=True)
        except Exception as e:
            logger.error(f"HelpDesk bot polling error: {e}")

    def _register_handlers(self) -> None:
        bot = self.bot

        # ── /start ─────────────────────────────────────────────────────────

        @bot.message_handler(commands=['start', 'help'])
        async def on_start(message):
            username = message.from_user.first_name or "there"
            await bot.reply_to(message, (
                f"👋 Hi, {username}!\n\n"
                "I'm the *FastAPI Foundry* support assistant.\n"
                "Ask me anything about the system — I'll search the documentation "
                "and answer using AI.\n\n"
                "Commands:\n"
                "/new — Start a new conversation\n"
                "/help — Show this message"
            ), parse_mode='Markdown')

        # ── /new — reset history ───────────────────────────────────────────

        @bot.message_handler(commands=['new'])
        async def on_new(message):
            _history.pop(message.chat.id, None)
            await bot.reply_to(message, "🔄 Conversation reset. Ask your question!")

        # ── Main message handler ───────────────────────────────────────────

        @bot.message_handler(func=lambda m: True, content_types=['text'])
        async def on_message(message):
            chat_id  = message.chat.id
            username = message.from_user.username or message.from_user.first_name or str(chat_id)
            question = message.text.strip()

            if not question:
                return

            _save(chat_id, username, "user", question)

            # Show typing indicator while processing
            await bot.send_chat_action(chat_id, "typing")

            # RAG search
            context = await _rag_search(question, self._rag_profile)

            # Generate answer (typing indicator may expire for long models — resend)
            await bot.send_chat_action(chat_id, "typing")
            answer = await _generate(chat_id, question, context)

            _save(chat_id, username, "assistant", answer)
            _update_history(chat_id, question, answer)

            # Split long answers (Telegram limit: 4096 chars)
            for chunk in _split(answer, 4000):
                await bot.reply_to(message, chunk)

        # ── Unsupported content ────────────────────────────────────────────

        @bot.message_handler(content_types=['photo', 'document', 'voice', 'video'])
        async def on_unsupported(message):
            await bot.reply_to(message, "⚠️ Please send text questions only.")


def _split(text: str, limit: int) -> list[str]:
    """Split text into chunks no longer than limit characters.

    Args:
        text (str): Source text.
        limit (int): Maximum chunk length.

    Returns:
        list[str]: List of chunks.
    """
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    while text:
        chunks.append(text[:limit])
        text = text[limit:]
    return chunks


helpdesk_bot = HelpdeskBot()
