# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Model Router — Orchestrator Core
# =============================================================================
# Description:
#   Central routing logic for AI Assistant orchestrator.
#   Dispatches generate requests to the correct backend by model prefix.
#
#   Workflow:
#     request.model  →  detect_backend()  →  backend + clean_model_id
#                                         ↓
#                          ┌──────────────┼──────────────┬──────────────┐
#                          ▼              ▼              ▼              ▼
#                       Foundry      HuggingFace     llama.cpp      Ollama     LM Studio
#                    (ONNX/local)   (PyTorch/Hub)  (GGUF/CPU)   (local HTTP) (native REST)
#                          └──────────────┴──────────────┴──────────────┴──────────────┘
#                                         ↓
#                          {"success": bool, "content": str,
#                           "model": str, "usage": {...}}
#
#   Model prefix routing:
#     foundry::model-id   → Microsoft Foundry Local (ONNX)
#     hf::model-id        → HuggingFace Transformers (PyTorch)
#     llama::path.gguf    → llama.cpp (GGUF / CPU)
#     ollama::model-name  → Ollama (local HTTP)
#     lmstudio::model-key → LM Studio (local HTTP)
#
#   No prefix → legacy bare ID forwarded to Foundry with deprecation warning.
#
# File: src/models/router.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Added workflow diagram to header
#   - Enriched docstrings with examples
#   - Added type annotations to private backend functions
# Changes in 0.7.0:
#   - Created: extracted routing from generate.py / ai_endpoints.py
#   - Added foundry:: prefix support
#   - Unified response shape across all backends
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)

# ── Prefix constants — single source of truth ────────────────────────────────
PREFIX_FOUNDRY = "foundry::"
PREFIX_HF      = "hf::"
PREFIX_LLAMA   = "llama::"
PREFIX_OLLAMA  = "ollama::"
PREFIX_LMSTUDIO = "lmstudio::"

_KNOWN_PREFIXES = (PREFIX_FOUNDRY, PREFIX_HF, PREFIX_LLAMA, PREFIX_OLLAMA, PREFIX_LMSTUDIO)


def detect_backend(model: Optional[str]) -> tuple[str, str]:
    """Detect backend and strip prefix from model ID.

    Workflow:
        model string → prefix check → (backend_name, clean_id)

    Args:
        model: Raw model string from request. Supported formats:
            - ``'foundry::qwen3-0.6b-generic-cpu:4'``
            - ``'hf::Qwen/Qwen2.5-0.5B-Instruct'``
            - ``'llama::D:/models/gemma-2b-q4.gguf'``
            - ``'ollama::qwen2.5:0.5b'``
            - ``'lmstudio::ibm/granite-4-micro'``
            - ``None`` or ``''`` → defaults to Foundry with empty model ID

    Returns:
        tuple[str, str]: ``(backend, clean_model_id)``

            - ``backend``: one of ``'foundry'``, ``'hf'``, ``'llama'``, ``'ollama'``
            - ``clean_model_id``: model ID with prefix stripped

    Example:
        >>> detect_backend("foundry::qwen3-0.6b")
        ('foundry', 'qwen3-0.6b')

        >>> detect_backend("hf::Qwen/Qwen2.5-0.5B")
        ('hf', 'Qwen/Qwen2.5-0.5B')

        >>> detect_backend("llama::D:/models/q4.gguf")
        ('llama', 'D:/models/q4.gguf')

        >>> detect_backend("ollama::mistral")
        ('ollama', 'mistral')

        >>> detect_backend("lmstudio::ibm/granite-4-micro")
        ('lmstudio', 'ibm/granite-4-micro')

        >>> detect_backend(None)
        ('foundry', '')

        >>> detect_backend("bare-model-id")  # legacy, warns
        ('foundry', 'bare-model-id')
    """
    if not model:
        return "foundry", ""

    m = str(model)

    if m.startswith(PREFIX_FOUNDRY):
        return "foundry", m[len(PREFIX_FOUNDRY):]
    if m.startswith(PREFIX_HF):
        return "hf", m[len(PREFIX_HF):]
    if m.startswith(PREFIX_LLAMA):
        return "llama", m[len(PREFIX_LLAMA):]
    if m.startswith(PREFIX_OLLAMA):
        return "ollama", m[len(PREFIX_OLLAMA):]
    if m.startswith(PREFIX_LMSTUDIO):
        return "lmstudio", m[len(PREFIX_LMSTUDIO):]

    # Legacy: bare model ID — forward to Foundry with deprecation warning.
    # Kept for backward compatibility with old integrations.
    logger.warning(
        f"⚠️ Bare model ID '{m}' has no backend prefix. "
        f"Use 'foundry::{m}' explicitly. Forwarding to Foundry (legacy)."
    )
    return "foundry", m


