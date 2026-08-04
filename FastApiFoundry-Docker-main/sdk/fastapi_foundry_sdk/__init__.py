# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Foundry SDK — Public API
# =============================================================================
# Description:
#   SDK for FastAPI Foundry project. Covers all capabilities:
#   text generation, chat, RAG, batch, model management,
#   MCP PowerShell servers, HuggingFace, llama.cpp, Ollama.
#
# File: __init__.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .client import FastAPIFoundryClient
from .mcp_client import MCPPowerShellClient

__all__ = [
    "FastAPIFoundryClient",
    "MCPPowerShellClient",
]
