#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Orchestrator: Assign Torrents and Sync Paths
# =============================================================================
# Описание:
#   Комплексный запуск: сначала интеллектуальное сопоставление ID торрентов,
#   затем синхронизация путей сохранения в qBittorrent.
#
# File: orchestrator_torrent.py
# =============================================================================

import sys
import subprocess
from pathlib import Path

def run_orchestrator():
    print("=== Начало процесса оркестрации торрентов ===")
    
    # 1. Запуск assign_torrents_ids.py
    print("\n--- Этап 1: Интеллектуальное сопоставление (assign_torrents_ids.py) ---")
    try:
        # Используем subprocess для вызова, чтобы переменные окружения не перемешивались
        result_assign = subprocess.run([sys.executable, 'assign_torrents_ids.py'], check=True)
        print("✅ Этап 1 завершен успешно.")
    except subprocess.CalledProcessError:
        print("❌ Ошибка на этапе 1 (assign_torrents_ids.py). Прерывание.")
        return 1

    # 2. Запуск update_torrents_path.py
    print("\n--- Этап 2: Синхронизация путей (update_torrents_path.py) ---")
    try:
        result_sync = subprocess.run([sys.executable, 'update_torrents_path.py'], check=True)
        print("✅ Этап 2 завершен успешно.")
    except subprocess.CalledProcessError:
        print("❌ Ошибка на этапе 2 (update_torrents_path.py).")
        return 1
        
    print("\n=== Процесс успешно завершен ===")
    return 0

if __name__ == '__main__':
    sys.exit(run_orchestrator())