def _default_temperature() -> float:
    """Return default temperature from config.defaults, fallback 0.7."""
    try:
        from config_manager import config as _cfg
        return _cfg.foundry_temperature
    except Exception:
        return 0.7


def _default_max_tokens() -> int:
    """Return default max_tokens from config.defaults, fallback 2048."""
    try:
        from config_manager import config as _cfg
        return _cfg.foundry_max_tokens
    except Exception:
        return 2048


async def route_generate(
    prompt: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> dict:
    """Route a generation request to the correct backend.

    Workflow:
        prompt + model → detect_backend() → backend call → unified response

    Args:
        prompt:      Input text (required, non-empty).
        model:       Model ID with prefix, e.g. ``'foundry::qwen3-0.6b'``.
                     If ``None``, routes to Foundry and uses its first loaded model.
        temperature: Sampling temperature (0.0–2.0, default from config.defaults.temperature).
        max_tokens:  Maximum tokens to generate (default from config.defaults.max_tokens).

    Returns:
        dict: On success::

            {"success": True, "content": "...", "model": "foundry::...", "usage": {...}}

        On failure::

            {"success": False, "error": "description"}

        Special error on Foundry model not loaded::

            {"success": False, "error": "...", "error_code": "model_not_loaded", "model_id": "..."}

    Example:
        >>> result = await route_generate("Hello", model="foundry::qwen3-0.6b")
        >>> result["success"]
        True

        >>> result = await route_generate("Summarize", model="hf::Qwen/Qwen2.5-0.5B")

        >>> result = await route_generate("Code review", model="ollama::codellama")

        >>> result = await route_generate("Translate", model="llama::D:/models/q4.gguf")

        >>> result = await route_generate("Summarize", model="lmstudio::ibm/granite-4-micro")
    """
    if not prompt:
        return {"success": False, "error": "Prompt is required"}

    # Apply config defaults when caller did not pass explicit values
    if temperature is None:
        temperature = _default_temperature()
    if max_tokens is None:
        max_tokens = _default_max_tokens()

    backend, clean_model = detect_backend(model)

    try:
        if backend == "hf":
            result = await _generate_hf(prompt, clean_model, temperature, max_tokens)
        elif backend == "llama":
            result = await _generate_llama(prompt, clean_model, temperature, max_tokens)
        elif backend == "ollama":
            result = await _generate_ollama(prompt, clean_model, temperature, max_tokens)
        elif backend == "lmstudio":
            result = await _generate_lmstudio(prompt, clean_model, temperature, max_tokens)
        else:
            result = await _generate_foundry(prompt, clean_model or None, temperature, max_tokens)
    except Exception as exc:
        logger.error("Model generation crashed for backend=%s model=%s: %s", backend, clean_model, exc, exc_info=True)
        return {"success": False, "error": str(exc), "backend": backend}

    if not result.get("success"):
        logger.error(
            "Model generation failed for backend=%s model=%s: %s",
            backend,
            clean_model,
            result.get("error", "unknown error"),
        )
    return result


# ── Backend implementations ───────────────────────────────────────────────────

async def _generate_foundry(
    prompt: str,
    model: Optional[str],
    temperature: float,
    max_tokens: int,
) -> dict:
    """Call Foundry Local backend.

    Args:
        prompt: Input text.
        model: Foundry model ID (without prefix), or None to use first loaded.
        temperature: Sampling temperature.
        max_tokens: Max tokens to generate.

    Returns:
        dict: Unified response with ``model`` prefixed as ``foundry::<id>``.
    """
    from .foundry_client import foundry_client

    result = await foundry_client.generate_text(
        prompt, model=model, temperature=temperature, max_tokens=max_tokens
    )

    # Propagate model_not_loaded error to caller
    if result.get("error_code") == "model_not_loaded":
        return {
            "success": False,
            "error": result["error"],
            "error_code": "model_not_loaded",
            "model_id": result.get("model_id"),
        }

    if "content" not in result:
        return {"success": False, "error": result.get("error", "Foundry error")}

    return {
        "success": True,
        "content": result["content"],
        "model": f"{PREFIX_FOUNDRY}{result['model']}",
        "usage": result.get("usage") or {},
    }


async def _generate_hf(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> dict:
    """Call HuggingFace Transformers backend.

    Args:
        prompt: Input text.
        model: HuggingFace model ID (without prefix), e.g. ``'Qwen/Qwen2.5-0.5B'``.
        temperature: Sampling temperature.
        max_tokens: Max new tokens to generate.

    Returns:
        dict: Unified response with ``model`` prefixed as ``hf::<id>``.
    """
    from .hf_client import hf_client

    result = await hf_client.generate(
        prompt, model_id=model, temperature=temperature, max_new_tokens=max_tokens
    )

    if not result.get("content"):
        return {"success": False, "error": result.get("error") or "HF generation error"}

    return {
        "success": True,
        "content": result["content"],
        "model": f"{PREFIX_HF}{model}",
        "usage": {},
    }


async def _generate_llama(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> dict:
    """Call llama.cpp backend via its OpenAI-compatible HTTP API.

    Requires llama.cpp server to be running (started via ``/api/v1/llama/start``).

    Args:
        prompt: Input text.
        model: Path to GGUF file (without prefix), used only for response labeling.
        temperature: Sampling temperature.
        max_tokens: Max tokens to generate.

    Returns:
        dict: Unified response with ``model`` prefixed as ``llama::<path>``.
    """
    from .llama_registry import resolve_llama_server

    server = resolve_llama_server(model)
    if not server:
        return {
            "success": False,
            "error": f"llama.cpp model is not configured: {model}",
            "model": f"{PREFIX_LLAMA}{model}",
        }

    openai_url = server.openai_url

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{openai_url.rstrip('/')}/chat/completions",
                json={
                    "model": "llama",  # llama.cpp ignores model name, uses loaded model
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False,
                },
            ) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"llama.cpp HTTP {resp.status}: {await resp.text()}"}
                data = await resp.json()

        choices = data.get("choices") or []
        if not choices:
            return {"success": False, "error": "llama.cpp returned no choices"}

        content = choices[0].get("message", {}).get("content", "")
        return {
            "success": True,
            "content": content,
            "model": f"{PREFIX_LLAMA}{server.alias}",
            "llama_url": server.url,
            "usage": data.get("usage") or {},
        }
    except Exception as e:
        logger.error(f"❌ llama.cpp request failed: {e}")
        return {"success": False, "error": str(e)}


async def _generate_ollama(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> dict:
    """Call Ollama backend.

    Requires Ollama service running locally (default port 11434).

    Args:
        prompt: Input text.
        model: Ollama model name (without prefix), e.g. ``'qwen2.5:0.5b'``.
        temperature: Sampling temperature.
        max_tokens: Max tokens to generate.

    Returns:
        dict: Unified response with ``model`` prefixed as ``ollama::<name>``.
    """
    from .ollama_client import ollama_client

    result = await ollama_client.generate(
        prompt, model=model, temperature=temperature, max_tokens=max_tokens
    )

    if not result.get("content"):
        return {"success": False, "error": result.get("error") or "Ollama generation error"}

    return {
        "success": True,
        "content": result["content"],
        "model": f"{PREFIX_OLLAMA}{model}",
        "usage": {},
    }


async def _generate_lmstudio(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> dict:
    """Call LM Studio backend via native REST API v1.

    Requires LM Studio server running locally (default http://localhost:1234).

    Args:
        prompt: Input text.
        model: LM Studio model key (without prefix), e.g. ``'ibm/granite-4-micro'``.
        temperature: Sampling temperature.
        max_tokens: Max output tokens.

    Returns:
        dict: Unified response with ``model`` prefixed as ``lmstudio::<key>``.
    """
    from .lmstudio_client import lmstudio_client

    result = await lmstudio_client.generate(
        prompt, model=model, temperature=temperature, max_tokens=max_tokens
    )

    if not result.get("success"):
        return {"success": False, "error": result.get("error") or "LM Studio generation error"}

    return {
        "success": True,
        "content": result.get("content", ""),
        "model": f"{PREFIX_LMSTUDIO}{result.get('model') or model}",
        "usage": result.get("usage") or {},
        "response_id": result.get("response_id"),
    }
