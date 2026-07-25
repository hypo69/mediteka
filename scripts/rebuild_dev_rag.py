# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Переиндексация контекста разработчика
# =============================================================================
# Описание:
#   Скрипт запускает перестроение RAG-индекса для кода и документации.
#
# File: rebuild_dev_rag.py
# Project: gemini-simplechat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
from src.ai.dev_rag import build_dev_rag
from src.logger import logger

def main():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Ошибка: Переменная окружения GEMINI_API_KEY не установлена.")
        return

    print("🔄 Запуск переиндексации кодовой базы и документации...")
    try:
        build_dev_rag(api_key)
        print("✅ Индекс разработчика успешно перестроен.")
    except Exception as e:
        print(f"❌ Ошибка при переиндексации: {e}")
        logger.error(f"Ошибка rebuild_dev_rag: {e}", exc_info=True)

if __name__ == "__main__":
    main()
