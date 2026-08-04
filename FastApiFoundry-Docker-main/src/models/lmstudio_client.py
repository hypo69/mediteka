# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LM Studio Local Provider Client
# =============================================================================
# Description:
#   Async client for LM Studio native REST API v1.
#   Supports model listing, load/unload/download management, and generation
#   through /api/v1/chat.
#
# File: src/models/lmstudio_client.py
# Project: Ai Assistant (Docker)
# =============================================================================

import json
import logging
import os
from typing import Any, AsyncGenerator, Optional

import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://localhost:1234"


def _get_config_section() -> dict:
    try:
        from ..core.config import config
        return config.get_section("lmstudio")
    except Exception:
        return {}


def _get_base_url() -> str:
    env_url = os.getenv("LMSTUDIO_BASE_URL", "")
    if env_url:
        return env_url.rstrip("/")
    return str(_get_config_section().get("base_url") or DEFAULT_BASE_URL).rstrip("/")


def _get_api_key() -> str:
    return os.getenv("LMSTUDIO_API_KEY", "") or str(_get_config_section().get("api_key") or "")


def _get_default_model() -> str:
    return os.getenv("LMSTUDIO_DEFAULT_MODEL", "") or str(_get_config_section().get("default_model") or "")


def _get_timeout_seconds() -> int:
    try:
        return int(_get_config_section().get("request_timeout_sec") or 300)
    except (TypeError, ValueError):
        return 300


def _extract_message_content(data: dict) -> str:
    """Extract assistant text from LM Studio /api/v1/chat response."""
    parts: list[str] = []
    for item in data.get("output") or []:
        if item.get("type") == "message":
            content = item.get("content", "")
            if isinstance(content, str):
                parts.append(content)
    return "".join(parts)


