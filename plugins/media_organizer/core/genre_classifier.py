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

# Промпты для поэтапных запросов
_PROMPT_BASE = """Верни ТОЛЬКО JSON (без markdown) для {media_type} "{raw_name}"{genres_hint}.
Поля: title, title_ru(название на русском), title_orig(оригинальное название на языке оригинала),
year(int), type, main_category, country, genres(list), directors(list), cast(list[5]),
num_of_seasons(int|null), num_of_seasons(list[int]|null),
status("завершён"|"продолжается"|"отменён"|null),
rating({{"imdb": float|null, "tmdb": float|null}}),
awards(list[string]|null)."""

_PROMPT_PLOT = """Верни ТОЛЬКО JSON с полями plot, atmosphere, why_watch(string), mood(string) для {media_type} "{title}"."""

_PROMPT_final_verdict = """Верни ТОЛЬКО JSON с полями:
- final_verdict (string|null) — финал фильма или всего сериала
- quote (string|null) — культовая цитата
Для {media_type} "{title}"."""

_PROMPT_final_verdict_SEASONS = """Верни ТОЛЬКО JSON с полями:
- seasons (list|null) — для сериала: массив сезонов, каждый содержит season_number (int), description (string), episodes (массив с полями episode_number (int), begins (string), ends (string)), final_verdict (string|null)
- can_stop_at (string|null) — для сериала: после какого сезона можно остановиться если качество упало, иначе null
Для {media_type} "{title}"."""

_PROMPT_FACTS = """Верни ТОЛЬКО JSON с полями:
- facts (list[string], 3-5 фактов) — интересные факты о {media_type} "{title}", съёмках, актёрах
- similar (list[string], 3-5 названий) — похожие фильмы/сериалы
- review — объект с полями:
  - rating (string) — одно из: "отличный" | "хороший" | "средний"
  - liked (string) — что понравилось зрителям (актёрская игра, сюжет, атмосфера и т.д.)
  - disliked (string|null) — что не понравилось зрителям, или null
"""

_PROMPT_EPISODES_TEMPLATE = """Верни ТОЛЬКО JSON для сериала "{title}".
{instructions}

Структура — список сезонов (промежуточный формат для распределения по строкам БД):"""


def get_prompt_episodes(title: str, granularity: str) -> str:
    """Получение промпта для запроса эпизодов по уровню детализации.

    Args:
        title (str): Название сериала.
        granularity (str): Уровень детализации ('episode', 'arc', 'season', 'overview').

    Returns:
        str: Промпт для запроса к модели.
    """
    prompts = {
        'episode': """Структура: Каждый сезон → каждый эпизод → подробное описание событий.

[
  {{
    "season_number": 1,
    "episodes": [
      {{"episode_number": 1, "begins": "с чего начинается серия (2-3 предложения)", "ends": "чем заканчивается серия (2 предложения)"}},
      ...
    ]
  }},
  ...
]
""",
        'arc': """Структура: Сезон → сюжетные арки → краткие описания серий.

[
  {{
    "season_number": 1,
    "arcs": [
      {{
        "arc_name": "название арки",
        "episodes": [1, 2, 3],
        "summary": "описание арки (2-3 предложения)",
        "key_episodes": [
          {{"episode_number": 1, "summary": "краткое описание серии (1-2 предложения)"}}
        ]
      }},
      ...
    ]
  }},
  ...
]
""",
        'season': """Структура: Сезон → основные линии → финал.

[
  {{
    "season_number": 1,
    "summary": "подробное описание сезона (3-5 абзацев)",
    "main_plot_lines": ["описание основных сюжетных линий"],
    "key_events": ["ключевые события сезона"],
    "ending_summary": "описание финала сезона"
  }},
  ...
]
""",
        'overview': """Структура: Общая хроника сезона/периода.

[
  {{
    "season_number": 1,
    "summary": "краткое описание сезона (1-2 предложения)"
  }},
  ...
]
""",
    }
    instructions = prompts.get(granularity, prompts['overview'])
    return _PROMPT_EPISODES_TEMPLATE.format(title=title, instructions=instructions)


