# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Text Extractor for RAG — Package Init
# =============================================================================
# Description:
#   Exports the main TextExtractor class and Settings for use in the RAG pipeline.
#
# File: src/rag/text_extractor_4_rag/__init__.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .config import settings
from .extractors import TextExtractor

__all__ = ["TextExtractor", "settings"]
