# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Logging Configuration Bootstrap
# =============================================================================
# Description:
#   Thin bootstrap that applies log level and suppresses noisy libraries.
#   All handler setup lives in src/logger/__init__.py.
#
# File: logging_config.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging

from src.logger import configure_logging


def setup_logging(log_level: str = 'INFO') -> None:
    """Apply log level to the root logger and suppress noisy libraries.

    Args:
        log_level (str): Logging level name (DEBUG, INFO, WARNING, ERROR).

    Example:
        >>> setup_logging('DEBUG')
    """
    configure_logging(log_level)
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.getLogger('fastapi-foundry').setLevel(level)

    # Suppress noisy third-party loggers
    for noisy in ('watchfiles', 'watchfiles.main', 'uvicorn.access'):
        logging.getLogger(noisy).setLevel(logging.WARNING)
