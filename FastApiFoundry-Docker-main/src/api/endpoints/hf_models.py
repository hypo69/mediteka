# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: HuggingFace Models API Endpoints
# =============================================================================
# Описание:
#   API endpoints для управления локальными HuggingFace моделями:
#   скачивание, загрузка в память, выгрузка, генерация текста.
#
# Примеры:
#   GET  /api/v1/hf/models
#   POST /api/v1/hf/models/download  {"model_id": "google/gemma-2b"}
#   POST /api/v1/hf/models/load      {"model_id": "google/gemma-2b"}
#   POST /api/v1/hf/models/unload    {"model_id": "google/gemma-2b"}
#   POST /api/v1/hf/generate         {"prompt": "Hello", "model_id": "google/gemma-2b"}
#
# File: src/api/endpoints/hf_models.py
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
import logging
import queue
import threading
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ...models.hf_client import hf_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hf", tags=["huggingface"])


@router.get("/hub/models")
async def list_hub_models() -> dict:
    """Список моделей пользователя с HuggingFace Hub.

    Использует HF_TOKEN из .env.
    Возвращает модели пользователя + популярные открытые text-generation модели.

    Returns:
        dict: success, username, user_models (list), public_models (list);
              success=False, error, user_models=[], public_models if no token.
    """
    import os
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")

    if not token:
        return {
            "success": False,
            "error": "HF_TOKEN not set",
            "hint": "Set HF_TOKEN in Settings tab",
            "user_models": [],
            "public_models": _get_popular_public_models()
        }

    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token)

        # Модели пользователя
        user_info = api.whoami()
        username  = user_info.get("name", "")

        user_models_raw = list(api.list_models(author=username, limit=50))
        user_models = [
            {
                "id":       m.id,
                "private":  m.private,
                "downloads": getattr(m, "downloads", 0),
                "pipeline": getattr(m, "pipeline_tag", None),
            }
            for m in user_models_raw
        ]

        return {
            "success":      True,
            "username":     username,
            "user_models":  user_models,
            "public_models": _get_popular_public_models()
        }

    except Exception as e:
        logger.error(f"HF Hub error: {e}")
        return {
            "success":      False,
            "error":        str(e),
            "user_models":  [],
            "public_models": _get_popular_public_models()
        }


def _get_popular_public_models() -> list:
    """Список популярных публичных text-generation моделей.

    Разделён на две группы:
    - Без лицензии: Phi, Qwen, TinyLlama, DeepSeek — скачиваются сразу
    - С лицензией: Gemma, Llama, Mistral — нужно принять на huggingface.co

    Returns:
        list: [{"id": str, "size": str, "note": str}]
    """
    return [
        {"id": "microsoft/phi-2",                        "size": "~5 GB",  "note": "CPU-friendly, no license"},
        {"id": "microsoft/Phi-3-mini-4k-instruct",       "size": "~7 GB",  "note": "CPU-friendly, no license"},
        {"id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",     "size": "~2 GB",  "note": "Very fast on CPU"},
        {"id": "Qwen/Qwen2.5-0.5B-Instruct",             "size": "~1 GB",  "note": "Tiny, fast"},
        {"id": "Qwen/Qwen2.5-1.5B-Instruct",             "size": "~3 GB",  "note": "Good quality/speed"},
        {"id": "Qwen/Qwen2.5-7B-Instruct",               "size": "~15 GB", "note": "High quality"},
        {"id": "mistralai/Mistral-7B-Instruct-v0.3",     "size": "~14 GB", "note": "Accept license required"},
        {"id": "meta-llama/Llama-3.2-1B-Instruct",       "size": "~2 GB",  "note": "Accept license required"},
        {"id": "meta-llama/Llama-3.2-3B-Instruct",       "size": "~6 GB",  "note": "Accept license required"},
        {"id": "google/gemma-2-2b-it",                   "size": "~5 GB",  "note": "Accept license required"},
        {"id": "google/gemma-2-9b-it",                   "size": "~18 GB", "note": "Accept license required"},
        {"id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", "size": "~3 GB", "note": "No license"},
        {"id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",   "size": "~14 GB","note": "No license"},
    ]


@router.get("/models")
async def list_hf_models() -> dict:
    """Список скачанных и загруженных HF моделей.

    Returns:
        dict: success, downloaded (list), loaded (list).
    """
    return {
        "success": True,
        "downloaded": hf_client.list_downloaded(),
        "loaded": hf_client.list_loaded(),
    }


@router.post("/models/download")
async def download_hf_model(request: dict) -> dict:
    """Download model from HuggingFace Hub (blocking, no progress).

    Args:
        request: {model_id (str), token (str, optional)}

    Returns:
        dict: success, model_id, path on success; success=False, error on failure.

    Raises:
        HTTPException 400: model_id not provided.
    """
    model_id: str = request.get("model_id", "")
    token: str = request.get("token", "")

    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")

    logger.info(f"Downloading HF model: {model_id}")
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: hf_client.download_model(model_id, token or None)
    )
    return result


