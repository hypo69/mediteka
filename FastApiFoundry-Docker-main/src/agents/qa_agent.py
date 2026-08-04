# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: QA Agent — агент запуска тестов
# =============================================================================
# Description:
#   Агент для запуска pytest, анализа результатов и формирования отчёта.
#   Инструменты:
#     - run_tests(path, filter)  — запустить тесты, вернуть результат
#     - list_test_files()        — список тестовых файлов
#     - get_coverage()           — отчёт покрытия кода
#
#   Workflow:
#     prompt → run_tests → parse output → summary → answer
#
# File: src/agents/qa_agent.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Created
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseAgent, ToolDefinition

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PYTHON = sys.executable


class QAAgent(BaseAgent):
    """Agent that runs pytest and reports results.

    Workflow:
        user prompt
          └─ run_tests(path) → subprocess pytest → parse stdout
          └─ get_coverage()  → pytest --cov → parse report
          └─ answer with summary
    """

    name = "qa"
    description = "Запускает тесты, анализирует результаты, формирует отчёт о качестве кода"

    @property
    def tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="run_tests",
                description="Run pytest for a given path or filter. Returns pass/fail summary and output.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Test path or file, e.g. 'tests/' or 'tests/unit/test_dialogs.py'",
                        },
                        "filter": {
                            "type": "string",
                            "description": "Optional -k filter expression, e.g. 'test_save or test_list'",
                        },
                        "coverage": {
                            "type": "boolean",
                            "description": "Whether to collect coverage (default: false)",
                        },
                    },
                    "required": ["path"],
                },
            ),
            ToolDefinition(
                name="list_test_files",
                description="List all test files in the project.",
                parameters={"type": "object", "properties": {}, "required": []},
            ),
            ToolDefinition(
                name="get_coverage",
                description="Run pytest with coverage and return the coverage report.",
                parameters={
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "Source directory to measure, e.g. 'src'",
                        }
                    },
                    "required": [],
                },
            ),
        ]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if name == "run_tests":
            return await self._run_tests(
                arguments.get("path", "tests/"),
                arguments.get("filter"),
                arguments.get("coverage", False),
            )
        if name == "list_test_files":
            return self._list_test_files()
        if name == "get_coverage":
            return await self._get_coverage(arguments.get("source", "src"))
        return f"Unknown tool: {name}"

    async def _run_tests(self, path: str, filter_expr: str | None, coverage: bool) -> str:
        """Run pytest and return formatted output.

        Args:
            path: Test path relative to project root.
            filter_expr: Optional -k expression.
            coverage: Whether to add --cov flag.

        Returns:
            str: Formatted test result summary.
        """
        cmd = [_PYTHON, "-m", "pytest", path, "-v", "--tb=short", "--no-header"]
        if filter_expr:
            cmd += ["-k", filter_expr]
        if coverage:
            cmd += [f"--cov={_PROJECT_ROOT / 'src'}", "--cov-report=term-missing"]

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(_PROJECT_ROOT),
                    timeout=120,
                ),
            )
            output = result.stdout + result.stderr
            status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
            return f"{status} (exit {result.returncode})\n\n{output[-3000:]}"
        except subprocess.TimeoutExpired:
            return "❌ Timeout: тесты выполнялись дольше 120 секунд"
        except Exception as e:
            return f"❌ Error running tests: {e}"

    def _list_test_files(self) -> str:
        """List all test files in tests/ directory.

        Returns:
            str: Newline-separated list of test file paths.
        """
        tests_dir = _PROJECT_ROOT / "tests"
        if not tests_dir.exists():
            return "tests/ directory not found"
        files = sorted(tests_dir.rglob("test_*.py"))
        if not files:
            return "No test files found"
        return "\n".join(str(f.relative_to(_PROJECT_ROOT)) for f in files)

    async def _get_coverage(self, source: str) -> str:
        """Run pytest with coverage report.

        Args:
            source: Source directory to measure coverage for.

        Returns:
            str: Coverage report output.
        """
        return await self._run_tests("tests/", None, coverage=True)


qa_agent = QAAgent(foundry_client=None)  # foundry_client injected at endpoint level
