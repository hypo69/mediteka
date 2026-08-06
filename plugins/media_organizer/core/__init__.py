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
PROMPT_RESEARCH_FILE = __root__ / 'prompts' / 'media_organizer' / 'prompt_research.md'
PROMPT_CHAT_FILE = __root__ / 'prompts' / 'media_organizer' / 'system_instruction.md'
PROMPT_TTS_FILE = __root__ / 'prompts' / 'media_organizer' / 'prompt_tts.md'
TORRENTS_FILE = CONFIG_DIR / 'torrents_names.json.md'

def _build_instruction(file_path: Path, include_torrents: bool = False) -> str:
    """Загружает инструкцию, опционально добавляя список торрентов."""
    instruction_text = file_path.read_text(encoding="utf-8") if file_path.exists() else ''
    if include_torrents:
        torrents_text = TORRENTS_FILE.read_text(encoding="utf-8") if TORRENTS_FILE.exists() else ''
        if torrents_text and instruction_text:
            placeholder = "```jsonl\n\n\n\n"
            replacement = f"```jsonl\n{torrents_text}\n"
            instruction_text = instruction_text.replace(placeholder, replacement, 1)
    return instruction_text

SYSTEM_INSTRUCTION_RESEARCH = _build_instruction(PROMPT_RESEARCH_FILE, include_torrents=True)
SYSTEM_INSTRUCTION_CHAT = _build_instruction(PROMPT_CHAT_FILE)
SYSTEM_INSTRUCTION_TTS = _build_instruction(PROMPT_TTS_FILE)

# Сохраняем SYSTEM_INSTRUCTION для обратной совместимости (указывает на Research)
SYSTEM_INSTRUCTION = SYSTEM_INSTRUCTION_RESEARCH

# Категории по умолчанию (должны быть до импортов из genre_classifier для избежания circular import)
DEFAULT_CATEGORIES = [
    "Боевики", "Триллеры", "Приключения", "Драмы", "Семейные",
    "Исторические/Костюмированные", "Расследования", "Шпионы", "Мюзиклы", "Документальные"
]



# Импорты для совместимости
from plugins.media_organizer.core.genre_classifier import ensure_categories_in_db, get_categories_from_db

# Импорты для внешнего использования
# torrent_matcher удалён - всё перенесено в media_tracker
