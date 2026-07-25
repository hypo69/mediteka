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
from src.utils.get_free_port import get_free_port

def test_get_free_port_no_range():
    # Шаг 1: Поиск первого доступного порта без ограничений диапазона.
    # Ожидаемое состояние: Возвращается целое число (порт >= 1024).
    port = get_free_port(host='localhost')
    assert isinstance(port, int)
    assert port >= 1024

def test_get_free_port_single_range_success():
    # Шаг 1: Поиск порта в заданном диапазоне 3000-3005.
    # Ожидаемое состояние: Порт в диапазоне [3000, 3005].
    port = get_free_port(host='localhost', port_range='3000-3005')
    assert 3000 <= port <= 3005

def test_get_free_port_list_ranges_success():
    # Шаг 1: Поиск порта в списке диапазонов ['3000-3001', '8000-8001'].
    # Ожидаемое состояние: Порт в одном из диапазонов.
    port = get_free_port(host='localhost', port_range=['3000-3001', '8000-8001'])
    assert (3000 <= port <= 3001) or (8000 <= port <= 8001)

def test_get_free_port_invalid_range_format():
    # Шаг 1: Попытка передачи некорректного формата диапазона "3000-".
    # Ожидаемое состояние: Исключение ValueError.
    with pytest.raises(ValueError, match="Некорректный формат диапазона"):
        get_free_port(host='localhost', port_range='3000-')

def test_get_free_port_invalid_range_order():
    # Шаг 1: Попытка передачи некорректного диапазона "5000-4000" (min > max).
    # Ожидаемое состояние: Исключение ValueError.
    with pytest.raises(ValueError, match="Некорректный диапазон"):
        get_free_port(host='localhost', port_range='5000-4000')

def test_get_free_port_invalid_type():
    # Шаг 1: Попытка передачи некорректного типа данных в port_range (int).
    # Ожидаемое состояние: Исключение ValueError.
    with pytest.raises(ValueError, match="Некорректный тип диапазона"):
        get_free_port(host='localhost', port_range=123) # type: ignore
