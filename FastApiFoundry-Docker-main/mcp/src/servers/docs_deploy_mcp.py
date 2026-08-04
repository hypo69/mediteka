# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Docs Deploy MCP Server
# =============================================================================
# Description:
#   MCP STDIO server for deploying MkDocs built documentation to FTP.
#
#   Reads from environment (.env):
#     FTP_HOST, FTP_USER, FTP_PASSWORD, FTP_PORT (default: 21)
#     FTP_DOCS_RU  — remote path for Russian docs
#     FTP_DOCS_EN  — remote path for English docs
#
#   Tools:
#     docs_deploy_ru  — upload site/ru/ to FTP_DOCS_RU
#     docs_deploy_en  — upload site/en/ to FTP_DOCS_EN
#     docs_deploy_all — upload both languages
#     docs_status     — check remote docs directories on FTP
#
#   Workflow:
#     1. mkdocs build  →  site/ is generated locally
#     2. docs_deploy_ru / docs_deploy_en  →  upload to FTP
#
# Examples:
#   python ./mcp/src/servers/docs_deploy_mcp.py
#
# File: mcp/src/servers/docs_deploy_mcp.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import ftplib
import os
from pathlib import Path
from typing import Any

from mcp import Server, types

try:
    from src.logger.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)


def _ftp_connect() -> ftplib.FTP:
    """Create authenticated FTP connection from environment variables.

    Returns:
        ftplib.FTP: Connected and logged-in FTP instance.

    Raises:
        ValueError: If required env vars are missing.
    """
    host = os.getenv("FTP_HOST", "")
    user = os.getenv("FTP_USER", "")
    password = os.getenv("FTP_PASSWORD", "")
    port = int(os.getenv("FTP_PORT", "21"))

    if not host or not user or not password:
        raise ValueError("FTP_HOST, FTP_USER and FTP_PASSWORD must be set in .env")

    ftp = ftplib.FTP()
    ftp.connect(host, port, timeout=60)
    ftp.login(user, password)
    ftp.set_pasv(True)
    return ftp


def _ftp_mkdir_p(ftp: ftplib.FTP, remote_path: str) -> None:
    """Recursively create remote directories (like mkdir -p).

    Args:
        ftp: Active FTP connection.
        remote_path: Remote directory path to create.
    """
    parts = [p for p in remote_path.replace("\\", "/").split("/") if p]
    current = ""
    for part in parts:
        current = f"{current}/{part}"
        try:
            ftp.mkd(current)
        except ftplib.error_perm:
            pass  # Already exists


def _upload_dir(ftp: ftplib.FTP, local_dir: Path, remote_dir: str) -> tuple[int, int]:
    """Recursively upload a local directory to FTP.

    Args:
        ftp: Active FTP connection.
        local_dir: Local directory to upload.
        remote_dir: Remote destination path.

    Returns:
        tuple[int, int]: (files_uploaded, bytes_uploaded)
    """
    files_count = 0
    bytes_count = 0

    _ftp_mkdir_p(ftp, remote_dir)

    for item in sorted(local_dir.iterdir()):
        remote_path = f"{remote_dir}/{item.name}"
        if item.is_dir():
            sub_files, sub_bytes = _upload_dir(ftp, item, remote_path)
            files_count += sub_files
            bytes_count += sub_bytes
        elif item.is_file():
            with open(item, "rb") as f:
                ftp.storbinary(f"STOR {remote_path}", f)
            files_count += 1
            bytes_count += item.stat().st_size

    return files_count, bytes_count


def _deploy_lang(lang: str) -> dict:
    """Deploy built docs for one language to FTP.

    Args:
        lang: Language code — 'ru' or 'en'.

    Returns:
        dict: success, files, size_mb, remote_path, error.
    """
    env_key = f"FTP_DOCS_{lang.upper()}"
    remote_path = os.getenv(env_key, "")
    if not remote_path:
        return {"success": False, "error": f"{env_key} not set in .env"}

    # MkDocs builds to site/ — language subdirs are site/ru/, site/en/
    local_dir = Path("site") / lang
    if not local_dir.exists():
        return {
            "success": False,
            "error": f"Local build not found: {local_dir}. Run: mkdocs build"
        }

    try:
        ftp = _ftp_connect()
        files, total_bytes = _upload_dir(ftp, local_dir, remote_path)
        ftp.quit()
        size_mb = round(total_bytes / 1024 / 1024, 2)
        logger.info(f"✅ Deployed {lang}: {files} files ({size_mb} MB) → {remote_path}")
        return {
            "success": True,
            "lang": lang,
            "files": files,
            "size_mb": size_mb,
            "remote_path": remote_path,
        }
    except Exception as e:
        logger.error(f"❌ Deploy {lang} failed: {e}")
        return {"success": False, "lang": lang, "error": str(e)}


