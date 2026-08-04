# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Конвертация GGUF моделей в ONNX
# =============================================================================
# Описание:
#   Модуль конвертации локальных .gguf файлов в формат ONNX
#   с последующей оптимизацией через onnxruntime-tools.
#   Использует optimum[onnxruntime] для экспорта через HuggingFace Transformers.
#
# Примеры:
#   converter = GGUFConverter()
#   result = await converter.convert("models/gemma.gguf", "artifacts/onnx")
#
# File: src/converter/gguf_to_onnx.py
# Project: Ai Assistant (Docker)
# Version: 0.2.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Проверка зависимостей
CONVERTER_AVAILABLE = False
OPTIMIZER_AVAILABLE = False

try:
    from transformers import AutoTokenizer
    from optimum.onnxruntime import ORTModelForCausalLM
    CONVERTER_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ optimum[onnxruntime] не установлен: pip install optimum[onnxruntime]")

try:
    from onnxruntime.transformers import optimizer as ort_optimizer
    OPTIMIZER_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ onnxruntime-tools не установлен: pip install onnxruntime-tools")


@dataclass
class ConversionResult:
    success: bool
    output_dir: str = ""
    optimized_path: str = ""
    error: str = ""
    chunks_info: dict = field(default_factory=dict)


class GGUFConverter:
    """Конвертер GGUF → ONNX с опциональной оптимизацией"""

    async def convert(
        self,
        gguf_path: str,
        output_dir: str,
        model_type: str = "gpt2",
        opset: int = 17,
        optimize: bool = True,
    ) -> ConversionResult:
        """
        Конвертировать .gguf файл в ONNX.

        Args:
            gguf_path: Путь к .gguf файлу
            output_dir: Директория для сохранения результата
            model_type: Тип модели для оптимизатора ('gpt2', 'bert', 'bart')
            opset: Версия ONNX opset
            optimize: Запустить оптимизацию после экспорта

        Returns:
            ConversionResult с путями и статусом
        """
        if not CONVERTER_AVAILABLE:
            return ConversionResult(
                success=False,
                error="optimum[onnxruntime] не установлен. Выполните: pip install optimum[onnxruntime]"
            )

        src = Path(gguf_path)
        if not src.exists():
            return ConversionResult(success=False, error=f"Файл не найден: {gguf_path}")
        if src.suffix.lower() != ".gguf":
            return ConversionResult(success=False, error=f"Ожидается .gguf файл, получен: {src.suffix}")

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        logger.info(f"🔄 Начало конвертации: {src.name} → {out}")

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._export, str(src), str(out), opset
            )
            if not result.success:
                return result

            if optimize and OPTIMIZER_AVAILABLE:
                onnx_file = out / "model.onnx"
                if onnx_file.exists():
                    opt_path = await asyncio.get_event_loop().run_in_executor(
                        None, self._optimize, str(onnx_file), model_type
                    )
                    result.optimized_path = opt_path

            logger.info(f"✅ Конвертация завершена: {out}")
            return result

        except Exception as e:
            logger.error(f"❌ Ошибка конвертации: {e}")
            return ConversionResult(success=False, error=str(e))

    def _export(self, gguf_path: str, output_dir: str, opset: int) -> ConversionResult:
        """Экспорт модели через optimum (синхронный, запускается в executor)"""
        try:
            logger.info(f"📥 Загрузка токенизатора из: {gguf_path}")
            tokenizer = AutoTokenizer.from_pretrained(gguf_path)

            logger.info("📤 Экспорт в ONNX через ORTModelForCausalLM...")
            model = ORTModelForCausalLM.from_pretrained(
                gguf_path,
                export=True,
                opset=opset,
            )

            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)

            # Собираем информацию о результате
            out = Path(output_dir)
            onnx_files = list(out.glob("*.onnx"))
            chunks_info = {
                "onnx_files": [f.name for f in onnx_files],
                "total_size_mb": round(
                    sum(f.stat().st_size for f in onnx_files) / 1024 / 1024, 2
                ),
            }

            return ConversionResult(
                success=True,
                output_dir=output_dir,
                chunks_info=chunks_info,
            )

        except Exception as e:
            logger.error(f"❌ Ошибка экспорта: {e}")
            return ConversionResult(success=False, error=str(e))

    def _optimize(self, onnx_path: str, model_type: str) -> str:
        """Оптимизация ONNX модели (синхронная, запускается в executor)"""
        try:
            logger.info(f"⚡ Оптимизация: {onnx_path}")
            opt_model = ort_optimizer.optimize_model(onnx_path, model_type=model_type)
            output_path = onnx_path.replace(".onnx", "_optimized.onnx")
            opt_model.save_model_to_file(output_path)
            logger.info(f"✅ Оптимизированная модель: {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"⚠️ Оптимизация не удалась (модель сохранена без оптимизации): {e}")
            return ""

    @staticmethod
    def is_available() -> dict:
        """Проверить доступность зависимостей"""
        return {
            "converter": CONVERTER_AVAILABLE,
            "optimizer": OPTIMIZER_AVAILABLE,
        }


# Глобальный экземпляр
gguf_converter = GGUFConverter()
