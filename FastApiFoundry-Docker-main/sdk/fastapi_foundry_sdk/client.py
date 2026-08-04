# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Foundry SDK — Main Client
# =============================================================================
# Description:
#   Async HTTP client for FastAPI Foundry REST API (port 9696).
#   Covers: health, models, generate, batch, chat, RAG, config,
#   HuggingFace, llama.cpp, Ollama, agents, MCP endpoints.
#
# File: client.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class FastAPIFoundryClient:
    """Async client for FastAPI Foundry REST API.

    Covers all endpoints exposed by the FastAPI Foundry server (port 9696).
    Use as async context manager.

    Example:
        >>> async with FastAPIFoundryClient("http://localhost:9696") as client:
        ...     health = await client.health()
        ...     response = await client.generate("What is Python?")
        ...     print(response["content"])
    """

    def __init__(
        self,
        base_url: str = "http://localhost:9696",
        api_key: Optional[str] = None,
        timeout: int = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "FastAPIFoundryClient":
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        self._session = aiohttp.ClientSession(headers=headers, timeout=self._timeout)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _get(self, path: str) -> Dict[str, Any]:
        async with self._session.get(f"{self.base_url}{path}") as r:
            return await r.json()

    async def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        async with self._session.post(f"{self.base_url}{path}", json=data) as r:
            return await r.json()

    async def _patch(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        async with self._session.patch(f"{self.base_url}{path}", json=data) as r:
            return await r.json()

    # ── Health ────────────────────────────────────────────────────────────────

    async def health(self) -> Dict[str, Any]:
        """GET /api/v1/health — service health check.

        Returns:
            dict: status, foundry_status, llama_status, rag_status, models_count.
        """
        return await self._get("/api/v1/health")

    # ── Models ────────────────────────────────────────────────────────────────

    async def list_models(self) -> Dict[str, Any]:
        """GET /api/v1/models — list all available models across all backends."""
        return await self._get("/api/v1/models")

    async def load_model(self, model_id: str) -> Dict[str, Any]:
        """POST /api/v1/foundry/load — load a Foundry model.

        Args:
            model_id: Model alias, e.g. 'phi-4' or 'qwen3-0.6b-generic-cpu:4:4'.
        """
        return await self._post("/api/v1/foundry/load", {"model_id": model_id})

    async def unload_model(self, model_id: str) -> Dict[str, Any]:
        """POST /api/v1/foundry/unload — unload a Foundry model."""
        return await self._post("/api/v1/foundry/unload", {"model_id": model_id})

    async def foundry_models(self) -> Dict[str, Any]:
        """GET /api/v1/foundry/models — list Foundry catalog models."""
        return await self._get("/api/v1/foundry/models")

    # ── Generate ──────────────────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        use_rag: bool = False,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST /api/v1/generate — generate text with any backend model.

        Args:
            prompt: Input text.
            model: Model ID (Foundry alias, 'hf::model', 'llama::model', 'ollama::model').
            temperature: Sampling temperature.
            max_tokens: Max output tokens.
            use_rag: Inject RAG context into prompt.
            system_prompt: Optional system instruction.

        Returns:
            dict: success, content, model, usage.
        """
        data: Dict[str, Any] = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "use_rag": use_rag,
        }
        if model:
            data["model"] = model
        if system_prompt:
            data["system_prompt"] = system_prompt
        return await self._post("/api/v1/generate", data)

    async def batch_generate(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        use_rag: bool = False,
    ) -> Dict[str, Any]:
        """POST /api/v1/batch-generate — generate text for multiple prompts.

        Args:
            prompts: List of input texts.

        Returns:
            dict: success, results (list), total, succeeded, failed.
        """
        data: Dict[str, Any] = {
            "prompts": prompts,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "use_rag": use_rag,
        }
        if model:
            data["model"] = model
        return await self._post("/api/v1/batch-generate", data)

    # ── RAG ───────────────────────────────────────────────────────────────────

    async def rag_search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """POST /api/v1/rag/search — vector search in FAISS index.

        Args:
            query: Search query text.
            top_k: Number of results to return.

        Returns:
            dict: results (list of chunks with score, source, section).
        """
        return await self._post("/api/v1/rag/search", {"query": query, "top_k": top_k})

    async def rag_reload(self) -> Dict[str, Any]:
        """POST /api/v1/rag/reload — reload FAISS index from disk."""
        return await self._post("/api/v1/rag/reload", {})

    async def rag_status(self) -> Dict[str, Any]:
        """GET /api/v1/rag/status — RAG system status."""
        return await self._get("/api/v1/rag/status")

    # ── Config ────────────────────────────────────────────────────────────────

    async def get_config(self) -> Dict[str, Any]:
        """GET /api/v1/config — read current config.json."""
        return await self._get("/api/v1/config")

    async def patch_config(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        """PATCH /api/v1/config — update config values.

        Args:
            patch: Flat dict with dot-notation keys, e.g.
                   {'foundry_ai.default_model': 'phi-4', 'foundry_ai.temperature': 0.5}
        """
        return await self._patch("/api/v1/config", patch)

    # ── HuggingFace ───────────────────────────────────────────────────────────

    async def hf_list_models(self) -> Dict[str, Any]:
        """GET /api/v1/hf/models — list downloaded HuggingFace models."""
        return await self._get("/api/v1/hf/models")

    async def hf_generate(
        self,
        prompt: str,
        model_id: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """POST /api/v1/hf/generate — generate with HuggingFace Transformers.

        Args:
            model_id: HuggingFace model ID, e.g. 'microsoft/phi-2'.
        """
        return await self._post("/api/v1/hf/generate", {
            "prompt": prompt,
            "model_id": model_id,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
        })

    async def hf_load_model(self, model_id: str) -> Dict[str, Any]:
        """POST /api/v1/hf/load — load a HuggingFace model into memory."""
        return await self._post("/api/v1/hf/load", {"model_id": model_id})

    # ── llama.cpp ─────────────────────────────────────────────────────────────

    async def llama_status(self) -> Dict[str, Any]:
        """GET /api/v1/llama/status — llama.cpp server status."""
        return await self._get("/api/v1/llama/status")

    async def llama_generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """POST /api/v1/llama/generate — generate with llama.cpp (GGUF model)."""
        return await self._post("/api/v1/llama/generate", {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        })

    async def llama_start(self, model_path: str) -> Dict[str, Any]:
        """POST /api/v1/llama/start — start llama.cpp server with a GGUF model.

        Args:
            model_path: Absolute path to .gguf file.
        """
        return await self._post("/api/v1/llama/start", {"model_path": model_path})

    async def llama_stop(self) -> Dict[str, Any]:
        """POST /api/v1/llama/stop — stop llama.cpp server."""
        return await self._post("/api/v1/llama/stop", {})

    # ── Ollama ────────────────────────────────────────────────────────────────

    async def ollama_models(self) -> Dict[str, Any]:
        """GET /api/v1/ollama/models — list Ollama models."""
        return await self._get("/api/v1/ollama/models")

    async def ollama_generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """POST /api/v1/ollama/generate — generate with Ollama."""
        return await self._post("/api/v1/ollama/generate", {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })

    # ── Agent ─────────────────────────────────────────────────────────────────

    async def agent_run(self, task: str, agent_type: str = "default") -> Dict[str, Any]:
        """POST /api/v1/agent/run — run an AI agent task.

        Args:
            task: Task description for the agent.
            agent_type: Agent type identifier.
        """
        return await self._post("/api/v1/agent/run", {"task": task, "agent_type": agent_type})

    # ── MCP ───────────────────────────────────────────────────────────────────

    async def mcp_status(self) -> Dict[str, Any]:
        """GET /api/v1/mcp/status — MCP servers status."""
        return await self._get("/api/v1/mcp/status")

    async def mcp_execute(self, server: str, command: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """POST /api/v1/mcp/execute — execute a command on an MCP server.

        Args:
            server: MCP server name (e.g. 'powershell-stdio').
            command: Command/tool name to execute.
            params: Optional parameters dict.
        """
        return await self._post("/api/v1/mcp/execute", {
            "server": server,
            "command": command,
            "params": params or {},
        })

    # ── Restart ───────────────────────────────────────────────────────────────

    async def restart_service(self, service: str) -> Dict[str, Any]:
        """POST /api/v1/restart/{service} — restart a background service.

        Args:
            service: One of 'foundry', 'llama', 'docs', 'rag'.
        """
        return await self._post(f"/api/v1/restart/{service}", {})
