# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Converter API Endpoints
# =============================================================================
# Описание:
#   REST API endpoints для конвертации GGUF моделей в ONNX формат
#
# Примеры:
#   POST /api/v1/converter/convert
#   GET  /api/v1/converter/status
#
# File: src/api/endpoints/converter.py
# Project: Ai Assistant (Docker)
# Version: 0.2.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from ...converter.gguf_to_onnx import gguf_converter

router = APIRouter(prefix="/converter", tags=["Converter"])


class ConvertRequest(BaseModel):
    gguf_path: str
    output_dir: str = "./artifacts/onnx"
    model_type: str = "gpt2"
    opset: int = 17
    optimize: bool = True


@router.get("/status")
async def converter_status():
    """Проверить доступность зависимостей конвертера"""
    deps = gguf_converter.is_available()
    return {
        "success": True,
        "available": deps["converter"],
        "optimizer_available": deps["optimizer"],
        "dependencies": {
            "converter": "optimum[onnxruntime] + transformers",
            "optimizer": "onnxruntime-tools",
        },
        "install_hint": "pip install optimum[onnxruntime] onnxruntime-tools"
            if not deps["converter"] else None,
    }


@router.post("/convert")
async def convert_gguf(request: ConvertRequest):
    """
    Конвертировать .gguf файл в ONNX.

    - **gguf_path**: путь к .gguf файлу на сервере
    - **output_dir**: директория для сохранения результата
    - **model_type**: тип модели для оптимизатора (gpt2, bert, bart)
    - **opset**: версия ONNX opset (рекомендуется 17)
    - **optimize**: запустить оптимизацию после экспорта
    """
    result = await gguf_converter.convert(
        gguf_path=request.gguf_path,
        output_dir=request.output_dir,
        model_type=request.model_type,
        opset=request.opset,
        optimize=request.optimize,
    )

    if result.success:
        return {
            "success": True,
            "output_dir": result.output_dir,
            "optimized_path": result.optimized_path or None,
            "info": result.chunks_info,
        }
    else:
        return {"success": False, "error": result.error}
