# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Computer Admin Agent — локальный администратор компьютера
# =============================================================================
# Description:
#   Агент администратора компьютера поверх typed Windows MCP tools.
#   Делает диагностику, инвентаризацию и ограниченные административные действия.
#
# File: src/agents/computer_admin_agent.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# =============================================================================

from typing import Any, Dict, List

from .base import BaseAgent, ToolDefinition
from .windows_os_agent import _call_mcp


_SYSTEM_PROMPT = (
    "Ты — ИИ-агент администратора локального Windows-компьютера. "
    "Твоя задача — помогать пользователю диагностировать состояние ПК, "
    "находить причины проблем, давать понятные рекомендации и выполнять "
    "только аккуратные административные действия через доступные инструменты. "
    "Работай в порядке 1 -> 2 -> 4 -> 3: сначала time-series/snapshot, затем rule engine, "
    "затем health scoring и correlation/root-cause summary, затем reasoning loop с моделью. "
    "Сначала собирай факты через invoke_os_diagnostic: система, диски, процессы, службы, "
    "события, защита, обновления и историю состояния. "
    "Если стандартных инструментов недостаточно, ты можешь сам составить diagnostic-only скрипт "
    "и выбрать язык: PowerShell для WMI/CIM, реестра, Event Log, служб и тонких настроек Windows; "
    "Python для анализа JSON/time-series, агрегаций, scoring, отчетов и проверки файлов проекта. "
    "Перед запуском кратко объясняй reason выбора языка в аргументе инструмента. "
    "Опасные действия вроде остановки службы, завершения процесса или удаления файлов "
    "выполняй только если пользователь явно попросил это сделать. Для очистки сначала "
    "используй dry_run=true и покажи пользователю, что будет удалено. "
    "Не придумывай результаты: если инструмент вернул ошибку или пустой ответ, так и скажи."
)