class DocsDeployMCPServer:
    """MCP server for deploying MkDocs documentation to FTP.

    Environment variables (from .env):
        FTP_HOST        — FTP server hostname or IP
        FTP_USER        — FTP username
        FTP_PASSWORD    — FTP password
        FTP_PORT        — FTP port (default: 21)
        FTP_DOCS_RU     — remote path for Russian docs
        FTP_DOCS_EN     — remote path for English docs
    """

    def __init__(self) -> None:
        self.server: Server = Server("docs-deploy-mcp")
        self.server.list_tools().callback(self.list_tools)
        self.server.call_tool().callback(self.call_tool)
        logger.info("Docs Deploy MCP server initialized")

    async def list_tools(self) -> list[types.Tool]:
        """Return available deployment tools."""
        return [
            types.Tool(
                name="docs_deploy_ru",
                description=(
                    "Deploy Russian documentation (site/ru/) to FTP. "
                    f"Remote path: {os.getenv('FTP_DOCS_RU', 'FTP_DOCS_RU not set')}. "
                    "Run mkdocs build first."
                ),
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="docs_deploy_en",
                description=(
                    "Deploy English documentation (site/en/) to FTP. "
                    f"Remote path: {os.getenv('FTP_DOCS_EN', 'FTP_DOCS_EN not set')}. "
                    "Run mkdocs build first."
                ),
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="docs_deploy_all",
                description="Deploy both Russian and English documentation to FTP.",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="docs_build_and_deploy",
                description=(
                    "Build MkDocs documentation and deploy all languages to FTP. "
                    "Runs: mkdocs build → upload ru → upload en."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "lang": {
                            "type": "string",
                            "description": "Language to deploy: 'ru', 'en', or 'all' (default: 'all')",
                            "default": "all"
                        }
                    }
                },
            ),
            types.Tool(
                name="docs_status",
                description="Check remote docs directories on FTP (list files count per language).",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
        """Dispatch tool calls.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            list[types.TextContent]: Result as text.
        """
        logger.info(f"Docs deploy tool: {name}")
        try:
            if name == "docs_deploy_ru":
                result = await asyncio.get_event_loop().run_in_executor(None, _deploy_lang, "ru")
                return [types.TextContent(type="text", text=self._fmt(result))]

            if name == "docs_deploy_en":
                result = await asyncio.get_event_loop().run_in_executor(None, _deploy_lang, "en")
                return [types.TextContent(type="text", text=self._fmt(result))]

            if name == "docs_deploy_all":
                ru = await asyncio.get_event_loop().run_in_executor(None, _deploy_lang, "ru")
                en = await asyncio.get_event_loop().run_in_executor(None, _deploy_lang, "en")
                lines = [self._fmt(ru), self._fmt(en)]
                return [types.TextContent(type="text", text="\n".join(lines))]

            if name == "docs_build_and_deploy":
                lang = arguments.get("lang", "all")
                # Build first
                build_result = await self._build_docs()
                if not build_result["success"]:
                    return [types.TextContent(type="text", text=f"❌ Build failed: {build_result['error']}")]

                lines = [f"✅ Build complete ({build_result.get('output', '')[:200]})"]
                langs = ["ru", "en"] if lang == "all" else [lang]
                for l in langs:
                    r = await asyncio.get_event_loop().run_in_executor(None, _deploy_lang, l)
                    lines.append(self._fmt(r))
                return [types.TextContent(type="text", text="\n".join(lines))]

            if name == "docs_status":
                result = await asyncio.get_event_loop().run_in_executor(None, self._check_status)
                return [types.TextContent(type="text", text=result)]

        except Exception as e:
            logger.error(f"Tool {name} error: {e}")
            return [types.TextContent(type="text", text=f"❌ Error: {e}")]

        raise ValueError(f"Unknown tool: {name}")

    async def _build_docs(self) -> dict:
        """Run mkdocs build subprocess.

        Returns:
            dict: success, output, error.
        """
        proc = await asyncio.create_subprocess_exec(
            "mkdocs", "build",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
        output = stdout.decode("utf-8", errors="replace") if stdout else ""
        if proc.returncode == 0:
            return {"success": True, "output": output}
        return {"success": False, "error": output}

    def _check_status(self) -> str:
        """List file counts in remote docs directories.

        Returns:
            str: Status text with file counts per language.
        """
        lines = []
        for lang in ("ru", "en"):
            env_key = f"FTP_DOCS_{lang.upper()}"
            remote_path = os.getenv(env_key, "")
            if not remote_path:
                lines.append(f"⚠️  {lang}: {env_key} not set")
                continue
            try:
                ftp = _ftp_connect()
                items: list[str] = []
                try:
                    ftp.retrlines(f"LIST {remote_path}", items.append)
                except ftplib.error_perm:
                    items = []
                ftp.quit()
                lines.append(f"✅ {lang}: {len(items)} items at {remote_path}")
            except Exception as e:
                lines.append(f"❌ {lang}: {e}")
        return "\n".join(lines)

    @staticmethod
    def _fmt(result: dict) -> str:
        """Format deploy result as human-readable string.

        Args:
            result: Result dict from _deploy_lang.

        Returns:
            str: Formatted status line.
        """
        lang = result.get("lang", "?")
        if result.get("success"):
            return (
                f"✅ {lang}: {result['files']} files "
                f"({result['size_mb']} MB) → {result['remote_path']}"
            )
        return f"❌ {lang}: {result.get('error', 'unknown error')}"

    async def run(self) -> None:
        """Start the MCP STDIO server."""
        logger.info("Starting Docs Deploy MCP server")
        await self.server.run()


async def main() -> None:
    """Entry point."""
    server = DocsDeployMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
