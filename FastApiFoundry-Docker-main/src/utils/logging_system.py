# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Structured Logger Facade
# =============================================================================
# Description:
#   Thin facade over stdlib logging that adds structured JSON emission
#   and a timer context manager. All handler wiring is in src/logger/__init__.py.
#
# File: logging_system.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
import time
from contextlib import contextmanager
from typing import Optional

from ..logger import get_logger as _get_logger


class StructuredLogger:
    """Facade that adds structured JSON side-channel to a stdlib logger.

    Args:
        name (str): Logger name.

    Example:
        >>> log = StructuredLogger('my-module')
        >>> log.info("Request handled", status=200, duration=0.12)
    """

    def __init__(self, name: str) -> None:
        self._log = _get_logger(name)

    # ------------------------------------------------------------------
    # Standard levels — pass kwargs as JSON extra to the message
    # ------------------------------------------------------------------

    def _emit(self, level: int, message: str, **kwargs) -> None:
        if kwargs:
            extra_str = ' | ' + json.dumps(kwargs, ensure_ascii=False, default=str)
            self._log.log(level, message + extra_str)
        else:
            self._log.log(level, message)

    def debug(self, message: str, **kwargs) -> None:
        self._emit(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self._emit(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self._emit(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info=None, **kwargs) -> None:
        if kwargs:
            extra_str = ' | ' + json.dumps(kwargs, ensure_ascii=False, default=str)
            self._log.error(message + extra_str, exc_info=exc_info)
        else:
            self._log.error(message, exc_info=exc_info)

    def critical(self, message: str, **kwargs) -> None:
        self._emit(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs) -> None:
        if kwargs:
            extra_str = ' | ' + json.dumps(kwargs, ensure_ascii=False, default=str)
            self._log.exception(message + extra_str)
        else:
            self._log.exception(message)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @contextmanager
    def timer(self, operation: str, **kwargs):
        """Context manager that logs operation duration.

        Args:
            operation (str): Human-readable operation name.

        Example:
            >>> with log.timer('rag-search'):
            ...     results = rag.search(query)
        """
        start = time.time()
        try:
            yield
            self.info(f'✅ {operation}', duration=round(time.time() - start, 3), **kwargs)
        except Exception as exc:
            self.error(f'❌ {operation}', duration=round(time.time() - start, 3),
                       error=str(exc), exc_info=True, **kwargs)
            raise

    def log_api_request(self, method: str, path: str, status_code: int,
                        duration: float, **kwargs) -> None:
        """Log an HTTP API request.

        Args:
            method (str): HTTP method.
            path (str): Request path.
            status_code (int): Response status code.
            duration (float): Processing time in seconds.
        """
        self.info(
            f'API {method} {path} → {status_code} ({duration:.3f}s)',
            api_method=method, api_path=path,
            status_code=status_code, duration=duration,
            **kwargs,
        )

    def log_model_operation(self, model_id: str, operation: str,
                            status: str, duration: Optional[float] = None,
                            **kwargs) -> None:
        """Log a model lifecycle operation.

        Args:
            model_id (str): Model identifier.
            operation (str): Operation name (load, unload, generate).
            status (str): 'success' or 'error'.
            duration (float, optional): Duration in seconds.
        """
        msg = f'Model {operation}: {model_id} → {status}'
        if duration is not None:
            msg += f' ({duration:.3f}s)'
        level = logging.INFO if status == 'success' else logging.ERROR
        self._emit(level, msg, model_id=model_id, operation=operation,
                   status=status, duration=duration, **kwargs)


# ---------------------------------------------------------------------------
# Module-level singletons (backward compat)
# ---------------------------------------------------------------------------

def get_logger(name: str) -> StructuredLogger:
    """Return a StructuredLogger for the given name.

    Args:
        name (str): Logger name.

    Returns:
        StructuredLogger: Configured structured logger.

    Example:
        >>> log = get_logger('rag-system')
        >>> log.info("Index loaded", chunks=512)
    """
    return StructuredLogger(name)


logger = get_logger('fastapi-foundry')

debug    = logger.debug
info     = logger.info
warning  = logger.warning
error    = logger.error
critical = logger.critical
exception = logger.exception
