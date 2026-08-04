# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Translator Utility — free online translation services
# =============================================================================
# Description:
#   Translates incoming text to English before sending to AI model,
#   and translates responses back to the user's original language.
#   All settings are read from config.json section "translator".
#
#   Providers (no API keys required by default):
#     - mymemory      : MyMemory free API
#     - libretranslate: LibreTranslate public/private instance
#     - deepl         : DeepL free tier (DEEPL_API_KEY in .env)
#     - google        : Google Cloud Translation (GOOGLE_TRANSLATE_API_KEY in .env)
#
# Examples:
#   >>> from src.utils.translator import translator
#   >>> result = await translator.translate("Привет мир", target_lang="en")
#   >>> result["translated"]  # "Hello world"
#
# File: src/utils/translator.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
import os
import time
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

LANG_NAMES: dict[str, str] = {
    "en": "English", "ru": "Russian", "de": "German", "fr": "French",
    "es": "Spanish", "zh": "Chinese", "ja": "Japanese", "ar": "Arabic",
    "uk": "Ukrainian", "pl": "Polish", "it": "Italian", "pt": "Portuguese",
    "nl": "Dutch", "ko": "Korean", "tr": "Turkish", "he": "Hebrew",
}

DEEPL_LANG_MAP: dict[str, str] = {
    "en": "EN-US", "ru": "RU", "de": "DE", "fr": "FR", "es": "ES",
    "zh": "ZH", "ja": "JA", "uk": "UK", "pl": "PL", "it": "IT",
    "pt": "PT-PT", "nl": "NL", "ko": "KO", "tr": "TR",
}


def _cfg() -> dict:
    """Return translator section from config.json (lazy import to avoid circular deps)."""
    try:
        from ..core.config import config
        return config.get_raw_config().get("translator", {})
    except Exception:
        return {}


