# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Text Extractor for RAG — Configuration
# =============================================================================
# Description:
#   Settings for the text extraction module.
#   Reads the `text_extractor` section from the project-wide Config singleton
#   (config_manager.py → config.json).  Individual values can still be
#   overridden by environment variables (highest priority).
#
#   Priority: env var > config.json [text_extractor] > built-in default
#
# File: src/rag/text_extractors/text_extractor_4_rag/config.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Moved to src/rag/text_extractors/text_extractor_4_rag/
#   - All settings now fully sourced from config.json text_extractor section
#   - Added config.json keys: max_archive_nesting, max_extracted_size_mb,
#     max_libreoffice_memory_mb, max_tesseract_memory_mb
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
from typing import Any, List

from config_manager import config as _project_config


def _cfg(key: str, default: Any = None) -> Any:
    """Return a value from config.json → text_extractor section."""
    return _project_config.get_section("text_extractor").get(key, default)


def _env_int(key: str, fallback: int) -> int:
    raw = os.getenv(key)
    return int(raw) if raw is not None else fallback


def _env_bool(key: str, fallback: bool) -> bool:
    raw = os.getenv(key)
    return raw.lower() == "true" if raw is not None else fallback


def _env_str(key: str, fallback: str) -> str:
    return os.getenv(key, fallback)


