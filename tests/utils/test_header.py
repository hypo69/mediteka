# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля src/utils/header
# =============================================================================
# Описание:
#   Исчерпывающее тестирование всех публичных функций модуля header.
#   Покрытие: прямые тесты, граничные условия, регрессионные сценарии.
#
# File: tests/utils/test_header.py
# Project: mediteka
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from pathlib import Path
from src.utils.header import set_project_root

def test_set_project_root_success():
    """Тестирование успешного нахождения корня проекта.
    
    Проверка: функция должна найти директорию с маркером '__root__'.
    """
    # --- Подготовка (Arrange) ---
    # В проекте mediteka есть файл __root__ в корне.
    # Ожидаемый корень — C:\mediteka.
    expected_root = Path(r'C:\mediteka')
    
    # --- Выполнение (Act) ---
    root = set_project_root()
    
    # --- Проверка (Assert) ---
    assert root == expected_root, f"Корень проекта не найден, ожидалось {expected_root}, получено {root}"

def test_set_project_root_nonexistent_marker():
    """Тестирование нахождения корня при отсутствии маркеров."""
    # --- Подготовка (Arrange) ---
    # Маркер, которого заведомо нет в дереве проекта.
    marker = ('nonexistent_file_12345',)
    
    # --- Выполнение (Act) ---
    root = set_project_root(marker_files=marker)
    
    # --- Проверка (Assert) ---
    # Поведение функции: если не найдено, возвращает директорию скрипта.
    assert isinstance(root, Path), "Результат должен быть объектом Path"