class Translator:
    """Translate text using configurable online services.

    All provider URLs, keys and defaults are read from config.json
    section "translator" at call time — no restart required after settings change.
    """

    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None

    def _timeout(self) -> aiohttp.ClientTimeout:
        secs = _cfg().get("request_timeout_sec", 30)
        return aiohttp.ClientTimeout(total=secs)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout())
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def should_translate(self, request: dict) -> bool:
        """Determine whether translation is active for this request.

        Per-request field ``translate_model_dialog`` takes priority over global
        config ``translator.enabled``. Default when neither is set: False.

        Args:
            request: Raw request dict from the API endpoint.

        Returns:
            bool: True if translation pipeline should run for this request.

        Example:
            >>> translator.should_translate({"translate_model_dialog": True})
            True
            >>> translator.should_translate({})  # falls back to config
            False
        """
        per_request = request.get("translate_model_dialog")
        if per_request is not None:
            return bool(per_request)
        return _cfg().get("enabled", False)

    async def resolve_user_lang(self, prompt: str, user_language: str | None) -> str:
        """Return user language code, auto-detecting from prompt when not provided.

        Args:
            prompt: User input text used for detection.
            user_language: Explicit ISO 639-1 code or None for auto-detect.

        Returns:
            str: ISO 639-1 language code, e.g. 'ru', 'en', 'he'.

        Example:
            >>> await translator.resolve_user_lang("Привет", None)
            'ru'
        """
        if user_language:
            return user_language.lower().strip()
        det = await self.detect_language(prompt)
        return det.get("language") or "en"

    # ── Public API ────────────────────────────────────────────────────────

    async def translate(
        self,
        text: str,
        *,
        provider: str = "",
        source_lang: str = "auto",
        target_lang: str = "en",
        api_key: str = "",
    ) -> dict:
        """Translate text to target language.

        Args:
            text: Source text.
            provider: Override provider. Empty = use config default_provider.
            source_lang: ISO 639-1 code or "auto".
            target_lang: ISO 639-1 code.
            api_key: Optional key override for deepl/google/libretranslate.

        Returns:
            dict: success, translated, provider, source_lang, target_lang,
                  elapsed_ms, error.
        """
        if not text or not text.strip():
            return self._err("Empty text")

        used_provider = provider or _cfg().get("default_provider", "mymemory")
        t0 = time.monotonic()
        try:
            if used_provider == "mymemory":
                translated = await self._via_mymemory(text, source_lang, target_lang)
            elif used_provider == "libretranslate":
                translated = await self._via_libretranslate(text, source_lang, target_lang, api_key)
            elif used_provider == "deepl":
                translated = await self._via_deepl(text, target_lang, api_key)
            elif used_provider == "google":
                translated = await self._via_google(text, source_lang, target_lang, api_key)
            else:
                return self._err(f"Unknown provider: {used_provider}")

            elapsed = int((time.monotonic() - t0) * 1000)
            logger.info(f"✅ Translated via {used_provider} in {elapsed}ms")
            return {
                "success": True,
                "translated": translated,
                "provider": used_provider,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "elapsed_ms": elapsed,
                "error": None,
            }
        except Exception as e:
            logger.error(f"❌ Translation error ({used_provider}): {e}")
            return self._err(str(e), provider=used_provider)

    async def translate_for_model(
        self,
        text: str,
        *,
        provider: str = "",
        source_lang: str = "auto",
        api_key: str = "",
    ) -> dict:
        """Translate text to English for AI model input.

        Returns original unchanged if source_lang is already 'en'.

        Args:
            text: Source text to translate.
            provider: Override provider. Empty = use config default_provider.
            source_lang: ISO 639-1 code or "auto".
            api_key: Optional key override for deepl/google/libretranslate.

        Returns:
            dict: success, translated, original, was_translated, provider,
                  source_lang, target_lang, elapsed_ms, error.
        """
        if source_lang == "en":
            return {
                "success": True, "translated": text, "original": text,
                "was_translated": False, "provider": provider or _cfg().get("default_provider", "mymemory"),
                "source_lang": "en", "target_lang": "en", "elapsed_ms": 0, "error": None,
            }
        result = await self.translate(
            text, provider=provider, source_lang=source_lang,
            target_lang="en", api_key=api_key,
        )
        result["original"] = text
        result["was_translated"] = result["success"]
        return result

    async def translate_response(
        self,
        text: str,
        target_lang: str,
        *,
        provider: str = "",
        api_key: str = "",
    ) -> dict:
        """Translate AI response back to the user's original language.

        Args:
            text: English text from AI model.
            target_lang: User's original language code.
            provider: Override provider. Empty = use config default_provider.
            api_key: Optional key override.

        Returns:
            dict: same structure as translate().
        """
        if target_lang == "en":
            return {
                "success": True, "translated": text, "original": text,
                "was_translated": False, "provider": provider or _cfg().get("default_provider", "mymemory"),
                "source_lang": "en", "target_lang": "en", "elapsed_ms": 0, "error": None,
            }
        return await self.translate(
            text, provider=provider, source_lang="en",
            target_lang=target_lang, api_key=api_key,
        )

    async def detect_language(self, text: str) -> dict:
        """Detect language using MyMemory (free, no key required).

        Returns:
            dict: success, language (ISO 639-1), language_name, error.
        """
        if not text or not text.strip():
            return {"success": False, "language": None, "language_name": None, "error": "Empty text"}
        try:
            session = await self._get_session()
            params = {"q": text[:200], "langpair": "auto|en"}
            async with session.get("https://api.mymemory.translated.net/get", params=params) as resp:
                data = await resp.json()
                detected = data.get("responseData", {}).get("detectedLanguage") or ""
                code = detected.split("-")[0].lower() if detected else "unknown"
                name = LANG_NAMES.get(code, code.upper())
                return {"success": True, "language": code, "language_name": name, "error": None}
        except Exception as e:
            logger.error(f"❌ Language detection error: {e}")
            return {"success": False, "language": None, "language_name": None, "error": str(e)}

    async def batch_translate(
        self,
        texts: list[str],
        *,
        provider: str = "",
        source_lang: str = "auto",
        target_lang: str = "en",
        api_key: str = "",
    ) -> dict:
        """Translate a list of texts.

        Args:
            texts: List of source strings to translate.
            provider: Override provider. Empty = use config default_provider.
            source_lang: ISO 639-1 code or "auto".
            target_lang: ISO 639-1 target language code.
            api_key: Optional key override for deepl/google/libretranslate.

        Returns:
            dict: success, results (list of translate() dicts), total, failed, elapsed_ms.
        """
        if not texts:
            return {"success": False, "results": [], "total": 0, "failed": 0, "error": "Empty list"}

        t0 = time.monotonic()
        results = []
        failed = 0
        for text in texts:
            r = await self.translate(
                text, provider=provider, source_lang=source_lang,
                target_lang=target_lang, api_key=api_key,
            )
            results.append(r)
            if not r["success"]:
                failed += 1

        return {
            "success": True,
            "results": results,
            "total": len(texts),
            "failed": failed,
            "elapsed_ms": int((time.monotonic() - t0) * 1000),
        }

    # ── Providers ─────────────────────────────────────────────────────────

    async def _via_mymemory(self, text: str, source_lang: str, target_lang: str) -> str:
        """MyMemory free API — 500 words/day anonymous; set mymemory_email for 50K/day.

        Args:
            text: Source text.
            source_lang: ISO 639-1 code or "auto".
            target_lang: ISO 639-1 target language code.

        Returns:
            str: Translated text.

        Raises:
            RuntimeError: On non-200 HTTP response or API error status.
        """
        src = "autodetect" if source_lang == "auto" else source_lang
        session = await self._get_session()
        params: dict = {"q": text, "langpair": f"{src}|{target_lang}"}
        # Email from config raises daily limit to 50K words
        email = _cfg().get("mymemory_email") or os.getenv("MYMEMORY_EMAIL", "")
        if email:
            params["de"] = email

        async with session.get("https://api.mymemory.translated.net/get", params=params) as resp:
            if resp.status != 200:
                raise RuntimeError(f"MyMemory HTTP {resp.status}")
            data = await resp.json()
            status = data.get("responseStatus")
            if status != 200:
                details = data.get("responseDetails", "MyMemory error")
                # MyMemory returns 200 status but error text when language is unknown
                if "INVALID" in str(details).upper() or "UNKNOWN" in str(details).upper():
                    raise RuntimeError(f"MyMemory: unsupported language pair '{src}|{target_lang}'")
                raise RuntimeError(details)
            return data["responseData"]["translatedText"]

    async def _via_libretranslate(
        self, text: str, source_lang: str, target_lang: str, api_key: str
    ) -> str:
        """LibreTranslate — primary and fallback URLs from config.

        Args:
            text: Source text.
            source_lang: ISO 639-1 code or "auto".
            target_lang: ISO 639-1 target language code.
            api_key: Optional API key for the LibreTranslate instance.

        Returns:
            str: Translated text.

        Raises:
            RuntimeError: If all configured hosts are unavailable.
        """
        cfg = _cfg()
        primary = cfg.get("libretranslate_url", "https://libretranslate.com")
        fallback = cfg.get("libretranslate_fallback_url", "https://translate.argosopentech.com")
        hosts = [h for h in [primary, fallback] if h]

        src = "auto" if source_lang == "auto" else source_lang
        session = await self._get_session()
        payload: dict = {"q": text, "source": src, "target": target_lang, "format": "text"}
        key = api_key or cfg.get("libretranslate_api_key") or os.getenv("LIBRETRANSLATE_API_KEY", "")
        if key:
            payload["api_key"] = key

        last_err = ""
        for host in hosts:
            try:
                async with session.post(f"{host}/translate", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["translatedText"]
                    last_err = f"HTTP {resp.status}"
            except Exception as e:
                last_err = str(e)
        raise RuntimeError(f"LibreTranslate unavailable: {last_err}")

    async def _via_deepl(self, text: str, target_lang: str, api_key: str) -> str:
        """Translate via DeepL free tier API.

        Args:
            text: Source text.
            target_lang: ISO 639-1 target language code.
            api_key: DeepL API key (overrides DEEPL_API_KEY env var).

        Returns:
            str: Translated text.

        Raises:
            ValueError: If no API key is available.
            RuntimeError: On non-200 HTTP response.
        """
        key = api_key or os.getenv("DEEPL_API_KEY", "")
        if not key:
            raise ValueError("DEEPL_API_KEY not set in .env")
        tgt = DEEPL_LANG_MAP.get(target_lang, target_lang.upper())
        session = await self._get_session()
        async with session.post(
            "https://api-free.deepl.com/v2/translate",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"auth_key": key, "text": text, "target_lang": tgt},
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"DeepL HTTP {resp.status}: {await resp.text()}")
            data = await resp.json()
            return data["translations"][0]["text"]

    async def _via_google(
        self, text: str, source_lang: str, target_lang: str, api_key: str
    ) -> str:
        """Translate via Google Cloud Translation API.

        Args:
            text: Source text.
            source_lang: ISO 639-1 code or "auto".
            target_lang: ISO 639-1 target language code.
            api_key: Google Cloud API key (overrides GOOGLE_TRANSLATE_API_KEY env var).

        Returns:
            str: Translated text.

        Raises:
            ValueError: If no API key is available.
            RuntimeError: On non-200 HTTP response.
        """
        key = api_key or os.getenv("GOOGLE_TRANSLATE_API_KEY", "")
        if not key:
            raise ValueError("GOOGLE_TRANSLATE_API_KEY not set in .env")
        session = await self._get_session()
        payload: dict = {"q": text, "target": target_lang, "format": "text"}
        if source_lang != "auto":
            payload["source"] = source_lang
        async with session.post(
            f"https://translation.googleapis.com/language/translate/v2?key={key}",
            json=payload,
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Google Translate HTTP {resp.status}: {await resp.text()}")
            data = await resp.json()
            return data["data"]["translations"][0]["translatedText"]

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _err(msg: str, provider: str = "") -> dict:
        """Build a standard error response dict.

        Args:
            msg: Error message.
            provider: Provider name that caused the error.

        Returns:
            dict: success=False with all standard fields set to None/0.
        """
        return {
            "success": False, "translated": None, "provider": provider,
            "source_lang": None, "target_lang": None, "elapsed_ms": 0, "error": msg,
        }


# Global singleton
translator = Translator()
