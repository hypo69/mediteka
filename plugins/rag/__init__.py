# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Плагин RAG (Семантический поиск по медиатеке и базе знаний)
# =============================================================================
# Описание:
#   Обеспечивает интеллектуальный поиск фильмов/сериалов и технической документации.
#   Поддерживает:
#   - Рулетку/карусель случайного выбора тайтла
#   - Direct Play (запуск на плеере без LLM)
#   - Direct RAG (мгновенный возврат карточки из БД)
#   - Полнотекстовый/векторный поиск с суммаризацией через LLM
#   - Поиск по технической документации для разработчиков
#
# File: plugins/rag/__init__.py
# Project: gemini-simplechat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from typing import AsyncGenerator

from header import __root__
from plugins.media_organizer.core import MEDIA_DB
from plugins.media_organizer.core.media_rag_functions import (
    get_media_card,
    get_player_tools,
    make_play_dispatcher,
)
from plugins.plugin import BasePlugin
from src.logger import logger

_DEV_KEYWORDS = (
    "код", "функци", "класс", "модул", "скрипт", "ошибк", "баг",
    "architecture", "code", "dev", "doc", "fastapi", "router", "rag",
    "как работает", "где лежит", "почему не", "разработк", "индекс",
)

_MEDIA_KEYWORDS = (
    # Медиа-термины
    "фильм", "сериал", "кино", "мультфильм", "мульт", "мультик", "анимация",
    "кинематограф", "кинолента", "тайтл", "эпизод", "серия", "сезон",
    "трейлер", "тизер", "постер", "актер", "актриса", "режиссер", "в ролях",
    "сиквел", "приквел", "франшиза", "сага", "трилогия", "movie", "series",
    "cinema", "film", "episode", "season", "actor", "director", "cast",
    # Жанры и категории (рус/англ)
    "боевик", "боевики", "action",
    "комедия", "комедии", "комеди", "comedy",
    "триллер", "триллеры", "thriller",
    "драма", "драмы", "drama",
    "ужасы", "хоррор", "ужастик", "horror",
    "фантастика", "фантастик", "sci-fi",
    "фэнтези", "fantasy",
    "детектив", "детективы", "detective", "расследовани",
    "приключения", "adventure",
    "мелодрама", "мелодрамы", "romance",
    "криминал", "криминальн", "crime",
    "вестерн", "вестерны", "western",
    "семейный", "семейные", "family",
    "мистика", "мистическ", "mystery",
    "военный", "военные", "war",
    "исторический", "исторические", "история", "history",
    "документальный", "документальные", "документальн", "documentary",
    "мюзикл", "мюзиклы", "musical",
    "шпион", "шпионы", "шпионск", "spy",
    "биография", "биографическ", "bio",
    "спорт", "спортивн", "sport",
    "киберпанк", "cyberpunk",
    "аниме", "anime",
    # Рекомендации и действия
    "посоветуй", "порекомендуй", "подскажи", "порекомендуйте", "посоветуйте",
    "что посмотреть", "что глянуть", "посмотри", "посмотреть", "глянуть",
    "покажи", "найди", "список", "подборка", "подборку", "подбери", "подборки",
    "включи", "включай", "запусти", "запускай", "воспроизведи", "поставь",
    "play", "watch", "start", "open",
    "карусель", "случайн", "рандом",
    "новинки", "премьеры", "топ", "рейтинг",
)

_PLAY_KEYWORDS = (
    "включи", "включай", "запусти", "запускай", "воспроизведи",
    "поставь", "play", "watch", "start", "open",
)


