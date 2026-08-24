## \file tests/test_tools_structure.py
# -*- coding: utf-8 -*-
"""
Тесты структуры директорий проекта.

Проверяет наличие всех обязательных директорий, файлов и лончеров
согласно агентоориентированной стратегии проекта.

Документация: .ai_instructions/knowledge/LAUNCHER_GUIDE.md
"""

import pytest
from pathlib import Path


# Корень проекта определяется через header.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestToolsDirectoryStructure:
    """Проверяет структуру директории tools/."""

    def test_tools_directory_exists(self):
        """tools/ обязан существовать."""
        assert (PROJECT_ROOT / "tools").is_dir(), \
            "Директория tools/ не найдена в корне проекта"

    def test_tools_ai_directory_exists(self):
        """tools/ai/ обязан существовать."""
        assert (PROJECT_ROOT / "tools" / "ai").is_dir(), \
            "Директория tools/ai/ не найдена"

    def test_tools_setup_directory_exists(self):
        """tools/setup/ обязан существовать."""
        assert (PROJECT_ROOT / "tools" / "setup").is_dir(), \
            "Директория tools/setup/ не найдена"

    def test_tools_readme_exists(self):
        """tools/README.md обязан существовать."""
        assert (PROJECT_ROOT / "tools" / "README.md").is_file(), \
            "Файл tools/README.md не найден"

    def test_tools_ai_readme_exists(self):
        """tools/ai/README.md обязан существовать."""
        assert (PROJECT_ROOT / "tools" / "ai" / "README.md").is_file(), \
            "Файл tools/ai/README.md не найден"

    def test_tools_setup_readme_exists(self):
        """tools/setup/README.md обязан существовать."""
        assert (PROJECT_ROOT / "tools" / "setup" / "README.md").is_file(), \
            "Файл tools/setup/README.md не найден"


class TestAiToolsExist:
    """Проверяет наличие ключевых AI-инструментов в tools/ai/."""

    def test_rebuild_dev_rag_exists(self):
        """tools/ai/rebuild_dev_rag.py обязан существовать."""
        assert (PROJECT_ROOT / "tools" / "ai" / "rebuild_dev_rag.py").is_file()

    def test_search_code_exists(self):
        """tools/ai/search_code.py обязан существовать."""
        assert (PROJECT_ROOT / "tools" / "ai" / "search_code.py").is_file()

    def test_validate_rag_files_exists(self):
        """tools/ai/validate_rag_files.py обязан существовать."""
        assert (PROJECT_ROOT / "tools" / "ai" / "validate_rag_files.py").is_file()

    def test_update_docs_exists(self):
        """tools/ai/update_docs.py обязан существовать."""
        assert (PROJECT_ROOT / "tools" / "ai" / "update_docs.py").is_file()


class TestReportsDirectory:
    """Проверяет директорию reports/."""

    def test_reports_directory_exists(self):
        """reports/ обязан существовать."""
        assert (PROJECT_ROOT / "reports").is_dir(), \
            "Директория reports/ не найдена"

    def test_reports_readme_exists(self):
        """reports/README.md обязан существовать."""
        assert (PROJECT_ROOT / "reports" / "README.md").is_file(), \
            "Файл reports/README.md не найден"


class TestAiInstructionsDocuments:
    """Проверяет ключевые AI-документы."""

    def test_launcher_guide_exists(self):
        """LAUNCHER_GUIDE.md обязан существовать."""
        path = PROJECT_ROOT / ".ai_instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        assert path.is_file(), "LAUNCHER_GUIDE.md не найден"

    def test_launcher_guide_not_empty(self):
        """LAUNCHER_GUIDE.md не должен быть пустым."""
        path = PROJECT_ROOT / ".ai_instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        assert path.stat().st_size > 500, \
            "LAUNCHER_GUIDE.md слишком мал — вероятно, не заполнен"

    def test_scripts_tools_has_section_9(self):
        """scripts_tools.md должен содержать раздел 9 (структура директорий)."""
        path = PROJECT_ROOT / ".ai_instructions" / "knowledge" / "scripts_tools.md"
        content = path.read_text(encoding="utf-8")
        assert "## 9." in content or "# 9." in content, \
            "scripts_tools.md не содержит раздела 9 (структура директорий)"

    def test_model_guide_has_tools_ai_section(self):
        """MODEL_SCRIPT_EXECUTION_GUIDE.md должен упоминать tools/ai/."""
        path = PROJECT_ROOT / ".ai_instructions" / "knowledge" / "MODEL_SCRIPT_EXECUTION_GUIDE.md"
        content = path.read_text(encoding="utf-8")
        assert "tools/ai/" in content, \
            "MODEL_SCRIPT_EXECUTION_GUIDE.md не содержит раздела о tools/ai/"

    def test_gemini_md_has_launcher_guide_ref(self):
        """GEMINI.md должен ссылаться на LAUNCHER_GUIDE.md."""
        path = PROJECT_ROOT / "GEMINI.md"
        content = path.read_text(encoding="utf-8")
        assert "LAUNCHER_GUIDE" in content, \
            "GEMINI.md не содержит ссылки на LAUNCHER_GUIDE.md"


class TestCoreProjectFiles:
    """Проверяет наличие ключевых файлов проекта в корне."""

    def test_main_py_exists(self):
        """main.py обязан существовать."""
        assert (PROJECT_ROOT / "main.py").is_file()

    def test_manage_tools_exists(self):
        """manage_tools.py обязан существовать."""
        assert (PROJECT_ROOT / "manage_tools.py").is_file()

    def test_header_py_exists(self):
        """header.py обязан существовать (используется main.py и manage_tools.py)."""
        assert (PROJECT_ROOT / "header.py").is_file(), \
            "header.py отсутствует — main.py и manage_tools.py не запустятся"

    def test_env_example_exists(self):
        """.env.example обязан существовать для документации переменных."""
        assert (PROJECT_ROOT / ".env.example").is_file()