class LMStudioClient:
    """Async LM Studio REST API v1 client."""

    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=_get_timeout_seconds()))
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        api_key = _get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    async def _request(self, method: str, path: str, **kwargs: Any) -> tuple[int, Any]:
        session = await self._get_session()
        url = f"{_get_base_url()}{path}"
        headers = kwargs.pop("headers", None) or self._headers()
        async with session.request(method, url, headers=headers, **kwargs) as resp:
            text = await resp.text()
            if not text:
                return resp.status, {}
            try:
                return resp.status, json.loads(text)
            except json.JSONDecodeError:
                return resp.status, {"text": text}

    async def get_status(self) -> dict:
        """Check LM Studio API reachability through GET /api/v1/models."""
        url = _get_base_url()
        try:
            result = await self.list_models()
            return {
                "success": True,
                "running": result.get("success", False),
                "url": url,
                "api_url": f"{url}/api/v1",
                "models_count": result.get("count", 0) if result.get("success") else 0,
                "error": result.get("error"),
            }
        except Exception as e:
            return {"success": True, "running": False, "url": url, "api_url": f"{url}/api/v1", "error": str(e)}

    async def list_models(self) -> dict:
        """List models known to LM Studio."""
        try:
            status, data = await self._request("GET", "/api/v1/models")
            if status != 200:
                return {"success": False, "error": f"HTTP {status}: {data}"}
            models = data.get("models") or []
            return {"success": True, "models": models, "count": len(models)}
        except Exception as e:
            logger.debug("LM Studio list_models: server not available (%s)", e)
            return {"success": False, "error": str(e)}

    async def load_model(self, model: str, **load_options: Any) -> dict:
        """Load a model into LM Studio memory."""
        payload = {"model": model}
        payload.update({k: v for k, v in load_options.items() if v is not None})
        try:
            status, data = await self._request("POST", "/api/v1/models/load", json=payload)
            if status != 200:
                return {"success": False, "error": f"HTTP {status}: {data}"}
            return {"success": True, **data}
        except Exception as e:
            logger.error("LM Studio load_model failed for %s: %s", model, e)
            return {"success": False, "error": str(e)}

    async def unload_model(self, instance_id: str) -> dict:
        """Unload a loaded LM Studio model instance."""
        try:
            status, data = await self._request("POST", "/api/v1/models/unload", json={"instance_id": instance_id})
            if status != 200:
                return {"success": False, "error": f"HTTP {status}: {data}"}
            return {"success": True, **data}
        except Exception as e:
            logger.error("LM Studio unload_model failed for %s: %s", instance_id, e)
            return {"success": False, "error": str(e)}

    async def download_model(self, model: str, quantization: str = "") -> dict:
        """Start a model download job in LM Studio."""
        payload = {"model": model}
        if quantization:
            payload["quantization"] = quantization
        try:
            status, data = await self._request("POST", "/api/v1/models/download", json=payload)
            if status != 200:
                return {"success": False, "error": f"HTTP {status}: {data}"}
            return {"success": True, **data}
        except Exception as e:
            logger.error("LM Studio download_model failed for %s: %s", model, e)
            return {"success": False, "error": str(e)}

    async def download_status(self, job_id: str) -> dict:
        """Get LM Studio download job status."""
        try:
            status, data = await self._request("GET", f"/api/v1/models/download/status/{job_id}")
            if status != 200:
                return {"success": False, "error": f"HTTP {status}: {data}"}
            return {"success": True, **data}
        except Exception as e:
            logger.error("LM Studio download_status failed for %s: %s", job_id, e)
            return {"success": False, "error": str(e)}

    async def generate(
        self,
        prompt: str,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 512,
        context_length: Optional[int] = None,
        reasoning: Optional[str] = None,
        previous_response_id: Optional[str] = None,
    ) -> dict:
        """Generate text with LM Studio /api/v1/chat."""
        model_id = model or _get_default_model()
        if not model_id:
            return {"success": False, "error": "model is required"}

        payload: dict[str, Any] = {
            "model": model_id,
            "input": prompt,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "stream": False,
            "store": bool(previous_response_id),
        }
        if context_length is not None:
            payload["context_length"] = context_length
        if reasoning:
            payload["reasoning"] = reasoning
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id

        try:
            status, data = await self._request("POST", "/api/v1/chat", json=payload)
            if status != 200:
                return {"success": False, "error": f"HTTP {status}: {data}"}
            content = _extract_message_content(data)
            return {
                "success": True,
                "content": content,
                "model": data.get("model_instance_id") or model_id,
                "usage": data.get("stats") or {},
                "response_id": data.get("response_id"),
                "raw": data,
            }
        except Exception as e:
            logger.error("LM Studio generate failed for %s: %s", model_id, e)
            return {"success": False, "error": str(e)}

    async def stream_generate(
        self,
        prompt: str,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 512,
        context_length: Optional[int] = None,
        reasoning: Optional[str] = None,
        previous_response_id: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream message.delta chunks from LM Studio /api/v1/chat SSE."""
        model_id = model or _get_default_model()
        if not model_id:
            yield {"success": False, "error": "model is required", "finished": True}
            return

        payload: dict[str, Any] = {
            "model": model_id,
            "input": prompt,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "stream": True,
            "store": bool(previous_response_id),
        }
        if context_length is not None:
            payload["context_length"] = context_length
        if reasoning:
            payload["reasoning"] = reasoning
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id

        session = await self._get_session()
        try:
            async with session.post(
                f"{_get_base_url()}/api/v1/chat",
                headers=self._headers(),
                json=payload,
            ) as resp:
                if resp.status != 200:
                    yield {"success": False, "error": f"HTTP {resp.status}: {await resp.text()}", "finished": True}
                    return

                event_type = ""
                data_lines: list[str] = []
                async for raw_line in resp.content:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line:
                        async for event in self._handle_sse_event(event_type, data_lines):
                            yield event
                        event_type = ""
                        data_lines = []
                        continue
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                    elif line.startswith("data:"):
                        data_lines.append(line.split(":", 1)[1].strip())
        except Exception as e:
            logger.error("LM Studio stream_generate failed for %s: %s", model_id, e)
            yield {"success": False, "error": str(e), "finished": True}

    async def _handle_sse_event(self, event_type: str, data_lines: list[str]) -> AsyncGenerator[dict, None]:
        if not data_lines:
            return
        try:
            data = json.loads("\n".join(data_lines))
        except json.JSONDecodeError:
            return

        typ = data.get("type") or event_type
        if typ == "message.delta":
            yield {"success": True, "content": data.get("content", ""), "finished": False}
        elif typ == "error":
            yield {"success": False, "error": data.get("error", {}).get("message", "LM Studio stream error")}
        elif typ == "chat.end":
            result = data.get("result") or {}
            yield {
                "success": True,
                "content": "",
                "finished": True,
                "usage": result.get("stats") or {},
                "response_id": result.get("response_id"),
                "raw": result,
            }


lmstudio_client = LMStudioClient()
