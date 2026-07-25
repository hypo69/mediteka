# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Базовый класс плагинов
# =============================================================================
# Описание:
#   Абстрактный базовый класс для всех плагинов системы.
#   Обработка входящих сообщений с перехватом исключений.
#
# File: plugin.py
# Project: gemini-simplechat
# Package: plugins
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod

from src.logger import logger


class BasePlugin(ABC):
    """Абстрактный базовый класс для всех плагинов.

    Attributes:
        name (str): Уникальное имя плагина.
        ai: Экземпляр AI-модели.
    """

    name: str = 'base'

    def __init__(self, ai_model) -> None:
        """Инициализация плагина с AI-моделью.

        Args:
            ai_model: Экземпляр GoogleGenerativeAI или совместимой модели.

        Examples:
            >>> plugin = ConcretePlugin(ai_model)
        """
        self.ai = ai_model

    async def handle(self, message: str, **kwargs) -> str:
        """Обработка входящего сообщения с перехватом исключений.

        Args:
            message (str): Входящее текстовое сообщение.
            **kwargs: Дополнительные параметры (например, system_instruction, model_name).

        Returns:
            str: Ответ плагина или пустая строка если плагин неприменим.

        Exceptions:
            Exception: Логируется через logger, не пробрасывается выше.

        Examples:
            >>> response = await plugin.handle('скан медиатеки диск 1')
        """
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
    async def _handle(self, message: str, **kwargs) -> str:
        ...
