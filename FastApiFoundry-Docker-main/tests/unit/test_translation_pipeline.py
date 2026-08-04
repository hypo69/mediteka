# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests — translate_model_dialog pipeline
# =============================================================================
# Description:
#   Tests for the per-request translation pipeline triggered by
#   translate_model_dialog=true in API requests.
#
#   Covers:
#     - Translator.should_translate() priority logic
#     - Translator.resolve_user_lang() auto-detection fallback
#     - generate endpoint: prompt translated before model, response translated back
#     - generate endpoint: no translation when flag is False/absent
#     - chat/message endpoint: same pipeline
#
# File: tests/unit/test_translation_pipeline.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ── Translator.should_translate ───────────────────────────────────────────────

class TestShouldTranslate:
    """Tests for Translator.should_translate() priority logic."""

    @pytest.fixture
    def translator(self):
        from src.utils.translator import Translator
        return Translator()

    @pytest.mark.asyncio
    async def test_per_request_true_overrides_config(self, translator):
        """translate_model_dialog=True activates translation regardless of config."""
        with patch('src.utils.translator._cfg', return_value={"enabled": False}):
            result = await translator.should_translate({"translate_model_dialog": True})
        assert result is True

    @pytest.mark.asyncio
    async def test_per_request_false_overrides_config(self, translator):
        """translate_model_dialog=False disables translation regardless of config."""
        with patch('src.utils.translator._cfg', return_value={"enabled": True}):
            result = await translator.should_translate({"translate_model_dialog": False})
        assert result is False

    @pytest.mark.asyncio
    async def test_falls_back_to_config_enabled(self, translator):
        """When translate_model_dialog absent, uses config translator.enabled=True."""
        with patch('src.utils.translator._cfg', return_value={"enabled": True}):
            result = await translator.should_translate({})
        assert result is True

    @pytest.mark.asyncio
    async def test_falls_back_to_config_disabled(self, translator):
        """When translate_model_dialog absent, uses config translator.enabled=False."""
        with patch('src.utils.translator._cfg', return_value={"enabled": False}):
            result = await translator.should_translate({})
        assert result is False

    @pytest.mark.asyncio
    async def test_default_is_false_when_no_config(self, translator):
        """Default is False when config section is missing."""
        with patch('src.utils.translator._cfg', return_value={}):
            result = await translator.should_translate({})
        assert result is False


# ── Translator.resolve_user_lang ─────────────────────────────────────────────

class TestResolveUserLang:
    """Tests for Translator.resolve_user_lang()."""

    @pytest.fixture
    def translator(self):
        from src.utils.translator import Translator
        return Translator()

    @pytest.mark.asyncio
    async def test_explicit_lang_returned_as_is(self, translator):
        """Explicit user_language is returned lowercased without detection."""
        result = await translator.resolve_user_lang("Привет", "RU")
        assert result == "ru"

    @pytest.mark.asyncio
    async def test_auto_detect_called_when_no_lang(self, translator):
        """detect_language is called when user_language is None."""
        translator.detect_language = AsyncMock(return_value={"language": "he"})
        result = await translator.resolve_user_lang("שלום", None)
        translator.detect_language.assert_called_once_with("שלום")
        assert result == "he"

    @pytest.mark.asyncio
    async def test_fallback_to_en_on_detection_failure(self, translator):
        """Falls back to 'en' when detection returns no language."""
        translator.detect_language = AsyncMock(return_value={"language": None})
        result = await translator.resolve_user_lang("???", None)
        assert result == "en"


# ── generate endpoint translation pipeline ───────────────────────────────────

