# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Full API Reference Generator
# =============================================================================
# Description:
#   Scans all endpoint files in src/api/endpoints/,
#   extracts every @router route (method, path, docstring, params),
#   and generates docs/ru/dev/api_full.md — a single page with
#   all methods, their request fields and response shapes.
#
# File: scripts/Create-Doc/Generate-ApiReference.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import ast
import re
import sys
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[2]
ENDPOINTS  = ROOT / "src" / "api" / "endpoints"
OUT_FILE   = ROOT / "docs" / "ru" / "dev" / "api_full.md"

# Map endpoint file → base URL prefix (from app.py include_router calls)
PREFIX_MAP = {
    "health.py":              "/api/v1",
    "generate.py":            "/api/v1",
    "ai_endpoints.py":        "/api/v1",
    "chat_endpoints.py":      "/api/v1",
    "models.py":              "/api/v1",
    "openai_models.py":       "/v1",
    "foundry.py":             "/api/v1",
    "foundry_management.py":  "/api/v1",
    "foundry_models.py":      "/api/v1",
    "hf_models.py":           "/api/v1",
    "llama_cpp.py":           "/api/v1",
    "ollama.py":              "/api/v1",
    "lmstudio.py":            "/api/v1",
    "rag.py":                 "/api/v1",
    "rag_ingestor.py":        "/api/v1",
    "agent.py":               "/api/v1",
    "mcp_powershell.py":      "/api/v1",
    "mcp_agent_endpoints.py": "/api/v1",
    "config.py":              "/api/v1",
    "logs.py":                "/api/v1",
    "converter.py":           "/api/v1",
    "system_stats.py":        "/api/v1",
    "translator.py":          "/api/v1",
    "support.py":             "/api/v1",
    "helpdesk.py":            "/api/v1",
    "training.py":            "/api/v1",
    "recommender.py":         "/api/v1",
    "content_blocks.py":      "/api/v1",
    "security.py":            "/api/v1",
    "install.py":             "/api/v1",
    "processor.py":           "/api/v1",
}

# Section titles per file
SECTION_MAP = {
    "health.py":              "🏥 Health & Restart",
    "generate.py":            "⚡ Generate",
    "ai_endpoints.py":        "🤖 AI (расширенная генерация)",
    "chat_endpoints.py":      "💬 Chat (сессии)",
    "models.py":              "📋 Models (универсальные)",
    "openai_models.py":       "🔗 OpenAI-совместимые",
    "foundry.py":             "🏭 Foundry — статус",
    "foundry_management.py":  "🏭 Foundry — управление сервисом",
    "foundry_models.py":      "🏭 Foundry — модели",
    "hf_models.py":           "🤗 HuggingFace",
    "llama_cpp.py":           "🦙 llama.cpp",
    "ollama.py":              "🐋 Ollama",
    "lmstudio.py":            "🎛️ LM Studio",
    "rag.py":                 "🔍 RAG",
    "rag_ingestor.py":        "🔍 RAG Ingestor",
    "agent.py":               "🕵️ Agent",
    "mcp_powershell.py":      "🔌 MCP PowerShell",
    "mcp_agent_endpoints.py": "🔌 MCP Agent",
    "config.py":              "⚙️ Config",
    "logs.py":                "📜 Logs",
    "converter.py":           "🔄 Converter",
    "system_stats.py":        "📊 System Stats",
    "translator.py":          "🌍 Translator",
    "support.py":             "🆘 Support",
    "helpdesk.py":            "🎧 HelpDesk",
    "training.py":            "🎓 Training",
    "recommender.py":         "💡 Recommender",
    "content_blocks.py":      "📦 Content Blocks",
    "security.py":            "🔐 Security",
    "install.py":             "🛠️ Install",
    "processor.py":           "⚙️ Processor",
}

SKIP_FILES = {"__init__.py", "main.py", "README.md"}

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def extract_router_prefix(source: str) -> str:
    """Extract prefix from APIRouter(prefix=...) declaration."""
    m = re.search(r'APIRouter\s*\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', source)
    return m.group(1) if m else ""


def extract_routes(filepath: Path, base_prefix: str) -> list[dict]:
    """Parse a Python endpoint file and extract all route definitions."""
    source = filepath.read_text(encoding="utf-8", errors="ignore")
    router_prefix = extract_router_prefix(source)

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    routes = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue

        for decorator in node.decorator_list:
            # Match @router.get("/path") or @router.post("/path")
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not isinstance(func, ast.Attribute):
                continue
            method = func.attr.lower()
            if method not in HTTP_METHODS:
                continue

            # Extract path
            if not decorator.args:
                continue
            path_node = decorator.args[0]
            if not isinstance(path_node, ast.Constant):
                continue
            route_path = str(path_node.value)

            full_path = base_prefix + router_prefix + route_path

            # Extract docstring
            docstring = ast.get_docstring(node) or ""

            # Extract function signature params (excluding self, request: dict)
            params = []
            for arg in node.args.args:
                name = arg.arg
                if name in ("self",):
                    continue
                annotation = ""
                if arg.annotation:
                    annotation = ast.unparse(arg.annotation)
                params.append({"name": name, "type": annotation})

            routes.append({
                "method":    method.upper(),
                "path":      full_path,
                "func":      node.name,
                "docstring": docstring,
                "params":    params,
                "lineno":    node.lineno,
                "file":      filepath.name,
            })

    return routes


