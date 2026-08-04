# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Universal Full Reference Generator
# =============================================================================
# Description:
#   Scans the entire project root recursively and generates markdown
#   documentation mirroring the exact source tree under docs/ru/dev/code/
#
#   Exclusion rules:
#     - Directories starting with "." are skipped
#     - Directories in SKIP_DIRS are skipped
#     - Files whose name starts or ends with "~" are skipped
#     - Files not in SUPPORTED extensions are skipped
#     - __init__.py is skipped
#
#   For each directory:
#     - index.md is generated from README.md (if exists), relative links stripped
#     - Otherwise a stub index.md is created
#
#   For each supported file:
#     - .py   — ast: classes, functions, docstrings
#     - .ps1  — re:  functions, comment-based help
#     - .js   — re:  functions, JSDoc
#     - .ts   — same as .js
#     - .json — top-level keys and structure
#     - .html — title, comments, data-i18n keys
#
#   Nav is injected into mkdocs.yml between:
#     # AUTO_GENERATED_FULL_REF_START
#     # AUTO_GENERATED_FULL_REF_END
#
# Usage:
#   python scripts/Create-Doc/Generate-FullReference.py
#
# File: scripts/Create-Doc/Generate-FullReference.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import ast
import json
import os
import re
import sys
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[2]
MKDOCS = ROOT / "mkdocs.yml"
DOCS_OUT = ROOT / "docs" / "ru" / "dev" / "code"

MARKER_START = "# AUTO_GENERATED_FULL_REF_START"
MARKER_END   = "# AUTO_GENERATED_FULL_REF_END"

SUPPORTED = {".py", ".ps1", ".js", ".ts", ".json", ".html"}

# Directories to skip entirely
SKIP_DIRS = {
    "site", "logs", "archive", "bin", "rag_index", "training_data",
    "__pycache__", "venv", "node_modules", "dist", "build",
    ".hypothesis", ".git",
    # docs itself — already the output
    "docs",
    # generated output dir
    "code",
}

# Root-level directories to skip (too noisy or irrelevant for code reference)
SKIP_ROOT_DIRS = {
    "assets", "notebooks", "install",
}

