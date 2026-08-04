# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Client
# =============================================================================
# Description:
#   Thin async adapter for Microsoft Foundry Local using native REST API.
#
#   Uses Foundry Local REST API endpoints:
#     GET  /openai/status          - server status
#     GET  /openai/models          - cached models list
#     GET  /openai/loadedmodels    - loaded models list
#     GET  /openai/load/{name}     - load model into memory
#     GET  /openai/unload/{name}   - unload model from memory
#     POST /v1/chat/completions    - inference (OpenAI-compatible)
#
# File: foundry_client.py
# Project: AI Assistant (ai_assist)
# =============================================================================

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import AsyncIterator
from urllib.parse import urlparse

import aiohttp

from ..utils.foundry_utils import find_foundry_url

logger = logging.getLogger(__name__)


class FoundryClient:
    """Small OpenAI-compatible client for Foundry Local."""

    def __init__(self, base_url: str | None = None) -> None:
        env_port = os.getenv("FOUNDRY_DYNAMIC_PORT")
        self.base_url: str | None = base_url or (
            f"http://127.0.0.1:{env_port}/v1/" if env_port else None
        )
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.session: aiohttp.ClientSession | None = None
        logger.info("Foundry client: %s", self.base_url or "waiting for URL...")

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()

    async def _url_ok(self, base_url: str | None) -> bool:
        if not base_url:
            return False
        try:
            timeout = aiohttp.ClientTimeout(total=2)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{base_url.rstrip('/')}/models") as response:
                    return response.status == 200
        except Exception:
            return False

    async def _update_base_url(self) -> None:
        """Find the live Foundry OpenAI-compatible URL.

        Config is only a hint. The source of truth is the URL that actually
        answers GET /models.
        """
        from ..core.config import config

        candidates = [
            self.base_url,
            os.getenv("FOUNDRY_BASE_URL"),
            config.foundry_base_url,
            find_foundry_url(),
        ]

        seen: set[str] = set()
        for candidate in candidates:
            if not candidate:
                continue
            url = candidate.rstrip("/") + "/"
            if url in seen:
                continue
            seen.add(url)
            if await self._url_ok(url):
                self.base_url = url
                return

        self.base_url = None

    async def _request_json(self, method: str, path: str, **kwargs: object) -> tuple[int, object]:
        await self._update_base_url()
        if not self.base_url:
            return 0, {"error": "Foundry недоступен"}

        session = await self._get_session()
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        async with session.request(method, url, **kwargs) as response:
            text = await response.text()
            if not text:
                return response.status, {}
            try:
                return response.status, json.loads(text)
            except json.JSONDecodeError:
                return response.status, {"error": text}

    def _port(self) -> int | None:
        try:
            return urlparse(self.base_url or "").port
        except ValueError:
            return None

    async def health_check(self) -> dict:
        await self._update_base_url()
        if not self.base_url:
            return {
                "status": "disconnected",
                "error": "Foundry не найден",
                "url": None,
                "port": None,
                "timestamp": datetime.now().isoformat(),
            }

        status, data = await self._request_json("GET", "/models")
        if status == 200 and isinstance(data, dict):
            return {
                "status": "healthy",
                "models_count": len(data.get("data", [])),
                "url": self.base_url,
                "port": self._port(),
                "timestamp": datetime.now().isoformat(),
            }

        error = data.get("error") if isinstance(data, dict) else str(data)
        return {
            "status": "unhealthy",
            "error": f"HTTP {status}: {error}",
            "url": self.base_url,
            "port": self._port(),
            "timestamp": datetime.now().isoformat(),
        }

    async def list_available_models(self) -> dict:
        """Return cached models from Foundry /openai/models.

        Returns list of models that are already downloaded/cached locally.
        For full catalog, use /foundry/list endpoint.
        """
        status, data = await self._request_json("GET", "/openai/models")
        if status != 200 or not isinstance(data, list):
            error = data.get("error") if isinstance(data, dict) else str(data)
            return {"success": False, "error": f"HTTP {status}: {error}", "models": []}

        # Convert string list to model objects with id
        models = [{"id": m, "name": m} for m in data]
        return {"success": True, "models": models, "count": len(models)}

    async def list_models(self) -> dict:
        return await self.list_available_models()

    async def list_running_models(self) -> dict:
        """Return models actually loaded in memory using /openai/loadedmodels.

        This is the native Foundry endpoint for getting loaded models list.
        """
        status, data = await self._request_json("GET", "/openai/loadedmodels")
        if status != 200 or not isinstance(data, list):
            error = data.get("error") if isinstance(data, dict) else str(data)
            return {"success": False, "error": f"HTTP {status}: {error}", "models": []}

        # Convert string list to model objects
        models = [{"id": m, "name": m, "status": "loaded"} for m in data]
        return {"success": True, "models": models, "count": len(models), "source": "foundry-openai-loadedmodels"}

    async def load_model(self, model_id: str) -> dict:
        """Load model into memory using native /openai/load/{name} endpoint.

        Uses Foundry's native load endpoint instead of inference warm-up.
        Supports TTL and execution provider parameters.
        """
        logger.info("Loading Foundry model via native API: %s", model_id)
        
        # GET /openai/load/{name}?ttl=3600
        status, data = await self._request_json("GET", f"/openai/load/{model_id}?ttl=3600")
        
        if status == 200:
            return {"success": True, "message": f"Model {model_id} loaded", "model_id": model_id}
        
        error = data.get("error") if isinstance(data, dict) else str(data)
        return {"success": False, "error": f"HTTP {status}: {error}"}

    async def unload_model(self, model_id: str) -> dict:
        """Unload model from memory using native /openai/unload/{name} endpoint.

        Uses Foundry's native unload endpoint instead of SDK.
        """
        logger.info("Unloading Foundry model via native API: %s", model_id)
        
        # GET /openai/unload/{name}
        status, data = await self._request_json("GET", f"/openai/unload/{model_id}")
        
        if status == 200:
            return {"success": True, "message": f"Model {model_id} unloaded", "model_id": model_id}
        
        error = data.get("error") if isinstance(data, dict) else str(data)
        return {"success": False, "error": f"HTTP {status}: {error}"}

    async def _chat_completion(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> tuple[int, object]:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        return await self._request_json("POST", "/chat/completions", json=payload)

    async def _default_model(self) -> str | None:
        models_resp = await self.list_available_models()
        models = models_resp.get("models", [])
        if not models:
            return None
        return models[0].get("id")

    async def generate_text(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: object,
    ) -> dict:
        model = model or await self._default_model()
        if not model:
            return {"success": False, "error": "Нет доступных моделей Foundry"}

        status, data = await self._chat_completion(
            [{"role": "user", "content": prompt}],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if status == 200 and isinstance(data, dict):
            choices = data.get("choices") or []
            if choices:
                return {
                    "success": True,
                    "content": choices[0].get("message", {}).get("content", ""),
                    "model": model,
                    "usage": data.get("usage") or {},
                }
            return {"success": False, "error": "Некорректный ответ от Foundry"}

        error = data.get("error") if isinstance(data, dict) else str(data)
        result = {"success": False, "error": f"HTTP {status}: {error}"}
        if status == 400:
            result.update({"error_code": "model_not_loaded", "model_id": model})
        return result

    async def generate_stream(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: object,
    ) -> AsyncIterator[dict]:
        model = model or await self._default_model()
        if not model:
            yield {"success": False, "error": "Нет доступных моделей Foundry"}
            return

        await self._update_base_url()
        if not self.base_url:
            yield {"success": False, "error": "Foundry недоступен"}
            return

        session = await self._get_session()
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    yield {"success": False, "error": f"HTTP {response.status}: {await response.text()}"}
                    return

                async for line in response.content:
                    line_str = line.decode("utf-8", errors="replace").strip()
                    if not line_str.startswith("data: "):
                        continue
                    data_str = line_str[6:]
                    if data_str == "[DONE]":
                        yield {"success": True, "finished": True}
                        return
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or []
                    content = choices[0].get("delta", {}).get("content", "") if choices else ""
                    if content:
                        yield {"success": True, "content": content, "finished": False}
        except Exception as exc:
            yield {"success": False, "error": f"{type(exc).__name__}: {exc}"}

    async def completions(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        **kwargs: object,
    ) -> dict:
        model = model or await self._default_model()
        if not model:
            return {"success": False, "error": "Нет доступных моделей Foundry"}

        payload = {"model": model, "prompt": prompt, "temperature": temperature, "max_tokens": max_tokens, **kwargs}
        status, data = await self._request_json("POST", "/completions", json=payload)
        if status == 200 and isinstance(data, dict):
            return {"success": True, **data}
        error = data.get("error") if isinstance(data, dict) else str(data)
        return {"success": False, "error": f"HTTP {status}: {error}"}

    async def embeddings(self, input: str | list, model: str | None = None) -> dict:
        model = model or await self._default_model()
        if not model:
            return {"success": False, "error": "Нет доступных моделей Foundry"}

        status, data = await self._request_json("POST", "/embeddings", json={"input": input, "model": model})
        if status == 200 and isinstance(data, dict):
            return {"success": True, **data}
        error = data.get("error") if isinstance(data, dict) else str(data)
        return {"success": False, "error": f"HTTP {status}: {error}"}


foundry_client = FoundryClient()
