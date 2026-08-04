# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Logging Subsystem for FastAPI Foundry
# =============================================================================
# Description:
#   Cross-platform logging with rotating file handlers and structured JSONL.
#   Console + plain rotating log + errors-only log + structured JSONL.
#
# Examples:
#   >>> from src.logger import logger
#   >>> logger.info("✅ Server started")
#   >>> logger.error("❌ Connection failed", exc_info=True)
#
# File: __init__.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
import os
import sys
from datetime import date
from pathlib import Path


DEFAULT_LOG_DIR = Path('~/.ai-assist/logs').expanduser()
DEFAULT_MAX_LINES_PER_FILE = 5000
DEFAULT_RETENTION_DAYS = 7
DEFAULT_LEVEL = 'WARNING'


class DailyLineRotatingFileHandler(logging.Handler):
    """Write warning/error logs to daily files with a line limit."""

    def __init__(
        self,
        log_dir: Path,
        prefix: str = 'aiassistant',
        max_lines: int = DEFAULT_MAX_LINES_PER_FILE,
        retention_days: int = DEFAULT_RETENTION_DAYS,
        encoding: str = 'utf-8',
    ) -> None:
        super().__init__()
        self.log_dir = Path(log_dir).expanduser()
        self.prefix = prefix
        self.max_lines = max(1, int(max_lines or DEFAULT_MAX_LINES_PER_FILE))
        self.retention_days = max(1, int(retention_days or DEFAULT_RETENTION_DAYS))
        self.encoding = encoding
        self._current_date = ''
        self._current_index = 1
        self._current_lines = 0
        self._stream = None
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._open_for_today()
        self._cleanup_old_files()

    def _file_name(self, day: str, index: int) -> str:
        return f'{self.prefix}-{day}-{index:03d}.log'

    def _parse_file_date(self, path: Path) -> date | None:
        stem = path.stem
        parts = stem.split('-')
        if len(parts) < 5:
            return None
        try:
            return date.fromisoformat('-'.join(parts[1:4]))
        except ValueError:
            return None

    def _cleanup_old_files(self) -> None:
        today = date.today()
        for path in self.log_dir.glob(f'{self.prefix}-*.log'):
            file_date = self._parse_file_date(path)
            if file_date and (today - file_date).days >= self.retention_days:
                try:
                    path.unlink()
                except OSError:
                    pass

    def _line_count(self, path: Path) -> int:
        if not path.exists():
            return 0
        try:
            with path.open('r', encoding=self.encoding, errors='replace') as handle:
                return sum(1 for _ in handle)
        except OSError:
            return 0

    def _open_for_today(self) -> None:
        day = date.today().isoformat()
        candidates = sorted(self.log_dir.glob(f'{self.prefix}-{day}-*.log'))
        index = 1
        lines = 0
        if candidates:
            last = candidates[-1]
            try:
                index = int(last.stem.rsplit('-', 1)[-1])
            except ValueError:
                index = len(candidates)
            lines = self._line_count(last)
            if lines >= self.max_lines:
                index += 1
                lines = 0

        self._current_date = day
        self._current_index = index
        self._current_lines = lines
        if self._stream:
            self._stream.close()
        self._stream = (self.log_dir / self._file_name(day, index)).open(
            'a',
            encoding=self.encoding,
            errors='replace',
        )

    def _should_rotate(self) -> bool:
        return self._current_date != date.today().isoformat() or self._current_lines >= self.max_lines

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if self._should_rotate():
                if self._current_date != date.today().isoformat():
                    self._cleanup_old_files()
                    self._open_for_today()
                else:
                    self._current_index += 1
                    self._current_lines = 0
                    if self._stream:
                        self._stream.close()
                    self._stream = (
                        self.log_dir / self._file_name(self._current_date, self._current_index)
                    ).open('a', encoding=self.encoding, errors='replace')

            line = self.format(record)
            self._stream.write(line + '\n')
            self._stream.flush()
            self._current_lines += 1
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        if self._stream:
            self._stream.close()
            self._stream = None
        super().close()


def _read_logging_config() -> dict:
    try:
        path = Path('config.json')
        if path.exists():
            data = json.loads(path.read_text(encoding='utf-8'))
            return data.get('logging', {}) if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def get_log_settings() -> dict:
    cfg = _read_logging_config()
    return {
        'log_dir': cfg.get('log_dir') or os.getenv('AIASSISTANT_LOG_DIR') or str(DEFAULT_LOG_DIR),
        'level': cfg.get('level') or os.getenv('LOG_LEVEL') or DEFAULT_LEVEL,
        'max_lines_per_file': int(cfg.get('max_lines_per_file') or DEFAULT_MAX_LINES_PER_FILE),
        'retention_days': int(cfg.get('retention_days') or cfg.get('backup_count') or DEFAULT_RETENTION_DAYS),
    }


def configure_logging(log_level: str | None = None) -> None:
    settings = get_log_settings()
    level_name = (log_level or settings['level'] or DEFAULT_LEVEL).upper()
    level = getattr(logging, level_name, logging.WARNING)

    fmt_console = logging.Formatter(
        '%(asctime)s | %(levelname)-7s | %(name)-25s | %(message)s',
        datefmt='%H:%M:%S',
    )
    fmt_file = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-24s | %(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    root = logging.getLogger()
    for handler in list(root.handlers):
        if getattr(handler, '_aiassistant_managed', False):
            root.removeHandler(handler)
            handler.close()

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(fmt_console)
    console._aiassistant_managed = True
    root.addHandler(console)

    file_handler = DailyLineRotatingFileHandler(
        Path(settings['log_dir']),
        max_lines=settings['max_lines_per_file'],
        retention_days=settings['retention_days'],
    )
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(fmt_file)
    file_handler._aiassistant_managed = True
    root.addHandler(file_handler)

    root.setLevel(logging.DEBUG)

    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    uvicorn_error = logging.getLogger('uvicorn.error')
    uvicorn_error.setLevel(logging.WARNING)
    uvicorn_error.propagate = True


def _build_logger(name: str = 'fastapi-foundry') -> logging.Logger:
    """Build and configure the application logger.

    Args:
        name (str): Root logger name.

    Returns:
        logging.Logger: Configured logger instance.
    """
    configure_logging()
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    return log


logger: logging.Logger = _build_logger()


def get_logger(name: str) -> logging.Logger:
    """Return a child logger sharing the root handler chain.

    Args:
        name (str): Logger name (typically module __name__).

    Returns:
        logging.Logger: Configured logger instance.

    Example:
        >>> log = get_logger(__name__)
        >>> log.info("Module ready")
    """
    return logging.getLogger(name)
