# -*- coding: utf-8 -*-
import os
import shutil
import logging
import re
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from src.utils.translator import translator
from markitdown import MarkItDown
from ...utils.text_extractor import TextExtractor

logger = logging.getLogger(__name__)

class DocumentIngestor:
    """!
    Класс, отвечающий за подготовку данных к RAG.
    Инкапсулирует логику выбора инструментов и первичной обработки.
    """
    def __init__(self, settings: dict):
        self.settings = settings
        self.markitdown = MarkItDown()
        self.custom_extractor = TextExtractor(settings=settings)

    def _clean_text(self, text: str) -> str:
        """Очистка текста от лишних пробелов и пустых строк перед отправкой в RAG."""
        if not text:
            return ""
        # Удаляем HTML-теги, если они остались
        text = re.sub(r'<[^>]*>', '', text)
        # Удаляем Markdown-изображения ! [alt](url)
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        # Удаляем Markdown-ссылки, оставляя только текст: [текст](url) -> текст
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Удаляем лишние пробелы в конце каждой строки
        text = "\n".join(line.rstrip() for line in text.splitlines())
        # Заменяем 3 и более переноса строк на 2 (сохраняем структуру абзацев)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Заменяем множественные пробелы и табуляции на один пробел
        text = re.sub(r'[ \t]{2,}', ' ', text)
        return text.strip()

    async def process_upload(self, file: UploadFile) -> Tuple[str, str, str, str]:
        """Обработка загруженного файла."""
        source_name = file.filename
        temp_path = f"temp_{source_name}"
        logger.info(f"🚀 [Ingestion] Начало обработки файла: {source_name}")
        
        try:
            # Валидация размера файла перед сохранением
            max_mb = self.settings.get("max_file_size_mb", 20)
            if file.size and file.size > max_mb * 1024 * 1024:
                logger.warning(f"⛔ [Ingestion] Файл {source_name} слишком велик ({file.size} байт)")
                raise HTTPException(status_code=413, detail=f"Файл слишком велик. Максимальный размер: {max_mb} МБ")

            logger.debug(f"📂 [Ingestion] Сохранение во временный файл: {temp_path}")
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            ext = os.path.splitext(source_name)[1].lower()
            logger.debug(f"🔍 [Ingestion] Определено расширение: {ext}")
            
            content = ""
            method = "CustomExtractor"

            # Логика выбора инструмента (MarkItDown приоритетнее для офисных форматов)
            if ext in ['.docx', '.pptx', '.xlsx', '.pdf', '.html']:
                logger.info(f"🛠️ [Ingestion] Попытка извлечения через MarkItDown: {source_name}")
                try:
                    # Мы используем MarkItDown напрямую здесь для контроля
                    result = self.markitdown.convert(temp_path)
                    content = result.text_content
                    method = "MarkItDown"
                except Exception as e:
                    logger.warning(f"⚠️ [Ingestion] MarkItDown failed for {source_name}: {e}. Falling back to CustomExtractor.")
                    content = await self.custom_extractor.extract_from_file(temp_path)
            else:
                logger.info(f"🛠️ [Ingestion] Использование CustomExtractor для: {source_name}")
                content = await self.custom_extractor.extract_from_file(temp_path)

            cleaned_content = self._clean_text(content)
            # Определение языка
            lang_detection = await translator.detect_language(cleaned_content[:500]) # Анализируем первые 500 символов
            detected_lang = lang_detection.get("language", "unknown")
            logger.info(f"✅ [Ingestion] Успешно обработано: {source_name}. Символов: {len(content)} -> {len(cleaned_content)} (после очистки). Язык: {detected_lang}")
            
            return cleaned_content, source_name, method, detected_lang

        except Exception as e:
            logger.error(f"❌ [Ingestion] Критическая ошибка при обработке {source_name}: {e}", exc_info=True)
            raise
        finally:
            if os.path.exists(temp_path):
                logger.debug(f"🧹 [Ingestion] Удаление временного файла: {temp_path}")
                os.remove(temp_path)

    async def process_url(self, url: str) -> Tuple[str, str, str, str]:
        """Обработка контента по ссылке."""
        logger.info(f"🌐 [Ingestion] Начало извлечения из URL: {url}")
        content = await self.custom_extractor.extract_from_url(url)
        cleaned_content = self._clean_text(content)
        # Определение языка
        lang_detection = await translator.detect_language(cleaned_content[:500])
        detected_lang = lang_detection.get("language", "unknown")
        logger.info(f"✅ [Ingestion] URL обработан. Символов: {len(content)} -> {len(cleaned_content)}. Язык: {detected_lang}")
        
        return cleaned_content, url, "CustomExtractor", detected_lang