# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Local Models MCP Server
# =============================================================================
# Description:
#   MCP STDIO server bridging Claude Desktop (and other MCP clients) to local
#   AI models via FastAPI Foundry REST API on localhost:9696.
#
#   Supported tools:
#     - generate       : text generation (Foundry / llama.cpp / Ollama)
#     - chat           : stateful chat with session history
#     - list_models    : list all available local models
#     - rag_search     : semantic search over local knowledge base (RAG)
#     - health         : check FastAPI Foundry service status
#
#   Model routing (same as FastAPI Foundry):
#     no prefix        -> Foundry Local (ONNX)
#     llama::<path>    -> llama.cpp
#     ollama::<name>   -> Ollama
#     hf::<name>       -> HuggingFace Transformers
#
# Examples:
#   python local_models_mcp.py
#   FASTAPI_BASE_URL=http://localhost:9696 python local_models_mcp.py
#
# File: mcp-powershell-servers/src/servers/local_models_mcp.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
import logging
import os
import sys
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# ---------------------------------------------------------------------------
# Logging — file only, never stdout (STDIO protocol uses stdout for JSON-RPC)
# ---------------------------------------------------------------------------
_log_path = os.path.join(os.environ.get("TEMP", "/tmp"), "mcp-local-models.log")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(_log_path, encoding="utf-8")],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FASTAPI_BASE_URL: str = os.getenv("FASTAPI_BASE_URL", "http://localhost:9696")
HTTP_TIMEOUT: int = int(os.getenv("MCP_HTTP_TIMEOUT", "120"))

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
server: Server = Server("local-models-mcp")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Return all tools exposed by this MCP server."""
    return [
        types.Tool(
            name="generate",
            description=(
                "Generate text using a local AI model via FastAPI Foundry. "
                "Model prefixes: 'llama::' for llama.cpp, 'ollama::' for Ollama, "
                "'hf::' for HuggingFace, no prefix for Foundry Local."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Input prompt"},
                    "model": {
                        "type": "string",
                        "description": "Model ID with optional prefix",
                        "default": "",
                    },
                    "max_tokens": {"type": "integer", "default": 512},
                    "temperature": {"type": "number", "default": 0.7},
                },
                "required": ["prompt"],
            },
        ),
        types.Tool(
            name="chat",
            description="Send a chat message to a local AI model (stateful session).",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "User message"},
                    "model": {"type": "string", "default": ""},
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for history continuity (optional)",
                        "default": "mcp-default",
                    },
                    "max_tokens": {"type": "integer", "default": 512},
                },
                "required": ["message"],
            },
        ),
        types.Tool(
            name="list_models",
            description="List all available local AI models (Foundry, llama.cpp, Ollama, HuggingFace).",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="rag_search",
            description="Semantic search over the local RAG knowledge base (FAISS index).",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "default": 3, "description": "Number of results"},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="health",
            description="Check FastAPI Foundry service health and Foundry status.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Dispatch tool calls to FastAPI Foundry REST API.

    Args:
        name (str): Tool name.
        arguments (dict[str, Any]): Tool arguments.

    Returns:
        list[types.TextContent]: Response content.
    """
    logger.info(f"Tool call: {name}, args: {list(arguments.keys())}")

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            text = await _dispatch(client, name, arguments)
    except httpx.ConnectError:
        text = (
            f"❌ Cannot connect to FastAPI Foundry at {FASTAPI_BASE_URL}. "
            "Make sure the server is running: `venv\\Scripts\\python.exe run.py`"
        )
        logger.error(text)
    except httpx.TimeoutException:
        text = f"❌ Request timed out after {HTTP_TIMEOUT}s. The model may still be loading."
        logger.error(text)
    except Exception as ex:
        text = f"❌ Unexpected error: {ex}"
        logger.error(text, exc_info=True)

    return [types.TextContent(type="text", text=text)]


async def _dispatch(client: httpx.AsyncClient, name: str, arguments: dict[str, Any]) -> str:
    """Route tool name to the correct FastAPI endpoint.

    Args:
        client (httpx.AsyncClient): Shared HTTP client.
        name (str): Tool name.
        arguments (dict[str, Any]): Tool arguments.

    Returns:
        str: Response text.
    """
    if name == "generate":
        resp = await client.post(
            f"{FASTAPI_BASE_URL}/api/v1/generate",
            json={
                "prompt": arguments["prompt"],
                "model": arguments.get("model", ""),
                "max_tokens": arguments.get("max_tokens", 512),
                "temperature": arguments.get("temperature", 0.7),
            },
        )
        data = resp.json()
        if data.get("success"):
            return data.get("content", "")
        return f"❌ {data.get('error', 'Generation failed')}"

    if name == "chat":
        resp = await client.post(
            f"{FASTAPI_BASE_URL}/api/v1/ai/chat",
            json={
                "message": arguments["message"],
                "model": arguments.get("model", ""),
                "session_id": arguments.get("session_id", "mcp-default"),
                "max_tokens": arguments.get("max_tokens", 512),
            },
        )
        data = resp.json()
        if data.get("success"):
            return data.get("content", "")
        return f"❌ {data.get('error', 'Chat failed')}"

    if name == "list_models":
        resp = await client.get(f"{FASTAPI_BASE_URL}/api/v1/models")
        data = resp.json()
        models = data.get("models", data)
        return json.dumps(models, ensure_ascii=False, indent=2)

    if name == "rag_search":
        resp = await client.post(
            f"{FASTAPI_BASE_URL}/api/v1/rag/search",
            json={
                "query": arguments["query"],
                "top_k": arguments.get("top_k", 3),
            },
        )
        data = resp.json()
        results = data.get("results", data)
        return json.dumps(results, ensure_ascii=False, indent=2)

    if name == "health":
        resp = await client.get(f"{FASTAPI_BASE_URL}/api/v1/health")
        return json.dumps(resp.json(), ensure_ascii=False, indent=2)

    return f"❌ Unknown tool: {name}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def main() -> None:
    """Start MCP STDIO server."""
    logger.info(f"Starting local-models-mcp, FastAPI base: {FASTAPI_BASE_URL}")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
