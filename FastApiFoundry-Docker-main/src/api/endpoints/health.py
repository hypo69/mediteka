# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Health Check Endpoint
# =============================================================================
# Description:
#   Health check and service restart endpoints.
#   GET /api/v1/health — uniform status for all providers.
#   POST /api/v1/restart/{service} — restarts foundry|llama|docs|rag.
#
#   All provider status blocks share the same shape:
#     { "status": str, "active_model": str | null, ... }
#
# Examples:
#   >>> import requests
#   >>> r = requests.get('http://localhost:9696/api/v1/health')
#   >>> r.json()['llama_status']['active_model']
#   'gemma-4-E4B-it-Q4_K_M.gguf'
#
# File: health.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Changes in 0.8.0:
#   - All provider blocks unified: {status, active_model, ...}
#   - Added hf_status with libraries, token, downloaded/loaded counts
#   - Added real timestamp via datetime
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import subprocess
import sys
import aiohttp
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter
from config_manager import config

router = APIRouter()


def _check_rag_status() -> str:
    """Check RAG index availability."""
    if not config.rag_enabled:
        return 'disabled'
    index_dir = Path(config.rag_index_dir)
    return 'enabled' if (index_dir / 'faiss.index').exists() else 'no index'


async def _check_foundry_status() -> dict:
    """Check Foundry service: status + active_model.

    Returns:
        dict: status ('running'|'stopped'|'not_checked'), active_model.
    """
    try:
        from ...utils.command_agent import CommandAgent
        agent = CommandAgent()
        status_data = await agent.parse_foundry_status()
        
        is_running = status_data.get("status") in ["running", "degraded"]
        port = status_data.get("port")
        
        if is_running and port:
            # Try to get active model from Foundry API
            try:
                from ...models.foundry_client import foundry_client
                result = await foundry_client.list_available_models()
                if result.get("success"):
                    models = result.get("models", [])
                    active = models[0].get("id") if models else None
                    return {
                        "status": "running",
                        "active_model": active,
                        "models_loaded": len(models),
                        "port": port,
                        "url": f"http://127.0.0.1:{port}/v1/"
                    }
            except Exception:
                pass
            
            return {
                "status": "running",
                "active_model": None,
                "models_loaded": 0,
                "port": port,
                "url": f"http://127.0.0.1:{port}/v1/"
            }
        
        return {"status": "stopped", "active_model": None, "models_loaded": 0, "port": None, "url": None}
    except Exception:
        return {"status": "not_checked", "active_model": None, "models_loaded": 0, "port": None, "url": None}


async def _check_llama_status_health() -> dict:
    """Check llama.cpp server: status + active_model.

    Returns:
        dict: status ('running'|'loading'|'stopped'), active_model.
    """
    from .llama_cpp import llama_status
    try:
        result = await llama_status()
        if result.get("running"):
            return {
                "status":       "running",
                "active_model": result.get("active_model"),
                "url":          result.get("url"),
                "pid":          result.get("pid"),
            }
        if result.get("loading"):
            return {"status": "loading", "active_model": None, "url": result.get("url"), "pid": result.get("pid")}
        return {"status": "stopped", "active_model": None, "url": result.get("url"), "pid": None}
    except Exception:
        return {"status": "stopped", "active_model": None, "url": None, "pid": None}


