# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Лончер генерации RAG-индекса для ассистента кода
# =============================================================================
# Описание:
#   Точка входа для запуска генерации RAG-индекса FAISS из корня проекта.
#
# Примеры:
#   >>> python generate_code_helper_faiss_rag_index.py
#
# File: generate_code_helper_faiss_rag_index.py
# Project: gemini-simplechat
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в path, чтобы импорты из plugins работали
sys.path.append(os.getcwd())

from plugins.code_helper.rag.generate_index import generate
from src.logger import logger

def main() -> None:
    """Запуск индексации RAG."""
    logger.info("Запуск индексации RAG для code_helper...")
    generate()

if __name__ == '__main__':
    main()
