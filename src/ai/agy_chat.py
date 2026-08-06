# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Интеграция Antigravity SDK
# =============================================================================
# Описание:
#   Адаптер для взаимодействия с моделями Antigravity SDK (agy-flash, agy-pro).
#   Поддерживает потоковую генерацию (chat_stream) и одиночные запросы (ask).
#
# File: agy_chat.py
# Project: mediteka
# Package: src.ai
# Class: AgyChatBase
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import asyncio
from typing import Optional, List, Dict, AsyncGenerator

from google.antigravity import Agent, LocalAgentConfig
from src.logger.logger import logger
from src.secrets.api_key_state import load_api_keys


class AgyChatBase:
    """Обеспечение соединения и маршрутизации запросов к моделям Antigravity SDK.

    Реализует базовые интерфейсы чата (ask, chat_stream) для обеспечения
    совместимости с текущей архитектурой роутера FastAPI.

    Attributes:
        model_id (str): Идентификатор модели (например, agy-flash).
        system_instruction (str): Базовые системные инструкции для LLM.
        history (List[Dict[str, str]]): Локальная история диалога.
        api_key (str): Активный API ключ для инициализации агента.
    """

    def __init__(self, model_id: str, system_prompt: str = "") -> None:
        """Инициализация объекта подключения к AGY SDK."""
        self.model_id: str = model_id
        self.system_instruction: str = system_prompt
        self.history: List[Dict[str, str]] = []
        
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        # Сначала ищем специализированный ключ для AGY
        self.api_key = os.getenv('AGY_API_KEY', '').strip()
        
        # Если его нет, пытаемся взять из пула Gemini
        if not self.api_key:
            _api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
            api_keys, _, _ = load_api_keys(_api_key_names or None)
            self.api_key = api_keys[0] if api_keys else ""

    def clear_history(self) -> None:
        """Очистка локальной истории чата."""
        self.history = []

    async def ask(self, q: str, **kwargs) -> Optional[str]:
        """Отправка одиночного запроса к агенту.

        Args:
            q (str): Текстовый запрос пользователя.

        Returns:
            Optional[str]: Ответ модели в виде сплошного текста или None при ошибке.

        Exceptions:
            Exception: Любые сбои в SDK логируются и возвращают None.

        Examples:
            >>> chat = AgyChatBase('agy-flash', 'You are a helpful assistant')
            >>> answer = await chat.ask('Hello')
        """
        if not q or not q.strip():
            return None

        try:
            config = LocalAgentConfig(
                model=self.model_id,
                system_instructions=self.system_instruction,
                api_key=self.api_key
            )
            async with Agent(config) as agent:
                response = await agent.chat(q)
                text = ""
                async for token in response:
                    text += token
                return text
        except Exception as e:
            logger.error("Ошибка в AgyChatBase.ask", e, exc_info=True)
            return None

    async def chat_stream(
        self,
        q: str,
        history: Optional[List[Dict]] = None,
        system_instruction: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Отправка потокового запроса к агенту.

        Args:
            q (str): Текстовый запрос пользователя.
            history (Optional[List[Dict]]): Опциональная история диалога.
            system_instruction (Optional[str]): Переопределение системной инструкции.

        Yields:
            str: Фрагменты текста по мере генерации ответа.

        Exceptions:
            Exception: В случае ошибки стриминг возвращает сообщение об ошибке как строку.

        Examples:
            >>> chat = AgyChatBase('agy-flash')
            >>> async for chunk in chat.chat_stream('Расскажи сказку'):
            >>>     print(chunk)
        """
        if not q or not q.strip():
            return

        sys_prompt = system_instruction or self.system_instruction
        
        # Интеграция истории в контекст
        context = ""
        if history:
            for msg in history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if not content and 'parts' in msg:
                    content = " ".join([p.get('text', '') if isinstance(p, dict) else str(p) for p in msg['parts']])
                context += f"\n[{role}]: {content}"

        if context:
            sys_prompt = f"{sys_prompt}\n\nИстория диалога:\n{context}"

        try:
            config = LocalAgentConfig(
                model=self.model_id,
                system_instructions=sys_prompt,
                api_key=self.api_key
            )
            async with Agent(config) as agent:
                response = await agent.chat(q)
                async for token in response:
                    yield token
        except Exception as e:
            err_msg = f"Ошибка Antigravity SDK: {str(e)}"
            logger.error(err_msg, e, exc_info=True)
            yield err_msg