def _check_hf_status() -> dict:
    """Check HuggingFace: libraries, token, downloaded/loaded models + active_model.

    Returns:
        dict: status, active_model, transformers, torch, token_set,
              models_downloaded, models_loaded, models_dir.
    """
    import os
    from ...models.hf_client import hf_client, _get_models_dir

    try:
        import transformers
        transformers_ok = True
    except ImportError:
        transformers_ok = False

    try:
        import torch
        torch_ok = True
    except ImportError:
        torch_ok = False

    downloaded = hf_client.list_downloaded()
    loaded = hf_client.list_loaded()
    token_set = bool(os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN"))
    active = loaded[0].get("id") if loaded else None
    status = "ready" if (transformers_ok and torch_ok) else "libraries_missing"

    return {
        "status":            status,
        "active_model":      active,
        "transformers":      transformers_ok,
        "torch":             torch_ok,
        "token_set":         token_set,
        "models_downloaded": len(downloaded),
        "models_loaded":     len(loaded),
        "models_dir":        str(_get_models_dir()),
    }


async def _check_ollama_status() -> dict:
    """Check Ollama service: status + active_model.

    Returns:
        dict: status ('running'|'stopped'), active_model.
    """
    try:
        from ...models.ollama_client import ollama_client
        result = await ollama_client.list_models()
        if result.get("success"):
            models = result.get("models", [])
            active = (models[0].get("name") or models[0].get("id")) if models else None
            return {"status": "running", "active_model": active, "models_count": len(models)}
        return {"status": "stopped", "active_model": None, "models_count": 0}
    except Exception:
        return {"status": "stopped", "active_model": None, "models_count": 0}


async def _check_docs_status() -> str:
    """Check MkDocs documentation server availability."""
    port = config.get_section('docs_server').get('port', 9697)
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
            async with session.get(f'http://127.0.0.1:{port}/') as resp:
                return 'running' if resp.status == 200 else 'stopped'
    except Exception:
        return 'stopped'


@router.post("/restart/{service}")
async def restart_service(service: str) -> dict:
    """Restart a background service.

    Args:
        service: One of 'foundry', 'llama', 'docs', 'rag'.

    Returns:
        dict: success, message.
    """
    try:
        if service == 'foundry':
            subprocess.Popen(['foundry', 'service', 'start'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {'success': True, 'message': 'Foundry start command sent'}

        elif service == 'llama':
            llama_cfg = config.get_section('llama_cpp')
            model_path = llama_cfg.get('model_path', '')
            if not model_path or not Path(model_path).exists():
                return {'success': False, 'error': 'No model_path set in config.json → llama_cpp.model_path'}
            from .llama_cpp import llama_start
            return await llama_start({'model_path': model_path, 'port': llama_cfg.get('port', 9780)})

        elif service == 'docs':
            port = config.get_section('docs_server').get('port', 9697)
            root = Path(__file__).parents[4]
            subprocess.Popen(
                [sys.executable, '-m', 'mkdocs', 'serve', '-a', f'0.0.0.0:{port}'],
                cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return {'success': True, 'message': f'MkDocs started on port {port}'}

        elif service == 'rag':
            rag_cfg = config.get_section('rag_system')
            if not rag_cfg.get('enabled', False):
                return {'success': False, 'error': 'RAG is disabled in config.json → rag_system.enabled'}
            index_dir = Path(rag_cfg.get('index_dir', '~/.ai-assist/rag/default_index')).expanduser()
            if not (index_dir / 'faiss.index').exists():
                return {'success': False, 'error': f'No FAISS index found in {index_dir}'}
            from ...rag.rag_system import rag_system
            await rag_system.reload_index(index_dir=str(index_dir))
            return {'success': True, 'message': 'RAG index reloaded'}

        return {'success': False, 'error': f'Unknown service: {service}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.get("/health")
async def health_check() -> dict:
    """Проверка здоровья сервиса.

    All provider blocks share the shape: {status, active_model, ...}

    Returns:
        dict: status, foundry_status, llama_status, hf_status, ollama_status,
              docs_status, rag_status, timestamp.
    """
    try:
        foundry_status, llama_status, ollama_status, docs_status = await asyncio.gather(
            _check_foundry_status(),
            _check_llama_status_health(),
            _check_ollama_status(),
            _check_docs_status(),
        )
        hf_status = _check_hf_status()
        rag_status = _check_rag_status()
        foundry_running = foundry_status.get("status") in {"running", "healthy"}
        foundry_details = {
            "port": foundry_status.get("port"),
            "url": foundry_status.get("url"),
        } if foundry_running else None

        return {
            "status":         "healthy",
            "foundry_status": foundry_status,
            "foundry_status_legacy": "healthy" if foundry_running else foundry_status.get("status", "stopped"),
            "foundry_details": foundry_details,
            "models_count": foundry_status.get("models_loaded", 0),
            "llama_status":   llama_status,
            "hf_status":      hf_status,
            "ollama_status":  ollama_status,
            "docs_status":    docs_status,
            "rag_status":     rag_status,
            "timestamp":      datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "status":         "healthy",
            "foundry_status": {"status": "error", "active_model": None, "error": str(e)},
            "foundry_status_legacy": "error",
            "foundry_details": None,
            "models_count": 0,
            "llama_status":   {"status": "stopped", "active_model": None},
            "hf_status":      {"status": "error", "active_model": None, "error": str(e)},
            "ollama_status":  {"status": "stopped", "active_model": None},
            "docs_status":    "stopped",
            "rag_status":     "disabled",
            "timestamp":      datetime.now(timezone.utc).isoformat(),
        }
