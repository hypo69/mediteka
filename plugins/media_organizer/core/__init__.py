# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Конфигурация путей медиа-органайзера
# =============================================================================
# Описание:
#   Единый конфиг с путями к файлам медиа-органайзера.
#
# File: __init__.py
# Project: gemini-simplechat
# Package: plugins.media_organizer.core
# =============================================================================

from pathlib import Path

from header import __root__
from plugins.media_organizer.core.database import MediaDatabase

# Корневая директория плагина
_PLUGIN_DIR = Path(__file__).parent.parent

# Директории
DATA_DIR = _PLUGIN_DIR / 'data'
CONFIG_DIR = _PLUGIN_DIR / 'config'
REPORTS_DIR = _PLUGIN_DIR / 'reports'
EXAMPLES_DIR = _PLUGIN_DIR / 'examples'

# Output directory (alias for REPORTS_DIR for backward compatibility)
OUTPUT_DIR = REPORTS_DIR

# Файлы базы данных
MEDIA_DB = DATA_DIR / 'media.db'
MEDIA_RAG_DB = DATA_DIR / 'media_rag.db'
DB_FILE = MEDIA_DB  # Alias for backward compatibility

# Конфигурационные файлы
MEDIA_PATHS_FILE = CONFIG_DIR / 'media_paths.txt'
INSTRUCTION_FILE = __root__ / '.ai_instructions' / 'prompts' / 'media_organizer' / 'system_instruction.md'
TORRENTS_FILE = CONFIG_DIR / 'torrents_names.json.md'
PATHS_FILE = MEDIA_PATHS_FILE  # Alias for backward compatibility


def _build_system_instruction() -> str:
    """Объединяет общую инструкцию Media Organizer и данные торрентов."""
    instruction_text = INSTRUCTION_FILE.read_text(encoding="utf-8") if INSTRUCTION_FILE.exists() else ''
    torrents_text = TORRENTS_FILE.read_text(encoding="utf-8") if TORRENTS_FILE.exists() else ''
    
    if not instruction_text:
        return torrents_text
    
    if torrents_text:
        # Вставляем список торрентов в инструкцию перед закрывающим тегом ```
        placeholder = "```jsonl\n\n\n\n"
        replacement = f"```jsonl\n{torrents_text}\n"
        instruction_text = instruction_text.replace(placeholder, replacement, 1)
    
    return instruction_text


SYSTEM_INSTRUCTION = _build_system_instruction()

# Категории по умолчанию (должны быть до импортов из genre_classifier для избежания circular import)
DEFAULT_CATEGORIES = [
    "Боевики", "Триллеры", "Приключения", "Драмы", "Семейные",
    "Исторические/Костюмированные", "Расследования", "Шпионы", "Мюзиклы", "Документальные"
]

# Промпты для поэтапных запросов (должны быть до импортов из genre_classifier)
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

_PROMPT_EPISODES = """Верни ТОЛЬКО JSON для сериала "{title}".
Структура — список сезонов (промежуточный формат для распределения по строкам БД):
[
  {{
    "season_number": 1,
    "episodes": [
      {{"episode_number": 1, "begins": "с чего начинается серия (1-2 предложения)", "ends": "чем заканчивается серия (1 предложение)"}},
      ...
    ]
  }},
  ...
]
Для каждой серии: begins — с чего начинается серия, ends — чем она заканчивается."""

# Импорты для совместимости
from plugins.media_organizer.core.genre_classifier import ensure_categories_in_db, get_categories_from_db

# Импорты для внешнего использования
# torrent_matcher удалён - всё перенесено в media_tracker