class RAGPlugin(BasePlugin):
    """Плагин семантического поиска и воспроизведения медиаконтента."""

    name: str = "rag"

    def _is_media_query(self, message: str) -> bool:
        """Проверяет, относится ли запрос к медиатеке."""
        if not message:
            return False
        low = message.strip().lower()
        if any(kw in low for kw in _MEDIA_KEYWORDS):
            return True
        if len(low) >= 3 and MEDIA_DB.exists():
            try:
                with sqlite3.connect(MEDIA_DB) as conn:
                    row = conn.execute(
                        "SELECT 1 FROM media WHERE LOWER(title) = ? OR LOWER(title_ru) = ? OR LOWER(title_orig) = ? LIMIT 1",
                        (low, low, low)
                    ).fetchone()
                    if row:
                        return True
            except Exception:
                pass
        return False

    def _is_dev_query(self, message: str) -> bool:
        """Проверяет, относится ли запрос к технической документации/коду."""
        low = message.lower()
        return any(kw in low for kw in _DEV_KEYWORDS)

    def can_handle(self, message: str) -> bool:
        """Проверяет, может ли RAG плагин обработать входящее сообщение."""
        return self._is_media_query(message) or self._is_dev_query(message)

    async def _handle_carousel(self, kwargs: dict) -> AsyncGenerator[dict, None]:
        """Обрабатывает выбор случайного фильма (карусель)."""
        from src.fastapi.router_control import manager
        yield {"status": "🎡 Выбор случайного фильма через карусель..."}

        with sqlite3.connect(MEDIA_DB) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT title, title_ru, year, main_category, disk_name, plot, path FROM media "
                "WHERE (media_type = 'movie' OR media_type IS NULL OR media_type = '') "
                "  AND (title IS NOT NULL AND title != '') "
                "ORDER BY RANDOM() LIMIT 1"
            ).fetchone()

            if not row:
                row = conn.execute(
                    "SELECT title, title_ru, year, main_category, disk_name, plot, path FROM media "
                    "WHERE title IS NOT NULL AND title != '' "
                    "ORDER BY RANDOM() LIMIT 1"
                ).fetchone()

        if not row:
            yield {"text": "❌ Ошибка: База данных медиатеки пуста."}
            yield {"prompt_dump": "[Ошибка]: База данных пуста"}
            yield {"voice": "База данных медиатеки пуста."}
            return

        title = row['title']
        title_ru = row['title_ru']
        year = row['year']
        main_category = row['main_category']
        plot = row['plot']
        path = row['path']
        disk_name = row['disk_name']

        room_id = kwargs.get('room_id', 'default')
        has_player = room_id in manager.rooms and len(manager.rooms[room_id].get("player", [])) > 0

        if path and has_player:
            asyncio.create_task(manager.broadcast_to_role(room_id, "player", {
                "action": "play_file_by_path",
                "path": path
            }))

        status_msg = "🚀 Запускаю воспроизведение на плеере..." if has_player else "📱 Вы можете запустить воспроизведение локально или открыть стрим."

        response_text = (
            f"🎡 **Карусель выбрала случайный фильм!**\n\n"
            f"🎬 **Название:** <film>{title_ru or title}</film>\n"
            f"📅 **Год:** {year or 'Неизвестно'}\n"
            f"📂 **Категория:** {main_category or 'Без категории'}\n"
            f"💿 **Диск:** {disk_name or 'Неизвестно'}\n\n"
            f"📝 **Описание:** {plot or 'Нет описания.'}\n\n"
            f"{status_msg}"
        )

        yield {"prompt_dump": f"[Карусель]: {title_ru or title}"}
        yield {"text": response_text}
        yield {"voice": f"Я выбрала фильм {title_ru or title}. {status_msg}"}

    async def _handle_direct_play(self, best_item: dict, kwargs: dict) -> AsyncGenerator[dict, None]:
        """Прямой запуск фильма на плеере без обращения к LLM."""
        base_title = best_item.get('clean_title', best_item.get('title', ''))
        room_id = kwargs.get('room_id', '')

        file_path = ''
        stream_url = ''
        display_title = base_title
        try:
            with sqlite3.connect(MEDIA_DB) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT path, stream_url, title_ru, title FROM media "
                    "WHERE (LOWER(title) LIKE ? OR LOWER(title_ru) LIKE ?) "
                    "ORDER BY ROWID ASC LIMIT 1",
                    (f"%{base_title.lower()}%", f"%{base_title.lower()}%")
                ).fetchone()
                if row:
                    file_path = row['path'] or ''
                    stream_url = row['stream_url'] or ''
                    display_title = row['title_ru'] or row['title'] or base_title
                    if file_path.startswith(('http://', 'https://')):
                        stream_url = stream_url or file_path
                        file_path = ''
        except Exception as ex:
            logger.error(f"[RAGPlugin] Ошибка поиска пути: {ex}")

        from src.fastapi.router_control import manager
        has_player = room_id in manager.rooms and len(manager.rooms[room_id].get("player", [])) > 0

        if file_path and has_player:
            asyncio.create_task(manager.broadcast_to_role(room_id, "player", {
                "action": "play_file_by_path",
                "path": file_path
            }))
            response_text = f"🚀 Запускаю <film>{display_title}</film> на плеере..."
        elif stream_url and has_player:
            asyncio.create_task(manager.broadcast_to_role(room_id, "player", {
                "action": "play_url",
                "url": stream_url
            }))
            response_text = f"🌐 Открываю <film>{display_title}</film> онлайн..."
        elif stream_url:
            response_text = f"🌐 <film>{display_title}</film> доступен онлайн: {stream_url}"
        elif file_path:
            response_text = f"📱 Нашла <film>{display_title}</film>. Плеер не подключён — запустите вручную."
        else:
            response_text = f"❌ Не удалось найти «{base_title}» на дисках или онлайн."

        yield {"prompt_dump": f"[DIRECT PLAY — без LLM]\nНазвание: {display_title}\nФайл: {file_path or '—'}\nОнлайн: {stream_url or '—'}"}
        yield {"text": response_text}
        yield {"voice": response_text}

    async def _handle_direct_rag(self, best_item: dict) -> AsyncGenerator[dict, None]:
        """Прямой возврат карточки медиа из БД без вызова LLM."""
        raw_text = best_item.get('text', '')
        base_title = best_item.get('clean_title', best_item.get('title', ''))

        try:
            m_type = best_item.get('media_type') or best_item.get('type', 'series')
            card_json = get_media_card(best_item.get('disk_name', ''), base_title, m_type)
            card_data = json.loads(card_json)
            if not card_data.get('error') and (card_data.get('title') or card_data.get('title_ru')):
                yield {"status": f"⚡ Карточка медиа ({base_title})..."}
                yield {"prompt_dump": "[DIRECT RAG — без вызова LLM]\nОтправка JSON-карточки фильма."}
                yield {"text": card_json}
                yield {"voice": card_data.get('plot') or card_data.get('why_watch') or base_title}
                return
        except Exception as ex:
            logger.error(f"[RAGPlugin] Ошибка при парсинге карточки: {ex}")

        if raw_text:
            yield {"status": f"⚡ Ответ из локальной базы ({base_title})..."}
            yield {"prompt_dump": f"[DIRECT RAG — без вызова LLM]\nДокумент: {base_title}\n\n{raw_text[:300]}..."}
            fallback_text = f"🎬 **{base_title}**\n\n{raw_text}"
            yield {"text": fallback_text}
            yield {"voice": raw_text}

    async def _handle_llm_rag(self, message: str, results: list[dict], kwargs: dict) -> AsyncGenerator[dict, None]:
        """Генерация ответа ИИ с учетом данных RAG-поиска."""
        yield {"status": "🤖 Генерация ответа ИИ с учетом данных RAG..."}

        context_parts = []
        for idx, item in enumerate(results, 1):
            base_title = item.get('title', '').split(':')[0].replace('.txt', '').strip()
            m_type = item.get('media_type') or item.get('type', 'series')
            card_json = get_media_card(item.get('disk_name', ''), base_title, m_type)
            item_ctx = f"--- Документ {idx}: {item.get('title')} ---"
            try:
                card_data = json.loads(card_json)
                plot_desc = card_data.get('plot') or card_data.get('why_watch')
                if plot_desc:
                    item_ctx += f"\nОписание из базы: {plot_desc}"
            except Exception:
                pass
            if item.get('text'):
                item_ctx += f"\nСодержимое документа:\n{item.get('text')}"
            context_parts.append(item_ctx)

        # Если фильм не найден локально в RAG, запускаем поиск через активный плагин веб-поиска
        if not results:
            try:
                from plugins.web_search import WebSearchPlugin
                web_plugin = WebSearchPlugin(self.ai)
                engine = web_plugin._get_engine()
                yield {"status": f"🌐 Поиск информации в интернете ({engine})..."}

                web_text = ""
                if engine == "gemini":
                    web_text = await web_plugin.gemini_searcher.search_and_extract(message)
                elif engine == "agy":
                    web_text = await web_plugin.agy_searcher.search_and_extract(message)
                elif engine == "langchain":
                    from src.ai.langchain_agent import MediaSearchAgent
                    from header import __root__
                    agent = MediaSearchAgent(config_path=__root__ / "config.json")
                    search_res = await agent.search(message)
                    web_text = json.dumps(search_res, ensure_ascii=False, indent=2)
                else:
                    web_text = await web_plugin.playwright_searcher.search_and_extract(message)

                if web_text:
                    context_parts.append(f"--- Результаты веб-поиска ({engine}) ---\n{web_text}")
            except Exception as e:
                logger.warning(f"[RAGPlugin] Не удалось выполнить веб-поиск: {e}")

        context_str = "\n\n".join(context_parts)
        system_prompt = (
            "Ты — AI Assistant домашней медиатеки kino.davidka.net.\n"
            "1. Если фильм/сериал найден в локальной медиатеке, расскажи о нём на основе найденных данных и ОБЯЗАТЕЛЬНО укажи, что он есть в медиатеке.\n"
            "2. Если пользователь запрашивает подборку, категорию, жанр или рекомендации (например, 'боевики', 'комедии', 'что посмотреть'), представь список найденных фильмов/сериалов из локальной медиатеки с кратким описанием каждого и обязательно оберни каждое название в тег <film>Название</film>.\n"
            "3. Для сериалов ВСЕГДА представляй информацию на уровне ВСЕГО СЕРИАЛА (концепция, общий сюжет, количество сезонов, ключевые персонажи/актеры). Не своди ответ к отдельному сезону или эпизоду, даже если совпадение найдено по событиям конкретного сезона, за исключением случаев, когда пользователь сам явно спросил про конкретный сезон или серию.\n"
            "4. Если фильм/сериал отсутствует на локальных дисках, подробно расскажи о запрашиваемом тайтле на основе своих знаний или данных из интернета, "
            "и ОБЯЗАТЕЛЬНО оберни название фильма/сериала в тег <film>Название</film>, чтобы интерфейс предложил пользователю варианты загрузки или поиска.\n"
            "5. Отвечай ТОЛЬКО по сути вопроса пользователя на русском языке.\n\n"
            "Если пользователь просит включить/запустить/воспроизвести фильм или сериал:\n"
            "1) Если есть инструмент play_media(title) — используй его НЕМЕДЛЕННО.\n"
            "2) Если инструмента нет, ОБЯЗАТЕЛЬНО оберни название в тег <film>Название</film>.\n"
        )
        if context_str:
            system_prompt += f"\nРезультаты поиска в локальной медиатеке:\n{context_str}"
        else:
            system_prompt += "\nВ локальной медиатеке по данному запросу ничего не найдено."

        dynamic_context = kwargs.get('dynamic_context', '')
        if dynamic_context:
            system_prompt += f"\n\n--- Дополнительный контекст ---\n{dynamic_context}"

        room_id = kwargs.get('room_id', '')
        player_tools = get_player_tools()
        dispatcher = make_play_dispatcher(room_id)

        try:
            yield {"prompt_dump": system_prompt}
            yield {"status": "🎬 Выполняю команду..."}
            full_text = ""

            try:
                async for chunk in self.ai.ask_with_tools_stream(
                    message,
                    tools=player_tools,
                    tool_dispatcher=dispatcher,
                    system_instruction=system_prompt,
                    history=kwargs.get("history", []),
                    model_name=kwargs.get('model_name'),
                ):
                    if "text" in chunk and chunk["text"]:
                        full_text += chunk["text"]
                        yield {"text": chunk["text"]}
                    elif "status" in chunk and chunk["status"]:
                        yield {"status": chunk["status"]}
            except (NotImplementedError, AttributeError):
                async for chunk in self.ai.chat_stream(
                    message,
                    system_instruction=system_prompt,
                    history=kwargs.get("history", []),
                    model_name=kwargs.get('model_name'),
                ):
                    c = chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                    if c:
                        full_text += c
                        yield {"text": c}

            if not full_text:
                yield {"text": "Команда выполнена", "voice": "Команда выполнена"}
            else:
                yield {"voice": full_text}
        except Exception as e:
            logger.error(f"Ошибка при вызове ИИ в RAG-плагине: {e}")
            yield {"text": f"❌ Ошибка: {str(e)}"}

    async def _handle(self, message: str, **kwargs) -> AsyncGenerator[dict, None]:
        """Главный диспетчер обработки запроса."""
        low_message = message.lower()

        # 1. Медиа-поиск
        if self._is_media_query(message):
            if any(k in low_message for k in ("карусель", "случайн", "рандом")):
                async for chunk in self._handle_carousel(kwargs):
                    yield chunk
                return

            config_path = __root__ / 'config.json'
            rag_mode = "rag+model"
            try:
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                        rag_mode = cfg.get("rag", {}).get("mode", "rag+model")
            except Exception:
                pass

            results = []
            if rag_mode != "model":
                yield {"status": "🔍 Поиск в локальном RAG-индексе..."}
                try:
                    from plugins.media_organizer.core.media_rag_functions import search_media
                    results_json = search_media(message)
                except Exception as ex:
                    logger.error(f"[RAGPlugin] Ошибка вызова search_media: {ex}")
                    results_json = json.dumps({"results": []})
                results_data = json.loads(results_json)
                if "error" in results_data:
                    err_text = f"❌ Ошибка поиска: {results_data['error']}"
                    yield {"text": err_text, "prompt_dump": f"[Ошибка]: {err_text}", "voice": "Произошла ошибка при поиске"}
                    return
                results = results_data.get("results", [])
            else:
                yield {"status": "🤖 RAG отключён, переход к модели..."}

            unique_results = []
            seen_titles = set()
            for item in results:
                raw_title = item.get('title', '')
                base_title = raw_title.split(':')[0].replace('.txt', '').strip()
                if base_title.lower() not in seen_titles:
                    seen_titles.add(base_title.lower())
                    item['clean_title'] = base_title
                    unique_results.append(item)

            is_play_command = any(kw in low_message for kw in _PLAY_KEYWORDS)

            if is_play_command and unique_results:
                async for chunk in self._handle_direct_play(unique_results[0], kwargs):
                    yield chunk
                return

            # В режиме 'rag' (только локальная база) выдаем карточку или сообщение об отсутствии
            if rag_mode == "rag":
                if unique_results:
                    handled = False
                    async for chunk in self._handle_direct_rag(unique_results[0]):
                        handled = True
                        yield chunk
                    if handled:
                        return
                yield {
                    "status": "⚡ Ответ в локальной базе не найден.",
                    "text": f"❌ В локальной базе ничего не найдено по запросу «{message}».",
                    "prompt_dump": f"[DIRECT RAG]\nПо запросу «{message}» ничего не найдено.",
                    "voice": "В локальной базе ничего не найдено."
                }
                return

            # В режиме 'rag+model' и 'model' генерируем ответ через LLM с локальным контекстом
            async for chunk in self._handle_llm_rag(message, results, kwargs):
                yield chunk
            return

        # 2. Технический (dev) поиск
        if self._is_dev_query(message):
            yield {"status": "🛠️ Поиск по техническому контексту..."}
            from src.ai.dev_rag import rag_search_tool
            api_key = os.getenv('GEMINI_API_KEY', '')
            results_json = rag_search_tool(message, api_key=api_key)

            yield {"status": "🤖 Генерация технического ответа..."}
            system_prompt = (
                f"Ты — технический ассистент разработчика медиатеки. Ответь на вопрос пользователя, используя "
                f"результаты поиска по коду и технической документации проекта.\n\n"
                f"Найденные фрагменты кода и документации:\n{results_json}"
            )
            answer = await self.ai.chat(
                message,
                system_instruction=system_prompt,
                model_name=kwargs.get('model_name')
            )
            yield {"text": answer}
            return


plugin = RAGPlugin