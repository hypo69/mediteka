# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: RAG Agent — агент с доступом к векторному поиску
# =============================================================================
# Description:
#   Агент, который умеет искать контекст в RAG-индексе и формировать ответ
#   на основе найденных фрагментов через локальную модель Foundry.
#
#   Tools:
#     - rag_search     : поиск релевантных фрагментов в FAISS-индексе
#     - generate_answer: генерация ответа на основе контекста и вопроса
#
# File: src/agents/rag_agent.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
from typing import Any, Dict, List

from .base import BaseAgent, ToolDefinition
from ..rag.rag_system import rag_system

logger = logging.getLogger(__name__)


class RagAgent(BaseAgent):
    """Агент для ответов на вопросы с использованием RAG-контекста."""

    name = "rag"
    description = "Ищет релевантный контекст в базе знаний (RAG) и отвечает на вопросы"

    @property
    def tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="rag_search",
                description="Поиск релевантных фрагментов в базе знаний по запросу",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Поисковый запрос для векторного поиска"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Количество результатов (по умолчанию 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            ),
            ToolDefinition(
                name="generate_answer",
                description="Сформировать финальный ответ на основе найденного контекста",
                parameters={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Исходный вопрос пользователя"
                        },
                        "context": {
                            "type": "string",
                            "description": "Контекст из базы знаний для формирования ответа"
                        }
                    },
                    "required": ["question", "context"]
                }
            ),
        ]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Выполнить инструмент агента.

        Args:
            name (str): Имя инструмента ('rag_search' или 'generate_answer').
            arguments (Dict[str, Any]): Аргументы вызова.

        Returns:
            str: Результат выполнения инструмента.
        """
        if name == "rag_search":
            return await self._rag_search(arguments)
        if name == "generate_answer":
            return self._format_answer(arguments)
        return f"❌ Неизвестный инструмент: {name}"

    async def _rag_search(self, args: Dict[str, Any]) -> str:
        """Поиск в RAG-индексе.

        Args:
            args (Dict[str, Any]): query (str), top_k (int, optional).

        Returns:
            str: Найденные фрагменты или сообщение об отсутствии результатов.
        """
        query: str = args.get("query", "")
        top_k: int = int(args.get("top_k", 5))

        if not query.strip():
            return "❌ Пустой запрос"

        if not rag_system.index:
            return "⚠️ RAG-индекс не загружен. Загрузите документы через /api/v1/rag/index"

        results = await rag_system.search(query, top_k=top_k)

        if not results:
            return "Релевантные фрагменты не найдены"

        context = rag_system.format_context(results)
        sources = list({r.get("source", "unknown") for r in results})
        logger.info(f"✅ [rag] найдено {len(results)} фрагментов для: '{query[:60]}'")

        return f"Найдено фрагментов: {len(results)}\nИсточники: {', '.join(sources)}\n\n{context}"

    def _format_answer(self, args: Dict[str, Any]) -> str:
        """Форматирует промпт для финального ответа.

        Модель получит этот текст как результат tool_call и сформирует ответ.

        Args:
            args (Dict[str, Any]): question (str), context (str).

        Returns:
            str: Инструкция для модели с вопросом и контекстом.
        """
        question: str = args.get("question", "")
        context: str = args.get("context", "")

        return (
            f"Вопрос: {question}\n\n"
            f"Контекст из базы знаний:\n{context}\n\n"
            "Ответь на вопрос, опираясь только на предоставленный контекст. "
            "Если контекст не содержит ответа — скажи об этом явно."
        )
