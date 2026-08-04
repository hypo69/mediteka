# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Whisper Audio Extractor
# =============================================================================
# Description:
#   Local audio transcription extractor using faster-whisper.
#   Converts MP3, WAV, M4A, OGG, FLAC, WEBM to plain text for RAG indexing.
#   Runs fully offline — no cloud API required.
#
#   Install: pip install faster-whisper
#
#   Supported models (downloaded on first use to ~/.cache/huggingface/hub):
#     tiny, base, small, medium, large-v2, large-v3
#
# File: src/rag/text_extractors/whisper/extractor.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}


class WhisperExtractor:
    """Local audio transcription extractor using faster-whisper.

    Transcribes audio files to text suitable for RAG indexing.
    Model is lazy-loaded on first use and cached for subsequent calls.

    Args:
        model_size (str): Whisper model size. One of: tiny, base, small,
            medium, large-v2, large-v3. Default: 'base'.
        device (str): Compute device — 'cpu' or 'cuda'. Default: 'cpu'.
        compute_type (str): Quantization type. 'int8' for CPU (fastest),
            'float16' for GPU. Default: 'int8'.
        language (str | None): Force language code (e.g. 'ru', 'en').
            None = auto-detect. Default: None.

    Example:
        >>> extractor = WhisperExtractor(model_size="base")
        >>> result = extractor.extract_from_file("interview.mp3")
        >>> print(result["text"])
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str | None = None,
    ) -> None:
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._language = language
        self._model: Any = None

    def _get_model(self) -> Any:
        """Lazy-initialize faster-whisper model.

        Returns:
            WhisperModel: Loaded faster-whisper model instance.

        Exceptions:
            ImportError: If faster-whisper is not installed.
        """
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as e:
                raise ImportError(
                    "faster-whisper is not installed. Run: pip install faster-whisper"
                ) from e

            logger.info(f"📥 Loading Whisper model '{self._model_size}' on {self._device}...")
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )
            logger.info(f"✅ Whisper model '{self._model_size}' loaded")

        return self._model

    def is_supported(self, filename: str) -> bool:
        """Check if the file extension is supported for transcription.

        Args:
            filename (str): Filename or path to check.

        Returns:
            bool: True if the extension is in the supported set.

        Example:
            >>> WhisperExtractor().is_supported("lecture.mp3")
            True
            >>> WhisperExtractor().is_supported("report.pdf")
            False
        """
        return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS

    def extract_from_file(self, file_path: str | Path) -> dict[str, Any]:
        """Transcribe audio from a local file.

        Args:
            file_path (str | Path): Path to the audio file.

        Returns:
            dict[str, Any]: Dict with keys:
                - 'text' (str): Full transcription joined by spaces.
                - 'filename' (str): Original filename.
                - 'language' (str): Detected or forced language code.
                - 'segments' (list[dict]): Per-segment dicts with
                  'start', 'end', 'text'.

        Exceptions:
            FileNotFoundError: If file_path does not exist.
            ValueError: If file extension is not supported.
            ImportError: If faster-whisper is not installed.

        Example:
            >>> extractor = WhisperExtractor()
            >>> result = extractor.extract_from_file("meeting.wav")
            >>> result["language"]
            'ru'
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not self.is_supported(path.name):
            raise ValueError(
                f"Unsupported audio format: {path.suffix}. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        return self._transcribe(path, path.name)

    def extract_from_bytes(self, content: bytes, filename: str) -> dict[str, Any]:
        """Transcribe audio from raw bytes.

        Writes bytes to a temp file, transcribes, then cleans up.

        Args:
            content (bytes): Raw audio file bytes.
            filename (str): Original filename (used for extension detection).

        Returns:
            dict[str, Any]: Same structure as extract_from_file.

        Exceptions:
            ValueError: If file extension is not supported.
            ImportError: If faster-whisper is not installed.

        Example:
            >>> with open("audio.mp3", "rb") as f:
            ...     data = f.read()
            >>> result = extractor.extract_from_bytes(data, "audio.mp3")
        """
        if not self.is_supported(filename):
            raise ValueError(
                f"Unsupported audio format: {Path(filename).suffix}. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            return self._transcribe(tmp_path, filename)
        finally:
            tmp_path.unlink(missing_ok=True)

    def _transcribe(self, path: Path, filename: str) -> dict[str, Any]:
        """Run faster-whisper transcription on a file path.

        Args:
            path (Path): Path to the audio file on disk.
            filename (str): Display name for logging and result.

        Returns:
            dict[str, Any]: Transcription result with text, language, segments.
        """
        model = self._get_model()

        segments_iter, info = model.transcribe(
            str(path),
            language=self._language,
            beam_size=5,
            vad_filter=True,  # skip silent parts
        )

        segments = []
        texts = []
        for seg in segments_iter:
            segments.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
            })
            texts.append(seg.text.strip())

        full_text = " ".join(texts)
        logger.info(
            f"✅ Whisper transcribed: {filename} "
            f"[{info.language}, {len(full_text)} chars, {len(segments)} segments]"
        )

        return {
            "text": full_text,
            "filename": filename,
            "language": info.language,
            "segments": segments,
        }
