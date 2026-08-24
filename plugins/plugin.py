# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Базовый класс плагинов
# =============================================================================
# Описание:
#   Абстрактный базовый класс для всех плагинов системы.
#   Обработка входящих сообщений с перехватом исключений,
#   управление конфигурацией, манифестами настроек и действиями.
#
# File: plugin.py
# Project: gemini-simplechat
# Package: plugins
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from header import __root__
from src.logger import logger


class BasePlugin(ABC):
    """Абстрактный базовый класс для всех плагинов.

    Attributes:
        name (str): Уникальный системный идентификатор плагина.
        title (str): Человекочитаемое название плагина.
        description (str): Краткое описание назначения плагина.
        icon (str): Эмодзи или иконка Bootstrap/клиента.
        version (str): Версия плагина.
        category (str): Категория плагина (media, search, system, ai, tools).
        enabled (bool): Флаг активности плагина.
        ai: Экземпляр AI-модели.
    """

    name: str = 'base'
    title: str = 'Базовый плагин'
    description: str = 'Базовый функциональный плагин'
    icon: str = '🧩'
    version: str = '1.0.0'
    category: str = 'tools'
    enabled: bool = True

    def __init__(self, ai_model) -> None:
        """Инициализация плагина с AI-моделью.

        Args:
            ai_model: Экземпляр GoogleGenerativeAI или совместимой модели.

        Examples:
            >>> plugin = ConcretePlugin(ai_model)
        """
        self.ai = ai_model

    def can_handle(self, message: str) -> bool:
        """Проверяет, может ли плагин обработать сообщение.

        По умолчанию возвращает True. Плагины могут переопределить этот метод,
        чтобы избежать холостых вызовов в чат-роутере.
        """
        return self.enabled

    def get_config(self) -> Dict[str, Any]:
        """Возвращает текущую конфигурацию плагина из config.json."""
        try:
            cfg_path = __root__ / 'config.json'
            if cfg_path.exists():
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    plugins_block = cfg.get('plugins', {})
                    if isinstance(plugins_block, dict) and self.name in plugins_block:
                        return plugins_block[self.name]
                    # Fallback для существующих секций config.json
                    if self.name in cfg and isinstance(cfg[self.name], dict):
                        return cfg[self.name]
        except Exception as ex:
            logger.warning(f"[{self.name}] Ошибка чтения конфигурации: {ex}")
        return {}

    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Сохраняет обновленную конфигурацию плагина в config.json."""
        try:
            cfg_path = __root__ / 'config.json'
            cfg: Dict[str, Any] = {}
            if cfg_path.exists():
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)

            if 'plugins' not in cfg:
                cfg['plugins'] = {}

            current = cfg['plugins'].get(self.name, {})
            if isinstance(current, dict):
                current.update(new_config)
                cfg['plugins'][self.name] = current
            else:
                cfg['plugins'][self.name] = new_config

            # Также обновляем профильную секцию верхнего уровня если она существует
            if self.name in cfg and isinstance(cfg[self.name], dict):
                cfg[self.name].update(new_config)

            with open(cfg_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)

            return cfg['plugins'][self.name]
        except Exception as ex:
            logger.error(f"[{self.name}] Ошибка сохранения конфигурации: {ex}")
            return {}

    def get_manifest(self) -> Dict[str, Any]:
        """Возвращает манифест настроек и доступных действий для отображения в UI."""
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'version': self.version,
            'category': self.category,
            'enabled': self.enabled,
            'config': self.get_config(),
            'fields': [],
            'actions': [],
        }

    async def execute_action(self, action_name: str, params: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Выполняет специфическое действие плагина (например, сканирование, тест)."""
        method_name = f"action_{action_name}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            import inspect
            if inspect.iscoroutinefunction(method):
                return await method(params)
            else:
                return method(params)
        return {
            'success': False,
            'message': f"Действие '{action_name}' не поддерживается плагином {self.name}",
        }

    async def handle(self, message: str, **kwargs) -> Any:
        """Обработка входящего сообщения с перехватом исключений.

        Args:
            message (str): Входящее текстовое сообщение.
            **kwargs: Дополнительные параметры.

        Returns:
            Any: Результат обработки плагина или пустая строка.
        """
        if not self.enabled:
            return ''

        try:
            import inspect
            sig = inspect.signature(self._handle)
            if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
                res = self._handle(message, **kwargs)
            else:
                filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
                res = self._handle(message, **filtered_kwargs)

            if inspect.isasyncgen(res):
                return res
            else:
                return await res or ''
        except Exception as ex:
            logger.error(f'[{self.name}] Ошибка обработки сообщения', ex)
            return ''

    @abstractmethod
    async def _handle(self, message: str, **kwargs) -> Any:
        ...

