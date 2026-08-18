# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Gemini CLI Web Search Provider
# =============================================================================
# Описание:
#   Модуль веб-поиска через локальный терминальный агент Google Gemini CLI
#   с использованием GeminiCliChatBase для извлечения актуальных фактов,
#   новостей и источников из интернета.
#
# File: gemini_cli_searcher.py
# Project: mediteka
# Package: plugins.web_search
# Class: GeminiCliWebSearcher
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
from pathlib import Path
from typing import List, Dict, Any

from header import __root__
from src.logger.logger import logger
from src.ai.gemini_cli_chat import GeminiCliChatBase


class GeminiCliWebSearcher:
    """Провайдер веб-поиска через локальный инструмент Google Gemini CLI."""

    _DEFAULT_MODEL: str = "gemini-3.1-flash-lite"

    def __init__(self, model_id: str = "") -> None:
        """Инициализация поисковика Gemini CLI.

        Args:
            model_id: Идентификатор модели (если пусто, читается из config.json).
        """
        self._configured_model = model_id.strip()
        effective_model = self._configured_model or self._get_config_model()
        self._model_id: str = GeminiCliChatBase.normalize_model_id(effective_model)
        self._chat_client: GeminiCliChatBase = GeminiCliChatBase(
            model_id=self._model_id,
            system_prompt=self._get_default_system_instruction(),
        )

    def _get_default_system_instruction(self) -> str:
        """Возвращает системную инструкцию для поискового агента Gemini CLI."""
        return (
            "Ты — модуль автономного веб-поиска на базе Google Gemini CLI. "
            "Твоя задача — использовать веб-поиск для нахождения актуальной информации "
            "по запросу пользователя, структурировать факты и обязательно предоставить "
            "ссылки на источники информации на русском языке."
        )

    def _get_config_model(self) -> str:
        """Получение идентификатора модели из config.json.

        Returns:
            str: Название модели из конфигурации или _DEFAULT_MODEL при отсутствии.
        """
        cfg_path: Path = __root__ / "config.json"
        if not cfg_path.exists():
            return self._DEFAULT_MODEL

        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                ws = cfg.get("web_search", {})
                return ws.get("gemini_cli_model", self._DEFAULT_MODEL)
        except Exception as e:
            logger.warning(f"[GeminiCliWebSearcher] Ошибка чтения config.json: {e}")
            return self._DEFAULT_MODEL

    @property
    def model_id(self) -> str:
        """Получение текущего идентификатора модели."""
        return self._model_id

    @model_id.setter
    def model_id(self, val: str) -> None:
        """Установка и нормализация идентификатора модели."""
        norm_val = GeminiCliChatBase.normalize_model_id(val)
        self._model_id = norm_val
        self._chat_client.model_id = norm_val

    def _clean_output(self, raw_text: str) -> str:
        """Очистка вывода CLI от служебных сообщений.

        Args:
            raw_text: Сырой текстовый ответ от CLI.

        Returns:
            str: Очищенный текст для ответа.
        """
        if not raw_text or not raw_text.strip():
            return ""

        lines = raw_text.strip().splitlines()
        filtered_lines: List[str] = []
        for line in lines:
            if line.startswith("YOLO mode is enabled") or line.startswith("Loaded extension:"):
                continue
            filtered_lines.append(line)

        return "\n".join(filtered_lines).strip()

    async def search_and_extract(self, query: str, model: str = "") -> str:
        """Выполнение веб-поиска и извлечение данных через Gemini CLI.

        Args:
            query: Текстовый поисковый запрос пользователя.
            model: Опциональное переопределение модели.

        Returns:
            str: Сформированный контекст поиска с текстом и источниками.
        """
        clean_query = query.strip()
        if not clean_query:
            return "Пустой поисковый запрос."

        effective_model = model.strip() or self._model_id or self._get_config_model()
        normalized_model = GeminiCliChatBase.normalize_model_id(effective_model)
        self._chat_client.model_id = normalized_model

        prompt = (
            f"Найди актуальную, достоверную информацию в интернете по следующему запросу "
            f"и составь подробную выжимку фактов с указанием деталей и ссылок на источники:\n\n"
            f"Запрос: {clean_query}"
        )

        try:
            logger.info(f"[GeminiCliWebSearcher] Поиск через Gemini CLI (модель: {normalized_model}): '{clean_query}'")
            raw_result = await self._chat_client.ask(
                prompt,
                system_instruction=self._get_default_system_instruction(),
            )
            cleaned = self._clean_output(raw_result)
            if cleaned:
                return cleaned

            return f"Результаты поиска Gemini CLI по запросу '{clean_query}' не найдены."
        except Exception as e:
            logger.error(f"[GeminiCliWebSearcher] Ошибка поиска Gemini CLI: {e}")
            return f"Ошибка выполнения поиска через Gemini CLI: {str(e)}"
