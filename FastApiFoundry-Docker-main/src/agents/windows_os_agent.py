# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows OS Agent — специалист по тонким настройкам Windows
# =============================================================================
# Description:
#   Агент-специалист по Windows OS. Сценарий:
#     user prompt → RAG (база знаний по Windows) → model → MCP tools → ответ
#
#   Tools:
#     - rag_search        : поиск в базе знаний по Windows
#     - get_processes     : список процессов (CPU/RAM)
#     - get_services      : службы Windows
#     - get_disk_info     : использование дисков
#     - get_network_stats : TCP соединения и адаптеры
#     - get_system_info   : ОС, CPU, RAM, uptime
#     - get_startup_items : автозагрузка
#     - kill_process      : завершить процесс по PID
#
# File: src/agents/windows_os_agent.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseAgent, ToolDefinition
from ..rag.rag_system import rag_system

logger = logging.getLogger(__name__)

_MCP_SERVER = Path("mcp/src/servers/windows_os_mcp.py")

_SYSTEM_PROMPT = (
    "Ты — эксперт по тонким настройкам операционной системы Windows. "
    "Отвечай точно, используй данные из инструментов. "
    "Если нужна дополнительная информация — вызови соответствующий инструмент. "
    "Давай практические рекомендации по оптимизации и диагностике."
)


def _call_mcp(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Call windows_os_mcp.py via STDIO JSON-RPC."""
    if not _MCP_SERVER.exists():
        return f"❌ MCP сервер не найден: {_MCP_SERVER}"

    def _send(method: str, params: Dict) -> Dict:
        payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}) + "\n"
        try:
            proc = subprocess.run(
                [sys.executable, str(_MCP_SERVER)],
                input=payload, capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=30
            )
            for line in (proc.stdout or "").splitlines():
                line = line.strip()
                if line.startswith("{"):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
            return {"error": f"No JSON. stderr={proc.stderr[:200]}"}
        except subprocess.TimeoutExpired:
            return {"error": "timeout"}
        except Exception as e:
            return {"error": str(e)}

    _send("initialize", {"protocolVersion": "2024-11-05", "clientInfo": {"name": "ai_assist", "version": "0.7.1"}, "capabilities": {}})
    resp = _send("tools/call", {"name": tool_name, "arguments": arguments})

    if "error" in resp and "result" not in resp:
        return f"❌ MCP error: {resp['error']}"
    content = resp.get("result", {}).get("content", [])
    return "\n".join(c.get("text", "") for c in content if c.get("type") == "text") or "Нет данных"


class WindowsOsAgent(BaseAgent):
    """Агент-специалист по Windows OS.

    Сценарий: prompt → RAG (контекст) → model → MCP tools (реальные данные) → ответ.
    """

    name = "windows_os"
    description = "Специалист по тонким настройкам Windows: процессы, службы, сеть, диск, автозагрузка"

    @property
    def tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="rag_search",
                description="Поиск в базе знаний по Windows OS (документация, best practices, советы)",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Поисковый запрос"},
                        "top_k": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            ),
            ToolDefinition(
                name="get_processes",
                description="Список запущенных процессов Windows (топ N по CPU или памяти)",
                parameters={
                    "type": "object",
                    "properties": {
                        "sort_by": {"type": "string", "enum": ["cpu", "memory", "name"], "default": "cpu"},
                        "top": {"type": "integer", "default": 20}
                    }
                }
            ),
            ToolDefinition(
                name="get_services",
                description="Список служб Windows с фильтром по статусу",
                parameters={
                    "type": "object",
                    "properties": {
                        "filter_status": {"type": "string", "enum": ["all", "Running", "Stopped"], "default": "all"}
                    }
                }
            ),
            ToolDefinition(
                name="get_disk_info",
                description="Использование дискового пространства",
                parameters={"type": "object", "properties": {}}
            ),
            ToolDefinition(
                name="get_network_stats",
                description="Активные TCP соединения и сетевые адаптеры",
                parameters={"type": "object", "properties": {}}
            ),
            ToolDefinition(
                name="get_system_info",
                description="Общая информация о системе: ОС, CPU, RAM, uptime",
                parameters={"type": "object", "properties": {}}
            ),
            ToolDefinition(
                name="get_startup_items",
                description="Программы в автозагрузке Windows",
                parameters={"type": "object", "properties": {}}
            ),
            ToolDefinition(
                name="kill_process",
                description="Завершить процесс по PID",
                parameters={
                    "type": "object",
                    "properties": {"pid": {"type": "integer"}},
                    "required": ["pid"]
                }
            ),
        ]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute tool by name.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            str: Tool result.
        """
        if name == "rag_search":
            return await self._rag_search(arguments)

        # All other tools delegate to MCP server
        return _call_mcp(name, arguments)

    async def _rag_search(self, args: Dict[str, Any]) -> str:
        """Search RAG index for Windows OS knowledge.

        Args:
            args: query (str), top_k (int, optional).

        Returns:
            str: Found context or message about empty results.
        """
        query: str = args.get("query", "")
        top_k: int = int(args.get("top_k", 5))

        if not query.strip():
            return "❌ Пустой запрос"

        if not rag_system.index:
            return "⚠️ RAG-индекс не загружен"

        results = await rag_system.search(query, top_k=top_k)
        if not results:
            return "Релевантная информация в базе знаний не найдена"

        context = rag_system.format_context(results)
        sources = list({r.get("source", "unknown") for r in results})
        logger.info(f"✅ [windows_os] RAG: {len(results)} фрагментов для '{query[:60]}'")
        return f"Найдено: {len(results)} фрагментов. Источники: {', '.join(sources)}\n\n{context}"

    async def run(self, user_message: str, model: str, **kwargs: object) -> Any:
        """Inject system prompt before running the agent loop.

        Args:
            user_message: User's question.
            model: Model ID.
            **kwargs: Passed to BaseAgent.run.

        Returns:
            AgentResult
        """
        # Prepend system context to user message
        enriched = f"{_SYSTEM_PROMPT}\n\nЗапрос пользователя: {user_message}"
        return await super().run(enriched, model, **kwargs)
