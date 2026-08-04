// -*- coding: utf-8 -*-
// =============================================================================
// Process Name: Server debug tab — test FastAPI Foundry endpoints
// =============================================================================
// File: debug.js
// Project: FastApiFoundry (Docker)
// Version: 0.6.0
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

import { initI18n, t } from './js/i18n.js';

// ── Quick endpoint definitions ────────────────────────────────────────────────

const QUICK_ENDPOINTS = [
    // Core
    { g: 'Core', method: 'GET',  path: '/api/v1/health',                label: 'Health check' },
    { g: 'Core', method: 'GET',  path: '/api/v1/models',                label: 'All models' },
    { g: 'Core', method: 'GET',  path: '/api/v1/models/connected',      label: 'Connected models' },
    { g: 'Core', method: 'GET',  path: '/api/v1/config',                label: 'Config' },

    // Chat
    { g: 'Chat', method: 'POST', path: '/api/v1/chat/start',            label: 'Start session',
      body: { model: '' } },
    { g: 'Chat', method: 'POST', path: '/api/v1/chat/message',          label: 'Send message',
      body: { session_id: '', message: 'Hello!', model: '', max_tokens: 256 } },
    { g: 'Chat', method: 'GET',  path: '/api/v1/chat/models',           label: 'Chat models' },

    // Generate
    { g: 'Generate', method: 'POST', path: '/api/v1/generate',          label: 'Generate text',
      body: { prompt: 'Say hello in one sentence.', model: '', max_tokens: 128, temperature: 0.7 } },
    { g: 'Generate', method: 'POST', path: '/api/v1/generate',          label: 'Generate + RAG',
      body: { prompt: 'What is FastAPI Foundry?', model: '', use_rag: true, max_tokens: 256 } },

    // Foundry
    { g: 'Foundry', method: 'GET',  path: '/api/v1/foundry/status',     label: 'Service status' },
    { g: 'Foundry', method: 'GET',  path: '/api/v1/foundry/models/list',label: 'Models list' },
    { g: 'Foundry', method: 'GET',  path: '/foundry/models/loaded',     label: 'Loaded models' },
    { g: 'Foundry', method: 'GET',  path: '/foundry/models/cached',     label: 'Cached models' },

    // HuggingFace
    { g: 'HuggingFace', method: 'GET',  path: '/api/v1/hf/status',      label: 'HF status' },
    { g: 'HuggingFace', method: 'GET',  path: '/api/v1/hf/models',      label: 'Downloaded + loaded' },
    { g: 'HuggingFace', method: 'GET',  path: '/api/v1/hf/hub/models',  label: 'Hub models' },
    { g: 'HuggingFace', method: 'POST', path: '/api/v1/hf/generate',    label: 'HF generate',
      body: { model_id: 'Qwen/Qwen2.5-0.5B-Instruct', prompt: 'Hello!', max_new_tokens: 64 } },
    { g: 'HuggingFace', method: 'POST', path: '/api/v1/hf/models/load', label: 'Load model',
      body: { model_id: 'Qwen/Qwen2.5-0.5B-Instruct', device: 'auto' } },
    { g: 'HuggingFace', method: 'POST', path: '/api/v1/hf/models/unload', label: 'Unload model',
      body: { model_id: 'Qwen/Qwen2.5-0.5B-Instruct' } },
    { g: 'HuggingFace', method: 'POST', path: '/api/v1/hf/models/download', label: 'Download model',
      body: { model_id: 'Qwen/Qwen2.5-0.5B-Instruct' } },

    // llama.cpp
    { g: 'llama.cpp', method: 'GET',  path: '/api/v1/llama/status',     label: 'Server status' },
    { g: 'llama.cpp', method: 'GET',  path: '/api/v1/llama/models',     label: 'Scan GGUF models' },
    { g: 'llama.cpp', method: 'POST', path: '/api/v1/llama/stop',       label: 'Stop server', body: {} },

    // RAG
    { g: 'RAG', method: 'GET',  path: '/api/v1/rag/status',             label: 'RAG status' },
    { g: 'RAG', method: 'GET',  path: '/api/v1/rag/profiles',           label: 'Profiles list' },
    { g: 'RAG', method: 'GET',  path: '/api/v1/rag/dirs',               label: 'Indexable dirs' },
    { g: 'RAG', method: 'POST', path: '/api/v1/rag/search',             label: 'Search',
      body: { query: 'FastAPI Foundry', top_k: 3 } },
    { g: 'RAG', method: 'POST', path: '/api/v1/rag/clear',              label: 'Clear index', body: {} },
];

