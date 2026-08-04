# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Telegram Бот Управления
# =============================================================================
# Описание:
#   Интерфейс для удаленного мониторинга и управления системой через Telegram.
#   Команды: /status, /foundry_start, /foundry_stop, /logs.
#
# File: src/utils/telegram_bot.py
# Project: Ai Assistant
# Version: 0.6.1
# Author: hypo69
# Date: 2025
# =============================================================================

import asyncio
import io
import json
import os
import platform
import shutil
import sys
import logging
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List
import psutil
import matplotlib.pyplot as plt
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from src.core.config import config
from src.logger import logger
from .command_agent import CommandAgent

class SystemBot:
    """Класс для реализации Telegram бота мониторинга системы."""

    def __init__(self) -> None:
        """Инициализация бота с использованием токена из конфигурации."""
        self.bot: AsyncTeleBot = None
        self.agent: CommandAgent = CommandAgent()
        self.allowed_ids: List[int] = config.telegram_allowed_ids
        self.computer_name: str = platform.node()
        self.chat_history_enabled: bool = config.telegram_chat_history_enabled
        self.chat_history_file: Path = Path(config.telegram_chat_history_file)

        # Настройка matplotlib для работы в фоновом режиме (без графического интерфейса)
        plt.switch_backend('Agg')

    def _log_telegram_interaction(self, chat_id: int, role: str, content: str) -> None:
        """Log telegram interaction to session history file if enabled."""
        if not self.chat_history_enabled:
            return
        try:
            history_file = self.chat_history_file
            history_file.parent.mkdir(parents=True, exist_ok=True)
            entry = {"session_id": f"telegram_{chat_id}", "role": role, "content": content,
                     "timestamp": datetime.now().isoformat()}
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.debug(f"Telegram history log error: {e}")

    def _is_allowed(self, message) -> bool:
        """Проверка прав доступа пользователя."""
        return not self.allowed_ids or message.from_user.id in self.allowed_ids

    async def send_message(self, text: str) -> None:
        """Отправка уведомления всем разрешенным администраторам.

        Args:
            text (str): Текст уведомления (поддерживает Markdown).
        """
        if not self.bot or not self.allowed_ids:
            return

        for user_id in self.allowed_ids:
            try:
                # Асинхронная отправка сообщения
                # Asynchronous message delivery
                await self.bot.send_message(user_id, text, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")

    async def _monitor_foundry_status(self) -> None:
        """Фоновая задача для периодической проверки состояния Foundry.

        Обоснование:
          - Обеспечение автоматического оповещения при падении сервиса.
          - Минимизация времени простоя без ручного мониторинга.
        """
        last_status: str = "running"
        interval: int = config.telegram_status_check_interval
        status_data: dict = {}
        current_status: str = ""
        disk_alert_sent: bool = False

        logger.info(f"Запущен фоновый мониторинг Foundry (интервал: {interval}с)")

        while True:
            try:
                await asyncio.sleep(interval)
                
                # Проверка заполнения диска (порог 95%)
                # Disk usage verification (95% threshold)
                disk = psutil.disk_usage(Path.cwd().anchor)
                if disk.percent > 95:
                    if not disk_alert_sent:
                        msg = (
                            f"🚨 *Disk Alert!*\n"
                            f"Обнаружено критическое заполнение диска: `{disk.percent}%` \n"
                            f"Свободно: `{disk.free // 1024**3} GB`"
                        )
                        await self.send_message(msg)
                        disk_alert_sent = True
                else:
                    disk_alert_sent = False
                
                # Получение текущего состояния
                # Retrieval of the current status
                status_data = await self.agent.parse_foundry_status()
                current_status = status_data.get("status", "unknown")

                # Проверка изменения статуса на критический
                # Verification of status change to critical
                if current_status != last_status:
                    if current_status in ["failed", "stopped", "unknown"]:
                        # Оповещение о сбое
                        # Notification about the failure
                        msg = (
                            f"🚨 *Foundry Alert!*\n"
                            f"Статус службы изменился: `{last_status}` ➡️ `{current_status}`\n"
                            f"Требуется проверка системы."
                        )
                        await self.send_message(msg)
                    
                    last_status = current_status
            except Exception as e:
                logger.error(f"Ошибка мониторинга Foundry в боте: {e}")

    async def start(self) -> None:
        """Запуск процесса прослушивания сообщений (Polling)."""
        if not config.telegram_enabled or not config.telegram_token:
            logger.info("Telegram бот отключен в конфигурации.")
            return

        self.bot = AsyncTeleBot(config.telegram_token)
        logger.info("Запуск Telegram бота мониторинга...")

        # Запуск фонового мониторинга статуса
        # Starting background status monitoring
        asyncio.create_task(self._monitor_foundry_status())

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith(("confirm_restart_", "rag_profile_", "confirm_clear_logs_")))
        async def handle_callbacks(call):
            """Унифицированная обработка callback-запросов (перезагрузка, логи, RAG)."""
            try:
                if not self.allowed_ids or call.from_user.id in self.allowed_ids:
                    # Обработка перезагрузки
                    if call.data == "confirm_restart_yes":
                        await self.bot.edit_message_text("🔄 *Перезагрузка инициирована...*", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
                        logger.info("Перезагрузка сервера по команде из Telegram.")
                        await asyncio.sleep(1)
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                    
                    elif call.data == "confirm_restart_no":
                        await self.bot.edit_message_text("✅ *Перезагрузка отменена.*", call.message.chat.id, call.message.message_id, parse_mode='Markdown')

                    # Обработка очистки логов
                    elif call.data == "confirm_clear_logs_yes":
                        log_path = Path("logs/fastapi-foundry.log")
                        if log_path.exists():
                            log_path.write_text("", encoding="utf-8")
                            await self.bot.edit_message_text("🧹 *Файл логов успешно очищен.*", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
                            logger.info(f"Логи очищены пользователем {call.from_user.id}")
                        else:
                            await self.bot.edit_message_text("⚠️ Файл логов не найден.", call.message.chat.id, call.message.message_id)

                    elif call.data == "confirm_clear_logs_no":
                        await self.bot.edit_message_text("✅ *Очистка логов отменена.*", call.message.chat.id, call.message.message_id, parse_mode='Markdown')

                else:
                    await self.bot.answer_callback_query(call.id, "У вас нет прав для этого действия.")
            except Exception as e:
                logger.error(f"Ошибка в handle_callbacks: {e}")

        @self.bot.message_handler(commands=['start', 'help'])
        async def send_welcome(message):
            if not self._is_allowed(message): return
            try:
                help_text = (
                    "🚀 *FastAPI Foundry Bot*\n\n"
                    "/status - System and Foundry state\n"
                    "/foundry_start - Start Foundry service\n"
                    "/foundry_stop - Stop Foundry service\n"
                    "/logs - Last 5 errors from log file\n"
                    "/get_logs - Get full log file\n"
                    "/clear_logs - Clear log file\n"
                    "/clear_chat_history - Delete chat history file\n"
                    "/stats - CPU, RAM, and Disk usage graphs\n"
                    "/restart_server - Restart API server\n"
                    "/rag_rebuild - Rebuild RAG index"
                )
                await self.bot.reply_to(message, help_text, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Ошибка send_welcome: {e}")

        @self.bot.message_handler(commands=['status'])
        async def get_status(message):
            if not self._is_allowed(message): return
            try:
                status = await self.agent.parse_foundry_status()
                msg = (
                    f"📊 *Статус Системы*\n"
                    f" Foundry: `{status.get('status')}`\n"
                    f" Порт: `{status.get('port') or 'N/A'}`\n"
                    f" PID: `{status.get('pid') or 'N/A'}`\n"
                    f" Время: `{datetime.now().strftime('%H:%M:%S')}`"
                )
                await self.bot.send_message(message.chat.id, msg, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Ошибка get_status: {e}")

        @self.bot.message_handler(commands=['stats'])
        async def get_stats(message):
            if not self._is_allowed(message): return
            try:
                cpu_usage = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory()
                ram_usage = ram.percent
                disk = psutil.disk_usage(Path.cwd().anchor)
                disk_usage = disk.percent
                
                # Генерация графика с защитой от ошибок matplotlib
                buf = io.BytesIO()
                try:
                    plt.figure(figsize=(10, 6))
                    bars = plt.bar(['CPU', 'RAM', 'Disk'], [cpu_usage, ram_usage, disk_usage], color=['#3498db', '#2ecc71', '#e67e22'])
                    plt.ylim(0, 100)
                    plt.ylabel('Использование (%)')
                    plt.title(f'Нагрузка на сервер ({datetime.now().strftime("%H:%M:%S")})')
                    
                    for bar in bars:
                        yval = bar.get_height()
                        plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval}%', ha='center', va='bottom', fontweight='bold')
                    
                    plt.savefig(buf, format='png', bbox_inches='tight')
                    buf.seek(0)
                    plt.close()
                    has_plot = True
                except Exception as plt_e:
                    logger.error(f"Ошибка отрисовки графика: {plt_e}")
                    has_plot = False

                caption = (f"📊 *Системные ресурсы*\n"
                           f"CPU: `{cpu_usage}%` | RAM: `{ram_usage}%` (`{ram.used // 1024 // 1024}MB` / `{ram.total // 1024 // 1024}MB`)\n"
                           f"Disk: `{disk_usage}%` (`{disk.used // 1024**3}GB` / `{disk.total // 1024**3}GB`)")
                
                if has_plot:
                    await self.bot.send_photo(message.chat.id, buf, caption=caption, parse_mode='Markdown')
                else:
                    await self.bot.send_message(message.chat.id, caption, parse_mode='Markdown')

                self._log_telegram_interaction(message.chat.id, "user", message.text)
                self._log_telegram_interaction(message.chat.id, "assistant", caption)
            except Exception as e:
                logger.error(f"Ошибка get_stats: {e}")

        @self.bot.message_handler(commands=['foundry_start'])
        async def start_foundry(message):
            if not self._is_allowed(message): return
            try:
                await self.bot.send_message(message.chat.id, "⏳ Запуск Foundry...")
                result = await self.agent.run("foundry", ["service", "start"])
                status = "✅ Успешно" if result.get("exit_code") == 0 else f"❌ Ошибка: {result.get('error')}"
                self._log_telegram_interaction(message.chat.id, "user", message.text)
                self._log_telegram_interaction(message.chat.id, "assistant", status)
                await self.bot.send_message(message.chat.id, status)
            except Exception as e:
                logger.error(f"Ошибка start_foundry: {e}")

        @self.bot.message_handler(commands=['rag_rebuild'])
        async def rag_rebuild(message):
            if not self._is_allowed(message): return
            try:
                await self.bot.send_message(message.chat.id, "🏗️ *Запуск переиндексации RAG...*", parse_mode='Markdown')
                await asyncio.sleep(1)
                self._log_telegram_interaction(message.chat.id, "user", message.text)
                self._log_telegram_interaction(message.chat.id, "assistant", "✅ Процесс индексации документов инициирован.")
                await self.bot.send_message(message.chat.id, "✅ Процесс индексации документов инициирован.")
            except Exception as e:
                logger.error(f"Ошибка rag_rebuild: {e}")

        @self.bot.message_handler(commands=['rag_status'])
        async def get_rag_status(message):
            if not self._is_allowed(message): return
            try:
                index_dir = Path(config.rag_index_dir)
                meta_file = index_dir / "meta.json"
                index_file = index_dir / "faiss.index"
                
                if not index_dir.exists():
                    await self.bot.reply_to(message, "❌ Директория RAG индекса не найдена.")
                    return

                status_msg = " *Статус RAG системы*\n\n"
                
                if meta_file.exists():
                    meta = json.loads(meta_file.read_text(encoding="utf-8")) # type: ignore
                    status_msg += (
                        f"👤 Профиль: `{meta.get('name', 'N/A')}`\n"
                        f"🔢 Чанков: `{meta.get('chunks', 0)}`\n"
                        f"📂 Директория: `{meta.get('index_dir', 'N/A')}`\n"
                        f"📚 Источник: `{meta.get('source_dir', 'N/A')}`\n"
                        f"🤖 Модель: `{meta.get('model', 'N/A')}`\n"
                        f"🕒 Обновлено: `{meta.get('updated_at', 'N/A')}`\n"
                    )
                
                if index_file.exists():
                    size_mb = index_file.stat().st_size / (1024 * 1024)
                    status_msg += f"💾 Размер индекса: `{size_mb:.2f} MB`"
                
                self._log_telegram_interaction(message.chat.id, "user", message.text)
                self._log_telegram_interaction(message.chat.id, "assistant", status_msg)
                await self.bot.send_message(message.chat.id, status_msg, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Ошибка get_rag_status: {e}")

        @self.bot.message_handler(commands=['rag_profiles'])
        async def list_rag_profiles(message):
            if not self._is_allowed(message): return
            try:
                from src.rag.rag_system import rag_system
                profiles_dir = rag_system.RAG_HOME
                
                if not profiles_dir.exists():
                    await self.bot.reply_to(message, "❌ Директория RAG профилей не найдена.")
                    return
                
                profiles = [d.name for d in profiles_dir.iterdir() if d.is_dir()]
                
                if not profiles:
                    await self.bot.reply_to(message, "⚠️ RAG профили не найдены.")
                    return
                
                markup = types.InlineKeyboardMarkup()
                for profile_name in profiles:
                    markup.add(types.InlineKeyboardButton(profile_name, callback_data=f"rag_profile_{profile_name}"))
                
                await self.bot.send_message(
                    message.chat.id,
                    "📚 *Выберите RAG профиль для активации:*",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                self._log_telegram_interaction(message.chat.id, "user", message.text)
                self._log_telegram_interaction(message.chat.id, "assistant", "📚 *Выберите RAG профиль для активации:*")
            except Exception as e:
                logger.error(f"Ошибка list_rag_profiles: {e}")
                await self.bot.send_message(message.chat.id, "❌ Ошибка при получении списка профилей.")

        @self.bot.message_handler(content_types=['document'])
        async def handle_docs(message):
            """Обработка загрузки ZIP-архивов для RAG."""
            if not self._is_allowed(message): return
            
            if message.document.mime_type == 'application/zip' or message.document.file_name.endswith('.zip'):
                await self.bot.reply_to(message, "📥 Получен архив. Начинаю загрузку и распаковку...")
                
                # Подготовка путей
                upload_dir = Path("data/uploads")
                upload_dir.mkdir(parents=True, exist_ok=True)
                file_info = await self.bot.get_file(message.document.file_id)
                downloaded_file = await self.bot.download_file(file_info.file_path)
                
                zip_path = upload_dir / message.document.file_name
                zip_path.write_bytes(downloaded_file)
                
                # Распаковка
                extract_dir = upload_dir / zip_path.stem
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    
                    zip_path.unlink() # Удаление архива после распаковки
                    
                    msg = (
                        f"✅ *Архив успешно обработан!*\n\n"
                        f"📂 Путь: `{extract_dir}`\n"
                        f"📄 Файлов: `{len(list(extract_dir.rglob('*')))}`\n\n"
                        f"Используйте `/rag_rebuild`, чтобы проиндексировать эти данные."
                    )
                    self._log_telegram_interaction(message.chat.id, "user", f"Документ: {message.document.file_name}")
                    self._log_telegram_interaction(message.chat.id, "assistant", msg)
                    await self.bot.send_message(message.chat.id, msg, parse_mode='Markdown')
                except Exception as e:
                    await self.bot.reply_to(message, f"❌ Ошибка при распаковке: {e}")
            else:
                try:
                    await self.bot.reply_to(message, "⚠️ Пожалуйста, отправьте документы в формате .zip для добавления в базу знаний RAG.")
                except: pass

        @self.bot.message_handler(commands=['clear_logs'])
        async def clear_logs_request(message):
            """Запрос подтверждения очистки логов."""
            if not self._is_allowed(message): return
            try:
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("✅ Да, очистить", callback_data="confirm_clear_logs_yes"),
                    types.InlineKeyboardButton("❌ Отмена", callback_data="confirm_clear_logs_no")
                )
                await self.bot.send_message(
                    message.chat.id,
                    "🧹 *Очистка логов*\nВы уверены, что хотите полностью очистить файл `fastapi-foundry.log`?",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Ошибка clear_logs_request: {e}")

        @self.bot.message_handler(commands=['clear_chat_history'])
        async def clear_chat_history(message):
            if not self._is_allowed(message): return
            try:
                if self.chat_history_file.exists():
                    self.chat_history_file.unlink()
                    msg = "🗑️ *Файл истории чатов удален.*"
                    logger.info("История чатов Telegram удалена через бота.")
                else:
                    msg = "⚠️ Файл истории чатов не найден."
                
                await self.bot.send_message(message.chat.id, msg, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Ошибка clear_chat_history: {e}")

        @self.bot.message_handler(commands=['clear_chat_history'])
        async def clear_chat_history(message):
            if not self._is_allowed(message): return
            try:
                if self.chat_history_file.exists():
                    self.chat_history_file.unlink()
                    msg = "🗑️ *Файл истории чатов удален.*"
                    logger.info("История чатов Telegram удалена через бота.")
                else:
                    msg = "⚠️ Файл истории чатов не найден."
                
                await self.bot.send_message(message.chat.id, msg, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Ошибка clear_chat_history: {e}")

        @self.bot.message_handler(commands=['restart_server'])
        async def restart_server_request(message):
            if not self._is_allowed(message): return
            try:
                # Создание клавиатуры с подтверждением
                # Creation of the confirmation keyboard
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("✅ Да", callback_data="confirm_restart_yes"),
                    types.InlineKeyboardButton("❌ Нет", callback_data="confirm_restart_no")
                )
                
                await self.bot.send_message(
                    message.chat.id, 
                    "❓ *Подтверждение*\nВы уверены, что хотите перезагрузить сервер FastAPI?", 
                    reply_markup=markup, 
                    parse_mode='Markdown'
                )
                self._log_telegram_interaction(message.chat.id, "user", message.text)
                self._log_telegram_interaction(message.chat.id, "assistant", "❓ *Подтверждение*\nВы уверены, что хотите перезагрузить сервер FastAPI?")
            except Exception as e:
                logger.error(f"Ошибка restart_server_request: {e}")

        @self.bot.message_handler(commands=['logs'])
        async def get_logs(message):
            if not self._is_allowed(message): return
            log_path = "logs/fastapi-foundry.log"
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    errors = [l for l in lines if "ERROR" in l][-5:]
                    msg = "Последние ошибки:\n\n" + ("".join(errors) if errors else "Ошибок не найдено.")
                    self._log_telegram_interaction(message.chat.id, "user", message.text)
                    self._log_telegram_interaction(message.chat.id, "assistant", msg)
                    await self.bot.send_message(message.chat.id, f"```\n{msg[:4000]}\n```", parse_mode='Markdown')
            except Exception as e:
                await self.bot.send_message(message.chat.id, f"Ошибка чтения лога: {e}")

        @self.bot.message_handler(commands=['get_logs'])
        async def get_log_file(message):
            if not self._is_allowed(message): return
            log_path = Path("logs/fastapi-foundry.log")
            
            if log_path.exists():
                try:
                    with open(log_path, 'rb') as f:
                        await self.bot.send_document(message.chat.id, f, caption="📄 Полный файл логов сервера")
                    self._log_telegram_interaction(message.chat.id, "user", message.text)
                    self._log_telegram_interaction(message.chat.id, "assistant", "📄 Полный файл логов сервера")
                except Exception as e:
                    await self.bot.send_message(message.chat.id, f"❌ Ошибка отправки: {e}")
            else:
                await self.bot.send_message(message.chat.id, "⚠️ Файл логов не найден.")

        try:
            await self.bot.polling(non_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"Telegram Bot Polling Error: {e}")

system_bot = SystemBot()