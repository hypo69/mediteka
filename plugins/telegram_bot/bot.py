## \file plugins/telegram_bot/bot.py
# -*- coding: utf-8 -*-
"""Telegram-бот плагин: text↔speech↔text через Gemini."""

import asyncio
import os
import tempfile
from functools import partial
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from plugins.plugin import BasePlugin
from src.utils.convertors.tts import speech_recognizer, text2speech
from src.logger.logger import logger

load_dotenv()
_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")


class TelegramBotPlugin(BasePlugin):
    name = "telegram_bot"
    title = "Telegram Бот"
    description = "Интеграция с Telegram: распознавание голосовых сообщений, синтез речи, чат и пульт управления"
    icon = "✈️"
    version = "2.0.0"
    category = "system"

    def __init__(self, ai_model):
        super().__init__(ai_model)
        self._app: Application | None = None
        self._plugins: dict = {}

    def get_manifest(self) -> dict:
        has_token = bool(_BOT_TOKEN)
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'version': self.version,
            'category': self.category,
            'enabled': self.enabled,
            'config': self.get_config(),
            'fields': [
                {
                    'id': 'bot_token_status',
                    'label': 'Статус Telegram токена',
                    'type': 'readonly',
                    'default': 'Установлен в .env' if has_token else 'Токен не задан (TELEGRAM_BOT_TOKEN)',
                    'description': 'Конфигурация токена бота в файле окружения .env'
                }
            ],
            'actions': []
        }

    def set_plugins(self, plugins: dict) -> None:
        """Передача всех загруженных плагинов для роутинга сообщений."""
        self._plugins = plugins

    def can_handle(self, message: str) -> bool:
        return False

    async def _handle(self, message: str) -> str | None:
        """Плагин не перехватывает веб-запросы — только Telegram."""
        return None

    async def _process_message(self, message: str, tg_user) -> str:
        """Обработка входящего сообщения через плагины (RAG, и т.д.) и модель ИИ."""
        settings, db_user = self._get_user_settings(tg_user)
        system_instruction = settings.get('system_instruction')
        selected_model = settings.get('model')

        # Идентификатор комнаты для медиаплеера:
        # Если привязан реальный аккаунт, то room_id равен email. Иначе anon_<telegram_id>.
        email = db_user.get('email', '')
        if email and not email.endswith('@telegram.bot'):
            room_id = email.strip().lower()
        else:
            room_id = f"anon_{tg_user.id}"

        user_identifier = db_user.get('id')

        # Извлечение API ключа для User RAG
        api_key = getattr(self.ai, 'api_key', '') or ''
        if not api_key:
            try:
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()
            except Exception:
                pass

        # Поиск контекста в User RAG
        user_context_str = ""
        
        # Проверяем, нужно ли игнорировать старый контекст для простых управляющих слов/продолжений
        skip_past_context = False
        clean_msg = message.strip().lower()
        if len(clean_msg) < 25:
            control_words = {
                'да', 'нет', 'yes', 'no', 'ок', 'ok', 'хочу', 'конечно',
                'давай', 'проверь', 'найди', 'покажи', 'ладно', 'угу', 'yep', 'sure',
                'want', 'check', 'find', 'show', 'okay', 'отлично',
                'включи', 'запусти', 'play', 'start', 'open', 'открой', 'включай', 'запускай',
                'поставь', 'вруби', 'воспроизведи', 'сейчас', 'now', 'go'
            }
            words = set(clean_msg.replace('!', ' ').replace('.', ' ').replace(',', ' ').split())
            if words & control_words:
                skip_past_context = True

        if api_key and user_identifier and len(message.strip()) >= 5 and not skip_past_context:
            try:
                from src.ai.gemini.user_query_rag import search_user_context
                past_context = search_user_context(user_identifier, api_key, message, top_k=2, threshold=0.45)
                if past_context:
                    snippets = [item['text'] for item in past_context]
                    user_context_str = "\n[Контекст из предыдущих обсуждений пользователя]:\n" + "\n---\n".join(snippets)
            except Exception:
                pass

        # Предпочтения пользователя
        try:
            from src.user_manager.user_profile import get_recommendation_context
            pref_context = get_recommendation_context(user_identifier)
            if pref_context:
                user_context_str = f"{user_context_str}\n\n[Профиль предпочтений пользователя]:\n{pref_context}".strip()
        except Exception:
            pass

        final_system_instruction = system_instruction or getattr(self.ai, 'system_instruction', None)
        
        # Динамическая коррекция рода ответа под голос (если мужской -> женский род, если женский -> мужской род)
        voice_gender_instruction = ""
        tts_voice = settings.get('tts_voice', '') or os.getenv("TTS_VOICE", "ru-RU-DmitryNeural")
        voice_lower = tts_voice.lower()
        is_male_voice = any(name in voice_lower for name in ("dmitry", "yaraslaus", "male", "bayan", "aidar", "eugene", "georgy"))
        is_female_voice = any(name in voice_lower for name in ("svetlana", "elena", "female", "kseniya", "tanya", "aliona", "dariya"))
        if is_male_voice:
            voice_gender_instruction = "IMPORTANT: Выбран мужской голос озвучки. Модель должна отвечать строго от женского лица (в женском роде, используя глаголы и местоимения женского рода: 'я пошла', 'я сделала' и т.д.)."
        elif is_female_voice:
            voice_gender_instruction = "IMPORTANT: Выбран женский голос озвучки. Модель должна отвечать строго от мужского лица (в мужском роде, используя глаголы и местоимения мужского рода: 'я пошел', 'я сделал' и т.д.)."

        if voice_gender_instruction:
            if final_system_instruction:
                final_system_instruction = f"{final_system_instruction}\n\n{voice_gender_instruction}"
            else:
                final_system_instruction = voice_gender_instruction

        if user_context_str:
            if final_system_instruction:
                final_system_instruction = f"{final_system_instruction}\n\n{user_context_str}"
            else:
                final_system_instruction = user_context_str

        # Подготовка kwargs для плагинов
        kwargs = {
            'system_instruction': final_system_instruction,
            'room_id': room_id,
        }
        if selected_model:
            kwargs['model_name'] = selected_model

        # Проверка, относится ли запрос к медиа
        is_media = False
        rag_plugin = self._plugins.get('rag')
        if rag_plugin and hasattr(rag_plugin, '_is_media_query'):
            if rag_plugin._is_media_query(message):
                is_media = True

        full_response_text = ""

        # Последовательный опрос плагинов (пропускаем сам telegram_bot)
        for plugin in self._plugins.values():
            if plugin.name == 'telegram_bot':
                continue
            if plugin.name == 'rag' and not is_media:
                continue
            if is_media and plugin.name != 'rag':
                continue

            response = await plugin.handle(message, **kwargs)
            import inspect
            if inspect.isasyncgen(response):
                async for chunk in response:
                    if isinstance(chunk, dict) and 'text' in chunk:
                        full_response_text += chunk['text']
                if full_response_text:
                    break
            elif response:
                full_response_text = str(response)
                break

        # Если плагин обработал запрос
        if full_response_text:
            if api_key and user_identifier:
                try:
                    from src.ai.gemini.user_query_rag import index_user_query
                    index_user_query(user_identifier, api_key, message, full_response_text)
                except Exception:
                    pass
            return full_response_text

        if is_media:
            return "Не удалось найти информацию в базе данных медиатеки"

        # Прямой вызов ИИ-модели без chat_data_folder
        answer = await self.ai.chat(
            message,
            system_instruction=final_system_instruction,
            model_name=selected_model
        )

        if answer and api_key and user_identifier:
            try:
                from src.ai.gemini.user_query_rag import index_user_query
                index_user_query(user_identifier, api_key, message, answer)
            except Exception:
                pass

        return answer or "Модель не ответила."

    async def start(self) -> None:
        if not _BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN не задан в .env", None, False)
            return

        self._app = Application.builder().token(_BOT_TOKEN).build()
        self._app.add_handler(MessageHandler(filters.VOICE, self._on_voice))
        self._app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_text))
        
        # Add start, cabinet, settings, link command handlers
        from telegram.ext import CommandHandler, CallbackQueryHandler
        self._app.add_handler(CommandHandler("start", self._on_start))
        self._app.add_handler(CommandHandler("cabinet", self._on_cabinet))
        self._app.add_handler(CommandHandler("profile", self._on_cabinet))
        self._app.add_handler(CommandHandler("settings", self._on_settings))
        self._app.add_handler(CommandHandler("link", self._on_link))
        self._app.add_handler(CommandHandler("clean", self._on_clean))
        self._app.add_handler(CallbackQueryHandler(self._on_callback_query))

        await self._app.initialize()
        await self._app.start()
        
        # Регистрация команд в меню Telegram
        try:
            from telegram import BotCommand
            commands = [
                BotCommand("start", "Запустить бота"),
                BotCommand("cabinet", "Личный кабинет (статус привязки)"),
                BotCommand("settings", "Настройки бота"),
                BotCommand("link", "Привязать веб-аккаунт: /link <КОД>"),
                BotCommand("clean", "Умная интерактивная очистка медиатеки")
            ]
            await self._app.bot.set_my_commands(commands)
            logger.info("Команды бота успешно зарегистрированы в меню", None, False)
        except Exception as e:
            logger.error("Ошибка регистрации команд меню бота:", e, False)

        await self._app.updater.start_polling(drop_pending_updates=True)
        logger.info("Telegram-бот запущен", None, False)

    async def stop(self) -> None:
        if self._app:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()

    def _get_user_settings(self, tg_user) -> tuple[dict, dict]:
        """Получение или создание профиля пользователя в БД и его настроек."""
        from src.user_manager import user_manager
        db_user = user_manager.get_user_by_telegram_id(tg_user.id)
        if not db_user:
            temp_email = f"tg_{tg_user.id}@telegram.bot"
            db_user = user_manager.get_user_by_email(temp_email)
            if not db_user:
                user_id = user_manager.add_user(
                    email=temp_email,
                    name=tg_user.first_name or tg_user.username or "Telegram User",
                    role="user"
                )
                user_manager.update_user(user_id, telegram_id=tg_user.id, telegram_username=tg_user.username)
                db_user = user_manager.get_user_by_id(user_id)
            else:
                user_manager.update_user(db_user['id'], telegram_id=tg_user.id, telegram_username=tg_user.username)
                db_user = user_manager.get_user_by_id(db_user['id'])
        
        settings = user_manager.get_user_settings(db_user['id'])
        return settings, db_user

    async def _on_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Голос → текст → модель → голос (если включено в настройках)."""
        voice = update.message.voice
        tmp_ogg = Path(tempfile.gettempdir()) / f"tg_voice_{voice.file_id}.ogg"

        tg_file = await context.bot.get_file(voice.file_id)
        await tg_file.download_to_drive(tmp_ogg)

        loop = asyncio.get_event_loop()
        recognized = await loop.run_in_executor(
            None, partial(speech_recognizer, audio_file_path=tmp_ogg)
        )

        if not recognized or recognized.startswith(("Error", "Sorry", "Could not")):
            await update.message.reply_text("Не удалось распознать речь.")
            return

        await update.message.reply_text(f"🎤 {recognized}")

        settings, _ = self._get_user_settings(update.effective_user)
        
        answer = await self._process_message(recognized, update.effective_user)
        await self._send_response_with_smart_playback(update, context, answer, settings)

    async def _send_response_with_smart_playback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, answer: str, settings: dict) -> None:
        if not answer:
            await update.message.reply_text("Модель не ответила.")
            return

        import re
        from urllib.parse import quote
        from src.fastapi.router_control import manager
        from plugins.media_organizer.core.database import MediaDatabase
        from plugins.media_organizer.core.media_organizer import DB_FILE

        tg_user = update.effective_user
        db_user = self._get_user_settings(tg_user)[1]
        
        # Resolve room_id
        email = db_user.get('email', '')
        if email and not email.endswith('@telegram.bot'):
            room_id = email.strip().lower()
        else:
            room_id = f"anon_{tg_user.id}"

        # Find any <film>...</film> tags
        film_matches = re.findall(r'<film>(.*?)</film>', answer, re.IGNORECASE)
        
        reply_markup = None
        
        if film_matches:
            # Check if player is active
            has_player = room_id in manager.rooms and len(manager.rooms[room_id].get("player", [])) > 0
            
            # Find matching file path in database
            first_film_title = film_matches[0].strip()
            db = MediaDatabase(DB_FILE)
            records = db.export_all()
            
            film_path = None
            title_lower = first_film_title.lower()
            
            # Сначала проверяем — не является ли сам title YouTube-ссылкой
            if first_film_title.startswith(('http://', 'https://', 'youtube.com', 'youtu.be')):
                film_path = first_film_title
            else:
                for record in records:
                    r_title = record.get('title', '').lower()
                    r_title_ru = (record.get('title_ru', '') or '').lower()
                    r_title_orig = (record.get('title_orig', '') or '').lower()

                    match = (
                        title_lower == r_title or
                        title_lower == r_title_ru or
                        title_lower == r_title_orig or
                        r_title.startswith(title_lower) or
                        (r_title_ru and r_title_ru.startswith(title_lower)) or
                        (r_title_orig and r_title_orig.startswith(title_lower))
                    )
                    if match and record.get('path'):
                        film_path = record.get('path')
                        break
                    
                    # Дополнительно: проверяем по содержимому path — вдруг это YouTube-запись
                    rec_path = record.get('path', '')
                    if rec_path and ('youtube.com' in rec_path or 'youtu.be' in rec_path):
                        if title_lower in r_title or title_lower in r_title_ru:
                            film_path = rec_path
                            break

            
            if has_player:
                if film_path:
                    asyncio.create_task(manager.broadcast_to_role(room_id, "player", {
                        "action": "play_file_by_path",
                        "path": film_path
                    }))
                    if "Запускаю воспроизведение" not in answer:
                        answer += f"\n\n🚀 Запускаю воспроизведение «{first_film_title}» на вашем плеере..."
            else:
                if film_path:
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    encoded_path = quote(film_path)
                    mini_app_url = f"https://kino.davidka.net/tgmini?file={encoded_path}"
                    
                    keyboard = [
                        [InlineKeyboardButton("📱 Смотреть в Telegram", web_app={"url": mini_app_url})]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Remove misleading automated play message from text
                    answer = re.sub(r'🚀\s*Запускаю\s*воспроизведение.*?(?:\r?\n|$)', '', answer, flags=re.IGNORECASE)
                    answer += f"\n\n⚠️ Плеер kino.davidka.net не запущен на другом устройстве. Вы можете запустить воспроизведение прямо в Telegram:"

        # Deliver response
        if settings.get('tts_enabled', 1) == 1:
            audio_path = await text2speech(answer)
            if audio_path and not audio_path.startswith("Error"):
                try:
                    with open(audio_path, "rb") as f:
                        await update.message.reply_voice(voice=f, caption=answer[:1024], reply_markup=reply_markup)
                    return
                except Exception as voice_err:
                    logger.warning(f"Failed to send TTS as voice: {voice_err}. Trying as audio...")
                    try:
                        with open(audio_path, "rb") as f:
                            await update.message.reply_audio(audio=f, caption=answer[:1024], reply_markup=reply_markup)
                        return
                    except Exception as audio_err:
                        logger.error(f"Failed to send TTS as audio: {audio_err}")

        await update.message.reply_text(answer, reply_markup=reply_markup)

    async def _on_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Текст → модель → текст."""
        text = update.message.text.strip()
        
        import re
        # Разрешаем "link DC84C10C", "/link DC84C10C", "link /DC84C10C", "DC84C10C" и т.д.
        token_match = re.match(r'^(?:/?link\s+)?/?([A-F0-9]{8})$', text, re.IGNORECASE)
        if token_match:
            token = token_match.group(1).upper()
            tg_user = update.effective_user
            from src.user_manager import user_manager
            success = user_manager.link_telegram_account(token, tg_user.id, tg_user.username or tg_user.first_name)
            if success:
                await update.message.reply_text("🎉 **Ваш Telegram-аккаунт успешно связан с веб-профилем!**")
            else:
                await update.message.reply_text("❌ **Ошибка привязки аккаунта!**\nКод недействителен, истек (10 минут) или уже использован.")
            return

        settings, _ = self._get_user_settings(update.effective_user)
        answer = await self._process_message(text, update.effective_user)
        await self._send_response_with_smart_playback(update, context, answer, settings)

    async def _on_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка команды /start."""
        start_message = (
            "Добро пожаловать в AI Assistant! 🤖\n\n"
            "Я могу помочь вам с:\n"
            "• Ответами на вопросы\n"
            "• Просмотром медиафайлов\n"
            "• Синтезом речи\n\n"
            "Используйте кнопку «Пульт ДУ» для запуска управления или задавайте вопросы напрямую боту. "
            "Например, «расскажи о сериале Острые козырьки» или «посоветуй фильм на вечер»."
        )
        
        await update.message.reply_text(start_message)

    async def _on_cabinet(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Отображение данных личного кабинета пользователя."""
        from src.user_manager import user_manager
        tg_user = update.effective_user
        db_user = user_manager.get_user_by_telegram_id(tg_user.id)
        
        if not db_user or db_user.get('email', '').endswith('@telegram.bot'):
            msg = (
                "❌ **Ваш аккаунт Telegram не привязан к Google аккаунту!**\n\n"
                "Чтобы привязать аккаунт:\n"
                "1. Войдите через Google на веб-сайте.\n"
                "2. Перейдите в раздел **Кабинет**.\n"
                "3. Сгенерируйте код привязки.\n"
                "4. Отправьте боту команду: `/link <КОД>`"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
            return
            
        msg = (
            "🗂 **Ваш Личный Кабинет**\n\n"
            f"👤 **Имя**: {db_user.get('name')}\n"
            f"✉️ **Email**: {db_user.get('email')}\n"
            f"🔑 **Роль**: {db_user.get('role')}\n"
            f"📅 **Дата регистрации**: {db_user.get('created_at')}\n\n"
            "🔗 Аккаунт успешно связан с Telegram!"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def _on_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Связывание аккаунтов по сгенерированному на сайте токену."""
        if not context.args:
            await update.message.reply_text("Использование: `/link <код_из_личного_кабинета>`")
            return
            
        token = context.args[0]
        tg_user = update.effective_user
        
        from src.user_manager import user_manager
        # Если старый временный аккаунт существовал, мы можем его перетереть при связывании
        success = user_manager.link_telegram_account(token, tg_user.id, tg_user.username or tg_user.first_name)
        if success:
            await update.message.reply_text("🎉 **Ваш Telegram-аккаунт успешно связан с веб-профилем!**")
        else:
            await update.message.reply_text("❌ **Ошибка привязки аккаунта!**\nКод недействителен, истек (10 минут) или уже использован.")

    async def _on_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показ интерактивного меню настроек в Telegram-боте."""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        settings, _ = self._get_user_settings(update.effective_user)
        
        tts_status = "Вкл 🔊" if settings.get('tts_enabled', 1) == 1 else "Выкл 🔇"
        lang_status = settings.get('language', 'ru').upper()
        
        keyboard = [
            [InlineKeyboardButton(f"Озвучка ответов (TTS): {tts_status}", callback_data="toggle_tts")],
            [InlineKeyboardButton(f"Язык общения: {lang_status}", callback_data="toggle_lang")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚙️ **Настройки бота**", reply_markup=reply_markup, parse_mode="Markdown")

    async def _on_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка нажатий на инлайн-кнопки настроек."""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        query = update.callback_query
        await query.answer()
        
        tg_user = query.from_user
        settings, db_user = self._get_user_settings(tg_user)
        
        from src.user_manager import user_manager
        
        if query.data == "toggle_tts":
            new_tts = 0 if settings.get('tts_enabled', 1) == 1 else 1
            user_manager.update_user_settings(db_user['id'], tts_enabled=new_tts)
        elif query.data == "toggle_lang":
            new_lang = "en" if settings.get('language', 'ru') == "ru" else "ru"
            user_manager.update_user_settings(db_user['id'], language=new_lang)
            
        elif query.data.startswith("del_media_"):
            if db_user.get("role") != "admin":
                await query.answer("❌ Доступ запрещен (требуются права администратора)", show_alert=True)
                return
            title = query.data.replace("del_media_", "")
            from plugins.media_organizer.core.interactive_retention_agent import InteractiveRetentionAgent
            agent = InteractiveRetentionAgent()
            success, freed = agent.delete_candidate(title, dry_run=False)
            if success:
                await query.edit_message_text(f"✅ **{title}** успешно очищен с диска (освобождено {freed // 1_048_576} MB).\nФайлы переведены в состояние 'не загружать' в qBittorrent.")
            else:
                await query.edit_message_text(f"❌ Ошибка очистки **{title}**.")
            return
        elif query.data == "cancel_cleanup":
            await query.edit_message_text("Очистка отменена.")
            return
            
        # Заново получаем измененные настройки
        settings = user_manager.get_user_settings(db_user['id'])
        tts_status = "Вкл 🔊" if settings.get('tts_enabled', 1) == 1 else "Выкл 🔇"
        lang_status = settings.get('language', 'ru').upper()
        
        keyboard = [
            [InlineKeyboardButton(f"Озвучка ответов (TTS): {tts_status}", callback_data="toggle_tts")],
            [InlineKeyboardButton(f"Язык общения: {lang_status}", callback_data="toggle_lang")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)

    async def _on_clean(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Интерактивный опрос пользователя для очистки дискового пространства."""
        settings, db_user = self._get_user_settings(update.effective_user)
        if db_user.get("role") != "admin":
            await update.message.reply_text("❌ **Эта функция доступна только администраторам.**")
            return
            
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from plugins.media_organizer.core.interactive_retention_agent import InteractiveRetentionAgent
        
        agent = InteractiveRetentionAgent()
        candidates = agent.get_cleanup_candidates()
        
        if not candidates:
            await update.message.reply_text("💿 **Свободного места достаточно или старые сериалы не найдены.**")
            return
            
        msg = "📦 **Интерактивная очистка медиатеки**\n\nНиже представлены сериалы и фильмы, которые можно очистить с диска (их легко можно скачать повторно из торрентов):\n\n"
        keyboard = []
        
        for c in candidates:
            title = c["title"]
            size = c["size_mb"]
            reason = c["reason"]
            msg += f"• **{title}** — {size} MB ({reason})\n"
            keyboard.append([InlineKeyboardButton(f"🗑️ Удалить {title}", callback_data=f"del_media_{title}")])
            
        keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="cancel_cleanup")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
