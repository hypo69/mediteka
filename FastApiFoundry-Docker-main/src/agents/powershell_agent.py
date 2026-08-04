# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: PowerShell Agent — агент для работы с локальной системой
# =============================================================================
# Описание:
#   Инструменты:
#     - run_powershell : выполнить PowerShell через McpSTDIOServer.ps1
#     - run_wp_cli     : выполнить WP-CLI через McpWPCLIServer.ps1
#     - http_get       : HTTP GET запрос
#
# File: src/agents/powershell_agent.py
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from .base import BaseAgent, ToolDefinition

logger = logging.getLogger(__name__)


def _find_server_script(name: str) -> Optional[str]:
    p = Path("mcp/src/servers") / f"{name}.ps1"
    return str(p) if p.exists() else None


def _call_mcp_stdio(script_path: str, method: str, params: Dict) -> Dict:
    """Отправить один JSON-RPC запрос в STDIO сервер"""
    request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    # Почему: MCP-STDIO часто читает запрос построчно. Перевод строки нужен для `ReadLine`.
    request_input = request + "\n"
    try:
        proc = subprocess.run(
            ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path],
            input=request_input,
            capture_output=True,
            # Почему: Windows-потоковая декодировка по умолчанию CP1252 может падать,
            # что делает `proc.stdout`/`proc.stderr` пустыми и ломает парсинг JSON.
            # Принудительная UTF-8 декодировка с `replace` сохраняет полезный вывод.
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=str(Path.cwd()),
        )
        # Почему: `CompletedProcess.stdout` иногда приходит как `None`
        # (ошибка выполнения PWSh, нет стандартного вывода, несовместимый формат вывода).
        # Обработка `None` гарантирует корректный маршрут в ветку ошибок вместо падения инструмента.
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue

        # Почему: диагностика вывода MCP — через stderr при отсутствии JSON в stdout.
        # Сообщение расширено `stdout`/`stderr`, чтобы локализовать формат/ошибку запуска.
        return {
            "error": (
                "No JSON in stdout. "
                f"stdout_prefix={stdout[:300]!r}; "
                f"stderr_prefix={stderr[:300]!r}"
            )
        }
    except subprocess.TimeoutExpired:
        return {"error": "MCP server timeout (30s)"}
    except FileNotFoundError:
        return {"error": "pwsh not found. Install PowerShell 7+"}
    except Exception as e:
        return {"error": str(e)}


def _extract_content(response: Dict) -> str:
    result = response.get("result", {})
    content = result.get("content", [])
    if content:
        return "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
    if "error" in response:
        return f"❌ {response['error']}"
    return "Команда выполнена, результат пустой"


class PowerShellAgent(BaseAgent):
    """Агент для работы с локальной системой через MCP PowerShell серверы"""

    name = "powershell"
    description = "Выполняет команды PowerShell, WP-CLI и HTTP запросы на локальной машине"

    @property
    def tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="run_powershell",
                description="Выполняет PowerShell команду или скрипт на локальной машине",
                parameters={
                    "type": "object",
                    "properties": {
                        "script": {
                            "type": "string",
                            "description": "PowerShell код. Например: 'Get-ChildItem' или 'ls'"
                        },
                        "working_directory": {
                            "type": "string",
                            "description": "Рабочая директория (опционально)"
                        }
                    },
                    "required": ["script"]
                }
            ),
            ToolDefinition(
                name="run_wp_cli",
                description="Выполняет команду WP-CLI для управления WordPress",
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Аргументы WP-CLI. Например: 'post list'"
                        },
                        "working_directory": {
                            "type": "string",
                            "description": "Путь к директории WordPress"
                        }
                    },
                    "required": ["command"]
                }
            ),
            ToolDefinition(
                name="http_get",
                description="Выполняет HTTP GET запрос к указанному URL",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL для GET запроса"}
                    },
                    "required": ["url"]
                }
            ),
        ]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool by name.

        Args:
            name: Tool name ('run_powershell', 'run_wp_cli', 'http_get').
            arguments: Parsed JSON arguments from the model's tool_call.

        Returns:
            str: Tool execution result as a string.
        """
        if name == "run_powershell":
            return await self._run_powershell(arguments)
        if name == "run_wp_cli":
            return await self._run_wp_cli(arguments)
        if name == "http_get":
            return await self._http_get(arguments)
        return f"❌ Неизвестный инструмент: {name}"

    async def _run_powershell(self, args: Dict) -> str:
        """Execute PowerShell script via McpSTDIOServer.

        Args:
            args: Dict with keys: script (str), working_directory (str, optional).

        Returns:
            str: Script output or error message.
        """
        script_path = _find_server_script("McpSTDIOServer")
        if not script_path:
            return "❌ McpSTDIOServer.ps1 не найден"

        # Почему: модель может сформировать `working_directory`, которого нет на диске.
        # Привязка к текущей директории обеспечивает устойчивость tool-call.
        working_directory_raw = args.get("working_directory")
        working_directory = str(Path.cwd())
        if working_directory_raw:
            wd = Path(str(working_directory_raw))
            if wd.exists() and wd.is_dir():
                working_directory = str(wd)
            else:
                logger.warning(f"⚠️ Invalid working_directory: {working_directory_raw}. Fallback: {working_directory}")

        _call_mcp_stdio(script_path, "initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "FastApiFoundry", "version": "0.4.1"}
        })
        response = _call_mcp_stdio(script_path, "tools/call", {
            "name": "run-script",
            "arguments": {
                "script": args["script"],
                "workingDirectory": working_directory,
                "timeoutSeconds": 30
            }
        })
        return _extract_content(response)

    async def _run_wp_cli(self, args: Dict) -> str:
        """Execute WP-CLI command via McpWPCLIServer.

        Args:
            args: Dict with keys: command (str), working_directory (str, optional).

        Returns:
            str: WP-CLI output or error message.
        """
        script_path = _find_server_script("McpWPCLIServer")
        if not script_path:
            return "❌ McpWPCLIServer.ps1 не найден"

        # Почему: модель может сформировать `working_directory`, которого нет.
        working_directory_raw = args.get("working_directory")
        working_directory = str(Path.cwd())
        if working_directory_raw:
            wd = Path(str(working_directory_raw))
            if wd.exists() and wd.is_dir():
                working_directory = str(wd)
            else:
                logger.warning(f"⚠️ Invalid working_directory: {working_directory_raw}. Fallback: {working_directory}")

        _call_mcp_stdio(script_path, "initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "FastApiFoundry", "version": "0.4.1"}
        })
        response = _call_mcp_stdio(script_path, "tools/call", {
            "name": "run-wp-cli",
            "arguments": {
                "commandArguments": args["command"],
                "workingDirectory": working_directory
            }
        })
        return _extract_content(response)

    async def _http_get(self, args: Dict) -> str:
        """Execute HTTP GET request.

        Args:
            args: Dict with key: url (str).

        Returns:
            str: HTTP status and response body (first 2000 chars) or error message.
        """
        url = args.get("url", "")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    text = await resp.text()
                    return f"HTTP {resp.status}\n{text[:2000]}"
        except Exception as e:
            return f"❌ HTTP ошибка: {e}"