def format_docstring(doc: str) -> str:
    """Format docstring into clean markdown."""
    if not doc:
        return ""
    lines = doc.strip().splitlines()
    result = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        # Section headers: Args:, Returns:, Example:
        if stripped.endswith(":") and stripped[:-1] in (
            "Args", "Returns", "Return", "Exceptions", "Example", "Examples"
        ):
            result.append(f"\n**{stripped}**\n")
            in_section = True
        elif in_section and stripped.startswith(("prompt", "model", "request",
                                                  "temperature", "max_tokens",
                                                  "use_rag", "dict", "str", "bool",
                                                  "int", "float")):
            result.append(f"- `{stripped}`")
        else:
            result.append(line.rstrip())
    return "\n".join(result)


def method_badge(method: str) -> str:
    colors = {
        "GET":    "success",
        "POST":   "primary",
        "PUT":    "warning",
        "PATCH":  "warning",
        "DELETE": "danger",
    }
    color = colors.get(method, "secondary")
    return f'<span class="badge-{color.lower()}">{method}</span>'


def generate_page(all_sections: list[tuple[str, list[dict]]]) -> str:
    lines = [
        "# API Reference — полный справочник",
        "",
        "Базовый URL: `http://localhost:9696`  ",
        "Swagger UI: [`http://localhost:9696/docs`](http://localhost:9696/docs)",
        "",
        "!!! tip \"Интерактивный Swagger\"",
        "    Все методы можно вызвать прямо из браузера через Swagger UI.",
        "    Откройте `http://localhost:9696/docs` — там живые формы для каждого endpoint.",
        "",
        "---",
        "",
        "## Префиксы моделей",
        "",
        "| Префикс | Бэкенд |",
        "|---|---|",
        "| `foundry::model-id` | Microsoft Foundry Local |",
        "| `hf::model-id` | HuggingFace Transformers |",
        "| `llama::path/to/model.gguf` | llama.cpp |",
        "| `ollama::model-name` | Ollama |",
        "| `lmstudio::model-key` | LM Studio |",
        "",
        "---",
        "",
    ]

    for section_title, routes in all_sections:
        if not routes:
            continue
        lines.append(f"## {section_title}")
        lines.append("")

        for r in routes:
            method = r["method"]
            path   = r["path"]
            doc    = r["docstring"]
            params = r["params"]

            # Heading
            lines.append(f"### `{method}` {path}")
            lines.append("")

            # Short description (first line of docstring)
            if doc:
                first_line = doc.strip().splitlines()[0].strip()
                lines.append(first_line)
                lines.append("")

            # Parameters table (from function signature, non-dict params)
            path_params = re.findall(r"\{(\w+)\}", path)
            if path_params:
                lines.append("**Path параметры:**")
                lines.append("")
                lines.append("| Параметр | Тип |")
                lines.append("|---|---|")
                for p in path_params:
                    lines.append(f"| `{p}` | `str` |")
                lines.append("")

            # Request body fields from docstring Args section
            if doc and "Args:" in doc:
                args_section = doc.split("Args:")[1]
                # Stop at next section
                for stop in ("Returns:", "Exceptions:", "Example:", "Examples:"):
                    if stop in args_section:
                        args_section = args_section.split(stop)[0]
                args_lines = [l.strip() for l in args_section.strip().splitlines() if l.strip()]
                if args_lines:
                    lines.append("**Тело запроса / параметры:**")
                    lines.append("")
                    lines.append("| Поле | Описание |")
                    lines.append("|---|---|")
                    for al in args_lines:
                        # Format: "name (type): description"
                        m = re.match(r"(\w+)\s*\(([^)]+)\)\s*[:\-–]\s*(.*)", al)
                        if m:
                            fname, ftype, fdesc = m.group(1), m.group(2), m.group(3)
                            lines.append(f"| `{fname}` ({ftype}) | {fdesc} |")
                        elif al and not al.startswith("#"):
                            lines.append(f"| | {al} |")
                    lines.append("")

            # Returns from docstring
            if doc and "Returns:" in doc:
                ret_section = doc.split("Returns:")[1]
                for stop in ("Exceptions:", "Example:", "Examples:", "Args:"):
                    if stop in ret_section:
                        ret_section = ret_section.split(stop)[0]
                ret_lines = [l.strip() for l in ret_section.strip().splitlines() if l.strip()]
                if ret_lines:
                    lines.append("**Ответ:**")
                    lines.append("")
                    for rl in ret_lines[:3]:  # first 3 lines
                        lines.append(f"> {rl}")
                    lines.append("")

            lines.append("---")
            lines.append("")

    lines.append("*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-ApiReference.py`*")
    return "\n".join(lines)


def main() -> None:
    print(f"Scanning {ENDPOINTS} ...")

    # Ordered list of files to process
    ordered_files = [
        "health.py", "generate.py", "ai_endpoints.py", "chat_endpoints.py",
        "models.py", "openai_models.py",
        "foundry.py", "foundry_management.py", "foundry_models.py",
        "hf_models.py", "llama_cpp.py", "ollama.py", "lmstudio.py",
        "rag.py", "rag_ingestor.py",
        "agent.py", "mcp_powershell.py", "mcp_agent_endpoints.py",
        "config.py", "logs.py", "converter.py", "system_stats.py",
        "translator.py", "support.py", "helpdesk.py",
        "training.py", "recommender.py", "content_blocks.py",
        "security.py", "install.py", "processor.py",
    ]

    all_sections = []
    total_routes = 0

    for fname in ordered_files:
        fpath = ENDPOINTS / fname
        if not fpath.exists():
            continue
        base = PREFIX_MAP.get(fname, "/api/v1")
        routes = extract_routes(fpath, base)
        section = SECTION_MAP.get(fname, fname)
        all_sections.append((section, routes))
        total_routes += len(routes)
        print(f"  {fname}: {len(routes)} routes")

    page = generate_page(all_sections)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(page, encoding="utf-8")

    print(f"\nTotal routes: {total_routes}")
    print(f"Output: {OUT_FILE}")


if __name__ == "__main__":
    main()
