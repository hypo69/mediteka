# -*- coding: utf-8 -*-
"""Local content blocks API.

These endpoints expose structured content that can be rendered by external
surfaces such as WordPress blocks without coupling WordPress to MkDocs.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/content", tags=["content"])

_ROOT = Path(__file__).resolve().parents[3]
_BLOCKS_DIR = _ROOT / "content" / "blocks"


def _block_path(slug: str) -> Path:
    if not slug.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid block slug")
    return _BLOCKS_DIR / f"{slug}.json"


def _load_block(slug: str) -> dict[str, Any]:
    path = _block_path(slug)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Content block not found")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid block JSON: {exc}") from exc


def _render_block_html(block: dict[str, Any]) -> str:
    title = html.escape(str(block.get("title", "")))
    subtitle = html.escape(str(block.get("subtitle", "")))
    summary = html.escape(str(block.get("summary", "")))
    status = html.escape(str(block.get("status", "")))
    version = html.escape(str(block.get("version", "")))
    updated_at = html.escape(str(block.get("updated_at", "")))
    sections = block.get("sections") or []

    section_html = "\n".join(
        "<section class=\"ff-dimitrieva-section\">"
        f"<h3>{html.escape(str(section.get('heading', '')))}</h3>"
        f"<p>{html.escape(str(section.get('body', '')))}</p>"
        "</section>"
        for section in sections
        if isinstance(section, dict)
    )

    return f"""
<article class="ff-dimitrieva-block" data-content-block="dimitrieva">
  <header class="ff-dimitrieva-header">
    <p class="ff-dimitrieva-kicker">AI sterile environment</p>
    <h2>{title}</h2>
    <p class="ff-dimitrieva-subtitle">{subtitle}</p>
    <p class="ff-dimitrieva-summary">{summary}</p>
    <p class="ff-dimitrieva-meta">status: {status} · version: {version} · updated: {updated_at}</p>
  </header>
  <div class="ff-dimitrieva-sections">
    {section_html}
  </div>
</article>
""".strip()


@router.get("/blocks")
async def list_content_blocks() -> dict[str, Any]:
    """List locally available content blocks."""
    blocks = []
    for path in sorted(_BLOCKS_DIR.glob("*.json")):
        try:
            block = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        blocks.append({
            "slug": block.get("slug", path.stem),
            "title": block.get("title", path.stem),
            "status": block.get("status", "unknown"),
            "updated_at": block.get("updated_at", ""),
        })
    return {"success": True, "blocks": blocks}


@router.get("/blocks/{slug}")
async def get_content_block(slug: str) -> dict[str, Any]:
    """Return a structured content block."""
    return {"success": True, "block": _load_block(slug)}


@router.get("/blocks/{slug}/html", response_class=HTMLResponse)
async def get_content_block_html(slug: str) -> HTMLResponse:
    """Return a sanitized HTML rendering of a content block."""
    return HTMLResponse(_render_block_html(_load_block(slug)))
