# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Плагин RAG (Семантический поиск по медиатеке и базе знаний)
# =============================================================================
# Описание:
#   Обеспечивает интеллектуальный поиск фильмов/сериалов и технической документации.
#   Поддерживает:
#   - Рулетку/карусель случайного выбора тайтла
#   - Direct Play (запуск на плеере без LLM)
#   - Direct RAG (мгновенный возврат карточки из БД без вызова LLM)
#   - Direct Multi-item RAG (мгновенный возврат структурированного списка тайтлов из БД без LLM)
#   - Fallback через веб-поиск и LLM при отсутствии тайтла в локальной медиатеке
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
from typing import AsyncIterator, List, Dict, Any

from header import __root__
from plugins.media_organizer.core import MEDIA_DB
from plugins.media_organizer.core.media_rag_functions import (
    get_media_card,
    get_player_tools,
    make_play_dispatcher,
)
from plugins.plugin import BasePlugin
from src.logger.logger import logger

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



_GENERIC_STOP_WORDS = {
    "расскажи", "расскажите", "расскажи-ка", "покажи", "покажите", "найди", "найдите",
    "посоветуй", "посоветуйте", "порекомендуй", "порекомендуйте", "подскажи", "подскажите",
    "что", "как", "где", "когда", "кто", "чем", "почему", "зачем", "за", "про", "просто",
    "о", "об", "обо", "в", "во", "на", "с", "со", "из", "к", "ко", "по", "для", "от", "до",
    "фильм", "фильмы", "фильма", "фильме", "фильму", "фильмом", "фильмах", "фильмов",
    "кино", "кинолента", "кинокартина", "картина", "картину", "тайтл", "тайтлы", "видео",
    "сериал", "сериалы", "сериала", "сериале", "сериалу", "сериалом", "сериалах", "сериалов",
    "мультфильм", "мультфильмы", "мульт", "мультик", "мультики", "мультсериал", "аниме",
    "сезон", "сезоны", "сезона", "сезоне", "серия", "серии", "серий", "эпизод", "эпизоды",
    "сюжет", "описание", "информация", "информацию", "содержание", "смысл", "суть",
    "актер", "актеры", "актриса", "актрисы", "роль", "ролях", "режиссер", "режиссера",
    "онлайн", "смотреть", "посмотреть", "глянуть", "включи", "включай", "запусти", "запускай",
    "поставь", "скачать", "трейлер", "отзыв", "отзывы", "рейтинг", "топ", "новинка", "новинки",
    "хороший", "хорошие", "лучший", "лучшие", "интересный", "интересные", "какой", "какие",
    "пожалуйста", "плиз", "привет", "здравствуй", "здравствуйте",
    "the", "a", "an", "movie", "movies", "film", "films", "series", "show", "shows",
    "about", "tell", "me", "watch", "find", "search", "play", "info", "plot",
}

_GENRE_AND_DISCOVERY_WORDS = {
    "боевик", "боевики", "action",
    "комедия", "комедии", "комеди", "comedy",
    "триллер", "триллеры", "thriller",
    "драма", "драмы", "drama",
    "ужасы", "хоррор", "ужастик", "ужастики", "horror",
    "фантастика", "фантастик", "sci-fi",
    "фэнтези", "fantasy",
    "детектив", "детективы", "detective", "расследование", "расследования",
    "приключения", "adventure", "adventures",
    "мелодрама", "мелодрамы", "romance",
    "криминал", "криминальное", "crime",
    "вестерн", "вестерны", "western",
    "семейный", "семейные", "family",
    "мистика", "mystery",
    "военный", "военные", "war",
    "исторический", "исторические", "история", "history",
    "документальный", "документальные", "documentary",
    "мюзикл", "мюзиклы", "musical",
    "шпион", "шпионы", "шпионские", "spy",
    "биография", "биографические", "bio",
    "спорт", "спортивные", "sport",
    "киберпанк", "cyberpunk",
    "аниме", "anime",
    "посоветуй", "порекомендуй", "подскажи", "посоветуйте", "порекомендуйте",
    "подборка", "подборку", "подборки", "список", "топ", "лучшие", "новинки", "премьеры",
    "что посмотреть", "что глянуть", "посмотреть", "глянуть", "хороший", "хорошие",
}


