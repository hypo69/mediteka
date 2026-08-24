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

import argparse
from plugins.media_organizer.core.media_rag_functions import rebuild_rag_index

def main() -> None:
    """Запуск переиндексации RAG-индекса медиатеки."""
    parser = argparse.ArgumentParser(description="Переиндексация RAG-индекса.")
    parser.add_argument('--fresh', action='store_true', help="Выполнить бэкап и создать новый индекс с нуля.")
    args = parser.parse_args()
    
    print(f"Запуск переиндексации RAG-индекса медиатеки (fresh={args.fresh})...")
    result = rebuild_rag_index(fresh=args.fresh)
    print(result)

if __name__ == '__main__':
    main()