// ── State ─────────────────────────────────────────────────────────────────────

function getBaseUrl() {
    return document.getElementById('base-url').value.trim().replace(/\/$/, '');
}

function getApiKey() {
    return document.getElementById('api-key-input').value.trim();
}

function buildHeaders() {
    const h = { 'Content-Type': 'application/json' };
    const key = getApiKey();
    if (key) h['Authorization'] = `Bearer ${key}`;
    return h;
}

// ── Response display ──────────────────────────────────────────────────────────

function showResponse(text, ok, meta = '') {
    const box = document.getElementById('response-box');
    box.textContent = text;
    box.className = 'response-box ' + (ok ? 'ok' : 'err');
    document.getElementById('resp-meta').textContent = meta;
}

function showConnStatus(ok, text) {
    const el = document.getElementById('conn-status');
    el.textContent = text;
    el.className = 'status-pill ' + (ok ? 'ok' : 'err');
    el.style.display = '';
}

// ── Core fetch ────────────────────────────────────────────────────────────────

async function doRequest(method, path, body = null) {
    const url = getBaseUrl() + path;
    const t0  = Date.now();
    try {
        const opts = { method, headers: buildHeaders() };
        if (body && method !== 'GET') opts.body = JSON.stringify(body);

        const res  = await fetch(url, opts);
        const ms   = Date.now() - t0;
        const text = await res.text();

        let pretty = text;
        try { pretty = JSON.stringify(JSON.parse(text), null, 2); } catch {}

        const meta = `${method} ${path}  •  ${res.status} ${res.statusText}  •  ${ms}ms`;
        showResponse(pretty, res.ok, meta);
        return { ok: res.ok, status: res.status, text };
    } catch (e) {
        const ms = Date.now() - t0;
        showResponse(`❌ ${e.message}\n\nURL: ${url}`, false, `${method} ${path}  •  ${ms}ms`);
        return { ok: false, error: e.message };
    }
}

// ── Quick endpoint list ───────────────────────────────────────────────────────

function buildEndpointList(filter = '') {
    const list = document.getElementById('endpoint-list');
    list.innerHTML = '';

    const q = filter.toLowerCase();
    const filtered = q
        ? QUICK_ENDPOINTS.filter(ep =>
            ep.path.toLowerCase().includes(q) ||
            ep.label.toLowerCase().includes(q) ||
            ep.g.toLowerCase().includes(q))
        : QUICK_ENDPOINTS;

    // Group by ep.g
    const groups = {};
    filtered.forEach(ep => {
        if (!groups[ep.g]) groups[ep.g] = [];
        groups[ep.g].push(ep);
    });

    const GROUP_COLORS = {
        'Core':        '#6c757d',
        'Chat':        '#0d6efd',
        'Generate':    '#198754',
        'Foundry':     '#6610f2',
        'HuggingFace': '#fd7e14',
        'llama.cpp':   '#dc3545',
        'RAG':         '#0dcaf0',
    };

    Object.entries(groups).forEach(([group, eps]) => {
        // Group header
        const hdr = document.createElement('div');
        hdr.style.cssText = `padding:3px 12px;font-size:10px;font-weight:700;letter-spacing:.05em;
            text-transform:uppercase;color:${GROUP_COLORS[group] || '#6c757d'};
            background:#f8f9fa;border-bottom:1px solid #dee2e6;`;
        hdr.textContent = group;
        list.appendChild(hdr);

        eps.forEach(ep => {
            const row = document.createElement('div');
            row.className = 'ep-row';

            row.innerHTML = `
                <span class="method-badge method-${ep.method.toLowerCase()}">${ep.method}</span>
                <span class="ep-path text-truncate" title="${ep.path}">${ep.path}</span>
                <span class="ep-label">${ep.label}</span>
            `;

            row.addEventListener('click', () => {
                document.querySelectorAll('.ctrl-tab').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.ctrl-panel').forEach(p => p.classList.remove('active'));
                document.querySelector('[data-ctrl="custom"]').classList.add('active');
                document.getElementById('ctrl-custom').classList.add('active');

                document.getElementById('req-method').value = ep.method;
                document.getElementById('req-path').value   = ep.path;
                document.getElementById('req-body').value   = ep.body
                    ? JSON.stringify(ep.body, null, 2) : '';

                doRequest(ep.method, ep.path, ep.body || null);
            });

            list.appendChild(row);
        });
    });

    if (!filtered.length) {
        const empty = document.createElement('div');
        empty.className = 'text-muted small text-center p-3';
        empty.textContent = 'No endpoints match';
        list.appendChild(empty);
    }
}

