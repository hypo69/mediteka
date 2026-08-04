# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Ollama Local Model Client
# =============================================================================
# Description:
#   Async client for Ollama — a local AI model server with OpenAI-compatible API.
#   Supports listing available models, pulling new models from Ollama Hub,
#   deleting models, and text generation via /api/generate.
#
# Examples:
#   >>> from src.models.ollama_client import ollama_client
#   >>> await ollama_client.list_models()
#   >>> await ollama_client.pull_model("qwen2.5:0.5b")
#   >>> result = await ollama_client.generate("Hello", model="qwen2.5:0.5b")
#
# File: src/models/ollama_client.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
import os
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_HOST = "http://localhost:11434"


def _get_base_url() -> str:
    """Get Ollama base URL from env or config.json.

    Returns:
        str: Base URL, e.g. http://localhost:11434
    """
    env_url = os.getenv("OLLAMA_BASE_URL", "")
    if env_url:
        return env_url.rstrip("/")
    try:
        from ..core.config import config
        url = config.get_section("ollama").get("base_url", DEFAULT_HOST)
        return url.rstrip("/")
    except Exception:
        return DEFAULT_HOST


class OllamaClient:
    """Async client for Ollama local model server.

    Communicates with Ollama REST API (http://localhost:11434).
    All methods return {"success": bool, ...} — never raise to callers.

    Example:
        >>> from src.models.ollama_client import ollama_client
        >>> import asyncio
        >>> asyncio.run(ollama_client.list_models())
        {"success": True, "models": [...]}
    """

    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = aiohttp.ClientTimeout(total=300)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Lazy-init aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_status(self) -> dict:
        """Check if Ollama server is reachable.

        Returns:
            dict: {"success": bool, "running": bool, "url": str, "version": str}
        """
        url = _get_base_url()
        try:
            session = await self._get_session()
            async with session.get(f"{url}/api/version", timeout=aiohttp.ClientTimeout(total=3)) as r:
                data = await r.json()
                return {
                    "success": True,
                    "running": True,
                    "url": url,
                    "openai_url": f"{url}/v1",
                    "version": data.get("version", "unknown"),
                }
        except Exception as e:
            return {"success": True, "running": False, "url": url, "openai_url": f"{url}/v1", "error": str(e)}

    async def list_models(self) -> dict:
        """List locally available Ollama models.

        Returns:
            dict: {"success": bool, "models": [{"name": str, "size_gb": float, ...}]}
        """
        url = _get_base_url()
        try:
            session = await self._get_session()
            async with session.get(f"{url}/api/tags") as r:
                if r.status != 200:
                    return {"success": False, "error": f"HTTP {r.status}"}
                data = await r.json()
                models = [
                    {
                        "name": m.get("name", ""),
                        "size_gb": round(m.get("size", 0) / 1024 ** 3, 2),
                        "modified_at": m.get("modified_at", ""),
                        "digest": m.get("digest", "")[:12],
                    }
                    for m in data.get("models", [])
                ]
                return {"success": True, "models": models, "count": len(models)}
        except Exception as e:
            logger.debug(f"Ollama list_models: server not available ({e})")
            return {"success": False, "error": str(e)}

    async def pull_model(self, model: str) -> dict:
        """Pull (download) a model from Ollama Hub.

        Args:
            model: Model name, e.g. "qwen2.5:0.5b" or "llama3.2:1b".

        Returns:
            dict: {"success": bool, "model": str}
        """
        url = _get_base_url()
        try:
            session = await self._get_session()
            async with session.post(
                f"{url}/api/pull",
                json={"name": model, "stream": False},
                timeout=aiohttp.ClientTimeout(total=3600),
            ) as r:
                data = await r.json()
                if r.status != 200:
                    return {"success": False, "error": data.get("error", f"HTTP {r.status}")}
                logger.info(f"✅ Ollama pulled: {model}")
                return {"success": True, "model": model, "status": data.get("status", "success")}
        except Exception as e:
            logger.error(f"❌ Ollama pull error ({model}): {e}")
            return {"success": False, "error": str(e)}

    async def delete_model(self, model: str) -> dict:
        """Delete a local Ollama model.

        Args:
            model: Model name, e.g. "qwen2.5:0.5b".

        Returns:
            dict: {"success": bool, "model": str}
        """
        url = _get_base_url()
        try:
            session = await self._get_session()
            async with session.delete(f"{url}/api/delete", json={"name": model}) as r:
                if r.status not in (200, 204):
                    text = await r.text()
                    return {"success": False, "error": text or f"HTTP {r.status}"}
                logger.info(f"✅ Ollama deleted: {model}")
                return {"success": True, "model": model}
        except Exception as e:
            logger.error(f"❌ Ollama delete error ({model}): {e}")
            return {"success": False, "error": str(e)}

    async def generate(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> dict:
        """Generate text via Ollama /api/generate.

        Args:
            prompt:      Input text.
            model:       Model name, e.g. "qwen2.5:0.5b".
            max_tokens:  Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            dict: {"success": bool, "content": str, "model": str}
        """
        url = _get_base_url()
        try:
            session = await self._get_session()
            async with session.post(
                f"{url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens, "temperature": temperature},
                },
            ) as r:
                data = await r.json()
                if r.status != 200:
                    return {"success": False, "error": data.get("error", f"HTTP {r.status}")}
                return {"success": True, "content": data.get("response", ""), "model": model}
        except Exception as e:
            logger.error(f"❌ Ollama generate error ({model}): {e}")
            return {"success": False, "error": str(e)}


ollama_client = OllamaClient()
