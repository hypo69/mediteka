# -*- coding: utf-8 -*-
import os
import logging
import asyncio
from typing import Optional

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None
from markitdown import MarkItDown

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None

logger = logging.getLogger(__name__)

class TextExtractor:
    """!
    Кастомный экстрактор для специфических задач: OCR и Web-scraping с JS.
    """
    def __init__(self, settings: dict = None):
        self.settings = settings or {}
        self.ocr_langs = self.settings.get("extractor_ocr_langs", "rus+eng")
        self.enable_js = self.settings.get("extractor_enable_js", False)
        self.md = MarkItDown()

    async def extract_from_file(self, file_path: str) -> str:
        """Извлечение текста с поддержкой OCR для изображений."""
        ext = os.path.splitext(file_path)[1].lower()
        
        # Если это изображение, используем Tesseract
        if ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return await self._run_ocr(file_path)
        # Если это PDF, пробуем OCR, если MarkItDown не справился (этот TextExtractor - фолбэк)
        if ext == '.pdf' and pytesseract and convert_from_path:
            return await self._run_ocr_on_pdf(file_path)
        
        # XLSX обрабатываем через MarkItDown внутри экстрактора, как запрашивалось
        if ext == '.xlsx':
            try:
                loop = asyncio.get_event_loop()
                # MarkItDown.convert - синхронный метод
                result = await loop.run_in_executor(None, self.md.convert, file_path)
                return result.text_content
            except Exception as e:
                logger.error(f"Ошибка MarkItDown при обработке XLSX: {e}")
                return ""

        # Фолбэк для текстовых файлов
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")
            return ""

    async def extract_from_url(self, url: str) -> str:
        """Извлечение контента из URL с поддержкой JavaScript."""
        if self.enable_js:
            return await self._extract_with_playwright(url)
        return await self._extract_simple_html(url)

    async def extract_text_from_image(self, image_path: str) -> str:
        """Public OCR API for callers that already extracted an image file."""
        return await self._run_ocr(image_path)

    async def _run_ocr(self, image_path: str) -> str:
        """Выполнение оптического распознавания символов."""
        if not pytesseract:
            return "[Ошибка: pytesseract не установлен]"
        
        try:
            # Запуск OCR в отдельном потоке, чтобы не блокировать event loop
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None, 
                lambda: pytesseract.image_to_string(Image.open(image_path), lang=self.ocr_langs)
            )
            return text
        except Exception as e:
            logger.error(f"OCR Error: {e}")
            return ""

    async def _extract_with_playwright(self, url: str) -> str:
        """Рендеринг страницы через Playwright."""
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(url, timeout=self.settings.get("extractor_web_timeout", 30) * 1000)
                content = await page.content() # Или извлечение чистого текста через JS
                text = await page.evaluate("() => document.body.innerText")
                await browser.close()
                return text
        except Exception as e:
            logger.error(f"Playwright Error: {e}")
            return await self._extract_simple_html(url)

    async def _extract_simple_html(self, url: str) -> str:
        """Простой захват HTML (без JS)."""
        import requests
        from bs4 import BeautifulSoup
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text(separator='\n')
        except Exception as e:
            logger.error(f"HTML Extraction Error: {e}")
            return ""

    async def _run_ocr_on_pdf(self, pdf_path: str) -> str:
        """Выполнение OCR на PDF-файле, постранично."""
        if not pytesseract or not convert_from_path:
            return "[Ошибка: pytesseract или pdf2image не установлены]"
        
        try:
            loop = asyncio.get_event_loop()
            # Конвертируем PDF в список изображений
            images = await loop.run_in_executor(None, convert_from_path, pdf_path)
            
            all_text = []
            for i, image in enumerate(images):
                logger.debug(f"Выполнение OCR на странице {i+1} PDF: {pdf_path}")
                text = await loop.run_in_executor(None, lambda: pytesseract.image_to_string(image, lang=self.ocr_langs))
                all_text.append(text)
            return "\n\n".join(all_text)
        except Exception as e:
            logger.error(f"OCR PDF Error: {e}")
            return ""