class Settings:
    """Text extractor settings resolved from the project Config singleton.

    Resolution order (highest wins):
      1. Environment variable
      2. config.json → ``text_extractor`` section  (via Config singleton)
      3. Built-in default
    """

    def __init__(self) -> None:
        self.VERSION: str = "1.10.8"

        # ── File processing ────────────────────────────────────────────────
        _max_mb: int = _cfg("max_file_size_mb", 20)
        self.MAX_FILE_SIZE: int = _env_int("MAX_FILE_SIZE", _max_mb * 1024 * 1024)
        self.PROCESSING_TIMEOUT_SECONDS: int = _env_int(
            "PROCESSING_TIMEOUT_SECONDS", _cfg("processing_timeout_seconds", 300)
        )

        # ── OCR ────────────────────────────────────────────────────────────
        self.OCR_LANGUAGES: str = _env_str("OCR_LANGUAGES", _cfg("ocr_languages", "rus+eng"))
        self.TESSERACT_CMD: str = _cfg("tesseract_cmd", "")

        # ── Web extractor ──────────────────────────────────────────────────
        self.ENABLE_JAVASCRIPT: bool = _env_bool("ENABLE_JAVASCRIPT", _cfg("enable_javascript", False))
        self.MAX_IMAGES_PER_PAGE: int = _env_int("MAX_IMAGES_PER_PAGE", _cfg("max_images_per_page", 20))
        self.WEB_PAGE_TIMEOUT: int = _env_int("WEB_PAGE_TIMEOUT", _cfg("web_page_timeout", 30))

        # ── Resource limits ────────────────────────────────────────────────
        self.ENABLE_RESOURCE_LIMITS: bool = _env_bool(
            "ENABLE_RESOURCE_LIMITS", _cfg("enable_resource_limits", True)
        )
        self.MAX_SUBPROCESS_MEMORY: int = _env_int("MAX_SUBPROCESS_MEMORY", 1024 * 1024 * 1024)
        _lo_mb: int = _cfg("max_libreoffice_memory_mb", 1536)
        self.MAX_LIBREOFFICE_MEMORY: int = _env_int("MAX_LIBREOFFICE_MEMORY", _lo_mb * 1024 * 1024)
        _tess_mb: int = _cfg("max_tesseract_memory_mb", 512)
        self.MAX_TESSERACT_MEMORY: int = _env_int("MAX_TESSERACT_MEMORY", _tess_mb * 1024 * 1024)
        self.MAX_OCR_IMAGE_PIXELS: int = _env_int("MAX_OCR_IMAGE_PIXELS", 50 * 1024 * 1024)

        # ── Archive limits ─────────────────────────────────────────────────
        self.MAX_ARCHIVE_SIZE: int = _env_int("MAX_ARCHIVE_SIZE", 20 * 1024 * 1024)
        _extracted_mb: int = _cfg("max_extracted_size_mb", 100)
        self.MAX_EXTRACTED_SIZE: int = _env_int("MAX_EXTRACTED_SIZE", _extracted_mb * 1024 * 1024)
        self.MAX_ARCHIVE_NESTING: int = _env_int("MAX_ARCHIVE_NESTING", _cfg("max_archive_nesting", 3))

        # ── JS rendering (advanced) ────────────────────────────────────────
        self.ENABLE_BASE64_IMAGES: bool = _env_bool("ENABLE_BASE64_IMAGES", True)
        self.WEB_PAGE_DELAY: int = _env_int("WEB_PAGE_DELAY", 3)
        self.ENABLE_LAZY_LOADING_WAIT: bool = _env_bool("ENABLE_LAZY_LOADING_WAIT", True)
        self.JS_RENDER_TIMEOUT: int = _env_int("JS_RENDER_TIMEOUT", 10)
        self.MAX_SCROLL_ATTEMPTS: int = _env_int("MAX_SCROLL_ATTEMPTS", 3)
        self.MIN_IMAGE_SIZE_FOR_OCR: int = _env_int("MIN_IMAGE_SIZE_FOR_OCR", 22500)
        self.IMAGE_DOWNLOAD_TIMEOUT: int = _env_int("IMAGE_DOWNLOAD_TIMEOUT", 15)
        self.HEAD_REQUEST_TIMEOUT: int = _env_int("HEAD_REQUEST_TIMEOUT", 10)
        self.FILE_DOWNLOAD_TIMEOUT: int = _env_int("FILE_DOWNLOAD_TIMEOUT", 60)
        self.DEFAULT_USER_AGENT: str = _env_str("DEFAULT_USER_AGENT", "Text Extraction Bot 1.0")

        # ── SSRF protection ────────────────────────────────────────────────
        self.BLOCKED_IP_RANGES: str = _env_str(
            "BLOCKED_IP_RANGES",
            "127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,"
            "169.254.0.0/16,::1/128,fe80::/10",
        )
        self.BLOCKED_HOSTNAMES: str = _env_str(
            "BLOCKED_HOSTNAMES",
            "localhost,host.docker.internal,ip6-localhost,ip6-loopback",
        )

        # ── Workers ────────────────────────────────────────────────────────
        self.WORKERS: int = _env_int("WORKERS", 1)
        self.API_PORT: int = _env_int("API_PORT", 7555)
        self.DEBUG: bool = _env_bool("DEBUG", _project_config.get_section("development").get("debug", False))

        # ── Supported formats (static) ─────────────────────────────────────
        self.SUPPORTED_FORMATS = {
            "images_ocr": ["jpg", "jpeg", "png", "tiff", "tif", "bmp", "gif", "webp"],
            "documents": ["doc", "docx", "pdf", "rtf", "odt"],
            "spreadsheets": ["csv", "xls", "xlsx", "ods"],
            "presentations": ["pptx", "ppt"],
            "structured_data": ["json", "xml", "yaml", "yml"],
            "source_code": [
                "py", "pyx", "pyi", "pyw",
                "js", "jsx", "ts", "tsx", "mjs", "cjs",
                "java", "jav",
                "c", "cpp", "cxx", "cc", "c++", "h", "hpp", "hxx", "h++",
                "cs", "csx",
                "php", "php3", "php4", "php5", "phtml",
                "rb", "rbw", "rake", "gemspec",
                "go", "mod", "sum",
                "rs", "rlib",
                "swift",
                "kt", "kts",
                "scala", "sc",
                "r", "rmd",
                "sql", "ddl", "dml",
                "sh", "bash", "zsh", "fish", "ksh", "csh", "tcsh",
                "ps1", "psm1", "psd1",
                "pl", "pm", "pod", "t",
                "lua",
                "bsl", "os",
                "ini", "cfg", "conf", "config", "toml", "properties",
                "css", "scss", "sass", "less", "styl",
                "tex", "latex", "rst", "adoc", "asciidoc",
                "jsonl", "ndjson", "jsonc",
                "dockerfile", "containerfile",
                "makefile", "mk", "mak",
                "gitignore", "gitattributes", "gitmodules",
            ],
            "other": ["txt", "html", "htm", "md", "markdown", "epub", "eml", "msg"],
            "archives": [
                "zip", "rar", "7z", "tar", "gz", "bz2", "xz",
                "tgz", "tbz2", "txz", "tar.gz", "tar.bz2", "tar.xz",
            ],
        }

        self.MIME_TO_EXTENSION = {
            "application/pdf": "pdf",
            "application/msword": "doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "application/vnd.ms-excel": "xls",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
            "application/vnd.ms-powerpoint": "ppt",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
            "application/zip": "zip",
            "application/x-rar-compressed": "rar",
            "application/x-7z-compressed": "7z",
            "application/x-tar": "tar",
            "application/gzip": "gz",
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/gif": "gif",
            "image/bmp": "bmp",
            "image/tiff": "tiff",
            "text/plain": "txt",
            "text/html": "html",
            "text/csv": "csv",
            "application/json": "json",
            "application/xml": "xml",
            "text/xml": "xml",
        }

    @property
    def all_supported_extensions(self) -> List[str]:
        """All supported file extensions as a flat list."""
        extensions = []
        for group in self.SUPPORTED_FORMATS.values():
            extensions.extend(group)
        return extensions


# Lazy singleton: re-reads config.json values on each access via _project_config.
# Since _project_config is itself a singleton that can be reloaded, Settings
# must NOT be frozen at import time. We keep a module-level instance but
# expose a reload() helper so callers can refresh after config.reload_config().
_settings_instance: "Settings | None" = None


def _get_settings() -> "Settings":
    """Return the module-level Settings instance, creating it on first call."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


class _SettingsProxy:
    """Proxy that forwards attribute access to the Settings singleton.

    Allows callers to write ``settings.MAX_FILE_SIZE`` while still
    supporting ``settings.reload()`` after ``config.reload_config()``.
    """

    def __getattr__(self, name: str) -> Any:
        return getattr(_get_settings(), name)

    def reload(self) -> None:
        """Re-create the Settings instance from the current config.json values."""
        global _settings_instance
        _settings_instance = Settings()


settings: Any = _SettingsProxy()
