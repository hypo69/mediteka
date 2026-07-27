# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Генерация RAG-индекса для ассистента кода
# =============================================================================
# Описание:
#   Скрипт собирает файлы документации и кода, выполняет векторизацию
#   через API Gemini и сохраняет FAISS-индекс для RAG.
#
# Примеры:
#   >>> from plugins.code_helper.rag.generate_index import generate
#   >>> generate()
#
# File: generate_index.py
# Project: gemini-simplechat
# Package: plugins.code_helper.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import sys
import json
from pathlib import Path
from typing import List, Dict

# Добавляем корневую директорию проекта в sys.path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from plugins.code_helper.rag.engine import FaissEngine
from src.logger import logger

# Список исключений
EXCLUDED_DIRS = {
    '.git', '.pytest_cache', '.vs', '__pycache__', 'venv', 
    'htmlcov', 'site', 'node_modules', '.venv'
}
EXCLUDED_FILES = {
    '.env', '.gitignore', '.gitattributes', 'all_duplicates_with_ids.csv', 'all_media_data.csv',
    'deletion_candidates_all.csv', 'deletion_candidates.csv', 'duplicates_report_candidates.csv',
    'duplicates_report.csv', 'inferred_titles_report.csv', 'physical_check_results.csv',
    'potential_duplicates.csv'
}

def get_api_key() -> str:
    """Получение API ключа Gemini из src/secrets/gemini_keys.json."""
    keys_file = Path(r"C:\mediateka\src\secrets\gemini_keys.json")
    if not keys_file.exists():
        logger.error(f"Файл ключей {keys_file} не найден.")
        return ''
    
    try:
        with open(keys_file, 'r', encoding='utf-8') as f:
            keys = json.load(f)
            # Используем ключ для 'fmashulia' как было предложено
            api_key = keys.get("fmashulia", {}).get("api_key")
            if not api_key:
                logger.error("API ключ для 'fmashulia' не найден.")
                return ''
            return api_key
    except Exception as e:
        logger.error(f"Ошибка при чтении файла ключей: {e}")
        return ''

def get_files_to_index() -> List[Path]:
    """Сбор списка файлов для индексации с учетом исключений."""
    project_root = Path(r"C:\mediateka")
    aux_dir = project_root / "knowledge" / "rag_auxiliary"
    files_to_index = []

    # 1. Сканирование корня с исключениями
    for root, dirs, files in os.walk(project_root):
        # Модифицируем список dirs на месте для пропуска исключенных директорий
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        for file in files:
            if file in EXCLUDED_FILES:
                continue
            
            file_path = Path(root) / file
            if file_path.suffix in [".py", ".md"]:
                files_to_index.append(file_path)

    # 2. Добавление файлов из rag_auxiliary
    if aux_dir.exists():
        for file_path in aux_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".py", ".md"]:
                if file_path not in files_to_index:
                    files_to_index.append(file_path)
    
    return files_to_index

import asyncio
# ... (остальные импорты)

async def generate() -> bool:
    """Сбор и индексация документов для code_helper (без БД)."""
    rag_dir: Path = Path(__file__).parent

    files = get_files_to_index()
    if not files:
        logger.warning("Файлы для индексации не найдены.")
        return False

    engine = FaissEngine(rag_dir)

    # Полная переиндексация
    engine.index.reset()
    engine.metadatas = []

    docs: List[Dict] = []
    for file_path in files:
        try:
            text: str = file_path.read_text(encoding='utf-8')
            docs.append({
                'text': f"Файл: {file_path.name}\nСодержимое:\n{text}",
                'meta': {'path': str(file_path)}
            })
        except Exception as e:
            logger.error(f"Ошибка чтения {file_path}", e)

    if docs:
        # Теперь awaited
        success: bool = await engine.add_documents(docs)
        if success:
            logger.info(f"Индекс успешно создан. Индексировано файлов: {len(docs)}")
            return True
        return False
    else:
        logger.warning("Не удалось прочитать файлы для индексации.")
        return False

if __name__ == '__main__':
    asyncio.run(generate())

