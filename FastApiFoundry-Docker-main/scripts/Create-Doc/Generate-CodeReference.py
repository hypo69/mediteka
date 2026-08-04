# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Code Reference Generator
# =============================================================================
# Description:
#   Generates mkdocstrings-based .md files for all Python modules in src/
#   mirroring the source tree structure under docs/ru/dev/code/src/
#
#   Rules:
#     - Each directory → index.md built from README.md (if exists)
#     - Each .py file  → <stem>.md with mkdocstrings ::: directive
#     - Nav in mkdocs.yml mirrors the exact directory tree
#     - Skips __init__.py, archived dirs (*~), __pycache__
#
# File: scripts/Create-Doc/Generate-CodeReference.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Changes in 0.8.0:
#   - Directory index pages built from README.md
#   - Nav mirrors exact source tree (no flat grouping)
#   - Skips __init__.py
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import os
import re
from pathlib import Path

ROOT     = Path(__file__).resolve().parents[2]
SRC_DIR  = ROOT / "src"
DOCS_OUT = ROOT / "docs" / "ru" / "dev" / "code" / "src"
MKDOCS   = ROOT / "mkdocs.yml"

SKIP_DIRS  = {"__pycache__", ".git", "venv", "site"}
SKIP_FILES = {"__init__.py"}

# Human-readable titles for known directory names
TITLE_MAP = {
    "src":                  "src/",
    "api":                  "api/",
    "endpoints":            "endpoints/",
    "agents":               "agents/",
    "converter":            "converter/",
    "core":                 "core/",
    "db":                   "db/",
    "logger":               "logger/",
    "models":               "models/",
    "rag":                  "rag/",
    "text_extractors":      "text_extractors/",
    "text_extractor_4_rag": "text_extractor_4_rag/",
    "markitdown":           "markitdown/",
    "whisper":              "whisper/",
    "training":             "training/",
    "utils":                "utils/",
}


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIRS or name.endswith("~")


def dir_title(name: str) -> str:
    return TITLE_MAP.get(name, f"{name}/")


def file_title(stem: str) -> str:
    return stem.replace("_", " ").title()


def file_to_module(py_file: Path) -> str:
    """src/api/app.py → src.api.app"""
    rel = py_file.relative_to(ROOT)
    return str(rel).replace(os.sep, ".").replace("/", ".").removesuffix(".py")


def make_index_md(directory: Path, out_md: Path) -> None:
    """Generate index.md for a directory from its README.md or a stub."""
    readme = directory / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8", errors="ignore")
    else:
        rel = directory.relative_to(SRC_DIR)
        content = f"# {directory.name}/\n\n`{rel}`\n"

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(content, encoding="utf-8")


def make_file_md(py_file: Path, out_md: Path) -> None:
    """Generate <stem>.md with mkdocstrings directive."""
    module  = file_to_module(py_file)
    title   = file_title(py_file.stem)
    rel_src = str(py_file.relative_to(ROOT)).replace(os.sep, "/")

    content = f"""# {title}

**Файл:** `{rel_src}`

::: {module}
    options:
      show_root_heading: true
      show_source: true
      members_order: source
      show_if_no_docstring: true

---

*Проект: AI Assistant (ai_assist) · v0.8.0*
"""
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(content, encoding="utf-8")


def nav_path(md_file: Path) -> str:
    """Absolute path → relative to docs/ru/ for mkdocs nav."""
    return str(md_file.relative_to(ROOT / "docs" / "ru")).replace(os.sep, "/")


def process_dir(src_dir: Path, docs_dir: Path, indent: int) -> list[str]:
    """
    Recursively process src_dir → docs_dir.
    Returns nav lines (indented yaml list).
    """
    nav: list[str] = []
    pad = "  " * indent

    # Directory index page
    index_md = docs_dir / "index.md"
    make_index_md(src_dir, index_md)
    title = dir_title(src_dir.name)
    nav.append(f"{pad}- {title}:")

    inner_pad = "  " * (indent + 1)

    # index.md entry
    nav.append(f"{inner_pad}- Обзор: {nav_path(index_md)}")

    # Collect children: subdirs first, then files
    try:
        children = sorted(src_dir.iterdir())
    except PermissionError:
        return nav

    subdirs = [c for c in children if c.is_dir() and not should_skip_dir(c.name)]
    pyfiles = [
        c for c in children
        if c.is_file() and c.suffix == ".py" and c.name not in SKIP_FILES
    ]

    # Recurse into subdirectories
    for sub in subdirs:
        sub_docs = docs_dir / sub.name
        sub_nav  = process_dir(sub, sub_docs, indent + 1)
        nav.extend(sub_nav)

    # Python files
    for py in pyfiles:
        out_md = docs_dir / py.with_suffix(".md").name
        make_file_md(py, out_md)
        nav.append(f"{inner_pad}- {file_title(py.stem)}: {nav_path(out_md)}")

    return nav


def update_mkdocs_nav(nav_lines: list[str]) -> None:
    START = "# AUTO_GENERATED_CODE_REF_START"
    END   = "# AUTO_GENERATED_CODE_REF_END"

    yml = MKDOCS.read_text(encoding="utf-8")
    if START not in yml:
        print("WARNING: markers not found in mkdocs.yml — skipping nav update")
        return

    # Each nav line gets 8 spaces base indent (matches existing mkdocs.yml style)
    block = "\n".join(f"        {line}" for line in nav_lines)
    pattern     = rf"{re.escape(START)}.*?{re.escape(END)}"
    replacement = f"{START}\n{block}\n        {END}"
    new_yml = re.sub(pattern, replacement, yml, flags=re.DOTALL)
    MKDOCS.write_text(new_yml, encoding="utf-8")
    print("mkdocs.yml nav updated")


def main() -> None:
    print(f"Scanning {SRC_DIR} ...")

    nav_lines = process_dir(SRC_DIR, DOCS_OUT, indent=0)

    # Write nav fragment for inspection
    fragment = DOCS_OUT / "_nav_fragment.yml"
    fragment.parent.mkdir(parents=True, exist_ok=True)
    fragment.write_text("\n".join(nav_lines), encoding="utf-8")
    print(f"Nav fragment: {fragment}")

    update_mkdocs_nav(nav_lines)

    count = sum(1 for _ in DOCS_OUT.rglob("*.md") if _.name != "_nav_fragment.yml")
    print(f"Output: {DOCS_OUT}")
    print(f"Generated {count} .md files")


if __name__ == "__main__":
    main()
