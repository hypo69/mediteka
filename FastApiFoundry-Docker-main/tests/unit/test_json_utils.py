# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: JSON Utils Unit Tests
# =============================================================================
# Description:
#   Validation of JSON parsing functions from src/utils/
#
# File: tests/unit/test_json_utils.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Moved to tests/unit/ (was scattered in scripts/ and root)
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import json
from src.utils.json import j_loads


class TestJsonUtils:
    """Unit tests for JSON parsing utilities."""

    def test_j_loads_valid(self):
        """Validation of correct JSON string."""
        result = j_loads('{"status": "ok"}')
        assert result["status"] == "ok"

    def test_j_loads_empty(self):
        """Validation of empty JSON object."""
        assert j_loads("{}") == {}

    def test_j_loads_error(self):
        """Validation of exception on malformed JSON."""
        with pytest.raises(json.JSONDecodeError):
            j_loads('{"status":')

    def test_unicode_support(self):
        """Validation of Cyrillic Unicode support."""
        result = j_loads('{"msg": "Тест"}')
        assert result["msg"] == "Тест"
