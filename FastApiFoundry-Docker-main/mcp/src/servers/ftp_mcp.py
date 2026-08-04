# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FTP MCP Server
# =============================================================================
# Description:
#   MCP server for working with FTP servers.
#   Credentials are read from environment variables (set in .env):
#     FTP_HOST, FTP_USER, FTP_PASSWORD, FTP_PORT (default: 21)
#
#   Tools:
#     ftp_list     — list files in a directory
#     ftp_upload   — upload a local file to FTP
#     ftp_download — download a file from FTP to local path
#     ftp_delete   — delete a file on FTP
#     ftp_rename   — rename or move a file on FTP
#
# Examples:
#   python ./mcp-powershell-servers/src/servers/ftp_mcp.py
#
# File: mcp-powershell-servers/src/servers/ftp_mcp.py
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


def _get_ftp_connection() -> ftplib.FTP:
    """Create and return an authenticated FTP connection.

    Reads FTP_HOST, FTP_USER, FTP_PASSWORD, FTP_PORT from environment.

    Returns:
        ftplib.FTP: Connected and authenticated FTP instance.

    Raises:
        ValueError: If required env vars are missing.
        ftplib.all_errors: On connection or auth failure.
    """
    host = os.getenv("FTP_HOST", "")
    user = os.getenv("FTP_USER", "")
    password = os.getenv("FTP_PASSWORD", "")
    port = int(os.getenv("FTP_PORT", "21"))

    if not host or not user or not password:
        raise ValueError("FTP_HOST, FTP_USER and FTP_PASSWORD must be set in .env")

    ftp = ftplib.FTP()
    ftp.connect(host, port, timeout=30)
    ftp.login(user, password)
    ftp.set_pasv(True)
    return ftp