def _extract_specific_title_keywords(query: str) -> list[str]:
    """Извлекает ключевые слова названия фильма/сериала для адресных запросов."""
    import re
    # 1. Если есть кавычки — берем содержимое внутри кавычек
    quoted = re.findall(r'["«»\'](.*?)["«»\']', query)
    if quoted:
        q_text = " ".join(quoted).strip()
        words = [w.lower() for w in re.findall(r'[a-zA-Zа-яА-Я0-9]+', q_text) if len(w) >= 2]
        meaningful_quoted = [w for w in words if w not in _GENERIC_STOP_WORDS]
        if meaningful_quoted:
            return meaningful_quoted

    # 2. Иначе очищаем от стоп-слов и жанровых категорий
    all_words = [w.lower() for w in re.findall(r'[a-zA-Zа-яА-Я0-9]+', query) if len(w) >= 2]
    meaningful = [w for w in all_words if w not in _GENERIC_STOP_WORDS]

    # Если все оставшиеся слова — это жанры/категории/подборки, то это не адресный запрос
    if not meaningful or all(w in _GENRE_AND_DISCOVERY_WORDS for w in meaningful):
        return []

    return [w for w in meaningful if w not in _GENRE_AND_DISCOVERY_WORDS]


def _is_item_title_match(item: dict, title_keywords: list[str]) -> bool:
    """Проверяет, совпадает ли хотя бы одно ключевое слово названия с документом."""
    if not title_keywords:
        return True

    searchable_texts = []
    meta = item.get('meta', {})
    for key in ('title', 'clean_title', 'title_ru', 'title_orig'):
        val = item.get(key) or meta.get(key)
        if val:
            searchable_texts.append(str(val).lower())

    raw_text = item.get('text', '')
    if raw_text:
        first_line = raw_text.split('\n')[0].strip().lower()
        searchable_texts.append(first_line)

    combined_text = " ".join(searchable_texts)

    for kw in title_keywords:
        kw_clean = kw.strip().lower()
        if len(kw_clean) < 3:
            if kw_clean in combined_text.split():
                return True
        else:
            stem = kw_clean[:max(3, len(kw_clean) - 1)]
            if stem in combined_text:
                return True
    return False


def _format_count_word(count: int) -> str:
    """Формирует текстовое числительное для количества вариантов."""
    _words = {
        1: "один вариант",
        2: "два варианта",
        3: "три варианта",
        4: "четыре варианта",
        5: "пять вариантов",
        6: "шесть вариантов",
        7: "семь вариантов",
        8: "восемь вариантов",
        9: "девять вариантов",
        10: "десять вариантов",
    }
    return _words.get(count, f"{count} вариантов")


def _format_voice_for_narrator(text: str) -> str:
    """Формирует естественный, благозвучный текст для озвучивания диктором без разметки."""
    if not text:
        return ""
    import re
    # 1. Извлечение названий из тегов <film>
    clean = re.sub(r'<film>(.*?)</film>', r'«\1»', text, flags=re.IGNORECASE)
    # 2. Очистка Markdown разметки
    clean = re.sub(r'#+\s*', '', clean)
    clean = re.sub(r'\*\*(.*?)\*\*', r'\1', clean)
    clean = re.sub(r'\*(.*?)\*', r'\1', clean)
    clean = re.sub(r'__([^_]+)__', r'\1', clean)
    clean = re.sub(r'_([^_]+)_', r'\1', clean)
    clean = re.sub(r'`([^`]+)`', r'\1', clean)
    clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
    # 3. Удаление эмодзи и спецзначков
    clean = re.sub(r'[🎬📂👤📝💡✨💬📱❌🔍🌐🤖🛠️🎡📡⏳⬆️⬇️💾📥▶️⚡—–]+', ' ', clean)
    # 4. Преобразование заголовков секций в связный текст
    clean = re.sub(r'(?:Жанр|Режиссёр|В главных ролях|В ролях|Сюжет|Почему стоит посмотреть|Основные сведения):\s*', '', clean)
    # 5. Нормализация пробелов
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Ограничение длины речи диктора (до 350-400 символов) для комфортного восприятия на слух
    if len(clean) > 380:
        sentences = [s.strip() for s in clean.split('.') if s.strip()]
        short_parts = []
        cur_len = 0
        for s in sentences:
            if cur_len + len(s) + 2 <= 320:
                short_parts.append(s)
                cur_len += len(s) + 2
            else:
                break
        if short_parts:
            clean = ". ".join(short_parts) + "."
        else:
            clean = clean[:320].rsplit(' ', 1)[0] + "."

        if not clean.endswith('?'):
            clean += " Включить этот фильм или рассказать подробнее?"

    return clean


