# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Инициализация плагина langchain_media
# =============================================================================
# Описание:
#   Экспортирует класс плагина для автоматической загрузки системой.
#
# File: __init__.py
# Project: mediteka
# Package: plugins.langchain_media
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .langchain_media import LangChainMediaPlugin

def plugin(ai_model):
    """Фабрика для создания экземпляра плагина.
    Вызывается загрузчиком в plugins/__init__.py
    """
    return LangChainMediaPlugin(ai_model)
