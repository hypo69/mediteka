# -*- coding: utf-8 -*-
import pytest
from src.utils.text_extractor import TextExtractor

@pytest.mark.asyncio
class TestTextExtractorLogic:
    """Тесты маппинга форматов в TextExtractor."""

    async def test_xlsx_uses_markitdown(self, mocker):
        """Проверка, что XLSX файлы направляются в MarkItDown."""
        extractor = TextExtractor()
        
        # Мокаем MarkItDown, чтобы не запускать тяжелую конвертацию
        mock_md = mocker.patch.object(extractor, 'md')
        mock_md.convert.return_value.text_content = "Excel Data"
        
        result = await extractor.extract_from_file("test.xlsx")
        
        assert result == "Excel Data"
        mock_md.convert.assert_called_once_with("test.xlsx")

    async def test_image_uses_ocr(self, mocker):
        """Проверка, что изображения направляются в Tesseract (OCR)."""
        extractor = TextExtractor()
        
        # Мокаем pytesseract
        mock_ocr = mocker.patch('src.utils.text_extractor.pytesseract.image_to_string')
        mock_ocr.return_value = "Text from Image"
        
        # Мокаем открытие изображения
        mocker.patch('PIL.Image.open')
        
        result = await extractor.extract_from_file("test.png")
        
        assert result == "Text from Image"
        mock_ocr.assert_called_once()

    async def test_fallback_to_plain_text(self, mocker):
        """Проверка фолбэка для обычных текстовых файлов."""
        extractor = TextExtractor()
        mocker.patch("builtins.open", mocker.mock_open(read_data="plain text"))
        
        result = await extractor.extract_from_file("test.txt")
        assert result == "plain text"