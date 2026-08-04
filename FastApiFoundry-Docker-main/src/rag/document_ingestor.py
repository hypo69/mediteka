# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Ингестация документов (Document Ingestor)
# =============================================================================
# Описание:
#   Подготовка данных для RAG: очистка, извлечение текста и определение языка.
#   Обеспечивает асинхронную обработку и нормализацию контента для индексации.
#
# File: src/rag/document_ingestor.py
# Project: FastApiFoundry
# Package: src.rag
# Version: 0.8.3
# Author: hypo69
# Date: 2025
# =============================================================================

import asyncio
import os
import zipfile
import tarfile
import tempfile
import shutil
import logging
import re
from typing import Optional, Tuple, Dict, Any, List
from markitdown import MarkItDown
from ..utils.text_extractor import TextExtractor
from src.utils.translator import translator

try:
    import py7zr
except ImportError:
    py7zr = None

try:
    import rarfile
except ImportError:
    rarfile = None

# Список паттернов для игнорирования при рекурсивном обходе архивов
IGNORE_PATTERNS = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.ds_store', '.idea', '.vscode'}

logger = logging.getLogger(__name__)

from fastapi import HTTPException, UploadFile
from pdf2image import convert_from_path
import PyPDF2 # For PDF metadata extraction
import docx # For DOCX metadata extraction



