# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Text Extractors — Package Init
# =============================================================================
# Description:
#   Aggregates all text extractor backends for the RAG pipeline.
#   Available backends:
#     - text_extractor_4_rag: multi-format extractor (40+ formats)
#     - markitdown: Microsoft MarkItDown extractor (Markdown-focused)
#
# File: src/rag/text_extractors/__init__.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Created as parent package for text extractor backends
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .text_extractor_4_rag import TextExtractor, settings
from .markitdown import MarkItDownExtractor
from .whisper import WhisperExtractor

__all__ = ["TextExtractor", "settings", "MarkItDownExtractor", "WhisperExtractor"]