class ComputerAdminAgent(BaseAgent):
    """ИИ-агент для администрирования локального Windows-компьютера."""

    name = "computer_admin"
    description = "Администрирует Windows-компьютер: диагностика, службы, процессы, диски, события, обновления, Defender"

    @property
    def tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="invoke_os_diagnostic",
                description=(
                    "Запустить production PowerShell toolkit: snapshot, time-series JSONL, "
                    "rule engine, correlation, health score, JSON/HTML/RST отчеты"
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "output_dir": {"type": "string", "description": "Папка для отчетов. Пусто = logs/os_diagnostic"},
                        "window_hours": {"type": "integer", "default": 24, "minimum": 1, "maximum": 720},
                        "skip_events": {"type": "boolean", "default": False},
                        "no_store": {"type": "boolean", "default": False},
                    },
                },
            ),
            ToolDefinition(
                name="run_powershell_check",
                description=(
                    "Выполнить временный PowerShell diagnostic-only скрипт, созданный моделью. "
                    "Выбирай для WMI/CIM, Event Log, служб, реестра и Windows-настроек"
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "script": {"type": "string", "description": "PowerShell код только для диагностики и чтения данных"},
                        "timeout_seconds": {"type": "integer", "default": 30, "minimum": 1, "maximum": 120},
                        "reason": {"type": "string", "description": "Почему выбран PowerShell"},
                    },
                    "required": ["script"],
                },
            ),
            ToolDefinition(
                name="run_python_check",
                description=(
                    "Выполнить временный Python diagnostic-only скрипт, созданный моделью. "
                    "Выбирай для анализа JSON/time-series, вычислений, агрегаций и отчетов"
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "script": {"type": "string", "description": "Python код только для диагностики, чтения и анализа"},
                        "timeout_seconds": {"type": "integer", "default": 30, "minimum": 1, "maximum": 120},
                        "reason": {"type": "string", "description": "Почему выбран Python"},
                    },
                    "required": ["script"],
                },
            ),
            ToolDefinition(
                name="get_system_info",
                description="Получить общую информацию о системе: ОС, CPU, RAM, uptime",
                parameters={"type": "object", "properties": {}},
            ),
            ToolDefinition(
                name="get_disk_info",
                description="Показать использование дискового пространства по всем дискам",
                parameters={"type": "object", "properties": {}},
            ),
            ToolDefinition(
                name="get_processes",
                description="Показать топ процессов Windows по CPU, памяти или имени",
                parameters={
                    "type": "object",
                    "properties": {
                        "sort_by": {"type": "string", "enum": ["cpu", "memory", "name"], "default": "cpu"},
                        "top": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100},
                    },
                },
            ),
            ToolDefinition(
                name="get_services",
                description="Показать службы Windows с фильтром по статусу",
                parameters={
                    "type": "object",
                    "properties": {
                        "filter_status": {"type": "string", "enum": ["all", "Running", "Stopped"], "default": "all"}
                    },
                },
            ),
            ToolDefinition(
                name="get_event_logs",
                description="Получить последние события Windows Event Log по журналу и уровню",
                parameters={
                    "type": "object",
                    "properties": {
                        "log_name": {"type": "string", "enum": ["System", "Application", "Security"], "default": "System"},
                        "level": {"type": "string", "enum": ["Critical", "Error", "Warning", "Information"], "default": "Error"},
                        "newest": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100},
                    },
                },
            ),
            ToolDefinition(
                name="get_network_stats",
                description="Показать активные TCP соединения и сетевые адаптеры",
                parameters={"type": "object", "properties": {}},
            ),
            ToolDefinition(
                name="get_startup_items",
                description="Показать программы в автозагрузке Windows",
                parameters={"type": "object", "properties": {}},
            ),
            ToolDefinition(
                name="get_installed_apps",
                description="Показать установленные приложения Windows",
                parameters={"type": "object", "properties": {}},
            ),
            ToolDefinition(
                name="get_local_users",
                description="Показать локальных пользователей Windows и состояние учетных записей",
                parameters={"type": "object", "properties": {}},
            ),
            ToolDefinition(
                name="get_scheduled_tasks",
                description="Показать задания планировщика Windows",
                parameters={
                    "type": "object",
                    "properties": {
                        "task_state": {"type": "string", "enum": ["all", "Ready", "Running", "Disabled"], "default": "all"}
                    },
                },
            ),
            ToolDefinition(
                name="get_defender_status",
                description="Показать состояние Microsoft Defender",
                parameters={"type": "object", "properties": {}},
            ),
            ToolDefinition(
                name="get_windows_update_status",
                description="Показать состояние Windows Update и последние обновления",
                parameters={"type": "object", "properties": {}},
            ),
            ToolDefinition(
                name="control_service",
                description="Запустить, остановить или перезапустить службу Windows по имени",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Service name, e.g. wuauserv"},
                        "action": {"type": "string", "enum": ["start", "stop", "restart"]},
                    },
                    "required": ["name", "action"],
                },
            ),
            ToolDefinition(
                name="kill_process",
                description="Завершить процесс по PID, только по явной просьбе пользователя",
                parameters={
                    "type": "object",
                    "properties": {"pid": {"type": "integer", "description": "Process ID"}},
                    "required": ["pid"],
                },
            ),
            ToolDefinition(
                name="cleanup_temp_files",
                description="Оценить или удалить старые временные файлы. По умолчанию dry_run=true",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Папка очистки. Пусто = текущий TEMP"},
                        "dry_run": {"type": "boolean", "default": True},
                        "older_than_days": {"type": "integer", "default": 7, "minimum": 1, "maximum": 365},
                    },
                },
            ),
        ]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a typed Windows administration tool."""
        allowed = {tool.name for tool in self.tools}
        if name not in allowed:
            return f"Неизвестный инструмент: {name}"
        return _call_mcp(name, arguments)

    async def run(self, user_message: str, model: str, **kwargs) -> Any:
        """Inject administrator behavior rules before running the agent loop."""
        enriched = f"{_SYSTEM_PROMPT}\n\nЗапрос пользователя: {user_message}"
        return await super().run(enriched, model, **kwargs)
