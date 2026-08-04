# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Full API Coverage Test Suite
# =============================================================================
# Description:
#   Pytest test suite that calls every /api/v1/* endpoint with all documented
#   request fields. Requires a running server (default: http://localhost:9696).
#
#   Run:
#     pytest tests/test_api_coverage.py -v
#     pytest tests/test_api_coverage.py -v --base-url http://localhost:9696
#
# File: tests/test_api_coverage.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import time
import pytest
import requests

# ── Fixtures ──────────────────────────────────────────────────────────────────

def pytest_addoption(parser):
    parser.addoption('--base-url', default='http://localhost:9696', help='Server base URL')


@pytest.fixture(scope='session')
def base_url(request):
    return request.config.getoption('--base-url').rstrip('/')


@pytest.fixture(scope='session')
def model(base_url):
    """Auto-detect first working model from /api/v1/models."""
    try:
        r = requests.get(f'{base_url}/api/v1/models', timeout=10)
        models = r.json().get('models', []) if r.ok else []
    except Exception:
        return ''
    for m in models[:8]:
        mid = (m.get('id') or '').strip()
        if not mid:
            continue
        try:
            probe = requests.post(
                f'{base_url}/api/v1/generate',
                json={'prompt': 'OK', 'model': mid, 'temperature': 0.1, 'max_tokens': 4, 'use_rag': False},
                timeout=30,
            )
            if probe.ok and probe.json().get('success'):
                return mid
        except Exception:
            continue
    return ''


@pytest.fixture(scope='session')
def session_id(base_url, model):
    """Create a chat session for session-dependent tests."""
    try:
        r = requests.post(
            f'{base_url}/api/v1/chat/start',
            json={'model': model or 'default'},
            timeout=5,
        )
        return r.json().get('session_id', f'qa-{int(time.time())}')
    except Exception:
        return f'qa-{int(time.time())}'


# ── Helpers ───────────────────────────────────────────────────────────────────

def get(base_url, path, timeout=15):
    return requests.get(f'{base_url}{path}', timeout=timeout)


def post(base_url, path, body, timeout=15):
    return requests.post(f'{base_url}{path}', json=body, timeout=timeout)


def patch(base_url, path, body, timeout=15):
    return requests.patch(f'{base_url}{path}', json=body, timeout=timeout)


def delete(base_url, path, timeout=15):
    return requests.delete(f'{base_url}{path}', timeout=timeout)


# ── Health & System ───────────────────────────────────────────────────────────

