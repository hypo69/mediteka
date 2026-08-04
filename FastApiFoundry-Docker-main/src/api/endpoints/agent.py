# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Agent Endpoints — роутер для агентов
# =============================================================================
# Описание:
#   Тонкий роутер. Вся логика агентов — в src/agents/.
#   Добавить нового агента:
#     1. Создать src/agents/my_agent.py (наследовать BaseAgent)
#     2. Зарегистрировать в AGENTS ниже
#
# File: src/api/endpoints/agent.py
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...models.foundry_client import foundry_client
from ...agents.powershell_agent import PowerShellAgent
from ...agents.rag_agent import RagAgent
from ...agents.keystroke_agent import KeystrokeAgent
from ...agents.mcp_agent import McpAgent
from ...agents.windows_os_agent import WindowsOsAgent
from ...agents.computer_admin_agent import ComputerAdminAgent
from ...agents.recommender_agent import RecommenderAgent
from ...agents.google_agent import GoogleAgent

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Реестр агентов ────────────────────────────────────────────────────────────
# Чтобы добавить нового агента — добавь его сюда:
#   "my_agent": MyAgent(foundry_client)

def _build_registry():
    return {
        "powershell": PowerShellAgent(foundry_client),
        "rag": RagAgent(foundry_client),
        "keystroke": KeystrokeAgent(foundry_client),
        "mcp": McpAgent(foundry_client),
        "windows_os": WindowsOsAgent(foundry_client),
        "computer_admin": ComputerAdminAgent(foundry_client),
        "recommender": RecommenderAgent(foundry_client),
        "google": GoogleAgent(foundry_client),
    }

_registry = None

def get_registry():
    global _registry
    if _registry is None:
        _registry = _build_registry()
    return _registry


def select_agent_name(message: str, requested_agent: str, registry: dict) -> str:
    """Select an agent for auto mode.

    The first implementation routes OS administration tasks to ComputerAdminAgent.
    It is intentionally small while the system has one autonomous diagnostic agent.
    """
    if requested_agent and requested_agent != "auto":
        return requested_agent

    if "computer_admin" in registry:
        return "computer_admin"
    if registry:
        return next(iter(registry.keys()))
    return requested_agent


# ── Schemas ───────────────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    message: str
    agent: str = "auto"
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    max_iterations: int = 5


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/agent/list")
async def list_agents():
    """Список зарегистрированных агентов"""
    registry = get_registry()
    return {
        "success": True,
        "agents": [
            {"name": a.name, "description": a.description}
            for a in registry.values()
        ]
    }


@router.get("/agent/{agent_name}/tools")
async def list_agent_tools(agent_name: str):
    """Список инструментов конкретного агента"""
    registry = get_registry()
    agent = registry.get(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return {
        "success": True,
        "agent": agent_name,
        "tools": [t.name for t in agent.tools],
        "descriptions": {t.name: t.description for t in agent.tools}
    }


@router.post("/agent/run")
async def run_agent(request: AgentRequest):
    """
    Запустить агента.

    Агент сам решает какие инструменты вызвать для ответа на вопрос.
    По умолчанию используется агент 'powershell'.
    """
    from ...core.config import config

    registry = get_registry()
    selected_agent = select_agent_name(request.message, request.agent, registry)
    agent = registry.get(selected_agent)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{selected_agent}' not found. Available: {list(registry.keys())}")

    model = request.model or config.foundry_default_model
    if not model:
        raise HTTPException(status_code=400, detail="Модель не указана и не задана в config.json")

    logger.info(f"🤖 Agent '{selected_agent}' запущен: '{request.message[:60]}' model={model}")

    result = await agent.run(
        user_message=request.message,
        model=model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        max_iterations=request.max_iterations,
    )

    return {
        "success": result.success,
        "answer": result.answer,
        "tool_calls": [
            {"tool": tc.tool, "arguments": tc.arguments, "result": tc.result}
            for tc in result.tool_calls
        ],
        "iterations": result.iterations,
        "agent": request.agent,
        "selected_agent": selected_agent,
        **({"error": result.error} if result.error else {}),
        **({"note": result.note} if result.note else {}),
    }
