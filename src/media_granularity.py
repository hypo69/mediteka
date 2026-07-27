# -*- coding: utf-8 -*-
# =============================================================================
# Название модуля: Определение уровня детализации сюжета для сериалов
# =============================================================================
# Описание:
#   Модуль предоставляет функции для автоматического определения уровня
#   детализации описания сюжета в зависимости от структуры повествования.
#
#   Четыре категории детализации:
#   - episode: подробно каждая серия (Breaking Bad, Dark, 24)
#   - arc: сюжетные арки, серии кратко (Game of Thrones, The Boys)
#   - season: только сезон целиком (Великолепный век, дорамы)
#   - overview: только общая история (долгие сериалы >15 сезонов)
#
# File: media_granularity.py
# Project: mediteka
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from typing import Dict, List, Optional, Tuple

# =============================================================================
# ПОРоги классификации
# =============================================================================

# Минимальное количество сезонов для "очень длинного" сериала
LONG_RUNNING_THRESHOLD = 15

# Минимальное количество эпизодов в сезоне для "тянучки"
EPISODES_PER_SEASON_DRAMA_THRESHOLD = 40

# Минимальное количество эпизодов в сезоне для "динамичного" сериала
EPISODES_PER_SEASON_ACTION_THRESHOLD = 12

# =============================================================================
# ОПРЕДЕЛЕНИЕ УРОВНЯ ДЕТАЛИЗАЦИИ
# =============================================================================


def determine_granularity(
    num_of_seasons: int,
    num_episodes_per_season: Optional[List[int]] = None,
    avg_episodes_per_season: Optional[int] = None,
) -> str:
    """Определение уровня детализации сюжета для сериала.

    Args:
        num_of_seasons (int): Количество сезонов.
        num_episodes_per_season (Optional[List[int]]): Список количества эпизодов по сезонам.
        avg_episodes_per_season (Optional[int]): Среднее количество эпизодов в сезоне.

    Returns:
        str: Уровень детализации: 'episode', 'arc', 'season', 'overview'.

    Examples:
        >>> determine_granularity(5, [10, 10, 10, 10, 10])
        'episode'
        >>> determine_granularity(3, [22, 24, 22])
        'arc'
        >>> determine_granularity(5, [50, 50, 50, 50, 50])
        'season'
        >>> determine_granularity(20, [22]*20)
        'overview'
    """
    # Если нет информации о сезонах - берем overview как fallback
    if num_of_seasons <= 0:
        return 'overview'

    # Если очень много сезонов (>15) - overview
    if num_of_seasons > LONG_RUNNING_THRESHOLD:
        return 'overview'

    # Если есть информация о количестве эпизодов
    if num_episodes_per_season is not None and len(num_episodes_per_season) > 0:
        # Вычисляем среднее количество эпизодов на сезон
        if avg_episodes_per_season is None:
            avg_episodes_per_season = sum(num_episodes_per_season) // len(num_episodes_per_season)

        # Если сезонов мало (1-3) и эпизодов много (40+) - season (тянучка, например турецкие/дорамы)
        if avg_episodes_per_season >= EPISODES_PER_SEASON_DRAMA_THRESHOLD:
            return 'overview' # Для нескончаемых серий выдаем только краткий вердикт

        # Если сезонов 3-8 и эпизодов среднее (12-24) - arc
        if 3 < num_of_seasons <= 8 and EPISODES_PER_SEASON_ACTION_THRESHOLD <= avg_episodes_per_season <= 24:
            return 'arc'

        # Если сезонов мало (1-4) и эпизодов мало (≤12) - episode
        if num_of_seasons <= 4 and avg_episodes_per_season <= EPISODES_PER_SEASON_ACTION_THRESHOLD:
            return 'episode'

    # Если среднее количество эпизодов известно
    if avg_episodes_per_season is not None:
        if avg_episodes_per_season >= EPISODES_PER_SEASON_DRAMA_THRESHOLD:
            return 'overview'
        if 12 <= avg_episodes_per_season <= 24:
            return 'arc'
        if avg_episodes_per_season < 12:
            return 'episode'

    # Базовая эвристика по сезонам
    if num_of_seasons <= 4:
        return 'episode'
    if num_of_seasons <= 8:
        return 'arc'
    if num_of_seasons <= 15:
        return 'season'

    # Fallback
    return 'overview'


def determine_granularity_from_record(record: Dict) -> str:
    """Определение уровня детализации по записи из БД.

    Args:
        record (Dict): Запись из таблицы media.

    Returns:
        str: Уровень детализации.
    """
    num_of_seasons = record.get('num_of_seasons', 0)

    # Получаем список количества эпизодов по сезонам
    num_episodes_raw = record.get('num_episodes_per_season')
    num_episodes_per_season: Optional[List[int]] = None
    if num_episodes_raw:
        if isinstance(num_episodes_raw, list):
            num_episodes_per_season = num_episodes_raw
        elif isinstance(num_episodes_raw, str):
            import json
            try:
                num_episodes_per_season = json.loads(num_episodes_raw)
            except Exception:
                num_episodes_per_season = None

    # Вычисляем среднее количество эпизодов на сезон
    avg_episodes_per_season: Optional[int] = None
    if num_episodes_per_season and len(num_episodes_per_season) > 0:
        avg_episodes_per_season = sum(num_episodes_per_season) // len(num_episodes_per_season)

    return determine_granularity(num_of_seasons, num_episodes_per_season, avg_episodes_per_season)


