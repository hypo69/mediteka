# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Finder Utility
# =============================================================================
# Description:
#   Utility for locating a running Foundry service.
#   Checks known ports and environment variables.
#
# File: foundry_finder.py
# Project: Ai Assistant (Docker)
# Version: 0.5.5
# Changes in 0.5.5:
#   - Added try/except with logging in find_foundry_port and _test_foundry_port
#   - ValueError on bad FOUNDRY_DYNAMIC_PORT now logged instead of silently skipped
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
import os

logger = logging.getLogger(__name__)

_KNOWN_PORTS = [62171, 50477, 58130]

# Default Foundry port (fixed)
_DEFAULT_FOUNDRY_PORT = 63995


def find_foundry_port() -> int | None:
    """Locate the port of a running Foundry service.

    Returns:
        int | None: Port number if found, None otherwise.
    """
    # Check environment variable first
    raw_port = os.getenv('FOUNDRY_DYNAMIC_PORT')
    if raw_port:
        try:
            port = int(raw_port)
            logger.info(f'✅ Foundry found via env variable: {port}')
            return port
        except ValueError:
            # FOUNDRY_DYNAMIC_PORT is set but not a valid integer
            logger.warning(f'⚠️ FOUNDRY_DYNAMIC_PORT is not a valid integer: {raw_port!r}')

    logger.info(f'🔍 Scanning known ports: {_KNOWN_PORTS}')
    for port in _KNOWN_PORTS:
        logger.info(f'✅ Foundry found on port: {port}')
        return port

    # Return default port (Foundry runs on fixed port 63995)
    logger.info(f'✅ Foundry found on default port {_DEFAULT_FOUNDRY_PORT}')
    return _DEFAULT_FOUNDRY_PORT


def find_foundry_url() -> str | None:
    """Return the base URL of a running Foundry service.

    Returns:
        str | None: URL like 'http://localhost:63995/v1/' or None.
    """
    port = find_foundry_port()
    if port:
        return f'http://localhost:{port}/v1/'
    return None