// ── Load models into chat-model input ────────────────────────────────────────

async function loadModels() {
    const res = await doRequest('GET', '/api/v1/models');
    if (!res.ok) return;
    try {
        const data = JSON.parse(res.text);
        const models = data.models || data.data || [];
        if (!models.length) return;
        // Put first model id as suggestion
        const input = document.getElementById('chat-model');
        if (!input.value) input.value = models[0].id || models[0];
    } catch {}
}

// ── Chat test ─────────────────────────────────────────────────────────────────

async function sendChat() {
    const model  = document.getElementById('chat-model').value.trim();
    const prompt = document.getElementById('chat-prompt').value.trim();
    if (!prompt) return;

    const body = {
        messages: [{ role: 'user', content: prompt }],
        model:    model || undefined,
        max_tokens: 512,
    };
    // Remove undefined keys
    if (!body.model) delete body.model;

    await doRequest('POST', '/api/v1/chat', body);
}

// ── Custom request ────────────────────────────────────────────────────────────

async function sendCustom() {
    const method = document.getElementById('req-method').value;
    const path   = document.getElementById('req-path').value.trim();
    const raw    = document.getElementById('req-body').value.trim();

    let body = null;
    if (raw && method !== 'GET') {
        try { body = JSON.parse(raw); }
        catch { showResponse(`❌ Invalid JSON in request body:\n${raw}`, false, ''); return; }
    }

    await doRequest(method, path, body);
}

// ── Health check ──────────────────────────────────────────────────────────────

async function checkHealth() {
    const res = await doRequest('GET', '/api/v1/health');
    if (res.ok) {
        showConnStatus(true, '✓ Connected');
    } else {
        showConnStatus(false, `✗ ${res.status || 'Unreachable'}`);
    }
}

// ── Control tabs ────────────────────────────────────────────────────────────

function initCtrlTabs() {
    document.querySelectorAll('.ctrl-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.ctrl-tab').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.ctrl-panel').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('ctrl-' + btn.dataset.ctrl).classList.add('active');
        });
    });
}

// ── Init ──────────────────────────────────────────────────────────────────────

async function init() {
    await initI18n();
    buildEndpointList();
    initCtrlTabs();

    // Restore saved base URL
    chrome.storage.sync.get(['debugBaseUrl', 'debugApiKey'], d => {
        if (d.debugBaseUrl) document.getElementById('base-url').value = d.debugBaseUrl;
        if (d.debugApiKey)  document.getElementById('api-key-input').value = d.debugApiKey;
    });

    // Save base URL on change
    document.getElementById('base-url').addEventListener('change', () => {
        chrome.storage.sync.set({ debugBaseUrl: getBaseUrl() });
    });
    document.getElementById('api-key-input').addEventListener('change', () => {
        chrome.storage.sync.set({ debugApiKey: getApiKey() });
    });

    document.getElementById('btn-health').addEventListener('click', checkHealth);
    document.getElementById('btn-send').addEventListener('click', sendCustom);
    document.getElementById('btn-chat').addEventListener('click', sendChat);
    document.getElementById('btn-load-models').addEventListener('click', loadModels);

    document.getElementById('ep-filter').addEventListener('input', e => {
        buildEndpointList(e.target.value);
    });

    document.getElementById('btn-copy').addEventListener('click', () => {
        const text = document.getElementById('response-box').textContent;
        navigator.clipboard.writeText(text).catch(() => {});
    });

    document.getElementById('btn-clear-resp').addEventListener('click', () => {
        const box = document.getElementById('response-box');
        box.textContent = t('debug.response_placeholder');
        box.className = 'response-box';
        document.getElementById('resp-meta').textContent = '';
        document.getElementById('conn-status').style.display = 'none';
    });

    // Auto-check on load
    checkHealth();
}

init();