class FtpMCPServer:
    """MCP server for FTP file operations.

    Reads connection parameters from environment variables:
        FTP_HOST     — FTP server hostname or IP
        FTP_USER     — FTP username
        FTP_PASSWORD — FTP password
        FTP_PORT     — FTP port (default: 21)
    """

    def __init__(self) -> None:
        self.server: Server = Server("ftp-mcp")
        self.server.list_tools().callback(self.list_tools)
        self.server.call_tool().callback(self.call_tool)
        logger.info("FTP MCP server initialized")

    async def list_tools(self) -> list[types.Tool]:
        """Return the list of available FTP tools.

        Returns:
            list[types.Tool]: Tool definitions for all FTP operations.
        """
        return [
            types.Tool(
                name="ftp_list",
                description="List files and directories on FTP server",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "default": "/",
                            "description": "Remote directory path (default: /)"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="ftp_upload",
                description="Upload a local file to FTP server",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "local_path": {
                            "type": "string",
                            "description": "Absolute local path to the file"
                        },
                        "remote_path": {
                            "type": "string",
                            "description": "Destination path on FTP (e.g. /public_html/file.txt)"
                        }
                    },
                    "required": ["local_path", "remote_path"]
                }
            ),
            types.Tool(
                name="ftp_download",
                description="Download a file from FTP server to local path",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "remote_path": {
                            "type": "string",
                            "description": "Path to the file on FTP"
                        },
                        "local_path": {
                            "type": "string",
                            "description": "Local destination path"
                        }
                    },
                    "required": ["remote_path", "local_path"]
                }
            ),
            types.Tool(
                name="ftp_delete",
                description="Delete a file on FTP server",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "remote_path": {
                            "type": "string",
                            "description": "Path to the file on FTP to delete"
                        }
                    },
                    "required": ["remote_path"]
                }
            ),
            types.Tool(
                name="ftp_rename",
                description="Rename or move a file on FTP server",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "from_path": {
                            "type": "string",
                            "description": "Current path of the file on FTP"
                        },
                        "to_path": {
                            "type": "string",
                            "description": "New path / name on FTP"
                        }
                    },
                    "required": ["from_path", "to_path"]
                }
            ),
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
        """Dispatch a tool call to the appropriate FTP operation.

        Args:
            name: Tool name.
            arguments: Tool arguments dict.

        Returns:
            list[types.TextContent]: Result as text content.
        """
        logger.info(f"FTP tool call: {name}")

        try:
            if name == "ftp_list":
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._ftp_list, arguments.get("path", "/")
                )
            if name == "ftp_upload":
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._ftp_upload,
                    arguments["local_path"], arguments["remote_path"]
                )
            if name == "ftp_download":
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._ftp_download,
                    arguments["remote_path"], arguments["local_path"]
                )
            if name == "ftp_delete":
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._ftp_delete, arguments["remote_path"]
                )
            if name == "ftp_rename":
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._ftp_rename,
                    arguments["from_path"], arguments["to_path"]
                )
        except Exception as e:
            logger.error(f"FTP error in {name}: {e}")
            return [types.TextContent(type="text", text=f"❌ FTP error: {e}")]

        raise ValueError(f"Unknown tool: {name}")

    def _ftp_list(self, path: str) -> list[types.TextContent]:
        """List files in a remote directory.

        Args:
            path: Remote directory path.

        Returns:
            list[types.TextContent]: Directory listing as text.
        """
        ftp = _get_ftp_connection()
        try:
            lines: list[str] = []
            ftp.cwd(path)
            ftp.retrlines("LIST", lines.append)
            result = f"📁 {path}:\n" + "\n".join(lines) if lines else f"📁 {path}: (empty)"
            return [types.TextContent(type="text", text=result)]
        finally:
            ftp.quit()

    def _ftp_upload(self, local_path: str, remote_path: str) -> list[types.TextContent]:
        """Upload a local file to FTP.

        Args:
            local_path: Local file path.
            remote_path: Destination path on FTP.

        Returns:
            list[types.TextContent]: Success or error message.
        """
        src = Path(local_path)
        if not src.exists():
            return [types.TextContent(type="text", text=f"❌ Local file not found: {local_path}")]

        ftp = _get_ftp_connection()
        try:
            with open(src, "rb") as f:
                ftp.storbinary(f"STOR {remote_path}", f)
            size_kb = round(src.stat().st_size / 1024, 1)
            return [types.TextContent(type="text", text=f"✅ Uploaded {src.name} ({size_kb} KB) → {remote_path}")]
        finally:
            ftp.quit()

    def _ftp_download(self, remote_path: str, local_path: str) -> list[types.TextContent]:
        """Download a file from FTP.

        Args:
            remote_path: File path on FTP.
            local_path: Local destination path.

        Returns:
            list[types.TextContent]: Success or error message.
        """
        dest = Path(local_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        ftp = _get_ftp_connection()
        try:
            with open(dest, "wb") as f:
                ftp.retrbinary(f"RETR {remote_path}", f.write)
            size_kb = round(dest.stat().st_size / 1024, 1)
            return [types.TextContent(type="text", text=f"✅ Downloaded {remote_path} → {local_path} ({size_kb} KB)")]
        finally:
            ftp.quit()

    def _ftp_delete(self, remote_path: str) -> list[types.TextContent]:
        """Delete a file on FTP.

        Args:
            remote_path: File path on FTP to delete.

        Returns:
            list[types.TextContent]: Success or error message.
        """
        ftp = _get_ftp_connection()
        try:
            ftp.delete(remote_path)
            return [types.TextContent(type="text", text=f"✅ Deleted: {remote_path}")]
        finally:
            ftp.quit()

    def _ftp_rename(self, from_path: str, to_path: str) -> list[types.TextContent]:
        """Rename or move a file on FTP.

        Args:
            from_path: Current file path on FTP.
            to_path: New file path on FTP.

        Returns:
            list[types.TextContent]: Success or error message.
        """
        ftp = _get_ftp_connection()
        try:
            ftp.rename(from_path, to_path)
            return [types.TextContent(type="text", text=f"✅ Renamed: {from_path} → {to_path}")]
        finally:
            ftp.quit()

    async def run(self) -> None:
        """Start the MCP server STDIO loop."""
        logger.info("Starting FTP MCP server")
        await self.server.run()


async def main() -> None:
    """Entry point."""
    server = FtpMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