class RAGPlugin(BasePlugin):
    """Плагин семантического поиска и воспроизведения медиаконтента."""

    name: str = "rag"
    title: str = "RAG Семантический поиск"
    description: str = "Семантический векторный поиск по локальной медиатеке, прямой Direct-RAG запуск и интеграция с базой знаний"
    icon: str = "🧠"
    version: str = "2.1.0"
    category: str = "ai"

    def get_manifest(self) -> dict:
        cfg = self.get_config()
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'version': self.version,
            'category': self.category,
            'enabled': self.enabled,
            'config': cfg,
            'fields': [
                {
                    'id': 'mode',
                    'label': 'Режим работы RAG',
                    'type': 'select',
                    'default': cfg.get('mode', 'rag+model'),
                    'options': [
                        {'value': 'rag+model', 'label': 'RAG + Модель (гибридный)'},
                        {'value': 'rag', 'label': 'Direct RAG (только локальная БД)'},
                        {'value': 'model', 'label': 'Direct Model (только ИИ без RAG)'}
                    ],
                    'description': 'Стратегия обработки пользовательских запросов'
                }
            ],
            'actions': [
                {
                    'id': 'rebuild_index',
                    'label': '🔄 Перестроить индекс',
                    'description': 'Пересоздание эмбеддингов локальной медиатеки',
                    'color': 'primary'
                },
                {
                    'id': 'status',
                    'label': '📊 Проверить статус',
                    'description': 'Получить статус готовности и размер RAG-индекса',
                    'color': 'info'
                }
            ]
        }

    async def action_rebuild_index(self, params: dict) -> dict:
        """Перестройка RAG-индекса."""
        try:
            from plugins.media_organizer.core.media_rag_functions import rebuild_rag_index
            res = rebuild_rag_index()
            return {'success': True, 'result': res, 'message': 'Перестройка RAG-индекса запущена'}
        except Exception as ex:
            return {'success': False, 'message': f'Ошибка перестройки RAG: {ex}'}

    async def action_status(self, params: dict) -> dict:
        """Проверка статуса RAG."""
        try:
            from plugins.media_organizer.core.media_rag_functions import get_rag_status
            res = get_rag_status()
            return {'success': True, 'result': res, 'message': 'Статус RAG получен'}
        except Exception as ex:
            return {'success': False, 'message': f'Ошибка получения статуса: {ex}'}

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
                    conn.create_function("py_lower", 1, lambda s: s.lower() if s else "")
                    row = conn.execute(
                        "SELECT 1 FROM media WHERE py_lower(title) LIKE ? OR py_lower(title_ru) LIKE ? OR py_lower(title_orig) LIKE ? LIMIT 1",
                        (f"%{low}%", f"%{low}%", f"%{low}%")
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

    async def _handle_carousel(self, kwargs: dict) -> AsyncIterator[dict]:
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
        voice_status = "Запускаю воспроизведение на плеере." if has_player else "Включить воспроизведение, рассказать подробнее или выбрать другой фильм?"

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
        yield {"voice": f"Карусель выбрала фильм {title_ru or title}. {voice_status}"}

    async def _handle_direct_play(self, best_item: dict, kwargs: dict) -> AsyncIterator[dict]:
        """Прямой запуск фильма на плеере без обращения к LLM."""
        base_title = best_item.get('clean_title', best_item.get('title', ''))
        room_id = kwargs.get('room_id', '')

        file_path = ''
        stream_url = ''
        display_title = base_title
        try:
            with sqlite3.connect(MEDIA_DB) as conn:
                conn.row_factory = sqlite3.Row
                conn.create_function("py_lower", 1, lambda s: s.lower() if s else "")
                row = conn.execute(
                    "SELECT path, stream_url, title_ru, title FROM media "
                    "WHERE (py_lower(title) LIKE ? OR py_lower(title_ru) LIKE ?) "
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
            response_text = f"📱 Найдено: <film>{display_title}</film>. Плеер не подключён — запустите вручную."
        else:
            response_text = f"❌ Не удалось найти «{base_title}» на дисках или онлайн."

        yield {"prompt_dump": f"[DIRECT PLAY — без LLM]\nНазвание: {display_title}\nФайл: {file_path or '—'}\nОнлайн: {stream_url or '—'}"}
        yield {"text": response_text}
        yield {"voice": response_text}

    async def _handle_direct_rag(self, best_item: dict) -> AsyncIterator[dict]:
        """Прямой возврат карточки медиа из БД без вызова LLM."""
        raw_text = best_item.get('text', '')
        base_title = best_item.get('clean_title', best_item.get('title', ''))

        try:
            m_type = best_item.get('media_type') or best_item.get('type', 'series')
            card_json = get_media_card(best_item.get('disk_name', ''), base_title, m_type)
            card_data = json.loads(card_json)
            if not card_data.get('error') and (card_data.get('title') or card_data.get('title_ru')):
                display_title = card_data.get('title_ru') or card_data.get('title') or base_title
                orig_title = card_data.get('title_orig', '')
                year = card_data.get('year', '')
                country = card_data.get('country', '')
                genres_list = card_data.get('genres') or []
                genres_str = ", ".join(genres_list) if genres_list else (card_data.get('main_category') or '')
                directors_list = card_data.get('directors') or []
                directors_str = ", ".join(directors_list)
                cast_list = card_data.get('cast') or []
                cast_str = ", ".join(cast_list[:5])
                plot_desc = card_data.get('plot') or card_data.get('why_watch') or ""
                why_watch = card_data.get('why_watch', '')

                # Построение структурированного Markdown описания
                md_header = f"🎬 **<film>{display_title}</film>**"
                meta_chips = []
                if orig_title and orig_title.strip().lower() != display_title.strip().lower():
                    meta_chips.append(f"*{orig_title}*")
                if year:
                    meta_chips.append(f"{year} г.")
                if country:
                    meta_chips.append(country)
                if meta_chips:
                    md_header += f" ({', '.join(meta_chips)})"

                md_body = []
                if genres_str:
                    md_body.append(f"📂 **Жанр:** {genres_str}")
                if directors_str:
                    md_body.append(f"🎬 **Режиссёр:** {directors_str}")
                if cast_str:
                    md_body.append(f"👤 **В главных ролях:** {cast_str}")
                if plot_desc:
                    md_body.append(f"\n📝 **Сюжет:**\n{plot_desc}")
                if why_watch and why_watch.strip() != plot_desc.strip():
                    md_body.append(f"\n💡 **Почему стоит посмотреть:**\n{why_watch}")

                full_md_text = md_header + "\n" + "\n".join(md_body)

                yield {"status": f"⚡ Карточка медиа ({display_title})..."}
                yield {"prompt_dump": f"[DIRECT RAG — без вызова LLM]\nКарточка: {display_title}"}
                yield {"text": full_md_text}

                primary_genre = genres_list[0].strip().lower() if genres_list else ""
                actors_part = ""
                if cast_list:
                    if len(cast_list) >= 2:
                        actors_part = f"в главных ролях {cast_list[0]} и {cast_list[1]}"
                    else:
                        actors_part = f"в главной роли {cast_list[0]}"

                first_sent = ""
                if plot_desc:
                    first_sent = plot_desc.split('.')[0].strip()
                    if len(first_sent) > 150:
                        first_sent = first_sent[:147] + "..."

                desc_parts = [f"Найден фильм {display_title}"]
                if primary_genre:
                    desc_parts.append(primary_genre)
                if actors_part:
                    desc_parts.append(actors_part)

                summary = " — ".join(desc_parts[:2])
                if len(desc_parts) > 2:
                    summary += f", {desc_parts[2]}"

                if first_sent:
                    summary += f". {first_sent}"

                cta = "Включить этот фильм, рассказать о нём подробнее или поискать другой?"
                voice_text = f"{summary}. {cta}"
                yield {"voice": voice_text}
                return
        except Exception as ex:
            logger.error(f"[RAGPlugin] Ошибка при парсинге карточки: {ex}")

        if raw_text:
            clean_heading = base_title
            if raw_text.startswith('#'):
                first_line = raw_text.split('\n')[0].lstrip('#').strip()
                if first_line:
                    clean_heading = first_line

            yield {"status": f"⚡ Ответ из локальной базы ({clean_heading})..."}
            yield {"prompt_dump": f"[DIRECT RAG — без вызова LLM]\nДокумент: {clean_heading}"}
            fallback_text = f"🎬 **<film>{clean_heading}</film>**\n\n{raw_text}"
            yield {"text": fallback_text}
            clean_raw = raw_text.split('.')[0].strip()[:200]
            cta = "Включить этот фильм, рассказать подробнее или поискать другой?"
            yield {"voice": f"В локальной медиатеке найден {clean_heading}. {clean_raw}. {cta}"}

    async def _handle_direct_multi_items(self, message: str, items: list[dict], kwargs: dict) -> AsyncIterator[dict]:
        """Прямой возврат структурированного списка найденных фильмов/сериалов из БД без вызова LLM."""
        dynamic_ctx = kwargs.get('dynamic_context', '')
        is_male = "мужского лица" in dynamic_ctx
        found_word = "нашел" if is_male else "нашла"

        yield {"status": f"⚡ Формирование списка из локальной медиатеки ({len(items)} тайтлов)..."}

        formatted_items = []
        voice_item_summaries = []
        seen_display_titles = set()

        for item in items:
            base_title = item.get('clean_title', item.get('title', ''))
            m_type = item.get('media_type') or item.get('type', 'series')
            disk_name = item.get('disk_name', '')

            card_data = {}
            try:
                card_json = get_media_card(disk_name, base_title, m_type)
                card_data = json.loads(card_json)
            except Exception as ex:
                logger.warning(f"[RAGPlugin] Не удалось получить карточку для {base_title}: {ex}")

            display_title = card_data.get('title_ru') or card_data.get('title') or base_title
            norm_title = display_title.strip().lower()
            if norm_title in seen_display_titles:
                continue
            seen_display_titles.add(norm_title)

            orig_title = card_data.get('title_orig', '')
            year = card_data.get('year') or item.get('year', '')

            genres_list = card_data.get('genres') or []
            genres_str = ", ".join(genres_list) if genres_list else (card_data.get('main_category') or item.get('category', ''))
            primary_genre = genres_list[0].strip().lower() if genres_list else ""

            cast_list = card_data.get('cast') or []
            cast_str = ", ".join(cast_list[:4]) if cast_list else ""

            plot = card_data.get('plot') or card_data.get('why_watch') or item.get('text', '')
            if len(plot) > 250:
                plot = plot[:247] + "..."

            idx = len(formatted_items) + 1
            if idx <= 5:
                item_header = f"{idx}. 🎬 **<film>{display_title}</film>**"
                meta_chips = []
                if orig_title and orig_title.strip().lower() != display_title.strip().lower():
                    meta_chips.append(f"*{orig_title}*")
                if year:
                    meta_chips.append(f"{year} г.")
                if genres_str:
                    meta_chips.append(f"📂 {genres_str}")
                if meta_chips:
                    item_header += f" ({', '.join(meta_chips)})"

                item_body = []
                if cast_str:
                    item_body.append(f"   👤 **В ролях:** {cast_str}")
                if plot:
                    item_body.append(f"   📝 {plot}")

                formatted_items.append(item_header + ("\n" + "\n".join(item_body) if item_body else ""))

            if len(voice_item_summaries) < 3:
                actors_part = ""
                if cast_list:
                    if len(cast_list) >= 2:
                        actors_part = f"в главных ролях {cast_list[0]} и {cast_list[1]}"
                    else:
                        actors_part = f"в главной роли {cast_list[0]}"

                if primary_genre and actors_part:
                    voice_summary = f"{display_title} — {primary_genre}, {actors_part}."
                elif actors_part:
                    voice_summary = f"{display_title}, {actors_part}."
                elif primary_genre:
                    voice_summary = f"{display_title} — {primary_genre}."
                else:
                    plot_snippet = card_data.get('why_watch') or card_data.get('plot') or ""
                    if plot_snippet:
                        first_sent = plot_snippet.split('.')[0].strip()
                        if len(first_sent) > 80:
                            first_sent = first_sent[:77] + "..."
                        voice_summary = f"{display_title} — {first_sent}."
                    else:
                        voice_summary = f"{display_title}."
                voice_item_summaries.append(voice_summary)

        full_text = f"🎬 **Я {found_word} в локальной медиатеке:**\n\n" + "\n\n".join(formatted_items)

        count_str = _format_count_word(len(formatted_items))
        intro = f"Я {found_word} в локальной медиатеке {count_str}."
        items_speech = " ".join(voice_item_summaries)
        cta = "Какой фильм включить, рассказать подробнее или поискать другой вариант?"
        voice_text = f"{intro} {items_speech} {cta}".strip()

        yield {"prompt_dump": f"[DIRECT RAG — без вызова LLM]\nНайдено {len(formatted_items)} тайтлов по запросу «{message}»."}
        yield {"text": full_text}
        yield {"voice": voice_text}

    async def _handle_llm_rag(self, message: str, results: list[dict], kwargs: dict) -> AsyncIterator[dict]:
        """Генерация ответа ИИ при отсутствии результатов в локальной медиатеке."""
        yield {"status": "🤖 Поиск информации и генерация ответа ИИ..."}

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
                elif engine == "gemini_cli":
                    web_text = await web_plugin.gemini_cli_searcher.search_and_extract(message)
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
            "Ты — AI Assistant домашней медиатеки kino.davidka.net. Отвечай от женского лица (например: 'Я нашла', 'Я подобрала').\n\n"
            "СТАНДАРТЫ ОФОРМЛЕНИЯ:\n"
            "1. При описании одного фильма или сериала используй чёткую структуру:\n"
            "🎬 **<film>Название на русском</film>** *(Original Title, Год, Страна)*\n"
            "📂 **Жанр:** жанры\n"
            "🎬 **Режиссёр:** имя\n"
            "👤 **В главных ролях:** ключевые актёры\n\n"
            "📝 **Сюжет:**\nКраткая завязка и интрига без спойлеров (2-3 предложения).\n\n"
            "💡 **Почему стоит посмотреть:**\nГлавные достоинства (атмосфера, актёрская игра, награды).\n\n"
            "💬 *Включить этот фильм, рассказать подробнее или поискать другой вариант?*\n\n"
            "2. При запросе подборки / рекомендаций (например, 'боевики', 'комедии', 'что посмотреть'):\n"
            "🎬 **Я подобрала для вас отличные фильмы:**\n\n"
            "1. 🎬 **<film>Название 1</film>** *(Год, Жанр)* — краткая завязка (1-2 предложения).\n"
            "2. 🎬 **<film>Название 2</film>** *(Год, Жанр)* — краткая завязка (1-2 предложения).\n\n"
            "💬 *Какой фильм включить или о каком рассказать подробнее?*\n\n"
            "3. Для сериалов ВСЕГДА представляй информацию на уровне ВСЕГО СЕРИАЛА (концепция, сюжет, количество сезонов, ключевые персонажи), не сводя к одной серии.\n"
            "4. Если фильм есть в локальной медиатеке — обязательно укажи это. Если нет на дисках — подробно расскажи на основе знаний/интернета и обязательно оберни название в <film>Название</film>.\n"
            "5. При запросе включить/запустить — вызови инструмент play_media(title) или напиши 'Запускаю <film>Название</film>...'.\n"
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
            yield {"status": "🎬 Генерация ответа..."}
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
                fallback_msg = f"❌ Не удалось получить ответ от ассистента по запросу «{message}»."
                yield {"text": fallback_msg, "voice": "Не удалось получить ответ."}
            else:
                clean_voice = _format_voice_for_narrator(full_text)
                yield {"voice": clean_voice}
        except Exception as e:
            logger.error(f"Ошибка при вызове ИИ в RAG-плагине: {e}")
            yield {"text": f"❌ Ошибка: {str(e)}"}

    async def _handle(self, message: str, **kwargs) -> AsyncIterator[dict]:
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

            # Проверка адресности запроса (поиск конкретного тайтла)
            title_keywords = _extract_specific_title_keywords(message)
            if title_keywords and unique_results:
                matched_results = [item for item in unique_results if _is_item_title_match(item, title_keywords)]
                if not matched_results:
                    logger.info(f"[RAGPlugin] Адресный запрос '{message}' (ключи: {title_keywords}) не совпал с локальными результатами. Переход к веб-поиску/LLM.")
                    unique_results = []
                else:
                    unique_results = matched_results

            is_play_command = any(kw in low_message for kw in _PLAY_KEYWORDS)

            if is_play_command and unique_results:
                async for chunk in self._handle_direct_play(unique_results[0], kwargs):
                    yield chunk
                return

            # Если результаты найдены в локальной базе — отдаем напрямую без обращения к LLM
            if unique_results:
                if len(unique_results) == 1:
                    handled = False
                    async for chunk in self._handle_direct_rag(unique_results[0]):
                        handled = True
                        yield chunk
                    if handled:
                        return
                else:
                    async for chunk in self._handle_direct_multi_items(message, unique_results, kwargs):
                        yield chunk
                    return

            # Если в локальной базе ничего не найдено
            if rag_mode == "rag":
                yield {
                    "status": "⚡ Ответ в локальной базе не найден.",
                    "text": f"❌ В локальной базе ничего не найдено по запросу «{message}».",
                    "prompt_dump": f"[DIRECT RAG]\nПо запросу «{message}» ничего не найдено.",
                    "voice": "В локальной базе ничего не найдено."
                }
                return

            # В режиме 'rag+model' и 'model' при отсутствии локальных результатов — поиск в интернете / LLM
            async for chunk in self._handle_llm_rag(message, results=[], kwargs=kwargs):
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