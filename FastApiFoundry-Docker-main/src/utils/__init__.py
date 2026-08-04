# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Utils Module Initialization
# =============================================================================
# Description:
#   Utilities module initialization for FastAPI Foundry.
#   Exports config helpers and the Translator utility.
#
# File: src/utils/__init__.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .env_processor import process_config, load_env_variables, validate_config
from .translator import Translator, translator

__all__ = [
    'process_config',
    'load_env_variables',
    'validate_config',
    'Translator',
    'translator',
]