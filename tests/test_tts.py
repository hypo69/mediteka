"""
Тесты модуля src/tts
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path


class TestTTSEdge:
    """Тесты edge.py TTS."""

    @pytest.mark.asyncio
    async def test_synthesize_edge(self):
        """Тест синтеза речи edge-tts."""
        from src.tts.edge import synthesize
        
        with patch('src.tts.edge') as mock_tts:
            # Проверка что функция существует
            assert callable(synthesize)


class TestTTSGTTS:
    """Тесты gtts.py TTS."""

    @pytest.mark.asyncio
    async def test_synthesize_gtts(self):
        """Тест синтеза речи gtts."""
        from src.tts.gtts import synthesize
        
        with patch('src.tts.gtts') as mock_tts:
            assert callable(synthesize)


class TestTTSSilero:
    """Тесты silero.py TTS."""

    def test_get_silero_model(self):
        """Тест загрузки модели Silero."""
        from src.tts.silero import get_silero_model
        
        with patch('src.tts.silero') as mock_silero:
            # Проверка что функция существует
            assert callable(get_silero_model)

    @pytest.mark.asyncio
    async def test_synthesize_silero(self):
        """Тест синтеза речи Silero."""
        from src.tts.silero import synthesize
        
        with patch('src.tts.silero') as mock_silero:
            assert callable(synthesize)


class TestTTSInit:
    """Тесты __init__.py TTS."""

    @pytest.mark.asyncio
    async def test_synthesize_speech(self):
        """Тест синтеза речи (обертка)."""
        from src.tts import synthesize_speech
        
        # Проверка что функция существует
        assert callable(synthesize_speech)


class TestTTSIntegration:
    """Интеграционные тесты TTS."""

    @pytest.mark.asyncio
    async def test_synthesize_all_systems(self, tmp_path):
        """Тест синтеза для всех систем."""
        from src.tts import synthesize_speech
        
        test_file = tmp_path / 'test.mp3'
        text = "Тестовый текст для синтеза речи"
        
        with patch('src.tts.synthesize_speech') as mock_synth:
            mock_synth.return_value = AsyncMock()
            
            result = await synthesize_speech(text, test_file, "edge-tts", "ru-RU-DmitryNeural")
            
            mock_synth.assert_called_once()
