# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Logs API Endpoints
# =============================================================================
# Description:
#   REST endpoints for the log viewer tab.
#   Supports file selection, level filtering, text search, pagination.
#
# File: logs.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ...logger import configure_logging, get_log_settings

router = APIRouter()
logger = logging.getLogger(__name__)

_LOG_PREFIX = 'aiassistant'


class LogSettingsRequest(BaseModel):
    max_lines_per_file: int = Field(default=5000, ge=100, le=200000)
    retention_days: int = Field(default=7, ge=1, le=365)
    level: str = Field(default='WARNING')


def _log_dir() -> Path:
    return Path(get_log_settings()['log_dir']).expanduser().resolve()


def _resolve_file(filename: str) -> Path:
    """Return validated path inside the configured log directory or raise 404."""
    root = _log_dir()
    path = (root / Path(filename).name).resolve()
    if root not in path.parents and path != root:
        raise HTTPException(status_code=400, detail='Invalid file path')
    if not path.exists():
        raise HTTPException(status_code=404, detail=f'File not found: {filename}')
    return path


def _list_files() -> list[Path]:
    root = _log_dir()
    root.mkdir(parents=True, exist_ok=True)
    return sorted(
        root.glob(f'{_LOG_PREFIX}-*.log'),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


@router.get('/logs/files')
async def list_log_files() -> dict[str, Any]:
    """Return available log files with size info."""
    files = []
    for p in _list_files():
        files.append({
            'name': p.name,
            'size': p.stat().st_size,
            'size_kb': round(p.stat().st_size / 1024, 1),
            'modified': p.stat().st_mtime,
        })
    return {'success': True, 'files': files, 'log_dir': str(_log_dir())}


@router.get('/logs/settings')
async def get_logs_settings() -> dict[str, Any]:
    """Return log storage and retention settings."""
    return {'success': True, 'settings': get_log_settings()}


@router.get('/logs/health')
async def get_logs_health() -> dict[str, Any]:
    """Return simple warning/error metrics for the settings page."""
    errors_count = 0
    warnings_count = 0
    api_requests = 0
    durations = []

    for path in _list_files():
        try:
            with path.open(encoding='utf-8', errors='replace') as handle:
                for line in handle:
                    if ' ERROR ' in line or '| ERROR' in line or ' CRITICAL ' in line or '| CRITICAL' in line:
                        errors_count += 1
                    elif ' WARNING ' in line or '| WARNING' in line:
                        warnings_count += 1
                    if 'HTTP ' in line and ' -> ' in line:
                        api_requests += 1
                        marker = line.rsplit('(', 1)[-1].split('s)', 1)[0]
                        try:
                            durations.append(float(marker))
                        except ValueError:
                            pass
        except OSError as e:
            logger.warning('Could not read log health from %s: %s', path.name, e)

    status = 'healthy'
    if errors_count:
        status = 'critical'
    elif warnings_count:
        status = 'warning'

    return {
        'success': True,
        'status': status,
        'metrics': {
            'errors_count': errors_count,
            'warnings_count': warnings_count,
            'api_requests': api_requests,
            'avg_response_time': round(sum(durations) / len(durations), 3) if durations else 0,
        },
    }


@router.post('/logs/settings')
async def save_logs_settings(request: LogSettingsRequest) -> dict[str, Any]:
    """Persist log viewer retention settings to config.json and apply them."""
    config_path = Path('config.json')
    try:
        raw = {}
        if config_path.exists():
            raw = json.loads(config_path.read_text(encoding='utf-8'))
        logging_cfg = raw.setdefault('logging', {})
        logging_cfg['log_dir'] = get_log_settings()['log_dir']
        logging_cfg['level'] = request.level.upper()
        logging_cfg['max_lines_per_file'] = request.max_lines_per_file
        logging_cfg['retention_days'] = request.retention_days
        config_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding='utf-8')
        configure_logging(request.level)
        logger.warning(
            'Log settings updated: max_lines_per_file=%s retention_days=%s',
            request.max_lines_per_file,
            request.retention_days,
        )
        return {'success': True, 'settings': get_log_settings()}
    except Exception as e:
        logger.error(f'Error saving log settings: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/logs')
async def get_logs(
    file: str = Query(default='', description='Log file name'),
    lines: int = Query(default=200, ge=1, le=5000, description='Max lines to return'),
    level: str = Query(default='', description='Filter by level: DEBUG|INFO|WARNING|ERROR'),
    search: str = Query(default='', description='Text search (case-insensitive)'),
    offset: int = Query(default=0, ge=0, description='Skip last N lines (pagination)'),
) -> dict[str, Any]:
    """Return filtered log lines from the requested file."""
    if not isinstance(file, str):
        file = ''
    if not file:
        files = _list_files()
        if not files:
            return {
                'success': True,
                'file': '',
                'lines': [],
                'returned': 0,
                'filtered_total': 0,
                'total_lines': 0,
                'has_more': False,
            }
        file = files[0].name
    path = _resolve_file(file)

    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            all_lines = [l.rstrip('\r\n') for l in f if l.strip()]
    except Exception as e:
        logger.error(f'Error reading {path}: {e}')
        raise HTTPException(status_code=500, detail=str(e))

    total = len(all_lines)

    # Apply filters
    filtered = all_lines
    if level:
        filtered = [l for l in filtered if f'| {level.upper()}' in l or f' {level.upper()} ' in l]
    if search:
        needle = search.lower()
        filtered = [l for l in filtered if needle in l.lower()]

    # Newest-first pagination: take from the tail
    filtered_total = len(filtered)
    start = max(0, filtered_total - lines - offset)
    end   = max(0, filtered_total - offset)
    page  = filtered[start:end]

    return {
        'success': True,
        'file': file,
        'lines': page,
        'returned': len(page),
        'filtered_total': filtered_total,
        'total_lines': total,
        'has_more': start > 0,
    }


@router.post('/logs/clear')
async def clear_log(
    file: str = Query(default=''),
) -> dict[str, Any]:
    """Truncate a log file."""
    if not file:
        raise HTTPException(status_code=400, detail='File is required')
    path = _resolve_file(file)
    try:
        path.write_text('', encoding='utf-8')
        logger.info(f'Log file cleared: {file}')
        return {'success': True, 'message': f'{file} cleared'}
    except Exception as e:
        logger.error(f'Error clearing {file}: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/logs/download')
async def download_log(
    file: str = Query(default=''),
) -> FileResponse:
    """Download a log file."""
    if not file:
        raise HTTPException(status_code=400, detail='File is required')
    path = _resolve_file(file)
    return FileResponse(path=str(path), filename=file, media_type='text/plain')