def test_health(base_url):
    r = get(base_url, '/api/v1/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'healthy'


def test_system_stats(base_url):
    r = get(base_url, '/api/v1/system/stats')
    assert r.status_code == 200
    assert r.json()['success'] is True


# ── Models ────────────────────────────────────────────────────────────────────

def test_models(base_url):
    r = get(base_url, '/api/v1/models')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_models_connected(base_url):
    r = get(base_url, '/api/v1/models/connected')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_ai_models(base_url):
    r = get(base_url, '/api/v1/ai/models')
    assert r.status_code == 200


def test_ai_models_recommended(base_url):
    r = get(base_url, '/api/v1/ai/models/recommended')
    assert r.status_code == 200


def test_ai_health(base_url):
    r = get(base_url, '/api/v1/ai/health')
    assert r.status_code == 200


# ── Foundry ───────────────────────────────────────────────────────────────────

def test_foundry_status(base_url):
    r = get(base_url, '/api/v1/foundry/status')
    assert r.status_code == 200
    assert 'success' in r.json()


def test_foundry_models_list(base_url):
    r = get(base_url, '/api/v1/foundry/models/list')
    assert r.status_code == 200


# ── Generate ─────────────────────────────────────────────────────────────────

def test_generate_all_fields(base_url, model):
    if not model:
        pytest.skip('no model available')
    r = post(base_url, '/api/v1/generate', {
        'prompt': 'Say OK',
        'model': model,
        'temperature': 0.1,
        'max_tokens': 16,
        'use_rag': False,
        'top_k': 3,
        'translate_model_dialog': False,
        'user_language': 'en',
    }, timeout=120)
    assert r.status_code == 200
    d = r.json()
    assert d['success'] is True
    assert d.get('content')


def test_generate_with_rag(base_url, model):
    if not model:
        pytest.skip('no model available')
    r = post(base_url, '/api/v1/generate', {
        'prompt': 'What is RAG?',
        'model': model,
        'temperature': 0.2,
        'max_tokens': 32,
        'use_rag': True,
        'top_k': 3,
    }, timeout=120)
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_ai_generate_all_fields(base_url, model):
    if not model:
        pytest.skip('no model available')
    r = post(base_url, '/api/v1/ai/generate', {
        'prompt': 'Say OK',
        'model': model,
        'temperature': 0.1,
        'max_tokens': 16,
        'use_rag': False,
        'min_score': 0.0,
    }, timeout=120)
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_ai_chat_all_fields(base_url, model):
    if not model:
        pytest.skip('no model available')
    r = post(base_url, '/api/v1/ai/chat', {
        'messages': [{'role': 'user', 'content': 'Say OK'}],
        'model': model,
        'temperature': 0.1,
        'max_tokens': 16,
        'use_rag': False,
        'system_prompt': 'You are a helpful assistant.',
        'min_score': 0.0,
    }, timeout=120)
    assert r.status_code == 200
    d = r.json()
    assert d.get('choices') or d.get('success') is True


def test_ai_optimize(base_url):
    r = post(base_url, '/api/v1/ai/optimize', {
        'task_type': 'general',
        'model_preference': 'balanced',
    })
    assert r.status_code == 200


# ── Chat Sessions ─────────────────────────────────────────────────────────────

def test_chat_start(base_url, model):
    r = post(base_url, '/api/v1/chat/start', {'model': model or 'default'})
    assert r.status_code == 200
    d = r.json()
    assert d['success'] is True
    assert d.get('session_id')


def test_chat_message(base_url, model, session_id):
    if not model:
        pytest.skip('no model available')
    r = post(base_url, '/api/v1/chat/message', {
        'session_id': session_id,
        'message': 'Say OK',
        'model': model,
        'temperature': 0.1,
        'max_tokens': 16,
        'source_lang': 'auto',
        'locale': 'en',
    }, timeout=120)
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_chat_history_get(base_url, session_id):
    r = get(base_url, f'/api/v1/chat/history/{session_id}')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_chat_models(base_url):
    r = get(base_url, '/api/v1/chat/models')
    assert r.status_code == 200


def test_chat_history_list(base_url):
    r = get(base_url, '/api/v1/chat/history/list?limit=10&offset=0')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_chat_history_save(base_url, model, session_id):
    r = post(base_url, '/api/v1/chat/history/save', {
        'messages': [{'role': 'user', 'content': 'test'}],
        'session_id': session_id,
        'model': model or '',
        'title': 'QA test',
        'aborted': False,
    })
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_chat_history_cleanup(base_url):
    r = post(base_url, '/api/v1/chat/history/cleanup', {
        'retention_days': 90,
        'max_size_mb': 100,
    })
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_chat_session_delete(base_url, session_id):
    r = delete(base_url, f'/api/v1/chat/session/{session_id}')
    assert r.status_code == 200
    assert r.json()['success'] is True


# ── RAG ───────────────────────────────────────────────────────────────────────

def test_rag_status(base_url):
    r = get(base_url, '/api/v1/rag/status')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_rag_dirs(base_url):
    r = get(base_url, '/api/v1/rag/dirs')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_rag_cwd(base_url):
    r = get(base_url, '/api/v1/rag/cwd')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_rag_profiles(base_url):
    r = get(base_url, '/api/v1/rag/profiles')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_rag_browse(base_url):
    r = get(base_url, '/api/v1/rag/browse')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_rag_search(base_url):
    r = post(base_url, '/api/v1/rag/search', {
        'query': 'test query',
        'top_k': 3,
        'min_score': 0.0,
    })
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_rag_extract_formats(base_url):
    r = get(base_url, '/api/v1/rag/extract/formats')
    assert r.status_code == 200


def test_rag_documents_list(base_url):
    r = get(base_url, '/api/v1/rag/documents')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_rag_documents_stats(base_url):
    r = get(base_url, '/api/v1/rag/documents/stats')
    assert r.status_code == 200
    assert r.json()['success'] is True


# ── Config ────────────────────────────────────────────────────────────────────

def test_config_get(base_url):
    r = get(base_url, '/api/v1/config')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_config_raw_get(base_url):
    r = get(base_url, '/api/v1/config/raw')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_config_env_raw_get(base_url):
    r = get(base_url, '/api/v1/config/env-raw')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_config_export(base_url):
    r = get(base_url, '/api/v1/config/export')
    assert r.status_code == 200


def test_config_provider_keys(base_url):
    r = get(base_url, '/api/v1/config/provider-keys')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_config_extension_export(base_url):
    r = get(base_url, '/api/v1/config/extension-export')
    assert r.status_code == 200
    assert r.json()['success'] is True


def test_config_patch_noop(base_url):
    r = patch(base_url, '/api/v1/config', {'_qa_test_noop': True})
    assert r.status_code == 200
    assert r.json()['success'] is True


# ── Translator ────────────────────────────────────────────────────────────────

def test_translator_config(base_url):
    r = get(base_url, '/api/v1/translate/config')
    assert r.status_code == 200
    assert 'enabled' in r.json()


def test_translate_detect(base_url):
    r = post(base_url, '/api/v1/translate/detect', {'text': 'Hello world'})
    assert r.status_code == 200


def test_translate_text(base_url):
    r = post(base_url, '/api/v1/translate', {
        'text': 'Hello',
        'source_lang': 'auto',
        'target_lang': 'ru',
        'provider': '',
        'api_key': '',
    })
    assert r.status_code == 200


# ── Logs ──────────────────────────────────────────────────────────────────────

def test_logs_get(base_url):
    r = get(base_url, '/api/v1/logs?lines=20')
    assert r.status_code == 200


# ── HuggingFace ───────────────────────────────────────────────────────────────

def test_hf_status(base_url):
    r = get(base_url, '/api/v1/hf/status')
    assert r.status_code == 200


def test_hf_models(base_url):
    r = get(base_url, '/api/v1/hf/models')
    assert r.status_code == 200


# ── llama.cpp ─────────────────────────────────────────────────────────────────

def test_llama_status(base_url):
    r = get(base_url, '/api/v1/llama/status')
    assert r.status_code == 200


def test_llama_models(base_url):
    r = get(base_url, '/api/v1/llama/models')
    assert r.status_code == 200


# ── Ollama ────────────────────────────────────────────────────────────────────

def test_ollama_status(base_url):
    r = get(base_url, '/api/v1/ollama/status')
    assert r.status_code == 200


def test_ollama_models(base_url):
    r = get(base_url, '/api/v1/ollama/models')
    assert r.status_code == 200
