# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Translator Endpoints
# =============================================================================
# Description:
#   REST endpoints for text translation and language detection.
#   Wraps src/utils/translator.py for use from the web UI and API clients.
#
# File: translator.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from fastapi import APIRouter
from ...utils.translator import translator
from ...core.config import config as app_config

router = APIRouter()


@router.post("/translate")
async def translate_text(request: dict) -> dict:
    """Translate text using the configured provider.

    Args:
        request: JSON body with fields:
            text (str):          Source text (required).
            source_lang (str):   ISO 639-1 code or 'auto' (default: 'auto').
            target_lang (str):   ISO 639-1 target code (default: 'en').
            provider (str):      Override provider (default: from config).
            api_key (str):       Optional API key override.

    Returns:
        dict: success, translated, provider, source_lang, target_lang,
              elapsed_ms, error.
    """
    text = request.get("text", "")
    if not text:
        return {"success": False, "error": "text is required"}
    return await translator.translate(
        text,
        provider=request.get("provider", ""),
        source_lang=request.get("source_lang", "auto"),
        target_lang=request.get("target_lang", "en"),
        api_key=request.get("api_key", ""),
    )


@router.post("/translate/detect")
async def detect_language(request: dict) -> dict:
    """Detect language of the given text.

    Args:
        request: JSON body with fields:
            text (str): Text to detect language for (required).

    Returns:
        dict: success, language (ISO 639-1), language_name, error.
    """
    text = request.get("text", "")
    if not text:
        return {"success": False, "language": None, "language_name": None, "error": "text is required"}
    return await translator.detect_language(text)


@router.get("/translate/config")
async def get_translator_config() -> dict:
    """Return current translator configuration (no secrets).

    Returns:
        dict: enabled, default_provider, available_providers.
    """
    cfg = app_config.get_raw_config().get("translator", {})
    return {
        "enabled": cfg.get("enabled", False),
        "default_provider": cfg.get("default_provider", "mymemory"),
        "available_providers": ["mymemory", "libretranslate", "deepl", "google"],
    }
