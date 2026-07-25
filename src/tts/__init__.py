# -*- coding: utf-8 -*-
"""
Unified interface for all TTS systems (Microsoft Edge, Google, Silero).
"""
from __future__ import annotations

from pathlib import Path
from src.tts import edge, gtts, silero
from src.logger import logger

async def synthesize_speech(text: str, file_path: Path, tts_system: str = "edge-tts", voice: str = "ru-RU-DmitryNeural"):
    """Synthesizes speech to a file using the selected TTS system and voice."""
    logger.info(f"Synthesizing using system: {tts_system}, voice/speaker: {voice}")
    
    if tts_system == "gtts":
        await gtts.synthesize(text, file_path, voice)
    elif tts_system == "silero":
        await silero.synthesize(text, file_path, voice)
    else:
        # Fallback to edge-tts
        await edge.synthesize(text, file_path, voice)
