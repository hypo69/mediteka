# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Utilities
# =============================================================================
# Description:
#   Shared utility functions for Foundry service interaction.
#
# File: src/utils/foundry_utils.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Changes in 0.6.0:
#   - MIT License update
#   - Unified headers and return type hints
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import os
import re
from pathlib import Path
import logging
from typing import Optional

from .process_utils import run_command

# Import requests only if available to avoid crashing during early startup checks
try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)

# Known ports often used by Foundry or local LLM proxies
_KNOWN_PORTS = [52632, 62171, 50477, 58130, 52987]

# Default Foundry port (fixed)
_DEFAULT_FOUNDRY_PORT = 63995

# Default cache location — reads from config.json (foundry_ai.models_dir) with env override
def _get_foundry_cache_dir() -> Path:
    env_override = os.getenv("FOUNDRY_CACHE_DIR", "")
    if env_override:
        return Path(env_override).expanduser()
    try:
        from config_manager import config as _cfg
        return Path(_cfg.foundry_models_dir)
    except Exception:
        return Path(os.path.expanduser("~/.foundry/cache/models"))

FOUNDRY_CACHE_DIR = _get_foundry_cache_dir()

def test_foundry_port(port: int) -> bool:
    """Check whether Foundry is responding on the given port.

    Args:
        port: TCP port to probe.

    Returns:
        bool: True if Foundry API responds with HTTP 200.
    """
    if requests is None:
        return False
    try:
        logger.debug(f'Probing port {port}...')
        resp = requests.get(f'http://127.0.0.1:{port}/v1/models', timeout=2)
        if resp.status_code == 200:
            return True
        logger.debug(f'Port {port}: HTTP {resp.status_code}')
        return False
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False
    except Exception as e:
        logger.warning(f'⚠️ Unexpected error probing port {port}: {e}')
        return False

def find_foundry_port() -> Optional[int]:
    """Locate the port of a running Foundry service.
    Order: 1. FOUNDRY_DYNAMIC_PORT env, 2. foundry service status output, 3. known ports, 4. default port 63995.

    Returns:
        int | None: Port number if found, None otherwise.
    """
    # 1. Check environment variable override
    raw_port = os.getenv('FOUNDRY_DYNAMIC_PORT')
    if raw_port and raw_port.isdigit() and test_foundry_port(int(raw_port)):
        return int(raw_port)

    # 2. Parse port from `foundry service status` output
    # Output contains: "running on http://127.0.0.1:PORT/..."
    try:
        result = run_command(['foundry', 'service', 'status'], timeout=10)
        output = (result.stdout or '') + (result.stderr or '')
        match = re.search(r'http://127\.0\.0\.1:(\d+)', output)
        if match:
            port = int(match.group(1))
            if test_foundry_port(port):
                logger.info(f'✅ Foundry found via status command on port {port}')
                return port
    except Exception as e:
        logger.debug(f'foundry service status failed: {e}')

    # 3. Last resort: scan known default ports
    for p in _KNOWN_PORTS:
        if test_foundry_port(p):
            return p

    # 4. Return default port (Foundry runs on fixed port 63995)
    if test_foundry_port(_DEFAULT_FOUNDRY_PORT):
        logger.info(f'✅ Foundry found on default port {_DEFAULT_FOUNDRY_PORT}')
        return _DEFAULT_FOUNDRY_PORT

    return None

def find_foundry_url() -> Optional[str]:
    """Return the base URL of a running Foundry service."""
    port = find_foundry_port()
    if port:
        return f'http://localhost:{port}/v1/'
    # If no port found, return default URL from config
    try:
        from config_manager import config
        return config.foundry_base_url or f'http://localhost:{_DEFAULT_FOUNDRY_PORT}/v1/'
    except Exception:
        return f'http://localhost:{_DEFAULT_FOUNDRY_PORT}/v1/'

def model_id_to_cache_dir(model_id: str) -> str:
    """Convert a Foundry model ID to its filesystem directory name.

    Foundry replaces ALL colons with dashes in the directory name.

    Examples:
        qwen3-0.6b-generic-cpu:4    -> qwen3-0.6b-generic-cpu-4
        qwen3-0.6b-generic-cpu:4:4  -> qwen3-0.6b-generic-cpu-4-4
        deepseek-r1-distill-qwen-14b-generic-cpu:4 -> deepseek-r1-distill-qwen-14b-generic-cpu-4
    """
    return model_id.replace(":", "-")


def _get_version_from_id(model_id: str) -> str:
    """Extract the last version segment from a model ID (after the last colon)."""
    if ":" in model_id:
        return model_id.rsplit(":", 1)[1]
    return ""


def is_foundry_model_cached(model_id: str) -> bool:
    """Check whether a model exists in the local Foundry cache directory.

    Foundry stores models under:
        <cache_dir>/Microsoft/<model_id_with_dashes>/v<version>/

    The cache root is resolved fresh each call so config changes take effect
    without restarting the server.
    """
    # Resolve cache dir fresh — avoids stale value from module-level init
    cache_dir = _get_foundry_cache_dir()

    # Foundry puts models inside a "Microsoft" subdirectory
    microsoft_dir = cache_dir / "Microsoft"
    if not microsoft_dir.exists():
        # Fallback: try the cache root itself (non-standard layout)
        microsoft_dir = cache_dir

    dir_name = model_id_to_cache_dir(model_id)
    model_dir = microsoft_dir / dir_name

    if not model_dir.exists():
        logger.debug(f"Cache miss: {model_dir} does not exist")
        return False

    # Verify version subfolder exists (v<last_segment>)
    version = _get_version_from_id(model_id)
    if version:
        version_dir = model_dir / f"v{version}"
        exists = version_dir.exists()
        logger.debug(f"Cache {'hit' if exists else 'miss'}: {version_dir}")
        return exists

    # No version in ID — presence of the directory is enough
    return True