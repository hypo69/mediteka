# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Text Utilities
# =============================================================================
# Description:
#   Shared text processing and model-related metrics.
#
# File: src/utils/text_utils.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Changes in 0.6.0:
#   - MIT License update
#   - Unified headers
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

def count_tokens_approx(text: str) -> int:
    """Approximate token count: ~4 chars per token.

    Args:
        text: Input string.

    Returns:
        int: Estimated token count (minimum 1).
    """
    return max(1, len(text) // 4)

def sanitize_for_filesystem(name: str) -> str:
    """Convert an arbitrary string to a safe directory or filename.
    Removes non-alphanumeric characters except hyphens and underscores.

    Args:
        name: Input string.
    Returns:
        str: Sanitized string.
    """
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name.strip())