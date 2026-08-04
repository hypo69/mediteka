# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Base Agent — базовый класс для всех агентов
# =============================================================================
# Описание:
#   Реализует агентный цикл: модель → tool_calls → выполнение → модель.
#   Каждый конкретный агент наследует BaseAgent и определяет:
#     - TOOLS       : список инструментов в формате OpenAI function calling
#     - _execute_tool : логику выполнения каждого инструмента
#
# File: src/agents/base.py
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .hitl_orchestrator import HITLOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, Any]

    def to_openai(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


@dataclass
class ToolCallResult:
    tool: str
    arguments: Dict[str, Any]
    result: str
    success: bool = True


@dataclass
class AgentResult:
    success: bool
    answer: str = ""
    tool_calls: List[ToolCallResult] = field(default_factory=list)
    iterations: int = 0
    error: str = ""
    note: str = ""


class BaseAgent(ABC):
    """
    Базовый класс агента.

    Подклассы должны определить:
      - tools: List[ToolDefinition]
      - _execute_tool(name, arguments) -> str
    """

    name: str = "base"
    description: str = ""

    def __init__(self, foundry_client):
        self.foundry_client = foundry_client
        self.hitl = HITLOrchestrator()

    @property
    @abstractmethod
    def tools(self) -> List[ToolDefinition]:
        """Список инструментов агента"""
        ...

    @abstractmethod
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Выполнить инструмент и вернуть результат как строку.

        Args:
            name: Tool name as defined in TOOLS.
            arguments: Parsed JSON arguments from the model's tool_call.

        Returns:
            str: Tool execution result as a string passed back to the model.
        """
        ...

    def tools_openai(self) -> List[Dict]:
        """Convert tool definitions to OpenAI function-calling format.

        Returns:
            List[Dict]: List of tool dicts in OpenAI {type, function} schema.
        """
        return [tool.to_openai() for tool in self.tools]

    async def run(
        self,
        user_message: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        max_iterations: int = 5,
    ) -> AgentResult:
        """Запустить агентный цикл.

        Args:
            user_message: User's input message.
            model: Foundry model ID to use.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens per model response.
            max_iterations: Maximum tool-call iterations before stopping.

        Returns:
            AgentResult: success, answer, tool_calls log, iterations count, error.
        """
        await self.foundry_client._update_base_url()
        if not self.foundry_client.base_url:
            return AgentResult(success=False, error="Foundry недоступен")

        if isinstance(model, str) and model.startswith("foundry::"):
            model = model[len("foundry::"):]

        messages = [{"role": "user", "content": user_message}]
        tool_calls_log: List[ToolCallResult] = []

        for iteration in range(max_iterations):
            logger.info(f"🤖 [{self.name}] итерация {iteration + 1}/{max_iterations}")

            payload = {
                "model": model,
                "messages": messages,
                "tools": self.tools_openai(),
                "tool_choice": "auto",
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            }

            try:
                session = await self.foundry_client._get_session()
                url = f"{self.foundry_client.base_url.rstrip('/')}/chat/completions"

                async with session.post(url, json=payload) as resp:
                    if resp.status in (400, 422):
                        # Модель не поддерживает tools — fallback
                        logger.warning(f"⚠️ [{self.name}] tools не поддерживаются, fallback")
                        payload.pop("tools", None)
                        payload.pop("tool_choice", None)
                        async with session.post(url, json=payload) as resp2:
                            if resp2.status != 200:
                                err = await resp2.text()
                                return AgentResult(success=False, error=f"HTTP {resp2.status}: {err}")
                            data = await resp2.json(content_type=None)
                        content = data["choices"][0]["message"]["content"]
                        return AgentResult(
                            success=True,
                            answer=content,
                            tool_calls=[],
                            iterations=iteration + 1,
                            note="Модель не поддерживает function calling",
                        )

                    if resp.status != 200:
                        err = await resp.text()
                        return AgentResult(success=False, error=f"HTTP {resp.status}: {err}")

                    data = await resp.json()

            except Exception as e:
                return AgentResult(success=False, error=str(e))

            choice = data["choices"][0]
            message = choice["message"]
            finish_reason = choice.get("finish_reason", "")
            messages.append(message)

            # Почему: `finish_reason` может быть `"stop"` даже при наличии `tool_calls`
            # (часть провайдеров/моделей использует `"stop"` как общий маркер конца шага).
            # Логика должна опираться на факт `tool_calls`, а не на `finish_reason`.
            tool_calls = message.get("tool_calls") or []

            # Финальный ответ — отсутствующие tool_calls
            if not tool_calls:
                return AgentResult(
                    success=True,
                    answer=message.get("content", ""),
                    tool_calls=tool_calls_log,
                    iterations=iteration + 1,
                )

            # Выполняем tool_calls
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                try:
                    fn_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    fn_args = {}

                # Проверка Human-in-the-loop (HITL)
                tool_def = next((t for t in self.tools if t.name == fn_name), None)
                tool_desc = tool_def.description if tool_def else ""
                
                if self.hitl.is_confirmation_required(fn_name, tool_desc):
                    logger.warning(f"⚠️ [{self.name}] Требуется подтверждение для: {fn_name}")
                    confirmed = await self.hitl.request_user_permission(fn_name, fn_args)
                    if not confirmed:
                        result_str = f"❌ Действие '{fn_name}' отклонено пользователем или таймаут."
                        logger.info(f"🚫 [{self.name}] {fn_name}: Отклонено")
                    else:
                        logger.info(f"🔧 [{self.name}] {fn_name}({fn_args}) [CONFIRMED]")
                        result_str = await self._execute_tool(fn_name, fn_args)
                else:
                    logger.info(f"🔧 [{self.name}] {fn_name}({fn_args})")
                    result_str = await self._execute_tool(fn_name, fn_args)

                logger.info(f"✅ [{self.name}] {fn_name}: {result_str[:80]}...")

                tcr = ToolCallResult(tool=fn_name, arguments=fn_args, result=result_str)
                tool_calls_log.append(tcr)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_str,
                })

        return AgentResult(
            success=True,
            answer="Достигнут лимит итераций",
            tool_calls=tool_calls_log,
            iterations=max_iterations,
        )
