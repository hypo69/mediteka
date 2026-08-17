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
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
from pathlib import Path
_root = Path(__file__).resolve().parents[3]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import argparse
from plugins.media_organizer.core.media_rag_functions import rebuild_rag_index


def main() -> None:
    """Запуск переиндексации RAG-индекса медиатеки."""
    parser = argparse.ArgumentParser(description="Переиндексация RAG-индекса.")
    args = parser.parse_args()

    print("Запуск переиндексации RAG-индекса медиатеки...")
    result = rebuild_rag_index()
    print(result)


if __name__ == '__main__':
    main()
