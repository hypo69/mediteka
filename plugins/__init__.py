# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Динамическая загрузка плагинов
# =============================================================================
# Описание:
#   Обход поддиректорий plugins/ и импорт каждого плагина через importlib.
#   Регистрация плагинов в словаре по имени.
#   Считывание и синхронизация состояния активности плагинов с config.json.
#
# File: __init__.py
# Project: gemini-simplechat
# Package: plugins
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from header import __root__
from src.logger import logger
from .plugin import BasePlugin


def _get_plugins_config() -> Dict[str, Any]:
    """Считывает настройки плагинов из config.json."""
    try:
        cfg_path = __root__ / 'config.json'
        if cfg_path.exists():
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                return cfg.get('plugins', {})
    except Exception as ex:
        logger.warning(f"Ошибка чтения блока plugins из config.json: {ex}")
    return {}


def load_plugins(ai_model) -> dict[str, BasePlugin]:
    """Динамическая загрузка всех плагинов из поддиректорий plugins/.

    Считывает состояние enabled из config.json и переменной окружения DISABLED_PLUGINS.

    Args:
        ai_model: Экземпляр AI-модели, передаваемый каждому плагину.

    Returns:
        dict[str, BasePlugin]: Словарь загруженных плагинов {name: instance}.

    Examples:
        >>> plugins = load_plugins(model)
    """
    disabled_raw = os.getenv('DISABLED_PLUGINS', '')
    disabled_env = {p.strip().lower() for p in disabled_raw.split(',') if p.strip()}
    plugins_cfg = _get_plugins_config()

    plugins: dict[str, BasePlugin] = {}
    plugins_dir = Path(__file__).parent

    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir() or plugin_dir.name.startswith('_'):
            continue

        plugin_folder_name = plugin_dir.name
        try:
            module = importlib.import_module(f'plugins.{plugin_folder_name}')
            if not hasattr(module, 'plugin'):
                logger.warning(f"Модуль 'plugins.{plugin_folder_name}' не содержит фабрики 'plugin'")
                continue

            plugin_factory = getattr(module, 'plugin')
            plugin_instance: BasePlugin = plugin_factory(ai_model)

            p_name = plugin_instance.name

            # Определение статуса активности (enabled)
            is_disabled_by_env = plugin_folder_name.lower() in disabled_env or p_name.lower() in disabled_env
            cfg_entry = plugins_cfg.get(p_name, {})
            is_enabled_by_cfg = True
            if isinstance(cfg_entry, dict) and 'enabled' in cfg_entry:
                is_enabled_by_cfg = bool(cfg_entry['enabled'])

            plugin_instance.enabled = (not is_disabled_by_env) and is_enabled_by_cfg
            plugins[p_name] = plugin_instance
            logger.info(f"Плагин '{p_name}' загружен (enabled={plugin_instance.enabled})")

        except Exception as ex:
            logger.warning(f"Загрузка плагина '{plugin_folder_name}' завершилась ошибкой", ex)

    return plugins


def get_all_plugins_registry(plugins: dict[str, BasePlugin]) -> List[Dict[str, Any]]:
    """Возвращает список манифестов всех зарегистрированных плагинов."""
    registry: List[Dict[str, Any]] = []
    for name, plugin_instance in plugins.items():
        try:
            manifest = plugin_instance.get_manifest()
            registry.append(manifest)
        except Exception as ex:
            logger.error(f"Ошибка получения манифеста для плагина {name}: {ex}")
            registry.append({
                'name': name,
                'title': name,
                'description': '',
                'icon': '🧩',
                'version': '1.0.0',
                'category': 'tools',
                'enabled': plugin_instance.enabled,
                'fields': [],
                'actions': [],
            })
    return registry

