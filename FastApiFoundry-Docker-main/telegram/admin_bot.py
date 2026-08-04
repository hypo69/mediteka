# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telegram Admin Bot
# =============================================================================
# Description:
#   Remote monitoring and management of FastAPI Foundry via Telegram.
#   Commands: /status, /stats, /foundry_start, /foundry_stop,
#             /logs, /get_logs, /clear_logs, /restart_server,
#             /rag_rebuild, /rag_status, /rag_profiles
#
#   Token: TELEGRAM_ADMIN_TOKEN in .env
#   Access: restricted to TELEGRAM_ADMIN_IDS (comma-separated user IDs)
#
# File: telegram/admin_bot.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import io
import json
import logging
import os
import platform
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import psutil
import matplotlib.pyplot as plt
from telebot.async_telebot import AsyncTeleBot
from telebot import types

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_manager import config
from src.utils.command_agent import CommandAgent

logger = logging.getLogger(__name__)

plt.switch_backend('Agg')


class AdminBot:
    """Admin bot: system monitoring and Foundry management."""

    def __init__(self) -> None:
        self.bot: Optional[AsyncTeleBot] = None
        self.agent: CommandAgent = CommandAgent()
        self.allowed_ids: List[int] = config.telegram_admin_ids
        self.computer_name: str = platform.node()

    # ── Access control ────────────────────────────────────────────────────

    def _is_allowed(self, message) -> bool:
        return not self.allowed_ids or message.from_user.id in self.allowed_ids

    # ── Broadcast to all admins ───────────────────────────────────────────

    async def broadcast(self, text: str) -> None:
        """Send a notification to all allowed admin IDs.

        Args:
            text (str): Markdown-formatted message text.
        """
        if not self.bot or not self.allowed_ids:
            return
        for uid in self.allowed_ids:
            try:
                await self.bot.send_message(uid, text, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Admin broadcast error to {uid}: {e}")

    # ── Background Foundry monitor ────────────────────────────────────────

    async def _monitor_foundry(self) -> None:
        """Periodically check Foundry status and disk usage; alert on issues."""
        last_status = "running"
        interval = config.telegram_status_check_interval
        disk_alert_sent = False

        while True:
            try:
                await asyncio.sleep(interval)

                # Disk usage alert at 95%
                disk = psutil.disk_usage(Path.cwd().anchor)
                if disk.percent > 95:
                    if not disk_alert_sent:
                        await self.broadcast(
                            f"🚨 *Disk Alert!*\n"
                            f"Usage: `{disk.percent}%`  Free: `{disk.free // 1024**3} GB`"
                        )
                        disk_alert_sent = True
                else:
                    disk_alert_sent = False

                # Foundry status change alert
                status_data = await self.agent.parse_foundry_status()
                current = status_data.get("status", "unknown")
                if current != last_status:
                    if current in ("failed", "stopped", "unknown"):
                        await self.broadcast(
                            f"🚨 *Foundry Alert!*\n"
                            f"Status changed: `{last_status}` ➡️ `{current}`"
                        )
                    last_status = current
            except Exception as e:
                logger.error(f"Admin monitor error: {e}")

    # ── Bot startup ───────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start admin bot polling. Exits silently if token is not set."""
        token = config.telegram_admin_token
        if not token:
            logger.info("Admin bot disabled (TELEGRAM_ADMIN_TOKEN not set).")
            return

        self.bot = AsyncTeleBot(token)
        logger.info("✅ Admin bot started.")
        asyncio.create_task(self._monitor_foundry())
        self._register_handlers()

        try:
            await self.bot.infinity_polling(skip_pending=True)
        except Exception as e:
            logger.error(f"Admin bot polling error: {e}")

    # ── Handlers ──────────────────────────────────────────────────────────

    def _register_handlers(self) -> None:
        bot = self.bot

        # ── Callbacks ─────────────────────────────────────────────────────

        @bot.callback_query_handler(func=lambda c: c.data.startswith(
            ("confirm_restart_", "confirm_clear_logs_", "rag_profile_")
        ))
        async def on_callback(call):
            if self.allowed_ids and call.from_user.id not in self.allowed_ids:
                await bot.answer_callback_query(call.id, "Access denied.")
                return
            try:
                cid, mid = call.message.chat.id, call.message.message_id

                if call.data == "confirm_restart_yes":
                    await bot.edit_message_text("🔄 *Restarting...*", cid, mid, parse_mode='Markdown')
                    await asyncio.sleep(1)
                    os.execv(sys.executable, [sys.executable] + sys.argv)

                elif call.data == "confirm_restart_no":
                    await bot.edit_message_text("✅ Restart cancelled.", cid, mid)

                elif call.data == "confirm_clear_logs_yes":
                    log_path = Path("logs/fastapi-foundry.log")
                    if log_path.exists():
                        log_path.write_text("", encoding="utf-8")
                        await bot.edit_message_text("🧹 *Log file cleared.*", cid, mid, parse_mode='Markdown')
                    else:
                        await bot.edit_message_text("⚠️ Log file not found.", cid, mid)

                elif call.data == "confirm_clear_logs_no":
                    await bot.edit_message_text("✅ Clear logs cancelled.", cid, mid)

            except Exception as e:
                logger.error(f"Admin callback error: {e}")

        # ── /start /help ───────────────────────────────────────────────────

        @bot.message_handler(commands=['start', 'help'])
        async def on_help(message):
            if not self._is_allowed(message):
                return
            await bot.reply_to(message, (
                "🔧 *FastAPI Foundry — Admin Bot*\n\n"
                "/status — Foundry & system status\n"
                "/stats — CPU / RAM / Disk chart\n"
                "/foundry\\_start — Start Foundry service\n"
                "/foundry\\_stop — Stop Foundry service\n"
                "/logs — Last 5 errors from log\n"
                "/get\\_logs — Download full log file\n"
                "/clear\\_logs — Clear log file\n"
                "/restart\\_server — Restart FastAPI server\n"
                "/rag\\_rebuild — Rebuild RAG index\n"
                "/rag\\_status — RAG index info\n"
                "/rag\\_profiles — List RAG profiles"
            ), parse_mode='Markdown')

        # ── /status ────────────────────────────────────────────────────────

        @bot.message_handler(commands=['status'])
        async def on_status(message):
            if not self._is_allowed(message):
                return
            try:
                s = await self.agent.parse_foundry_status()
                await bot.reply_to(message, (
                    f"📊 *System Status*\n"
                    f"Foundry: `{s.get('status')}`\n"
                    f"Port: `{s.get('port') or 'N/A'}`\n"
                    f"PID: `{s.get('pid') or 'N/A'}`\n"
                    f"Time: `{datetime.now().strftime('%H:%M:%S')}`"
                ), parse_mode='Markdown')
            except Exception as e:
                logger.error(f"on_status error: {e}")

        # ── /stats ─────────────────────────────────────────────────────────

        @bot.message_handler(commands=['stats'])
        async def on_stats(message):
            if not self._is_allowed(message):
                return
            try:
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory()
                disk = psutil.disk_usage(Path.cwd().anchor)

                buf = io.BytesIO()
                try:
                    fig, ax = plt.subplots(figsize=(8, 5))
                    bars = ax.bar(['CPU', 'RAM', 'Disk'],
                                  [cpu, ram.percent, disk.percent],
                                  color=['#3498db', '#2ecc71', '#e67e22'])
                    ax.set_ylim(0, 100)
                    ax.set_ylabel('Usage (%)')
                    ax.set_title(f'Server Load — {datetime.now().strftime("%H:%M:%S")}')
                    for b in bars:
                        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1,
                                f'{b.get_height():.0f}%', ha='center', fontweight='bold')
                    fig.savefig(buf, format='png', bbox_inches='tight')
                    buf.seek(0)
                    plt.close(fig)
                    has_plot = True
                except Exception:
                    has_plot = False

                caption = (
                    f"📊 *Resources*\n"
                    f"CPU: `{cpu}%`\n"
                    f"RAM: `{ram.percent}%` (`{ram.used // 1024**2} MB` / `{ram.total // 1024**2} MB`)\n"
                    f"Disk: `{disk.percent}%` (`{disk.used // 1024**3} GB` / `{disk.total // 1024**3} GB`)"
                )
                if has_plot:
                    await bot.send_photo(message.chat.id, buf, caption=caption, parse_mode='Markdown')
                else:
                    await bot.reply_to(message, caption, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"on_stats error: {e}")

        # ── /foundry_start /foundry_stop ───────────────────────────────────

        @bot.message_handler(commands=['foundry_start'])
        async def on_foundry_start(message):
            if not self._is_allowed(message):
                return
            await bot.reply_to(message, "⏳ Starting Foundry...")
            result = await self.agent.run("foundry", ["service", "start"])
            status = "✅ Started" if result.get("exit_code") == 0 else f"❌ Error: {result.get('error')}"
            await bot.send_message(message.chat.id, status)

        @bot.message_handler(commands=['foundry_stop'])
        async def on_foundry_stop(message):
            if not self._is_allowed(message):
                return
            await bot.reply_to(message, "⏳ Stopping Foundry...")
            result = await self.agent.run("foundry", ["service", "stop"])
            status = "✅ Stopped" if result.get("exit_code") == 0 else f"❌ Error: {result.get('error')}"
            await bot.send_message(message.chat.id, status)

        # ── /logs /get_logs ────────────────────────────────────────────────

        @bot.message_handler(commands=['logs'])
        async def on_logs(message):
            if not self._is_allowed(message):
                return
            log_path = Path("logs/fastapi-foundry.log")
            try:
                lines = log_path.read_text(encoding="utf-8").splitlines()
                errors = [l for l in lines if "ERROR" in l][-5:]
                text = "\n".join(errors) if errors else "No errors found."
                await bot.reply_to(message, f"```\n{text[:4000]}\n```", parse_mode='Markdown')
            except Exception as e:
                await bot.reply_to(message, f"❌ {e}")

        @bot.message_handler(commands=['get_logs'])
        async def on_get_logs(message):
            if not self._is_allowed(message):
                return
            log_path = Path("logs/fastapi-foundry.log")
            if log_path.exists():
                with open(log_path, 'rb') as f:
                    await bot.send_document(message.chat.id, f, caption="📄 Full log file")
            else:
                await bot.reply_to(message, "⚠️ Log file not found.")

        # ── /clear_logs ────────────────────────────────────────────────────

        @bot.message_handler(commands=['clear_logs'])
        async def on_clear_logs(message):
            if not self._is_allowed(message):
                return
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Yes, clear", callback_data="confirm_clear_logs_yes"),
                types.InlineKeyboardButton("❌ Cancel",     callback_data="confirm_clear_logs_no"),
            )
            await bot.reply_to(message,
                "🧹 *Clear logs?*\nThis will erase `fastapi-foundry.log`.",
                reply_markup=markup, parse_mode='Markdown')

        # ── /restart_server ────────────────────────────────────────────────

        @bot.message_handler(commands=['restart_server'])
        async def on_restart(message):
            if not self._is_allowed(message):
                return
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Yes", callback_data="confirm_restart_yes"),
                types.InlineKeyboardButton("❌ No",  callback_data="confirm_restart_no"),
            )
            await bot.reply_to(message,
                "❓ *Restart FastAPI server?*",
                reply_markup=markup, parse_mode='Markdown')

        # ── /rag_rebuild /rag_status /rag_profiles ─────────────────────────

        @bot.message_handler(commands=['rag_rebuild'])
        async def on_rag_rebuild(message):
            if not self._is_allowed(message):
                return
            await bot.reply_to(message, "🏗️ RAG re-indexing initiated.")

        @bot.message_handler(commands=['rag_status'])
        async def on_rag_status(message):
            if not self._is_allowed(message):
                return
            try:
                index_dir = Path(config.rag_index_dir)
                meta_file = index_dir / "meta.json"
                index_file = index_dir / "faiss.index"
                if not index_dir.exists():
                    await bot.reply_to(message, "❌ RAG index directory not found.")
                    return
                lines = ["📚 *RAG Status*"]
                if meta_file.exists():
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    lines += [
                        f"Profile: `{meta.get('name', 'N/A')}`",
                        f"Chunks: `{meta.get('chunks', 0)}`",
                        f"Model: `{meta.get('model', 'N/A')}`",
                        f"Updated: `{meta.get('updated_at', 'N/A')}`",
                    ]
                if index_file.exists():
                    lines.append(f"Index size: `{index_file.stat().st_size / 1024**2:.2f} MB`")
                await bot.reply_to(message, "\n".join(lines), parse_mode='Markdown')
            except Exception as e:
                logger.error(f"on_rag_status error: {e}")

        @bot.message_handler(commands=['rag_profiles'])
        async def on_rag_profiles(message):
            if not self._is_allowed(message):
                return
            try:
                from src.rag.rag_profile_manager import rag_profile_manager
                profiles = rag_profile_manager.list_profiles()
                if not profiles:
                    await bot.reply_to(message, "⚠️ No RAG profiles found.")
                    return
                markup = types.InlineKeyboardMarkup()
                for p in profiles:
                    label = f"{'✅' if p['has_index'] else '⚪'} {p['name']}"
                    markup.add(types.InlineKeyboardButton(label, callback_data=f"rag_profile_{p['name']}"))
                await bot.reply_to(message, "📚 *RAG Profiles:*",
                                   reply_markup=markup, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"on_rag_profiles error: {e}")

        # ── Document upload (ZIP → RAG) ────────────────────────────────────

        @bot.message_handler(content_types=['document'])
        async def on_document(message):
            if not self._is_allowed(message):
                return
            doc = message.document
            if not (doc.mime_type == 'application/zip' or doc.file_name.endswith('.zip')):
                await bot.reply_to(message, "⚠️ Send a .zip archive to add to the RAG knowledge base.")
                return

            await bot.reply_to(message, "📥 Downloading and extracting archive...")
            upload_dir = Path("data/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_info = await bot.get_file(doc.file_id)
            data = await bot.download_file(file_info.file_path)
            zip_path = upload_dir / doc.file_name
            zip_path.write_bytes(data)

            extract_dir = upload_dir / zip_path.stem
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(extract_dir)
                zip_path.unlink()
                count = len(list(extract_dir.rglob('*')))
                await bot.send_message(message.chat.id, (
                    f"✅ *Archive extracted!*\n"
                    f"Path: `{extract_dir}`\n"
                    f"Files: `{count}`\n\n"
                    f"Run `/rag_rebuild` to index."
                ), parse_mode='Markdown')
            except Exception as e:
                await bot.reply_to(message, f"❌ Extraction error: {e}")


admin_bot = AdminBot()
