# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Скрипт быстрого запуска переиндексации RAG
# =============================================================================
# Описание:
#   Импортирует и выполняет функцию перестроения RAG-индекса.
#
# File: rebuild_rag.py
# Project: gemini-simplechat
# Author: Antigravity
# =============================================================================

import sys
from plugins.media_organizer.core.media_rag_functions import rebuild_rag_index

def main() -> None:
    """Запуск переиндексации RAG-индекса медиатеки."""
    print("Запуск переиндексации RAG-индекса медиатеки...")
    result = rebuild_rag_index()
    print(result)

if __name__ == '__main__':
    main()