@router.get("/models/download/stream")
async def download_hf_model_stream(model_id: str, token: str = "") -> StreamingResponse:
    """Download HuggingFace model with SSE progress stream.

    Streams file-by-file progress events as Server-Sent Events.
    Each event is a JSON object with fields:
        type: 'file_start' | 'file_done' | 'done' | 'error'
        filename, file_index, total_files (for file events)
        path (for 'done'), error (for 'error')

    Args:
        model_id: HuggingFace model ID, e.g. 'Qwen/Qwen2.5-0.5B-Instruct'.
        token:    Optional HF token (overrides HF_TOKEN env var).

    Returns:
        StreamingResponse: text/event-stream
    """
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")

    progress_queue: queue.Queue = queue.Queue()

    def _run_download() -> None:
        def _cb(event: dict) -> None:
            progress_queue.put(event)

        result = hf_client.download_model(model_id, token or None, progress_callback=_cb)
        progress_queue.put({"type": "done", **result})

    thread = threading.Thread(target=_run_download, daemon=True)
    thread.start()

    async def _event_stream():
        loop = asyncio.get_event_loop()
        while True:
            try:
                event = await loop.run_in_executor(None, lambda: progress_queue.get(timeout=120))
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") in ("done", "error"):
                    break
            except Exception:
                yield f"data: {json.dumps({'type': 'error', 'error': 'timeout'})}\n\n"
                break

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


@router.post("/models/load")
async def load_hf_model(request: dict) -> dict:
    """Загрузить скачанную модель в память для inference.

    Args:
        request: JSON body с полями:
            model_id (str): HuggingFace model ID (обязательно).
            device (str):   'auto', 'cpu', 'cuda' (default: 'auto').

    Returns:
        dict: success, model_id, device on success; success=False, error on failure.

    Raises:
        HTTPException 400: model_id не передан.
    """
    model_id: str = request.get("model_id", "")
    device: str = request.get("device", "auto")

    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")

    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: hf_client.load_model(model_id, device)
    )
    return result


@router.post("/models/unload")
async def unload_hf_model(request: dict) -> dict:
    """Выгрузить модель из памяти (освободить RAM/VRAM).

    Args:
        request: JSON body с полями:
            model_id (str): HuggingFace model ID (обязательно).

    Returns:
        dict: success, model_id on success; success=False, error on failure.

    Raises:
        HTTPException 400: model_id не передан.
    """
    model_id: str = request.get("model_id", "")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")
    return hf_client.unload_model(model_id)


@router.post("/generate")
async def hf_generate(request: dict) -> dict:
    """Генерация текста через локальную HF модель.

    Args:
        request: JSON body с полями:
            model_id (str):       ID модели (должна быть загружена или скачана).
            prompt (str):         Входной текст.
            max_new_tokens (int): Максимум новых токенов (default: 512).
            temperature (float):  Температура (default: 0.7).

    Returns:
        dict: success, content, model on success; success=False, error on failure.

    Raises:
        HTTPException 400: model_id или prompt не переданы.
    """
    model_id: str = request.get("model_id", "")
    prompt: str = request.get("prompt", "")
    max_new_tokens: int = request.get("max_new_tokens", 512)
    temperature: float = request.get("temperature", 0.7)

    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    return await hf_client.generate(prompt, model_id, max_new_tokens, temperature)


@router.get("/status")
async def hf_status() -> dict:
    """Статус HuggingFace интеграции — доступность библиотек.

    Returns:
        dict: success, transformers ({available, version}),
              huggingface_hub ({available, version}),
              torch ({available, version, cuda}),
              hf_token_set (bool), models_dir (str), install_cmd (str).
    """
    try:
        import transformers
        transformers_ok = True
        transformers_version = transformers.__version__
    except ImportError:
        transformers_ok = False
        transformers_version = None

    try:
        import huggingface_hub
        hub_ok = True
        hub_version = huggingface_hub.__version__
    except ImportError:
        hub_ok = False
        hub_version = None

    try:
        import torch
        torch_ok = True
        cuda_available = torch.cuda.is_available()
        torch_version = torch.__version__
    except ImportError:
        torch_ok = False
        cuda_available = False
        torch_version = None

    import os
    from ...models.hf_client import _get_models_dir
    models_dir = _get_models_dir()

    return {
        "success": True,
        "transformers": {"available": transformers_ok, "version": transformers_version},
        "huggingface_hub": {"available": hub_ok, "version": hub_version},
        "torch": {"available": torch_ok, "version": torch_version, "cuda": cuda_available},
        "hf_token_set": bool(os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")),
        "models_dir": str(models_dir),
        "install_cmd": "pip install transformers accelerate huggingface_hub"
    }