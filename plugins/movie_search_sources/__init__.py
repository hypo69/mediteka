# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Инициализация плагина movie_search_sources
# =============================================================================
# Описание:
#   Экспортирует класс плагина для автоматической загрузки системой.
#
# File: __init__.py
# Project: mediteka
# Package: plugins.movie_search_sources
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .movie_search_sources import MovieSearchSourcesPlugin

def plugin(ai_model):
    """
    Фабрика для создания экземпляра плагина.
    Вызывается загрузчиком в plugins/__init__.py
    """
    return MovieSearchSourcesPlugin(ai_model)