class GenreClassifier:
    """Классификатор медиа по жанрам через TMDB и Gemini.

    Attributes:
        tmdb (TMDBClient): Экземпляр клиента TMDB.
        gemini: Экземпляр модели Gemini.
        db (MediaDatabase): Экземпляр базы данных.
        disk_name (str): Имя диска для сохранения записей.
    """

    def __init__(self, tmdb: TMDBClient, gemini, db: 'MediaDatabase', disk_name: str) -> None:
        """Инициализация классификатора.

        Args:
            tmdb (TMDBClient): Экземпляр клиента TMDB.
            gemini: Экземпляр модели Gemini.
            db (MediaDatabase): Экземпляр базы данных.
            disk_name (str): Имя диска.

        Examples:
            >>> classifier = GenreClassifier(tmdb, gemini, db, 'ДИСК 1')
        """
        self.tmdb = tmdb
        self.gemini = gemini
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
        """Картографирование медиа в категорию через Gemini.

        Args:
            raw_name (str): Исходное имя.
            genres (List[str]): Жанры из TMDB.
            media_type (str): Тип: 'movie' или 'series'.
            item_id (str): ID элемента.
            is_series (bool): True если это сериал.
            path (str): Путь к медиа.

        Returns:
            Dict: Данные медиа с категорией.

        Examples:
            >>> data = await classifier._map_category('Фауда', [' Drama', 'Thriller'], 'series', '1', True)
        """
        genres_hint = f" (жанры TMDB: {', '.join(genres)})" if genres else ''

        def parse(response: str, label: str = '') -> Dict:
            if not response:
                print(f"     ⚠️  {label} пустой ответ от модели")
                return {}
            clean = re.sub(r'```(?:json)?\s*|\s*```', '', response).strip()
            try:
                parsed = json.loads(clean)
                if label:
                    print(f"     📝 {label}: {json.dumps(parsed, ensure_ascii=False, indent=2)}")
                return parsed
            except Exception as e:
                print(f"     ❌ {label} ошибка парсинга JSON: {e}")
                print(f"     Ответ: {response[:500]}...")
                return {}

        PAUSE = 5

        print(f"  📤 BASE для '{raw_name}'...")
        r1 = parse(await self.gemini.ask(_PROMPT_BASE.format(
            media_type=media_type, raw_name=raw_name, genres_hint=genres_hint
        )), 'BASE')
        print(f"     ✅ BASE получен")
        data = {
            'title': r1.get('title', raw_name),
            'title_ru': r1.get('title_ru', ''),
            'title_orig': r1.get('title_orig', ''),
            'year': r1.get('year') or 0,
            'media_type': media_type,
            'main_category': r1.get('main_category', 'Драмы'),
            'country': r1.get('country', ''),
            'genres': r1.get('genres') or [],
            'directors': r1.get('directors') or [],
            'cast': r1.get('cast') or [],
            'num_of_seasons': r1.get('num_of_seasons', 0),
            'num_episodes_per_season': r1.get('num_episodes_per_season', []),
            'status': r1.get('status', ''),
            'rating': r1.get('rating') or {},
            'awards': r1.get('awards') or [],
            'path': path,
            'episodes_detail': [],
            'episode_scan_skipped': False,
            'plot_granularity': '',
        }
        await asyncio.sleep(PAUSE)

        print(f"  📤 PLOT для '{data['title']}'...")
        r2 = parse(await self.gemini.ask(_PROMPT_PLOT.format(media_type=media_type, title=data['title'])), 'PLOT')
        data.update({'plot': r2.get('plot', ''), 'atmosphere': r2.get('atmosphere', ''),
                     'why_watch': r2.get('why_watch', ''), 'mood': r2.get('mood', '')})
        print(f"     ✅ PLOT получен")
        await asyncio.sleep(PAUSE)

        print(f"  📤 final_verdict для '{data['title']}'...")
        r3 = parse(await self.gemini.ask(_PROMPT_final_verdict.format(media_type=media_type, title=data['title'])), 'final_verdict')
        data.update({'final_verdict': r3.get('final_verdict', ''), 'quote': r3.get('quote', '')})
        print(f"     ✅ final_verdict получен")
        await asyncio.sleep(PAUSE)

        # final_verdict_SEASONS только для сериалов
        if is_series:
            print(f"  📤 final_verdict_SEASONS для '{data['title']}'...")
            r3b = parse(await self.gemini.ask(_PROMPT_final_verdict_SEASONS.format(media_type=media_type, title=data['title'])), 'final_verdict_SEASONS')
            data.update({'can_stop_at': r3b.get('can_stop_at', '')})
            print(f"     ✅ final_verdict_SEASONS получен")
            await asyncio.sleep(PAUSE)

        print(f"  📤 FACTS для '{data['title']}'...")
        r4 = parse(await self.gemini.ask(_PROMPT_FACTS.format(media_type=media_type, title=data['title'])), 'FACTS')
        data.update({'facts': r4.get('facts') or [], 'similar': r4.get('similar') or [],
                     'review': r4.get('review') or {}})
        print(f"     ✅ FACTS получен")
        await asyncio.sleep(PAUSE)

        if is_series:
            # Определяем уровень детализации на основе количества сезонов и эпизодов
            num_seasons = data.get('num_of_seasons') or 0
            num_episodes_per_season = data.get('num_episodes_per_season')
            if isinstance(num_episodes_per_season, str):
                try:
                    num_episodes_per_season = json.loads(num_episodes_per_season)
                except Exception:
                    num_episodes_per_season = None
            
            # Вычисляем среднее количество эпизодов на сезон
            avg_episodes_per_season = None
            if num_episodes_per_season and isinstance(num_episodes_per_season, list) and len(num_episodes_per_season) > 0:
                avg_episodes_per_season = sum(num_episodes_per_season) // len(num_episodes_per_season)
            
            # Определяем уровень детализации
            granularity = determine_granularity_from_record(data)
            data['plot_granularity'] = granularity
            
            print(f"  📊 ПОДБОР ПРОМПТА: {granularity} ({get_granularity_display_name(granularity)})")
            
            # Проверяем, есть ли данные о сезонах из TMDB
            tmdb_seasons = None
            if self.tmdb:
                tmdb_info = self.tmdb.search_tv_series(raw_name, data.get('year'))
                if tmdb_info:
                    tmdb_details = self.tmdb.get_tv_details(tmdb_info['id'])
                    if tmdb_details and 'seasons' in tmdb_details:
                        tmdb_seasons = tmdb_details['seasons']
            
            # Если из TMDB есть информация о сезонах, суммируем эпизоды
            total_episodes = 0
            if tmdb_seasons:
                for season in tmdb_seasons:
                    if season.get('episode_count'):
                        total_episodes += season['episode_count']
            
            # Логика: пропускаем запрос эпизодов, если:
            # 1. Уровень детализации overview (очень длинные сериалы), ИЛИ
            # 2. Сезонов очень много (>15), ИЛИ
            # 3. Общее количество эпизодов очень велико (>100)
            SKIP_EPISODE_THRESHOLD_SEASONS = 15
            SKIP_EPISODE_THRESHOLD_TOTAL = 100
            
            if granularity == 'overview' or num_seasons > SKIP_EPISODE_THRESHOLD_SEASONS or total_episodes > SKIP_EPISODE_THRESHOLD_TOTAL:
                print(f"  ⚠️  EPISODES пропущен (granularity: {granularity}, сезонов: {num_seasons}, эпизодов: {total_episodes})")
                data['episodes_detail'] = []
                data['episode_scan_skipped'] = True
            else:
                print(f"  📤 EPISODES ({granularity}) для '{data['title']}'...")
                # Генерируем промпт на основе уровня детализации
                prompt_episodes = get_prompt_episodes(data['title'], granularity)
                r5 = parse(await self.gemini.ask(prompt_episodes), 'EPISODES')
                data['episodes_detail'] = r5.get('episodes_detail') or []
                data['episode_scan_skipped'] = False
                print(f"     ✅ EPISODES получен ({len(r5.get('episodes_detail', []))} сезонов)")

        return data


# =============================================================================
# GENRE CLASSIFIER (EXTENDED)
# =============================================================================

class PersistentGenreClassifier(GenreClassifier):
    """Классификатор с проверкой коллизий по всей БД."""

    def __init__(self, tmdb, gemini, db, disk_name) -> None:
        """Инициализация расширенного классификатора.

        Args:
            tmdb: Экземпляр клиента TMDB.
            gemini: Экземпляр модели Gemini.
            db (MediaDatabase): Экземпляр базы данных.
            disk_name (str): Имя диска.

        Examples:
            >>> classifier = PersistentGenreClassifier(tmdb, gemini, db, 'ДИСК 1')
        """
        super().__init__(tmdb, gemini, db, disk_name)

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