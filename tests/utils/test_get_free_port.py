# -*- coding: utf-8 -*-
# =============================================================================
# Тестирование модуля: get_free_port
# =============================================================================
# Описание:
#   Комплексное тестирование функционала поиска свободного порта.
#   Покрытие сценариев: поиск в диапазоне, список диапазонов, поиск первого доступного,
#   обработка некорректных данных.
#
# File: test_get_free_port.py
# Project: Наш интеллектуальный помощник
# Package: Tests.Utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from unittest.mock import patch
from src.utils.get_free_port import get_free_port

def test_get_free_port_no_range():
    # Шаг 1: Использование mock для симуляции доступности порта.
    # Ожидаемое состояние: Порт 1024 считается свободным.
    with patch('src.utils.get_free_port._is_port_in_use', return_value=False):
        port = get_free_port(host='localhost')
        assert port == 1024

def test_get_free_port_single_range_success():
    # Шаг 1: Поиск порта в заданном диапазоне 3000-4000.
    # Ожидаемое состояние: Порт в диапазоне [3000, 4000].
    port = get_free_port(host='127.0.0.1', port_range='3000-4000')
    assert 3000 <= port <= 4000

def test_get_free_port_list_ranges_success():
    # Шаг 1: Поиск порта в списке диапазонов ['3000-4000', '8000-9000'].
    # Ожидаемое состояние: Порт в одном из диапазонов.
    port = get_free_port(host='127.0.0.1', port_range=['3000-4000', '8000-9000'])
    assert (3000 <= port <= 4000) or (8000 <= port <= 9000)

def test_get_free_port_invalid_range_format():
    # Шаг 1: Попытка передачи некорректного формата диапазона "3000-".
    # Ожидаемое состояние: Исключение ValueError.
    with pytest.raises(ValueError, match="Ошибка парсинга диапазона"):
        get_free_port(host='localhost', port_range='3000-')

def test_get_free_port_invalid_range_order():
    # Шаг 1: Попытка передачи некорректного диапазона "5000-4000" (min > max).
    # Ожидаемое состояние: Исключение ValueError.
    with pytest.raises(ValueError, match="Ошибка парсинга диапазона"):
        get_free_port(host='localhost', port_range='5000-4000')

def test_get_free_port_invalid_type():
    # Шаг 1: Попытка передачи некорректного типа данных в port_range (int).
    # Ожидаемое состояние: Исключение ValueError.
    with pytest.raises(ValueError, match="Некорректный тип диапазона"):
        get_free_port(host='localhost', port_range=123) # type: ignore