SKIP_FILES = {"__init__.py"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def should_skip_dir(path: Path, is_root_child: bool = False) -> bool:
    name = path.name
    if name.startswith("."):
        return True
    if name in SKIP_DIRS:
        return True
    if is_root_child and name in SKIP_ROOT_DIRS:
        return True
    return False


def should_skip_file(path: Path) -> bool:
    name = path.name
    if name.startswith("~") or name.endswith("~"):
        return True
    if name in SKIP_FILES:
        return True
    if path.suffix.lower() not in SUPPORTED:
        return True
    return False


def file_title(stem: str) -> str:
    return stem.replace("_", " ").replace("-", " ").title()


def dir_title(name: str) -> str:
    return f"{name}/"


def code_block(lang: str, code: str) -> str:
    return f"```{lang}\n{code.strip()}\n```"


def to_nav_path(md_file: Path) -> str:
    return str(md_file.relative_to(ROOT / "docs" / "ru")).replace(os.sep, "/")


def strip_relative_links(content: str) -> str:
    """Replace [text](../x) and [text](./x) with just text to avoid broken links."""
    content = re.sub(r'\[([^\]]+)\]\(\.\.[^)]*\)', r'\1', content)
    content = re.sub(r'\[([^\]]+)\]\(\./[^)]*\)', r'\1', content)
    return content


# ── Extractors ────────────────────────────────────────────────────────────────

def extract_py(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return f"!!! warning \"Syntax error\"\n    {e}\n"

    sections: list[str] = []
    doc = ast.get_docstring(tree)
    if doc:
        sections += [doc.strip(), ""]

    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        kind = "Класс" if isinstance(node, ast.ClassDef) else "Функция"
        ndoc = ast.get_docstring(node) or ""
        try:
            sig = ast.unparse(node).splitlines()[0].rstrip(":")
        except Exception:
            sig = f"def {node.name}(...)"
        sections += [f"### `{node.name}` — {kind}", "", code_block("python", sig), ""]
        if ndoc:
            sections += [ndoc.strip(), ""]

    return "\n".join(sections) or "_Публичных символов не найдено._"


def extract_ps1(source: str) -> str:
    sections: list[str] = []

    header = []
    for line in source.splitlines():
        s = line.strip()
        if s.startswith("#"):
            header.append(s.lstrip("# ").strip())
        elif s == "" and header:
            break
        elif s:
            break
    if header:
        sections += ["\n".join(header), ""]

    func_re = re.compile(r'(?s)(<#.*?#>\s*)?function\s+([\w-]+)\s*\{', re.IGNORECASE)
    for m in func_re.finditer(source):
        hb   = m.group(1) or ""
        name = m.group(2)
        synopsis = description = ""
        examples: list[str] = []
        if hb:
            sm = re.search(r'\.SYNOPSIS\s*\n(.*?)(?=\.\w|\Z)', hb, re.DOTALL | re.IGNORECASE)
            if sm: synopsis = sm.group(1).strip()
            dm = re.search(r'\.DESCRIPTION\s*\n(.*?)(?=\.\w|\Z)', hb, re.DOTALL | re.IGNORECASE)
            if dm: description = dm.group(1).strip()
            for em in re.finditer(r'\.EXAMPLE\s*\n(.*?)(?=\.\w|\Z)', hb, re.DOTALL | re.IGNORECASE):
                examples.append(em.group(1).strip())
        sections += [f"### `{name}`", ""]
        if synopsis:    sections += [synopsis, ""]
        if description: sections += [description, ""]
        if examples:
            sections += ["**Примеры:**", ""]
            for ex in examples:
                sections += [code_block("powershell", ex), ""]

    return "\n".join(sections) or "_Функций не найдено._"


def extract_js(source: str) -> str:
    sections: list[str] = []
    jsdoc_re = re.compile(
        r'(/\*\*.*?\*/)\s*(?:export\s+)?(?:async\s+)?'
        r'(?:function\s+([\w$]+)|(?:const|let|var)\s+([\w$]+)\s*=\s*'
        r'(?:async\s+)?(?:function|\([^)]*\)\s*=>))',
        re.DOTALL
    )
    documented: set[str] = set()
    for m in jsdoc_re.finditer(source):
        jsdoc = m.group(1)
        name  = m.group(2) or m.group(3) or "anonymous"
        documented.add(name)
        dm = re.search(r'/\*\*\s*(.*?)(?=@|\*/)', jsdoc, re.DOTALL)
        desc = dm.group(1).strip().lstrip("* ").strip() if dm else ""
        params = re.findall(r'@param\s+\{([^}]+)\}\s+(\w+)\s*[-–]?\s*(.*)', jsdoc)
        sections += [f"### `{name}`", ""]
        if desc: sections += [desc, ""]
        if params:
            sections += ["| Параметр | Тип | Описание |", "|---|---|---|"]
            for pt, pn, pd in params:
                sections.append(f"| `{pn}` | `{pt}` | {pd} |")
            sections.append("")

    plain_re = re.compile(r'^(?:export\s+)?(?:async\s+)?function\s+([\w$]+)\s*\(', re.MULTILINE)
    for m in plain_re.finditer(source):
        if m.group(1) not in documented:
            sections += [f"### `{m.group(1)}`", ""]

    return "\n".join(sections) or "_Функций не найдено._"


def extract_json(source: str) -> str:
    try:
        data = json.loads(source)
    except json.JSONDecodeError as e:
        return f"!!! warning \"JSON parse error\"\n    {e}\n"
    sections: list[str] = []
    if isinstance(data, dict):
        sections += ["| Ключ | Тип | Значение |", "|---|---|---|"]
        for k, v in data.items():
            vt = type(v).__name__
            if isinstance(v, dict):
                preview = f"объект: {', '.join(f'`{x}`' for x in list(v)[:5])}"
            elif isinstance(v, list):
                preview = f"массив [{len(v)}]"
            elif isinstance(v, str) and len(v) > 80:
                preview = v[:77] + "..."
            else:
                preview = str(v)
            sections.append(f"| `{k}` | `{vt}` | {preview} |")
        sections += ["", "**Полная структура:**", "",
                     code_block("json", json.dumps(data, ensure_ascii=False, indent=2)[:3000])]
    elif isinstance(data, list):
        sections.append(f"Массив из **{len(data)}** элементов.")
        if data:
            sections += ["", "**Первый элемент:**",
                         code_block("json", json.dumps(data[0], ensure_ascii=False, indent=2))]
    return "\n".join(sections)


def extract_html(source: str) -> str:
    sections: list[str] = []
    tm = re.search(r'<title[^>]*>(.*?)</title>', source, re.IGNORECASE | re.DOTALL)
    if tm:
        sections += [f"**Title:** {tm.group(1).strip()}", ""]
    comments = [c.strip() for c in re.findall(r'<!--(.*?)-->', source, re.DOTALL)
                if len(c.strip()) > 10 and not c.strip().startswith("[")]
    if comments:
        sections += ["**Комментарии:**", ""]
        for c in comments[:5]:
            sections.append(f"> {c.splitlines()[0].strip()}")
        sections.append("")
    keys = sorted(set(re.findall(r'data-i18n(?:-\w+)?=["\']([^"\']+)["\']', source)))
    if keys:
        sections += [f"**i18n ключи** ({len(keys)}):", "",
                     ", ".join(f"`{k}`" for k in keys[:30])]
        if len(keys) > 30:
            sections.append(f"... и ещё {len(keys) - 30}")
        sections.append("")
    scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', source, re.IGNORECASE)
    links   = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', source, re.IGNORECASE)
    if scripts or links:
        sections += ["**Ресурсы:**", ""]
        for s in scripts: sections.append(f"- JS: `{s}`")
        for lnk in links: sections.append(f"- Link: `{lnk}`")
        sections.append("")
    return "\n".join(sections) or "_Значимых элементов не найдено._"


def extract(filepath: Path) -> str:
    source = filepath.read_text(encoding="utf-8", errors="ignore")
    ext = filepath.suffix.lower()
    if ext == ".py":           return extract_py(source)
    if ext == ".ps1":          return extract_ps1(source)
    if ext in (".js", ".ts"):  return extract_js(source)
    if ext == ".json":         return extract_json(source)
    if ext == ".html":         return extract_html(source)
    return "_Формат не поддерживается._"


# ── MD generators ─────────────────────────────────────────────────────────────

def make_index_md(directory: Path, out_md: Path) -> None:
    readme = directory / "README.md"
    if readme.exists():
        content = strip_relative_links(readme.read_text(encoding="utf-8", errors="ignore"))
    else:
        rel = directory.relative_to(ROOT)
        content = f"# {directory.name}/\n\n`{str(rel).replace(os.sep, '/')}`\n"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(content, encoding="utf-8")


def make_file_md(filepath: Path, out_md: Path) -> None:
    rel   = filepath.relative_to(ROOT)
    title = file_title(filepath.stem)
    body  = extract(filepath)
    content = f"""# {title}

**Файл:** `{str(rel).replace(os.sep, '/')}`  
**Тип:** `{filepath.suffix}`

---

{body}

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
"""
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(content, encoding="utf-8")


# ── Tree walker ───────────────────────────────────────────────────────────────

def process_dir(src_dir: Path, docs_dir: Path, indent: int,
                is_root_child: bool = False) -> list[str]:
    nav: list[str] = []
    pad       = "  " * indent
    inner_pad = "  " * (indent + 1)

    index_md = docs_dir / "index.md"
    make_index_md(src_dir, index_md)
    nav.append(f"{pad}- {dir_title(src_dir.name)}:")
    nav.append(f"{inner_pad}- Обзор: {to_nav_path(index_md)}")

    try:
        children = sorted(src_dir.iterdir())
    except PermissionError:
        return nav

    subdirs = [c for c in children
               if c.is_dir() and not should_skip_dir(c, is_root_child=False)]
    files   = [c for c in children
               if c.is_file() and not should_skip_file(c)]

    for sub in subdirs:
        nav.extend(process_dir(sub, docs_dir / sub.name, indent + 1))

    for f in files:
        out_md = docs_dir / f.with_suffix(".md").name
        make_file_md(f, out_md)
        nav.append(f"{inner_pad}- {file_title(f.stem)}: {to_nav_path(out_md)}")

    return nav


# ── mkdocs.yml injection ──────────────────────────────────────────────────────

def update_mkdocs(nav_lines: list[str]) -> None:
    yml = MKDOCS.read_text(encoding="utf-8")
    if MARKER_START not in yml:
        print(f"WARNING: {MARKER_START} not found in mkdocs.yml — skipping")
        return
    # 6 spaces indent to match Code Reference section in mkdocs.yml
    block = "\n".join(f"      {line}" for line in nav_lines)
    pattern = rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}"
    replacement = f"{MARKER_START}\n{block}\n      {MARKER_END}"
    MKDOCS.write_text(re.sub(pattern, replacement, yml, flags=re.DOTALL), encoding="utf-8")
    print("mkdocs.yml updated")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    # Top-level dirs to scan (everything except excluded)
    try:
        root_dirs = sorted(
            d for d in ROOT.iterdir()
            if d.is_dir() and not should_skip_dir(d, is_root_child=True)
        )
    except PermissionError:
        print("ERROR: cannot read project root")
        sys.exit(1)

    all_nav: list[str] = []
    total_files = 0

    for d in root_dirs:
        docs_dir = DOCS_OUT / d.name
        print(f"  {d.name}/")
        nav = process_dir(d, docs_dir, indent=0, is_root_child=True)
        all_nav.extend(nav)
        total_files += sum(1 for _ in docs_dir.rglob("*.md") if _.name != "_nav_fragment.yml")

    # Write combined nav fragment
    fragment = DOCS_OUT / "_nav_fragment.yml"
    DOCS_OUT.mkdir(parents=True, exist_ok=True)
    fragment.write_text("\n".join(all_nav), encoding="utf-8")

    update_mkdocs(all_nav)

    print(f"\nTotal .md files generated: {total_files}")
    print(f"Nav fragment: {fragment}")


if __name__ == "__main__":
    main()
