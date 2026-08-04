# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Generate Endpoint
# =============================================================================
# Description:
#   Text generation endpoint for AI Assistant orchestrator.
#   Routes requests to the correct backend via src.models.router.route_generate.
#   Per-request translation: user prompt → English → model → user language.
#   Fields: translate_model_dialog (bool, default true), user_language (str|null).
#   When user_language is null, language is auto-detected from the prompt.
#
#   Model prefix routing (handled by router.py):
#     foundry::model-id  → Foundry Local
#     hf::model-id       → HuggingFace
#     llama::path.gguf   → llama.cpp
#     ollama::model-name → Ollama
#     lmstudio::model    → LM Studio
#
# File: generate.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.0
# Changes in 0.7.0:
#   - Replaced manual if/elif backend dispatch with router.route_generate()
#   - Added foundry:: prefix support; bare IDs still work (legacy warning)
#   - Removed direct imports of foundry_client, hf_client, llama_status
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from fastapi import APIRouter
from ...models.router import route_generate
from ...rag.rag_system import rag_system
from ...core.config import config as app_config
from ...utils.text_utils import count_tokens_approx
from ...utils.api_utils import api_response_handler
from ...utils.translator import translator

router = APIRouter()

@router.post("/generate")
@api_response_handler
async def generate_text(request: dict) -> dict:
    """Generate text via the AI Assistant orchestrator.

    Routes to the correct backend based on model prefix:
    foundry:: / hf:: / llama:: / ollama:: / lmstudio::

    Args:
        request: JSON body with fields:
            prompt (str):                 Input text (required).
            model (str):                  Model ID with prefix, e.g. 'foundry::qwen3-0.6b'.
            temperature (float):          Generation temperature (default: 0.7).
            max_tokens (int):             Max tokens (default: 1000).
            use_rag (bool):               Inject RAG context (default: False).
            top_k (int):                  RAG results count (default: from config).
            translate_model_dialog (bool): Translate prompt→EN and response→user lang.
            user_language (str|null):     User language ISO 639-1. null = auto-detect.

    Returns:
        dict: success, content, model, usage, user_language, translated (bool)
    """
    prompt: str = request.get("prompt", "")
    model = request.get("model")
    temperature: float = request.get("temperature") if request.get("temperature") is not None else None
    max_tokens: int = request.get("max_tokens") if request.get("max_tokens") is not None else None
    use_rag: bool = bool(request.get("use_rag", False))
    top_k: int = request.get("top_k") or app_config.rag_top_k
    user_language: str | None = request.get("user_language") or None

    if not prompt:
        return {"success": False, "error": "Prompt is required"}

    do_translate: bool = await translator.should_translate(request)
    translated: bool = False

    if do_translate:
        user_lang = await translator.resolve_user_lang(prompt, user_language)
        tr_in = await translator.translate_for_model(prompt, source_lang=user_lang)
        prompt_for_model = tr_in["translated"] if tr_in["success"] and tr_in["was_translated"] else prompt
        translated = prompt_for_model != prompt
    else:
        user_lang = user_language or "en"
        prompt_for_model = prompt

    if use_rag:
        rag_results = await rag_system.search(prompt_for_model, top_k=top_k)
        if rag_results:
            context = rag_system.format_context(rag_results)
            prompt_for_model = f"Context:\n{context}\n\nQuestion: {prompt_for_model}"

    result = await route_generate(
        prompt=prompt_for_model,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    if not result.get("success"):
        return result

    content = result["content"]
    if do_translate:
        tr_out = await translator.translate_response(content, user_lang)
        content = tr_out["translated"] if tr_out["success"] else content

    raw_usage = result.get("usage") or {}
    return {
        "success": True,
        "content": content,
        "model": result["model"],
        "user_language": user_lang,
        "translated": translated,
        "usage": {
            "prompt_tokens":     raw_usage.get("prompt_tokens")     or count_tokens_approx(prompt_for_model),
            "completion_tokens": raw_usage.get("completion_tokens") or count_tokens_approx(content),
            "total_tokens":      raw_usage.get("total_tokens")      or count_tokens_approx(prompt_for_model) + count_tokens_approx(content),
        },
    }
