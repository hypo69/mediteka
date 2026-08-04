# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: MarkItDown Text Extractor
# =============================================================================
# Description:
#   Text extractor backend based on Microsoft MarkItDown.
#   Converts files and URLs to Markdown text for use in the RAG pipeline.
#   Supports: PDF, DOCX, PPTX, XLSX, images (OCR), HTML, CSV, JSON, XML,
#             ZIP, YouTube URLs, EPubs, audio (transcription), and more.
#
#   Install: pip install 'markitdown[all]'
#
# File: src/rag/text_extractors/markitdown/extractor.py
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


class MarkItDownExtractor:
    """Text extractor using Microsoft MarkItDown library.

    Converts files and URLs to Markdown text suitable for LLM/RAG pipelines.
    Preserves document structure: headings, lists, tables, links.

    Args:
        enable_plugins (bool): Enable third-party MarkItDown plugins. Default: False.
        llm_client (Any): Optional OpenAI-compatible client for image descriptions. Default: None.
        llm_model (str): Model name for LLM-based image descriptions. Default: None.
        docintel_endpoint (str): Azure Document Intelligence endpoint URL. Default: None.

    Example:
        >>> extractor = MarkItDownExtractor()
        >>> result = extractor.extract_from_file("document.pdf")
        >>> print(result["text"])
    """

    def __init__(
        self,
        enable_plugins: bool = False,
        llm_client: Any = None,
        llm_model: str | None = None,
        docintel_endpoint: str | None = None,
    ) -> None:
        self._enable_plugins = enable_plugins
        self._llm_client = llm_client
        self._llm_model = llm_model
        self._docintel_endpoint = docintel_endpoint
        self._md: Any = None

    def _get_client(self) -> Any:
        """Lazy-initialize MarkItDown client.

        Returns:
            MarkItDown: Initialized MarkItDown instance.

        Exceptions:
            ImportError: If markitdown package is not installed.
        """
        if self._md is None:
            try:
                from markitdown import MarkItDown
            except ImportError as e:
                raise ImportError(
                    "markitdown is not installed. Run: pip install 'markitdown[all]'"
                ) from e

            kwargs: dict[str, Any] = {"enable_plugins": self._enable_plugins}
            if self._llm_client:
                kwargs["llm_client"] = self._llm_client
                kwargs["llm_model"] = self._llm_model
            if self._docintel_endpoint:
                kwargs["docintel_endpoint"] = self._docintel_endpoint

            self._md = MarkItDown(**kwargs)
            logger.info("✅ MarkItDown client initialized")

        return self._md

    def extract_from_file(self, file_path: str | Path) -> dict[str, str]:
        """Extract text from a local file.

        Args:
            file_path (str | Path): Path to the file to convert.

        Returns:
            dict[str, str]: Dict with keys 'text' (Markdown content) and 'filename'.

        Exceptions:
            FileNotFoundError: If file_path does not exist.
            Exception: On conversion failure.

        Example:
            >>> extractor = MarkItDownExtractor()
            >>> result = extractor.extract_from_file("report.docx")
            >>> result["text"]
            '# Report Title'
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        md = self._get_client()
        result = md.convert_local(str(path))
        logger.info(f"✅ MarkItDown extracted: {path.name} ({len(result.text_content)} chars)")
        return {"text": result.text_content, "filename": path.name}

    def extract_from_bytes(self, content: bytes, filename: str) -> dict[str, str]:
        """Extract text from file bytes.

        Writes bytes to a temp file, converts, then cleans up.

        Args:
            content (bytes): Raw file bytes.
            filename (str): Original filename (used to determine format by extension).

        Returns:
            dict[str, str]: Dict with keys 'text' and 'filename'.

        Exceptions:
            Exception: On conversion failure.

        Example:
            >>> with open("doc.pdf", "rb") as f:
            ...     data = f.read()
            >>> result = extractor.extract_from_bytes(data, "doc.pdf")
        """
        suffix = Path(filename).suffix or ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            return self.extract_from_file(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

    def extract_from_url(self, url: str) -> dict[str, str]:
        """Extract text from a URL (web page, YouTube, remote file).

        Args:
            url (str): URL to fetch and convert.

        Returns:
            dict[str, str]: Dict with keys 'text' and 'url'.

        Exceptions:
            ValueError: If URL is empty.
            Exception: On fetch or conversion failure.

        Example:
            >>> result = extractor.extract_from_url("https://example.com/page")
            >>> result["text"]
            '# Page Title'
        """
        if not url:
            raise ValueError("URL must not be empty")

        md = self._get_client()
        result = md.convert(url)
        logger.info(f"✅ MarkItDown extracted URL: {url} ({len(result.text_content)} chars)")
        return {"text": result.text_content, "url": url}

    def extract_from_stream(self, stream: Any, filename: str) -> dict[str, str]:
        """Extract text from a file-like stream.

        Args:
            stream (Any): File-like object with a read() method.
            filename (str): Filename hint for format detection.

        Returns:
            dict[str, str]: Dict with keys 'text' and 'filename'.

        Exceptions:
            Exception: On conversion failure.

        Example:
            >>> with open("data.xlsx", "rb") as f:
            ...     result = extractor.extract_from_stream(f, "data.xlsx")
        """
        md = self._get_client()
        result = md.convert_stream(stream, file_extension=Path(filename).suffix)
        logger.info(f"✅ MarkItDown extracted stream: {filename} ({len(result.text_content)} chars)")
        return {"text": result.text_content, "filename": filename}
