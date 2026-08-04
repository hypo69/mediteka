# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Process Utilities
# =============================================================================
# Description:
#   Shared utility functions for consistent subprocess execution.
#   Handles encoding, error replacement, and output capturing.
#
# File: src/utils/process_utils.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Changes in 0.6.0:
#   - MIT License update
#   - Unified headers
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import subprocess
import logging
from typing import List, Any, Dict

logger = logging.getLogger(__name__)

# Standard keyword arguments for subprocess text-based operations
DEFAULT_SUBPROCESS_KWARGS: Dict[str, Any] = {
    "text": True,
    "encoding": "utf-8",
    "errors": "replace",
}

def run_command(args: List[str], timeout: int = 30, shell: bool = False, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a command via subprocess.run with project-standard defaults.

    Args:
        args: List of command arguments.
        timeout: Execution timeout in seconds.
        shell: Whether to use the shell.
        capture_output: Whether to capture stdout and stderr.

    Returns:
        subprocess.CompletedProcess: The result of the command execution.
    """
    try:
        logger.debug(f"Executing command: {' '.join(args)}")
        return subprocess.run(
            args,
            capture_output=capture_output,
            shell=shell,
            timeout=timeout,
            **DEFAULT_SUBPROCESS_KWARGS
        )
    except subprocess.TimeoutExpired as e:
        logger.error(f"❌ Command timed out ({timeout}s): {' '.join(args)}")
        raise
    except Exception as e:
        logger.error(f"❌ Error executing command {' '.join(args)}: {e}")
        raise