class DocumentIngestor:
    """Подготовка документов к индексации в RAG.

    Инкапсулирует выбор инструментов извлечения текста и первичную обработку.

    Архитектурное ограничение — временные файлы:
        Все внутренние методы (_process_file_recursive, MarkItDown, zipfile,
        tarfile, py7zr, rarfile) работают с путями к файлам на диске, а не
        с байтами в памяти. Поэтому process_upload() обязан сохранить
        содержимое UploadFile во временный файл перед обработкой.

        Временный файл создаётся через tempfile.mkstemp() в системной
        temp-директории (например %TEMP% или /tmp).
        Суффикс берётся из basename(filename), чтобы избежать ошибок
        при именах вида "ru/about.md" (webkitdirectory upload).
        Файл гарантированно удаляется в блоке finally.

        TODO: рефакторинг на работу с io.BytesIO позволит убрать temp-файлы,
        но требует переписать все зависимые экстракторы.
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

    async def _detect_language(self, text: str) -> str:
        """Определение языка с поддержкой различных стратегий (FastText или Translator)."""
        method = self.settings.get("lang_detection_method", "translator")
        
        if method == "fasttext":
            try:
                import fasttext
                model_path = self.settings.get("fasttext_model_path")
                if model_path and os.path.exists(model_path):
                    if not hasattr(self, '_ft_model'):
                        # Ленивая загрузка модели
                        self._ft_model = fasttext.load_model(model_path)
                    
                    # FastText ожидает текст без переносов строк для предсказания
                    prediction = self._ft_model.predict(text.replace('\n', ' ')[:500])
                    return prediction[0][0].replace('__label__', '')
            except Exception as e:
                logger.error(f"Ошибка FastText: {e}. Фолбэк на Translator.")

        # По умолчанию или при сбое используем MyMemory/Translator
        lang_detection = await translator.detect_language(text[:500])
        return lang_detection.get("language", "unknown")

    def _extract_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Извлечение метаданных из PDF-файла."""
        metadata = {}
        if not PyPDF2:
            logger.warning("PyPDF2 is not installed, cannot extract PDF metadata.")
            return metadata
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                info = reader.metadata
                if info:
                    metadata["author"] = info.author
                    metadata["creator"] = info.creator
                    metadata["producer"] = info.producer
                    metadata["creation_date"] = info.creation_date.isoformat() if info.creation_date else None
                    metadata["mod_date"] = info.mod_date.isoformat() if info.mod_date else None
                    metadata["title"] = info.title
                    metadata["subject"] = info.subject
                    metadata["keywords"] = info.keywords
        except Exception as e:
            logger.error(f"Ошибка при извлечении метаданных PDF из {file_path}: {e}")
        return {k: v for k, v in metadata.items() if v is not None} # Filter out None values

    def _extract_pdf_annotations(self, file_path: str) -> str:
        """Извлечение комментариев и заметок из PDF-файла."""
        annotations_text = []
        if not PyPDF2:
            return ""
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages):
                    if '/Annots' in page:
                        for annot in page['/Annots']:
                            # Get the actual annotation object
                            obj = annot.get_object()
                            subtype = obj.get('/Subtype')
                            
                            if subtype == '/Text': # Sticky note
                                author = obj.get('/T', 'Unknown Author')
                                contents = obj.get('/Contents', '')
                                if contents:
                                    annotations_text.append(f"Page {page_num + 1} - Comment by {author}: {contents}")
                            elif subtype == '/FreeText': # Text box
                                contents = obj.get('/Contents', '')
                                if contents:
                                    annotations_text.append(f"Page {page_num + 1} - Text Box: {contents}")
                            # Add other annotation types if needed, e.g., /Highlight, /StrikeOut
        except Exception as e:
            logger.debug(f"Отказ извлечения аннотаций PDF {file_path}: {e}")
        return "\n".join(annotations_text)

    def _extract_pdf_form_data(self, file_path: str) -> str:
        """Извлечение данных из интерактивных форм PDF (AcroForms)."""
        # Обоснование: формы содержат ключевую информацию, которая часто теряется при обычном извлечении текста.
        form_results = []
        if not PyPDF2:
            return ""
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                # Получение словаря полей формы
                fields = reader.get_fields()
                if fields:
                    for name, field in fields.items():
                        # Извлечение значения поля (/V)
                        value = field.get('/V')
                        if value:
                            form_results.append(f"{name}: {value}")
        except Exception as e:
            logger.debug(f"Отказ извлечения данных формы PDF {file_path}: {e}")
        
        return "\n".join(form_results)

    async def _ocr_images_in_docx(self, docx_path: str) -> str:
        """Извлечение текста из изображений внутри DOCX через OCR."""
        all_ocr_text = []
        try:
            with zipfile.ZipFile(docx_path, 'r') as z:
                # Поиск изображений в стандартной директории DOCX
                image_files = [f for f in z.namelist() if f.startswith('word/media/')]
                for img_name in image_files:
                    with z.open(img_name) as img_file:
                        img_data = img_file.read()
                        ext = os.path.splitext(img_name)[1]
                        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_img:
                            tmp_img.write(img_data)
                            tmp_img_path = tmp_img.name
                        
                        ocr_text = await self.custom_extractor.extract_text_from_image(tmp_img_path)
                        if ocr_text.strip():
                            all_ocr_text.append(f"--- OCR from image: {os.path.basename(img_name)} ---\n{ocr_text}")
                        
                        if os.path.exists(tmp_img_path):
                            os.remove(tmp_img_path)
        except Exception as e:
            logger.warning(f"⚠️ [Ingestion] Ошибка OCR изображений в DOCX {docx_path}: {e}")
        return "\n\n".join(all_ocr_text)

    def _extract_docx_metadata(self, file_path: str) -> Dict[str, Any]:
        """Извлечение метаданных из DOCX-файла."""
        metadata = {}
        if not docx:
            logger.warning("python-docx is not installed, cannot extract DOCX metadata.")
            return metadata
        try:
            document = docx.Document(file_path)
            properties = document.core_properties
            if properties:
                metadata["author"] = properties.author
                metadata["last_modified_by"] = properties.last_modified_by
                metadata["created"] = properties.created.isoformat() if properties.created else None
                metadata["modified"] = properties.modified.isoformat() if properties.modified else None
                metadata["title"] = properties.title
                metadata["subject"] = properties.subject
                metadata["keywords"] = properties.keywords
                metadata["category"] = properties.category
                metadata["comments"] = properties.comments
            return {k: v for k, v in metadata.items() if v is not None}
        except Exception as e:
            logger.error(f"Ошибка при извлечении метаданных DOCX из {file_path}: {e}")
        return metadata

    def _extract_docx_comments(self, file_path: str) -> str:
        """Извлечение комментариев и примечаний из DOCX-файла."""
        # Обоснование: Примечания и комментарии в Word часто содержат важные пояснения к тексту.
        comments = []
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                if 'word/comments.xml' in z.namelist():
                    from lxml import etree
                    comments_xml = z.read('word/comments.xml')
                    root = etree.fromstring(comments_xml)
                    # Пространство имен для WordprocessingML
                    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    for comment in root.xpath('//w:comment', namespaces=ns):
                        author = comment.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author', 'Unknown')
                        text_nodes = comment.xpath('.//w:t', namespaces=ns)
                        text = "".join([node.text for node in text_nodes if node.text])
                        if text.strip():
                            comments.append(f"Comment by {author}: {text}")
        except Exception as e:
            logger.debug(f"Отказ извлечения комментариев DOCX {file_path}: {e}")
        return "\n".join(comments)

    def _extract_docx_hyperlinks(self, file_path: str) -> str:
        """Извлечение гиперссылок из DOCX-файла."""
        # Обоснование: Гиперссылки содержат внешние источники, важные для полноты контекста RAG.
        links = []
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                file_list = z.namelist()
                if 'word/document.xml' in file_list and 'word/_rels/document.xml.rels' in file_list:
                    from lxml import etree
                    # 1. Загрузка карты отношений (ID -> URL)
                    rels_xml = z.read('word/_rels/document.xml.rels')
                    rels_root = etree.fromstring(rels_xml)
                    ns_rel = {'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'}
                    rel_map = {
                        rel.get('Id'): rel.get('Target')
                        for rel in rels_root.xpath('//rel:Relationship', namespaces=ns_rel)
                        if 'hyperlink' in rel.get('Type')
                    }

                    # 2. Поиск ссылок в основном документе
                    doc_xml = z.read('word/document.xml')
                    root = etree.fromstring(doc_xml)
                    ns_w = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    
                    for hl in root.xpath('//w:hyperlink', namespaces=ns_w):
                        r_id = hl.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                        url = rel_map.get(r_id)
                        if url:
                            text_nodes = hl.xpath('.//w:t', namespaces=ns_w)
                            link_text = "".join([t.text for t in text_nodes if t.text])
                            if link_text.strip():
                                links.append(f"{link_text}: {url}")
        except Exception as e:
            logger.debug(f"Отказ извлечения гиперссылок DOCX {file_path}: {e}")
        return "\n".join(links)

    def _extract_docx_tracked_changes(self, file_path: str) -> str:
        """Извлечение текста из заблокированных (Track Changes) правок в DOCX-файле."""
        tracked_changes_text = []
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                if 'word/document.xml' in z.namelist():
                    from lxml import etree
                    doc_xml = z.read('word/document.xml')
                    root = etree.fromstring(doc_xml)
                    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

                    # Извлечение вставленного текста
                    for ins in root.xpath('//w:ins', namespaces=ns):
                        author = ins.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author', 'Unknown')
                        date_str = ins.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}date', '')
                        text_nodes = ins.xpath('.//w:t', namespaces=ns)
                        text = "".join([node.text for node in text_nodes if node.text])
                        if text.strip():
                            tracked_changes_text.append(f"Inserted by {author} ({date_str}): {text}")

                    # Извлечение удаленного текста
                    for dele in root.xpath('//w:del', namespaces=ns):
                        author = dele.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author', 'Unknown')
                        date_str = dele.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}date', '')
                        text_nodes = dele.xpath('.//w:t', namespaces=ns)
                        text = "".join([node.text for node in text_nodes if node.text])
                        if text.strip():
                            tracked_changes_text.append(f"Deleted by {author} ({date_str}): {text}")

        except Exception as e:
            logger.debug(f"Отказ извлечения отслеживаемых изменений DOCX {file_path}: {e}")
        return "\n".join(tracked_changes_text)

    def _extract_docx_hidden_text(self, file_path: str) -> str:
        """Извлечение скрытого текста из DOCX-файла (теги w:vanish)."""
        hidden_texts = []
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                if 'word/document.xml' in z.namelist():
                    from lxml import etree
                    doc_xml = z.read('word/document.xml')
                    root = etree.fromstring(doc_xml)
                    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    # Ищем прогоны <w:r>, у которых в свойствах <w:rPr> есть тег <w:vanish/>
                    for run in root.xpath('//w:r[w:rPr/w:vanish]', namespaces=ns):
                        text_nodes = run.xpath('.//w:t', namespaces=ns)
                        text = "".join([node.text for node in text_nodes if node.text])
                        if text.strip():
                            hidden_texts.append(text)
        except Exception as e:
            logger.debug(f"Отказ извлечения скрытого текста DOCX {file_path}: {e}")
        return "\n".join(hidden_texts)

    def _extract_docx_custom_properties(self, file_path: str) -> Dict[str, Any]:
        """Извлечение пользовательских свойств (Custom Properties) из DOCX-файла."""
        custom_props = {}
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                if 'docProps/custom.xml' in z.namelist():
                    from lxml import etree
                    custom_xml = z.read('docProps/custom.xml')
                    root = etree.fromstring(custom_xml)
                    # Пространства имен для пользовательских свойств и типов данных
                    ns = {
                        'cp': 'http://schemas.openxmlformats.org/officeDocument/2006/custom-properties',
                        'vt': 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'
                    }
                    for prop in root.xpath('//cp:property', namespaces=ns):
                        name = prop.get('name')
                        val_nodes = prop.xpath('./vt:*', namespaces=ns)
                        if name and val_nodes:
                            # Добавляем префикс custom_ для отличия от стандартных метаданных
                            custom_props[f"custom_{name}"] = val_nodes[0].text
        except Exception as e:
            logger.debug(f"Отказ извлечения пользовательских свойств DOCX {file_path}: {e}")
        return custom_props

    def _check_archive_limits(self, name: str, files: int, max_files: int, size: int, max_mb: int) -> None:
        """Валидация количественных показателей архива перед распаковкой."""
        if files > max_files:
            logger.warning(f"⛔ [Ingestion] Лимит файлов превышен в {name}: {files} > {max_files}")
            raise HTTPException(status_code=413, detail=f"Архив содержит слишком много файлов (макс: {max_files})")
            
        size_mb = size / (1024 * 1024)
        if size_mb > max_mb:
            logger.warning(f"⛔ [Ingestion] Лимит распакованного размера превышен в {name}: {size_mb:.1f}MB > {max_mb}MB")
            raise HTTPException(status_code=413, detail=f"Распакованный размер слишком велик (макс: {max_mb}МБ)")

    async def _process_file_recursive(self, file_path: str, source_name: str) -> Tuple[str, str, Dict[str, Any]]:
        """Внутренний метод для рекурсивной обработки файлов (включая ZIP)."""
        ext = os.path.splitext(file_path)[1].lower()
        content = ""
        method = "CustomExtractor"
        metadata = {}

        is_tar = file_path.lower().endswith(('.tar.gz', '.tgz', '.tar.bz2', '.tar.xz', '.tar'))
        is_7z = ext == '.7z'
        is_rar = ext == '.rar'
        if ext == '.zip' or is_tar or is_7z or is_rar:
            if ext == '.zip':
                archive_type = "ZIP"
            elif is_tar:
                archive_type = "Tar"
            elif is_7z:
                archive_type = "7z"
            else:
                archive_type = "RAR"
            logger.info(f"📦 [Ingestion] Распаковка {archive_type}-архива: {source_name}")
            all_contents: List[str] = []
            with tempfile.TemporaryDirectory() as tmp_dir:
                try:
                    total_uncompressed_bytes = 0
                    total_files = 0
                    max_files = self.settings.get("max_files_per_archive", 1000)
                    max_uncompressed_mb = self.settings.get("max_uncompressed_size_mb", 100)

                    if ext == '.zip':
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            for info in zip_ref.infolist():
                                if not info.is_dir():
                                    total_files += 1
                                    total_uncompressed_bytes += info.file_size
                            self._check_archive_limits(source_name, total_files, max_files, total_uncompressed_bytes, max_uncompressed_mb)
                            zip_ref.extractall(tmp_dir)
                    elif is_tar:
                        with tarfile.open(file_path, 'r:*') as tar_ref:
                            for member in tar_ref.getmembers():
                                if member.isfile():
                                    total_files += 1
                                    total_uncompressed_bytes += member.size
                            self._check_archive_limits(source_name, total_files, max_files, total_uncompressed_bytes, max_uncompressed_mb)
                            tar_ref.extractall(tmp_dir)
                    elif is_7z:
                        if not py7zr:
                            raise HTTPException(status_code=422, detail="7z support not available: install py7zr")
                        with py7zr.SevenZipFile(file_path, 'r') as sz_ref:
                            for info in sz_ref.list():
                                if not info.is_dir:
                                    total_files += 1
                                    total_uncompressed_bytes += info.uncompressed
                            self._check_archive_limits(source_name, total_files, max_files, total_uncompressed_bytes, max_uncompressed_mb)
                            sz_ref.extractall(tmp_dir)
                    elif is_rar:
                        if not rarfile:
                            raise HTTPException(status_code=422, detail="RAR support not available: install rarfile")
                        with rarfile.RarFile(file_path, 'r') as rar_ref:
                            for info in rar_ref.infolist():
                                if not info.is_dir():
                                    total_files += 1
                                    total_uncompressed_bytes += info.file_size
                            self._check_archive_limits(source_name, total_files, max_files, total_uncompressed_bytes, max_uncompressed_mb)
                            rar_ref.extractall(tmp_dir)

                    for root, dirs, filenames in os.walk(tmp_dir):
                        dirs[:] = [d for d in dirs if d.lower() not in IGNORE_PATTERNS and not d.startswith('.')]
                        for member in filenames:
                            if member.lower() in IGNORE_PATTERNS or member.startswith('.'):
                                continue
                            m_path = os.path.join(root, member)
                            rel_path = os.path.relpath(m_path, tmp_dir)
                            m_content, _, _ = await self._process_file_recursive(m_path, rel_path)
                            if m_content:
                                all_contents.append(f"--- File: {rel_path} ---\n{m_content}")

                    content = "\n\n".join(all_contents)
                    method = f"{archive_type}Processor"
                except Exception as e:
                    if isinstance(e, HTTPException): raise
                    logger.error(f"Ошибка при обработке архива {source_name} ({archive_type}): {e}")
        
        elif ext in ['.docx', '.pptx', '.xlsx', '.pdf', '.html']:
            logger.info(f"🛠️ [Ingestion] Извлечение через MarkItDown: {source_name}")
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.markitdown.convert, file_path)
                content = result.text_content
                method = "MarkItDown"

                # Дополнительное извлечение текста из картинок внутри DOCX
                if ext == '.docx':
                    ocr_text = await self._ocr_images_in_docx(file_path)
                    if ocr_text:
                        content += f"\n\n--- OCR Content from Images ---\n{ocr_text}"
            except Exception as e:
                logger.warning(f"⚠️ MarkItDown failed for {source_name}: {e}. Fallback to Custom.")
                content = await self.custom_extractor.extract_from_file(file_path)
        else:
            content = await self.custom_extractor.extract_from_file(file_path)

        if ext == '.pdf':
            metadata.update(self._extract_pdf_metadata(file_path))
            # Дополнение контента данными из интерактивных форм
            form_data = self._extract_pdf_form_data(file_path)
            if form_data:
                content += f"\n\n--- PDF Form Data ---\n{form_data}"
            # Дополнение контента комментариями и заметками
            annotations_data = self._extract_pdf_annotations(file_path)
            if annotations_data:
                content += f"\n\n--- PDF Annotations ---\n{annotations_data}"
        elif ext == '.docx':
            metadata.update(self._extract_docx_metadata(file_path))
            # Дополнение контента комментариями и примечаниями Word
            docx_comments = self._extract_docx_comments(file_path)
            if docx_comments:
                content += f"\n\n--- DOCX Comments ---\n{docx_comments}"
            # Дополнение контента гиперссылками Word
            docx_links = self._extract_docx_hyperlinks(file_path)
            if docx_links:
                content += f"\n\n--- DOCX Hyperlinks ---\n{docx_links}"
            # Дополнение контента скрытым текстом Word
            docx_hidden = self._extract_docx_hidden_text(file_path)
            if docx_hidden:
                content += f"\n\n--- DOCX Hidden Text ---\n{docx_hidden}"
            # Дополнение контента отслеживаемыми изменениями Word
            docx_tracked_changes = self._extract_docx_tracked_changes(file_path)
            if docx_tracked_changes:
                content += f"\n\n--- DOCX Tracked Changes ---\n{docx_tracked_changes}"
            # Дополнение метаданных пользовательскими свойствами Word
            metadata.update(self._extract_docx_custom_properties(file_path))

        return content, method, metadata

    async def _finalize_and_detect(self, raw_content: str, source_name: str, method: str, meta: Dict[str, Any]) -> Tuple[str, str, str, Dict[str, Any]]:
        cleaned = self._clean_text(raw_content)
        meta["lang"] = await self._detect_language(cleaned)
        logger.info(f"✅ [Ingestion] Готово: {source_name}. Язык: {meta['lang']}")
        return cleaned, source_name, method, meta

    async def process_upload(self, file: UploadFile) -> Tuple[str, str, str, Dict[str, Any]]:
        """Обработка загруженного файла через временный файл на диске.

        Почему используется временный файл:
            FastAPI передаёт содержимое как UploadFile (SpooledTemporaryFile
            в памяти), но все нижележащие экстракторы (MarkItDown, zipfile,
            tarfile, py7zr, rarfile) требуют путь к файлу на диске.
            Поэтому байты сначала сбрасываются в tempfile.mkstemp(), а после
            обработки файл удаляется.

        Почему mkstemp, а не f"temp_{filename}":
            file.filename при загрузке директории через <input webkitdirectory>
            содержит относительный путь (например "ru/about.md"). Конкатенация
            "temp_" + "ru/about.md" даёт несуществующий путь "temp_ru/about.md".
            mkstemp создаёт файл в системной temp-директории, используя только
            расширение из basename(filename).

        Args:
            file (UploadFile): Загруженный файл. filename может содержать
                относительный путь (webkitdirectory), используется только
                как source_name для метаданных индекса.

        Returns:
            Tuple[str, str, str, Dict]: (text, source_name, method, metadata).
        """
        source_name = file.filename or "upload"
        suffix = os.path.splitext(os.path.basename(source_name))[1] or ".tmp"
        fd, temp_path = __import__("tempfile").mkstemp(suffix=suffix)
        os.close(fd)
        logger.info(f"🚀 [Ingestion] Начало обработки файла: {source_name}")
        
        try:
            # Валидация размера файла перед сохранением
            doc_metadata: Dict[str, Any] = {}
            max_mb = self.settings.get("max_file_size_mb", 20)
            if file.size and file.size > max_mb * 1024 * 1024:
                logger.warning(f"⛔ [Ingestion] Файл {source_name} слишком велик ({file.size} байт)")
                raise HTTPException(status_code=413, detail=f"Файл слишком велик. Максимальный размер: {max_mb} МБ")

            logger.debug(f"📂 [Ingestion] Сохранение во временный файл: {temp_path}")
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            content, method, meta = await self._process_file_recursive(temp_path, source_name)
            doc_metadata.update(meta)

            return await self._finalize_and_detect(content, source_name, method, doc_metadata)
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {source_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка при обработке файла: {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def process_url(self, url: str) -> Tuple[str, str, str, Dict[str, Any]]:
        """Обработка URL через TextExtractor."""
        raw_content = await self.custom_extractor.extract_from_url(url)
        return await self._finalize_and_detect(raw_content, url, "URLExtractor", {"source": url, "type": "url"})
