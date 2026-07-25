# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Router for API Key Management
# =============================================================================
# Description:
#   CRUD operations for Gemini API keys stored in src/secrets/gemini_keys.json.
#   Supports: list, add, remove, toggle status, get status.
#
# File: router_keys.py
# Project: ai-mediteka
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.logger import logger

router = APIRouter(prefix='/api/keys', tags=['keys'])

_KEYS_FILE = Path(__file__).parent.parent / 'secrets' / 'gemini_keys.json'
_DAY_SECONDS = 86400


# ============================================================================
# Pydantic Models
# ============================================================================

class KeyEntry(BaseModel):
    api_key: str
    status: str = 'active'
    last_run: Optional[str] = None
    exhausted_at: Optional[str] = None


class KeyCreateRequest(BaseModel):
    name: str
    api_key: str
    status: str = 'active'


class KeyUpdateRequest(BaseModel):
    status: Optional[str] = None
    name: Optional[str] = None


class KeyListResponse(BaseModel):
    keys: List[Dict]
    total: int


class KeyStatusResponse(BaseModel):
    name: str
    status: str
    last_run: Optional[str]
    exhausted_at: Optional[str]
    exhausted: bool
    reset_in_seconds: Optional[int]


# ============================================================================
# Internal Helper Functions
# ============================================================================

def _load_keys() -> Dict:
    """Load all keys from JSON file."""
    if _KEYS_FILE.exists():
        try:
            return json.loads(_KEYS_FILE.read_text(encoding='utf-8'))
        except Exception as ex:
            logger.error('Failed to load keys file', ex)
            raise HTTPException(status_code=500, detail='Failed to load keys file')
    return {}


def _save_keys(data: Dict) -> None:
    """Save keys to JSON file."""
    try:
        _KEYS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception as ex:
        logger.error('Failed to save keys file', ex)
        raise HTTPException(status_code=500, detail='Failed to save keys file')


def _now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _iso_to_ts(iso: str) -> float:
    """Convert ISO string to timestamp."""
    try:
        return datetime.fromisoformat(iso).timestamp()
    except Exception:
        return 0.0


def _check_exhaustion(entry: Dict) -> tuple[bool, Optional[int]]:
    """Check if key is exhausted and return seconds until reset."""
    exhausted_at = entry.get('exhausted_at')
    if not exhausted_at:
        return False, None
    
    elapsed = _now_ts() - _iso_to_ts(exhausted_at)
    remaining = _DAY_SECONDS - elapsed
    
    if remaining > 0:
        return True, int(remaining)
    return False, None


def _now_ts() -> float:
    """Return current Unix timestamp."""
    return datetime.now(timezone.utc).timestamp()


def _mask_key(api_key: str) -> str:
    """Mask API key for display: keep first 8 and last 4 chars."""
    if len(api_key) < 12:
        return '*' * len(api_key)
    return f"{api_key[:8]}...{api_key[-4:]}"


# ============================================================================
# API Endpoints
# ============================================================================

@router.get('', response_model=KeyListResponse)
async def list_keys() -> KeyListResponse:
    """List all API keys with masked values and status."""
    data = _load_keys()
    keys = []
    
    for name, entry in data.items():
        exhausted, reset_in = _check_exhaustion(entry)
        keys.append({
            'name': name,
            'api_key_masked': _mask_key(entry.get('api_key', '')),
            'status': entry.get('status', 'unknown'),
            'last_run': entry.get('last_run'),
            'exhausted_at': entry.get('exhausted_at'),
            'exhausted': exhausted,
            'reset_in_seconds': reset_in
        })
    
    return KeyListResponse(keys=keys, total=len(keys))


@router.get('/{key_name}', response_model=KeyStatusResponse)
async def get_key_status(key_name: str) -> KeyStatusResponse:
    """Get detailed status for a specific key."""
    data = _load_keys()
    
    if key_name not in data:
        raise HTTPException(status_code=404, detail=f'Key "{key_name}" not found')
    
    entry = data[key_name]
    exhausted, reset_in = _check_exhaustion(entry)
    
    return KeyStatusResponse(
        name=key_name,
        status=entry.get('status', 'unknown'),
        last_run=entry.get('last_run'),
        exhausted_at=entry.get('exhausted_at'),
        exhausted=exhausted,
        reset_in_seconds=reset_in
    )


@router.post('', status_code=201)
async def create_key(request: KeyCreateRequest) -> Dict[str, str]:
    """Add a new API key."""
    if not request.name or not request.api_key:
        raise HTTPException(status_code=400, detail='Name and API key are required')
    
    data = _load_keys()
    
    if request.name in data:
        raise HTTPException(status_code=409, detail=f'Key "{request.name}" already exists')
    
    data[request.name] = {
        'api_key': request.api_key,
        'status': request.status,
        'last_run': None,
        'exhausted_at': None
    }
    
    _save_keys(data)
    logger.info(f'Added new key: {request.name}')
    
    return {'message': f'Key "{request.name}" added successfully'}


@router.delete('/{key_name}')
async def delete_key(key_name: str) -> Dict[str, str]:
    """Delete an API key."""
    data = _load_keys()
    
    if key_name not in data:
        raise HTTPException(status_code=404, detail=f'Key "{key_name}" not found')
    
    del data[key_name]
    _save_keys(data)
    logger.info(f'Deleted key: {key_name}')
    
    return {'message': f'Key "{key_name}" deleted successfully'}


@router.patch('/{key_name}')
async def update_key(key_name: str, request: KeyUpdateRequest) -> Dict[str, str]:
    """Update key status or name."""
    data = _load_keys()
    
    if key_name not in data:
        raise HTTPException(status_code=404, detail=f'Key "{key_name}" not found')
    
    entry = data[key_name]
    
    if request.status:
        if request.status not in ('active', 'disabled'):
            raise HTTPException(status_code=400, detail='Status must be "active" or "disabled"')
        entry['status'] = request.status
    
    if request.name and request.name != key_name:
        if request.name in data:
            raise HTTPException(status_code=409, detail=f'Key "{request.name}" already exists')
        data[request.name] = entry
        del data[key_name]
    
    _save_keys(data)
    logger.info(f'Updated key: {key_name}')
    
    return {'message': f'Key "{key_name}" updated successfully'}


@router.post('/{key_name}/reset-quota')
async def reset_quota(key_name: str) -> Dict[str, str]:
    """Reset daily quota exhaustion for a key."""
    data = _load_keys()
    
    if key_name not in data:
        raise HTTPException(status_code=404, detail=f'Key "{key_name}" not found')
    
    if 'exhausted_at' in data[key_name]:
        del data[key_name]['exhausted_at']
        _save_keys(data)
        logger.info(f'Reset quota for key: {key_name}')
        return {'message': f'Quota reset for key "{key_name}"'}
    
    return {'message': f'Key "{key_name}" is not exhausted'}


# ============================================================================
# Initialization Function
# ============================================================================

def init_router() -> APIRouter:
    """Initialize the keys router."""
    return router