class TestGenerateTranslationPipeline:
    """Tests for translate_model_dialog in POST /api/v1/generate."""

    @pytest.mark.asyncio
    async def test_prompt_translated_to_en_before_model(self):
        """When translate_model_dialog=True, prompt is translated to EN before routing."""
        from src.api.endpoints.generate import generate_text

        translated_prompt = "Hello world"
        model_response = {"success": True, "content": "Answer in English", "model": "hf::test", "usage": {}}

        with patch('src.api.endpoints.generate.translator') as mock_tr, \
             patch('src.api.endpoints.generate.route_generate', new_callable=AsyncMock) as mock_route, \
             patch('src.api.endpoints.generate.rag_system') as mock_rag:

            mock_tr.should_translate = AsyncMock(return_value=True)
            mock_tr.resolve_user_lang = AsyncMock(return_value="ru")
            mock_tr.translate_for_model = AsyncMock(return_value={
                "success": True, "translated": translated_prompt, "was_translated": True
            })
            mock_tr.translate_response = AsyncMock(return_value={
                "success": True, "translated": "Ответ на русском"
            })
            mock_route.return_value = model_response
            mock_rag.search = AsyncMock(return_value=[])

            result = await generate_text({
                "prompt": "Привет мир",
                "model": "hf::test",
                "translate_model_dialog": True,
            })

        # Model received English prompt
        mock_route.assert_called_once()
        call_kwargs = mock_route.call_args
        assert call_kwargs[1]["prompt"] == translated_prompt or call_kwargs[0][0] == translated_prompt

        # Client received Russian response
        assert result["translated"] is True
        assert result["content"] == "Ответ на русском"

    @pytest.mark.asyncio
    async def test_no_translation_when_flag_false(self):
        """When translate_model_dialog=False, prompt goes to model unchanged."""
        from src.api.endpoints.generate import generate_text

        original_prompt = "Привет мир"
        model_response = {"success": True, "content": "Ответ", "model": "hf::test", "usage": {}}

        with patch('src.api.endpoints.generate.translator') as mock_tr, \
             patch('src.api.endpoints.generate.route_generate', new_callable=AsyncMock) as mock_route, \
             patch('src.api.endpoints.generate.rag_system') as mock_rag:

            mock_tr.should_translate = AsyncMock(return_value=False)
            mock_route.return_value = model_response
            mock_rag.search = AsyncMock(return_value=[])

            result = await generate_text({
                "prompt": original_prompt,
                "model": "hf::test",
                "translate_model_dialog": False,
            })

        mock_route.assert_called_once()
        call_prompt = mock_route.call_args[1].get("prompt") or mock_route.call_args[0][0]
        assert call_prompt == original_prompt
        assert result["translated"] is False

    @pytest.mark.asyncio
    async def test_english_prompt_not_translated(self):
        """English prompt is passed through without translation even when flag=True."""
        from src.api.endpoints.generate import generate_text

        model_response = {"success": True, "content": "Answer", "model": "hf::test", "usage": {}}

        with patch('src.api.endpoints.generate.translator') as mock_tr, \
             patch('src.api.endpoints.generate.route_generate', new_callable=AsyncMock) as mock_route, \
             patch('src.api.endpoints.generate.rag_system') as mock_rag:

            mock_tr.should_translate = AsyncMock(return_value=True)
            mock_tr.resolve_user_lang = AsyncMock(return_value="en")
            mock_tr.translate_for_model = AsyncMock(return_value={
                "success": True, "translated": "Hello", "was_translated": False
            })
            mock_tr.translate_response = AsyncMock(return_value={
                "success": True, "translated": "Answer"
            })
            mock_route.return_value = model_response
            mock_rag.search = AsyncMock(return_value=[])

            result = await generate_text({
                "prompt": "Hello",
                "model": "hf::test",
                "translate_model_dialog": True,
                "user_language": "en",
            })

        assert result["translated"] is False

    @pytest.mark.asyncio
    async def test_missing_prompt_returns_error(self):
        """Empty prompt returns success=False without calling translator."""
        from src.api.endpoints.generate import generate_text

        with patch('src.api.endpoints.generate.translator') as mock_tr:
            mock_tr.should_translate = AsyncMock(return_value=True)

            result = await generate_text({"translate_model_dialog": True})

        assert result["success"] is False
        assert "prompt" in result["error"].lower() or "required" in result["error"].lower()
        mock_tr.translate_for_model.assert_not_called() if hasattr(mock_tr, 'translate_for_model') else None


# ── translate_for_model / translate_response unit ────────────────────────────

class TestTranslatorMethods:
    """Unit tests for translate_for_model and translate_response."""

    @pytest.fixture
    def translator(self):
        from src.utils.translator import Translator
        return Translator()

    @pytest.mark.asyncio
    async def test_translate_for_model_skips_english(self, translator):
        """translate_for_model returns original unchanged for source_lang='en'."""
        result = await translator.translate_for_model("Hello", source_lang="en")
        assert result["was_translated"] is False
        assert result["translated"] == "Hello"

    @pytest.mark.asyncio
    async def test_translate_response_skips_english_target(self, translator):
        """translate_response returns original unchanged when target_lang='en'."""
        result = await translator.translate_response("Hello", "en")
        assert result["was_translated"] is False
        assert result["translated"] == "Hello"

    @pytest.mark.asyncio
    async def test_translate_for_model_calls_provider(self, translator):
        """translate_for_model calls underlying translate() for non-English input."""
        translator._via_mymemory = AsyncMock(return_value="Hello world")
        with patch('src.utils.translator._cfg', return_value={"default_provider": "mymemory"}):
            result = await translator.translate_for_model("Привет мир", source_lang="ru")
        assert result["success"] is True
        assert result["translated"] == "Hello world"
        assert result["was_translated"] is True

    @pytest.mark.asyncio
    async def test_translate_response_calls_provider(self, translator):
        """translate_response calls underlying translate() for non-English target."""
        translator._via_mymemory = AsyncMock(return_value="Привет мир")
        with patch('src.utils.translator._cfg', return_value={"default_provider": "mymemory"}):
            result = await translator.translate_response("Hello world", "ru")
        assert result["success"] is True
        assert result["translated"] == "Привет мир"
