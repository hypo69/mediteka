# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Классификация медиа по жанрам через TMDB и Gemini
# =============================================================================
# Описание:
#   Класс GenreClassifier для автоматической классификации фильмов и сериалов
#   с использованием TMDB и модели Gemini.
#   Класс PersistentGenreClassifier расширяет функционал проверкой коллизий.
#
# File: genre_classifier.py
# Project: gemini-simplechat
# Package: plugins.media_organizer.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import copy
import json
import re
from typing import Dict, List, Optional, Tuple

from plugins.media_organizer.core import DEFAULT_CATEGORIES
from plugins.media_organizer.core.media_scanner import TMDBClient


# =============================================================================
# КОНВЕРТОРЫ: media -> JSON / MD
# =============================================================================

def _split_records(records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Разделение записей на сериалы и фильмы с сортировкой по категории и названию.

    Args:
        records (List[Dict]): Плоский список записей из БД.

    Returns:
        Tuple[List[Dict], List[Dict]]: Отсортированные списки (series, movies).
    """
    key = lambda r: (r.get('main_category', ''), r.get('title', ''))
    series = sorted([r for r in records if r.get('num_of_seasons', 0) > 0], key=key)
    movies = sorted([r for r in records if r.get('num_of_seasons', 0) == 0], key=key)
    return series, movies


def get_categories_from_db(db: 'MediaDatabase') -> List[str]:
    """Получение списка категорий из БД.

    Args:
        db (MediaDatabase): Экземпляр базы данных.

    Returns:
        List[str]: Список названий категорий.

    Examples:
        >>> categories = get_categories_from_db(db)
    """
    # Используем DEFAULT_CATEGORIES вместо БД
    return list(DEFAULT_CATEGORIES)


def ensure_categories_in_db(db: 'MediaDatabase') -> None:
    """Убедиться, что начальные категории есть в БД.

    Args:
        db (MediaDatabase): Экземпляр базы данных.

    Examples:
        >>> ensure_categories_in_db(db)
    """
    # Таблица categories не используется, просто пропускаем
    pass


# =============================================================================
# GENRE CLASSIFIER
# =============================================================================

from src.media_granularity import (
    determine_granularity_from_record,
    get_prompt_by_granularity,
    get_granularity_display_name,
)

# Промпты для эпизодов больше не используются, так как все делает Research Agent.


class GenreClassifier:
    """Классификатор медиа по жанрам через TMDB и Gemini.

    Attributes:
        tmdb (TMDBClient): Экземпляр клиента TMDB.
        ai_research: Экземпляр модели Gemini для Research Agent.
        ai_chat: Экземпляр модели Gemini для Chat Generator.
        ai_tts: Экземпляр модели Gemini для TTS Generator.
        db (MediaDatabase): Экземпляр базы данных.
        disk_name (str): Имя диска для сохранения записей.
    """

    def __init__(self, tmdb: TMDBClient, ai_research, ai_chat, ai_tts, db: 'MediaDatabase', disk_name: str) -> None:
        """Инициализация классификатора.

        Args:
            tmdb (TMDBClient): Экземпляр клиента TMDB.
            ai_research: Экземпляр модели Gemini для Research Agent.
            ai_chat: Экземпляр модели Gemini для Chat Generator.
            ai_tts: Экземпляр модели Gemini для TTS Generator.
            db (MediaDatabase): Экземпляр базы данных.
            disk_name (str): Имя диска.
        """
        self.tmdb = tmdb
        self.ai_research = ai_research
        self.ai_chat = ai_chat
        self.ai_tts = ai_tts
        self.db = db
        self.disk_name = disk_name

    async def classify_media(self, movies: List[Dict], series: Dict) -> Tuple:
        """Классификация списка фильмов и словаря сериалов.

        Args:
            movies (List[Dict]): Список фильмов.
            series (Dict): Словарь сериалов.

        Returns:
            Tuple: (classified_movies, classified_series)

        Examples:
            >>> classified_movies, classified_series = await classifier.classify_media(movies, series)
        """
        classified_movies = await self._classify_list(movies, 'movie')
        classified_series = await self._classify_dict(series, 'series')
        return classified_movies, classified_series

    async def _classify_list(self, items: List[Dict], media_type: str) -> List[Dict]:
        """Классификация списка медиа.

        Args:
            items (List[Dict]): Список медиа.
            media_type (str): Тип: 'movie' или 'series'.

        Returns:
            List[Dict]: Классифицированный список.

        Examples:
            >>> result = await classifier._classify_list(movies, 'movie')
        """
        result: List[Dict] = []
        for item in items:
            raw_name = item['title']
            path = item.get('path', raw_name)
            print(f"DEBUG: [{media_type}] Обработка: {raw_name}, path={path}")

            # Проверка по path — если уже есть в БД по пути, пропускаем
            cached = self.db.get_media_by_path(path)
            if cached:
                print(f"⏭️  [{media_type}] {raw_name} — уже обработан, пропускаю")
                result.append({**item, **cached})
                continue

            print(f"🎬 [{media_type}] {raw_name} ...", end=' ', flush=True)
            genre_names: List[str] = []
            if self.tmdb:
                tmdb_info = self.tmdb.search_movie(raw_name, item.get('year'))
                if tmdb_info:
                    details = self.tmdb.get_movie_details(tmdb_info['id'])
                    if details and 'genres' in details:
                        genre_names = [g['name'] for g in details['genres']]
            try:
                info = await self._map_category(raw_name, genre_names, media_type, item.get('path', raw_name), False, path=item.get('path'))
                print(f"✅ {info.get('title')} [{info.get('main_category')}]")
            except Exception as ex:
                print(f"❌ {ex}")
                info = {'title': raw_name, 'year': 0, 'main_category': 'Драмы'}
            # Сохраняем raw_name как title в БД (имя файла НЕ должно меняться)
            save_data = {**info, 'title': raw_name}
            self.db.save_media(self.disk_name, media_type, save_data)
            result.append({**item, **info})
        return result

    async def _classify_dict(self, items: Dict, media_type: str) -> Dict:
        """Классификация словаря медиа.

        Args:
            items (Dict): Словарь медиа.
            media_type (str): Тип: 'movie' или 'series'.

        Returns:
            Dict: Классифицированный словарь.

        Examples:
            >>> result = await classifier._classify_dict(series, 'series')
        """
        result: Dict = {}
        for raw_name, item in items.items():
            path = item.get('path', raw_name)
            print(f"DEBUG: [{media_type}] Обработка: {raw_name}, path={path}")

            # Проверка по path — если уже есть в БД по пути, пропускаем
            cached = self.db.get_media_by_path(path)
            if cached:
                print(f"⏭️  [{media_type}] {raw_name} — уже обработан, пропускаю")
                result[cached.get('title', raw_name)] = {**item, **cached}
                continue

            print(f"📺 [{media_type}] {raw_name} ...", end=' ', flush=True)
            genre_names: List[str] = []
            if self.tmdb:
                tmdb_info = self.tmdb.search_tv_series(raw_name, item.get('year'))
                if tmdb_info:
                    details = self.tmdb.get_tv_details(tmdb_info['id'])
                    if details and 'genres' in details:
                        genre_names = [g['name'] for g in details['genres']]
            try:
                info = await self._map_category(raw_name, genre_names, media_type, raw_name, True, path=item.get('path'))
                print(f"✅ {info.get('title')} [{info.get('main_category')}]")
            except Exception as ex:
                print(f"❌ {ex}")
                info = {'title': raw_name, 'year': 0, 'main_category': 'Драмы'}
            # Сохраняем raw_name как title в БД (имя файла НЕ должно меняться)
            save_data = {**item, **info, 'title': raw_name}
            try:
                self.db.save_media(self.disk_name, media_type, save_data)
                print(f"💾 [{media_type}] {raw_name} сохранен в БД")
            except Exception as e:
                print(f"❌ [{media_type}] {raw_name} ошибка сохранения: {e}")
            result[raw_name] = save_data
        return result

    async def _map_category(self, raw_name: str, genres: List[str], media_type: str, item_id: str, is_series: bool, path: str = '') -> Dict:
        """Картографирование медиа в категорию через новые модели (Research, Chat, TTS)."""
        genres_hint = f" (жанры TMDB: {', '.join(genres)})" if genres else ''

        def parse_json(response: str, label: str = '') -> Dict:
            if not response:
                print(f"     ⚠️  {label} пустой ответ от модели")
                return {}
            clean = re.sub(r'```(?:json)?\s*|\s*```', '', response).strip()
            try:
                parsed = json.loads(clean)
                if label:
                    print(f"     📝 {label}: {json.dumps(parsed, ensure_ascii=False, indent=2)[:500]}...")
                return parsed
            except Exception as e:
                print(f"     ❌ {label} ошибка парсинга JSON: {e}")
                print(f"     Ответ: {response[:500]}...")
                return {}

        PAUSE = 2
        import pathlib
        
        input_data = {
            "title": raw_name,
            "genres": genres_hint,
            "type": media_type
        }
        input_str = json.dumps(input_data, ensure_ascii=False)
        
        # 1. Research Agent
        print(f"  📤 RESEARCH для '{raw_name}'...")
        r_research = parse_json(await self.ai_research.ask(input_str), 'RESEARCH')
        print(f"     ✅ RESEARCH получен")
        await asyncio.sleep(PAUSE)
        
        research_str = json.dumps(r_research, ensure_ascii=False)
        
        # 2. Chat Generator
        print(f"  📤 CHAT для '{raw_name}'...")
        r_chat = parse_json(await self.ai_chat.ask(research_str), 'CHAT')
        print(f"     ✅ CHAT получен")
        await asyncio.sleep(PAUSE)
        
        # 3. TTS Generator
        print(f"  📤 TTS для '{raw_name}'...")
        r_tts = await self.ai_tts.ask(research_str)
        print(f"     ✅ TTS получен")
        
        # Сохранение файлов в директорию медиа
        if path:
            try:
                ai_dir = pathlib.Path(path) / 'ai'
                if not ai_dir.exists():
                    ai_dir.mkdir(parents=True, exist_ok=True)
                
                (ai_dir / 'research.json').write_text(json.dumps(r_research, ensure_ascii=False, indent=2), encoding='utf-8')
                (ai_dir / 'chat.json').write_text(json.dumps(r_chat, ensure_ascii=False, indent=2), encoding='utf-8')
                (ai_dir / 'narrator.txt').write_text(r_tts, encoding='utf-8')
                print(f"     💾 Файлы ai/ сохранены в {ai_dir}")
            except Exception as e:
                print(f"     ❌ Ошибка сохранения файлов ai/: {e}")

        # Формирование словаря для базы данных (чтобы работали фильтры и веб-интерфейс)
        data = {
            'title': r_chat.get('title', r_research.get('title', raw_name)),
            'title_ru': r_chat.get('title_ru', ''),
            'title_orig': r_chat.get('title_orig', ''),
            'year': r_chat.get('year') or r_research.get('year', 0),
            'media_type': media_type,
            'main_category': r_chat.get('main_category', 'Драмы'),
            'country': r_chat.get('country', ''),
            'genres': r_chat.get('genres') or [],
            'directors': r_chat.get('directors') or [],
            'cast': r_chat.get('cast') or [],
            'num_of_seasons': r_chat.get('num_of_seasons', 0),
            'num_episodes_per_season': r_chat.get('num_episodes_per_season', []),
            'status': r_chat.get('status', ''),
            'rating': r_chat.get('rating') or {},
            'awards': r_chat.get('awards') or [],
            'path': path,
            'plot': r_chat.get('plot', ''),
            'atmosphere': r_chat.get('atmosphere', ''),
            'why_watch': r_chat.get('why_watch', ''),
            'mood': r_chat.get('mood_tags') or r_chat.get('mood', ''),
            'final_verdict': r_chat.get('final_verdict', ''),
            'quote': r_chat.get('quote', ''),
            'facts': r_chat.get('facts') or [],
            'similar': r_chat.get('similar') or [],
            'review': r_chat.get('review') or {},
            'episode_scan_skipped': r_research.get('episode_scan_skipped', False),
            'episodes_detail': r_chat.get('seasons', []) or r_research.get('seasons', []),
        }

        return data


# =============================================================================
# GENRE CLASSIFIER (EXTENDED)
# =============================================================================

class PersistentGenreClassifier(GenreClassifier):
    """Классификатор с проверкой коллизий по всей БД."""

    def __init__(self, tmdb, ai_research, ai_chat, ai_tts, db, disk_name) -> None:
        """Инициализация расширенного классификатора.

        Args:
            tmdb: Экземпляр клиента TMDB.
            ai_research: Экземпляр модели Gemini (Research).
            ai_chat: Экземпляр модели Gemini (Chat).
            ai_tts: Экземпляр модели Gemini (TTS).
            db (MediaDatabase): Экземпляр базы данных.
            disk_name (str): Имя диска.
        """
        super().__init__(tmdb, ai_research, ai_chat, ai_tts, db, disk_name)

    async def _map_category(self, raw_name, genres, media_type, item_id, is_series, path='') -> Dict:
        """Картографирование с проверкой коллизий.

        Сначала ищет по всей БД, если найдено на другом диске — спрашивает пользователя.

        Args:
            raw_name: Исходное имя.
            genres: Жанры из TMDB.
            media_type: Тип: 'movie' или 'series'.
            item_id: ID элемента.
            is_series: True если это сериал.
            path: Путь к медиа.

        Returns:
            Dict: Данные медиа с категорией.

        Examples:
            >>> data = await classifier._map_category(...)
        """
        # Поиск по всей БД (другой диск)
        cached = self.db.find_any_disk(raw_name)
        if cached and cached.get('disk_name') != self.disk_name:
            kind = 'сериал' if is_series else 'фильм'
            print(f"\n⚠️  [КОЛЛИЗИЯ] {raw_name!r} — {kind} уже есть на диске '{cached['disk_name']}'")
            print(f"   Название: {cached.get('title')}  |  Год: {cached.get('year')}  |  Категория: {cached.get('main_category')}")
            print(f"   ✅ Автоматически используем данные из локального хранилища (диск '{cached['disk_name']}')")
            cached['path'] = path
            self.db.save_media(self.disk_name, media_type, cached)
            return cached

        return await super()._map_category(raw_name, genres, media_type, item_id, is_series, path=path)