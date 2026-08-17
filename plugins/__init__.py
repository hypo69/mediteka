# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Динамическая загрузка плагинов
# =============================================================================
# Описание:
#   Обход поддиректорий plugins/ и импорт каждого плагина через importlib.
#   Регистрация плагинов в словаре по имени.
#   Плагины из DISABLED_PLUGINS (env, через запятую) пропускаются.
#
# File: __init__.py
# Project: gemini-simplechat
# Package: plugins
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import importlib
import os
from pathlib import Path

from src.logger import logger
from .plugin import BasePlugin


def load_plugins(ai_model) -> dict[str, BasePlugin]:
    """Динамическая загрузка всех плагинов из поддиректорий plugins/.

    Плагины, перечисленные в переменной окружения DISABLED_PLUGINS
    (через запятую), пропускаются при загрузке.

    Args:
        ai_model: Экземпляр AI-модели, передаваемый каждому плагину.

    Returns:
        dict[str, BasePlugin]: Словарь загруженных плагинов {name: instance}.

    Examples:
        >>> plugins = load_plugins(model)
    """
    disabled_raw = os.getenv('DISABLED_PLUGINS', '')
    disabled = {p.strip().lower() for p in disabled_raw.split(',') if p.strip()}
    if disabled:
        logger.info(f"Отключённые плагины (DISABLED_PLUGINS): {disabled}")

    plugins: dict[str, BasePlugin] = {}
    plugins_dir = Path(__file__).parent

    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir() or plugin_dir.name.startswith('_'):
            continue
        if plugin_dir.name.lower() in disabled:
            logger.info(f"Плагин '{plugin_dir.name}' отключён (DISABLED_PLUGINS)")
            continue
        try:
            module = importlib.import_module(f'plugins.{plugin_dir.name}')
            plugin: BasePlugin = module.plugin(ai_model)
            plugins[plugin.name] = plugin
        except Exception as ex:
            logger.warning(f"Загрузка плагина '{plugin_dir.name}' завершилась ошибкой", ex)

    return plugins