# =============================================================================
# Формирование промптов на основе уровня детализации
# =============================================================================

PROMPT_EPISODE_DRIVEN = """Верни ТОЛЬКО JSON для сериала "{title}".
Структура: Каждый сезон → каждый эпизод → подробное описание событий.

Структура — список сезонов (промежуточный формат):
[
  {{
    "season_number": 1,
    "episodes": [
      {{"episode_number": 1, "begins": "с чего начинается серия (2-3 предложения)", "ends": "чем заканчивается серия (2 предложения)", "key_events": "ключевые события (3-5 пунктов)", "character_arcs": "изменения персонажей (2-3 предложения)"}},
      ...
    ]
  }},
  ...
]

Правила:
- Детальный разбор КАЖДОЙ серии
- О��иши начало и конец каждой серии
- Укажи ключевые события (3-5 пунктов)
- Опиши изменения персонажей
- Все описания на русском языке"""

PROMPT_ARC_DRIVEN = """Верни ТОЛЬКО JSON для сериала "{title}".
Структура: Сезон → сюжетные арки → краткие описания серий.

Структура — список сезонов:
[
  {{
    "season_number": 1,
    "arcs": [
      {{
        "arc_name": "название арки",
        "episodes": [1, 2, 3],
        "summary": "описание арки (2-3 предложения)",
        "key_episodes": [
          {{"episode_number": 1, "summary": "краткое описание серии (1-2 предложения)"}},
          ...
        ]
      }},
      ...
    ]
  }},
  ...
]

Правила:
- Сначала опиши сюжетные арки сезона
- Для каждой арки укажи эпизоды и краткое описание
- Эпизоды внутри арки описываются кратко (1-2 предложения)
- Все описания на русском языке"""

PROMPT_SEASON_DRIVEN = """Верни ТОЛЬКО JSON для сериала "{title}".
Структура: Сезон → основные линии → финал.

Структура — список сезонов:
[
  {{
    "season_number": 1,
    "summary": "подробное описание сезона (3-5 абзацев)",
    "main_plot_lines": ["описание основных сюжетных линий (2-3 пункта)"],
    "key_events": ["ключевые события сезона (3-5 пунктов)"],
    "characters_developed": ["основные изменения персонажей (2-3 пункта)"],
    "ending_summary": "описание финала сезона (2-3 предложения)"
  }},
  ...
]

Правила:
- Подробно опиши весь сезон целиком
- Укажи основные сюжетные линии и их развитие
- Опиши ключевые события и финал сезона
- Эпизоды не описываются отдельно
- Все описания на русском языке"""

PROMPT_OVERVIEW = """Верни ТОЛЬКО JSON для сериала "{title}".
Структура: Общая хроника сезона/периода.

Структура — список сезонов:
[
  {{
    "season_number": 1,
    "period": "временной период (если известен)",
    "summary": "краткое описание сезона (1-2 предложения)"
  }},
  ...
]

Правила:
- Очень краткое описание каждого сезона (1-2 предложения)
- Не детализируй отдельные серии
- Укажи только основные повороты сюжета
- Все описания на русском языке"""


def get_prompt_by_granularity(granularity: str, title: str) -> str:
    """Получение промпта для запроса эпизодов по уровню детализации.

    Args:
        granularity (str): Уровень детализации ('episode', 'arc', 'season', 'overview').
        title (str): Название сериала.

    Returns:
        str: Промпт для запроса к модели.
    """
    prompts = {
        'episode': PROMPT_EPISODE_DRIVEN,
        'arc': PROMPT_ARC_DRIVEN,
        'season': PROMPT_SEASON_DRIVEN,
        'overview': PROMPT_OVERVIEW,
    }
    return prompts.get(granularity, PROMPT_OVERVIEW).format(title=title)


# =============================================================================
# Утилиты
# =============================================================================

def get_granularity_display_name(granularity: str) -> str:
    """Получение отображаемого названия уровня детализации.

    Args:
        granularity (str): Уровень детализации.

    Returns:
        str: Отображаемое название.
    """
    names = {
        'episode': 'Детальный (по эпизодам)',
        'arc': 'Арочный (по сюжетным линиям)',
        'season': 'Сезонный (целиком)',
        'overview': 'Обзорный (общая хроника)',
    }
    return names.get(granularity, 'Неизвестно')


def get_granularity_thresholds() -> Dict:
    """Получение порогов классификации.

    Returns:
        Dict: Словарь с порогами.
    """
    return {
        'long_running_threshold': LONG_RUNNING_THRESHOLD,
        'episodes_per_season_drama_threshold': EPISODES_PER_SEASON_DRAMA_THRESHOLD,
        'episodes_per_season_action_threshold': EPISODES_PER_SEASON_ACTION_THRESHOLD,
    }
