// -*- coding: utf-8 -*-
// =============================================================================
// Process Name: Models tab — unified model management
// =============================================================================
// Description:
//   Renders the Models tab:
//     - "Active Models" — models currently loaded/running (ready for API calls)
//     - "Available Models" — all known models grouped by provider, with
//       Load / Unload / Download actions per model
//
//   Data sources (polled in parallel):
//     GET /api/v1/foundry/models/cached   — Foundry models on disk (no service probe)
//     GET /api/v1/foundry/models/loaded   — Foundry models running in service
//     GET /api/v1/hf/models               — HuggingFace downloaded + loaded
//     GET /api/v1/llama/status            — llama.cpp running model
//     GET /api/v1/llama/models            — llama.cpp GGUF files on disk
//     GET /api/v1/ollama/models           — Ollama local models
//
// File: js/models.js
// Project: AI Assistant (ai_assist)
// Version: 0.7.1
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

import { showAlert } from './ui.js';

// ── Provider metadata ─────────────────────────────────────────────────────────

const PROVIDER_META = {
    foundry:      { label: 'Microsoft Foundry',  icon: 'bi-microsoft',          color: '#0078d4' },
    huggingface:  { label: 'HuggingFace',         icon: 'bi-boxes',              color: '#ff9d00' },
    llama:        { label: 'llama.cpp',            icon: 'bi-file-earmark-binary', color: '#7c3aed' },
    ollama:       { label: 'Ollama',               icon: 'bi-box-seam',           color: '#1a1a1a' },
};

// ── State ─────────────────────────────────────────────────────────────────────

const ACTIVE_MODEL_STORAGE = 'fastapi-foundry-active-model';

/** @type {{ provider: string, id: string, prefix: string }|null} */
let _activeModel = _loadActiveModel();

function _loadActiveModel() {
    try {
        const raw = localStorage.getItem(ACTIVE_MODEL_STORAGE);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

function _saveActiveModel(model) {
    _activeModel = model;
    window._savedChatModel = model?.prefix || '';
    try {
        if (model) localStorage.setItem(ACTIVE_MODEL_STORAGE, JSON.stringify(model));
        else localStorage.removeItem(ACTIVE_MODEL_STORAGE);
    } catch {}

    if (model?.prefix) {
        const patch = { 'foundry_ai.default_model': model.prefix };
        if (model.provider === 'llama' && model.id && model.id !== 'llama-server') {
            patch['llama_cpp.model_path'] = model.id;
        }
        fetch(`${window.API_BASE}/config`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(patch),
        }).catch(() => {});
    }
}

function _escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function _jsString(value) {
    return String(value ?? '')
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/\r/g, '\\r')
        .replace(/\n/g, '\\n');
}

function _modelFromPrefix(prefix) {
    if (!prefix || !prefix.includes('::')) return null;
    const [rawProvider, ...rest] = prefix.split('::');
    const id = rest.join('::');
    const provider = rawProvider === 'hf' ? 'huggingface' : rawProvider;
    return { provider, id, prefix };
}

// ── Fetch helpers ─────────────────────────────────────────────────────────────

async function _get(url) {
    try {
        const r = await fetch(url);
        return r.ok ? await r.json() : { success: false };
    } catch { return { success: false }; }
}

async function _post(url, body = {}) {
    try {
        const r = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        return r.ok ? await r.json() : { success: false };
    } catch { return { success: false }; }
}

// ── Data aggregation ──────────────────────────────────────────────────────────

/**
 * Collect model data from all providers in parallel.
 * Returns { active: [], byProvider: { foundry: [], huggingface: [], llama: [], ollama: [] } }
 */
async function _collectAllModels() {
    const [foundryCached, foundryLoaded, hfData, llamaStatus, llamaDisk, llamaLoaded, ollamaData] = await Promise.allSettled([
        _get(`${window.API_BASE}/foundry/models/cached`),
        _get(`${window.API_BASE}/foundry/models/loaded`),
        _get(`${window.API_BASE}/hf/models`),
        _get(`${window.API_BASE}/llama/status`),
        _get(`${window.API_BASE}/llama/models`),
        _get(`${window.API_BASE}/llama/v1/models`),
        _get(`${window.API_BASE}/ollama/models`),
    ]).then(results => results.map(r => r.status === 'fulfilled' ? r.value : { success: false }));

    const active = [];
    const byProvider = { foundry: [], huggingface: [], llama: [], ollama: [] };

    // ── Foundry ──────────────────────────────────────────────────────────────
    const loadedFoundryIds = new Set(
        (foundryLoaded.success ? (foundryLoaded.models || []) : []).map(m => m.id)
    );

    for (const m of (foundryLoaded.success ? (foundryLoaded.models || []) : [])) {
        const id = m.id;
        if (!id) continue;
        active.push({
            provider: 'foundry',
            id,
            label: m.alias || m.name || id,
            prefix: `foundry::${id}`,
        });
    }

    for (const m of (foundryCached.success ? (foundryCached.items || []) : [])) {
        byProvider.foundry.push({
            id:     m.id,
            label:  m.name || m.alias || m.id,
            size:   m.size || '',
            device: m.device || m.type || '',
            loaded: loadedFoundryIds.has(m.id),
            cached: true,
            prefix: `foundry::${m.id}`,
        });
    }

    for (const m of (foundryLoaded.success ? (foundryLoaded.models || []) : [])) {
        if (!m.id || byProvider.foundry.some(cached => cached.id === m.id)) continue;
        byProvider.foundry.push({
            id:     m.id,
            label:  m.alias || m.name || m.id,
            size:   '',
            device: '',
            loaded: true,
            cached: false,
            prefix: `foundry::${m.id}`,
        });
    }

    // ── HuggingFace ───────────────────────────────────────────────────────────
    const loadedHFIds = new Set(
        (hfData.success ? (hfData.loaded || []) : []).map(m => m.id)
    );

    for (const m of (hfData.success ? (hfData.loaded || []) : [])) {
        active.push({ provider: 'huggingface', id: m.id, label: m.id, prefix: `hf::${m.id}` });
    }

    for (const m of (hfData.success ? (hfData.downloaded || []) : [])) {
        byProvider.huggingface.push({
            id:     m.id,
            label:  m.id,
            size:   m.size_mb ? `${m.size_mb} MB` : '',
            loaded: loadedHFIds.has(m.id),
            cached: true,
            prefix: `hf::${m.id}`,
        });
    }

    // ── llama.cpp ─────────────────────────────────────────────────────────────
    const loadedLlamaId = llamaLoaded.success ? llamaLoaded.model_name : null;
    const loadedLlamaName = loadedLlamaId ? (loadedLlamaId.split(/[\/\\]/).pop() || loadedLlamaId) : '';
    if (llamaStatus.success && llamaStatus.running) {
        const llamaModelId = loadedLlamaId || _activeModel?.id || 'llama-server';
        const llamaModelName = loadedLlamaName || llamaModelId.split(/[\/\\]/).pop() || 'llama.cpp server';
        const llamaPrefix = _activeModel?.provider === 'llama' ? _activeModel.prefix : `llama::${llamaModelId}`;
        active.push({ provider: 'llama', id: llamaModelId, label: llamaModelName, prefix: llamaPrefix });
    }

    for (const m of (llamaDisk.success ? (llamaDisk.models || []) : [])) {
        const id = m.path || m.name;
        const isLoaded = Boolean(
            llamaStatus.success &&
            llamaStatus.running &&
            (loadedLlamaId === m.path || loadedLlamaId === m.name || loadedLlamaName === m.name || _activeModel?.prefix === `llama::${id}`)
        );
        byProvider.llama.push({
            id,
            label:  m.name || id,
            size:   m.size_gb ? `${m.size_gb} GB` : '',
            device: m.dir || '',
            loaded: isLoaded,
            cached: true,
            prefix: `llama::${id}`,
        });
    }

    if (!byProvider.llama.length && llamaStatus.success && llamaStatus.loading) {
        byProvider.llama.push({
            id:     'llama-server',
            label:  'llama.cpp (loading…)',
            size:   '',
            loaded: false,
            loading: true,
            cached: true,
            prefix: 'llama::llama-server',
        });
    }

    // ── Ollama ────────────────────────────────────────────────────────────────
    for (const m of (ollamaData.success ? (ollamaData.models || []) : [])) {
        const id = m.name || m.id;
        byProvider.ollama.push({
            id:     id,
            label:  id,
            size:   m.size_gb ? `${m.size_gb} GB` : '',
            loaded: false,   // Ollama manages its own memory — treat as available
            cached: true,
            prefix: `ollama::${id}`,
        });
    }

    return { active, byProvider };
}

// ── Render: Active models ─────────────────────────────────────────────────────

function _renderActive(active) {
    const el = document.getElementById('models-container');
    if (!el) return;

    if (!active.length) {
        el.innerHTML = `
            <div class="col-12 text-center text-muted py-4">
                <i class="bi bi-cpu fs-2 d-block mb-2 opacity-25"></i>
                <span data-i18n="models.no_models">No models loaded. Load a model from the Available section below.</span>
            </div>`;
        return;
    }

    el.innerHTML = active.map(m => {
        const meta  = PROVIDER_META[m.provider] || { label: m.provider, icon: 'bi-cpu', color: '#6c757d' };
        const isAct = _activeModel?.prefix === m.prefix;
        const providerArg = _jsString(m.provider);
        const idArg = _jsString(m.id);
        const prefixArg = _jsString(m.prefix);
        return `
        <div class="col-md-4 col-sm-6 p-2">
            <div class="card h-100 ${isAct ? 'border-primary' : ''}" style="font-size:.85rem">
                <div class="card-body p-3">
                    <div class="d-flex align-items-start gap-2 mb-2">
                        <i class="bi ${meta.icon} fs-5 flex-shrink-0" style="color:${meta.color}"></i>
                        <div class="overflow-hidden">
                            <div class="fw-semibold text-truncate" title="${_escapeHtml(m.id)}">${_escapeHtml(m.label)}</div>
                            <div class="text-muted" style="font-size:.75rem">${_escapeHtml(meta.label)}</div>
                        </div>
                        ${isAct ? '<span class="badge bg-primary ms-auto">Active</span>' : ''}
                    </div>
                    <code class="d-block text-truncate mb-2" style="font-size:.7rem;color:#6c757d">${_escapeHtml(m.prefix)}</code>
                    <div class="d-flex gap-1">
                        <button class="btn btn-sm ${isAct ? 'btn-primary' : 'btn-outline-primary'} flex-grow-1"
                                onclick="setActiveModel('${providerArg}','${idArg}','${prefixArg}')">
                            ${isAct ? '✓ Active' : 'Set Active'}
                        </button>
                        <button class="btn btn-sm btn-outline-danger"
                                onclick="unloadModel('${providerArg}','${idArg}')"
                                title="Unload from memory">
                            <i class="bi bi-stop-fill"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>`;
    }).join('');
}

// ── Render: Available models by provider ─────────────────────────────────────

function _renderAvailable(byProvider) {
    const el = document.getElementById('models-list');
    if (!el) return;

    const sections = [];

    for (const [provId, models] of Object.entries(byProvider)) {
        if (!models.length) continue;
        const meta = PROVIDER_META[provId] || { label: provId, icon: 'bi-cpu', color: '#6c757d' };

        const rows = models.map(m => {
            const idArg = _jsString(m.id);
            const provArg = _jsString(provId);
            const prefixArg = _jsString(m.prefix);
            const loadedBadge = m.loaded
                ? '<span class="badge bg-success me-1">Loaded</span>'
                : m.loading
                    ? '<span class="badge bg-warning text-dark me-1"><span class="spinner-border spinner-border-sm" style="width:.6em;height:.6em"></span> Loading</span>'
                    : '';
            const cachedBadge = m.cached === false
                ? '<span class="badge bg-info text-dark me-1">Running</span>'
                : '';
            const sizeBadge = m.size
                ? `<span class="badge bg-light text-dark me-1">${_escapeHtml(m.size)}</span>`
                : '';
            const deviceBadge = m.device
                ? `<span class="badge bg-light text-dark me-1">${_escapeHtml(m.device)}</span>`
                : '';

            const loadBtn = m.loaded
                ? `<button class="btn btn-sm btn-outline-danger" onclick="unloadModel('${provArg}','${idArg}')" title="Unload">
                       <i class="bi bi-stop-fill"></i>
                   </button>`
                : `<button class="btn btn-sm btn-outline-success" onclick="loadModel('${provArg}','${idArg}')" title="Load into memory">
                       <i class="bi bi-play-fill"></i> Load
                   </button>`;

            return `
            <div class="d-flex align-items-center px-3 py-2 border-bottom model-row"
                style="font-size:.85rem;gap:.5rem">
                <div class="flex-grow-1 overflow-hidden">
                    <span class="fw-semibold text-truncate d-block" title="${_escapeHtml(m.id)}">${_escapeHtml(m.label)}</span>
                    <div class="mt-1">${loadedBadge}${cachedBadge}${sizeBadge}${deviceBadge}
                        <code style="font-size:.7rem;color:#adb5bd">${_escapeHtml(m.prefix)}</code>
                    </div>
                </div>
                <div class="d-flex gap-1 flex-shrink-0">
                    ${loadBtn}
                    <button class="btn btn-sm btn-outline-secondary"
                            onclick="copyModelPrefix('${prefixArg}')" title="Copy prefix">
                        <i class="bi bi-clipboard"></i>
                    </button>
                </div>
            </div>`;
        }).join('');

        sections.push(`
        <div class="provider-section mb-0">
            <div class="px-3 py-2 d-flex align-items-center gap-2"
                 style="background:#f8f9fa;border-bottom:1px solid #dee2e6;position:sticky;top:0;z-index:1">
                <i class="bi ${meta.icon}" style="color:${meta.color}"></i>
                <span class="fw-semibold small">${meta.label}</span>
                <span class="badge bg-secondary ms-auto">${models.length}</span>
            </div>
            ${rows}
        </div>`);
    }

    if (!sections.length) {
        el.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="bi bi-inbox fs-2 d-block mb-2 opacity-25"></i>
                <div>No models found. Use Foundry, HuggingFace, llama.cpp or Ollama tabs to add models.</div>
            </div>`;
        return;
    }

    el.innerHTML = sections.join('');
}

// ── Public API ────────────────────────────────────────────────────────────────

/** Main refresh — called on tab open and by app.js on boot */
export async function refreshModels() {
    const activeEl = document.getElementById('models-container');
    const listEl   = document.getElementById('models-list');

    if (activeEl) activeEl.innerHTML = `
        <div class="col-12 text-center py-4">
            <div class="spinner-border spinner-border-sm text-secondary"></div>
        </div>`;
    if (listEl) listEl.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border spinner-border-sm text-secondary"></div>
        </div>`;

    const { active, byProvider } = await _collectAllModels();
    _renderActive(active);
    _renderAvailable(byProvider);
}

/** Load a model into memory */
export async function loadModel(provider, modelId) {
    let res;
    if (provider === 'foundry') {
        res = await _post(`${window.API_BASE}/foundry/models/load`, { model_id: modelId });
    } else if (provider === 'huggingface') {
        res = await _post(`${window.API_BASE}/hf/models/load`, { model_id: modelId, device: 'auto' });
    } else if (provider === 'llama') {
        res = await _post(`${window.API_BASE}/llama/start`, { model_path: modelId, copy_to_models: true });
    } else if (provider === 'ollama') {
        // Ollama manages its own memory — just confirm it's available
        setActiveModel(provider, modelId, `ollama::${modelId}`);
        showAlert(`Ollama model ${modelId} is managed by Ollama service`, 'info');
        return;
    } else {
        showAlert(`Load not supported for provider: ${provider}`, 'warning');
        return;
    }

    if (res.success) {
        setActiveModel(provider, modelId, `${provider === 'huggingface' ? 'hf' : provider}::${modelId}`);
        showAlert(`✅ Loading ${modelId}…`, 'success');
        window.loadModels?.();
        setTimeout(refreshModels, 2000);
    } else {
        showAlert(`❌ ${res.error || 'Load failed'}`, 'danger');
    }
}

/** Unload a model from memory */
export async function unloadModel(provider, modelId) {
    let res;
    if (provider === 'foundry') {
        res = await _post(`${window.API_BASE}/foundry/models/unload`, { model_id: modelId });
    } else if (provider === 'huggingface') {
        res = await _post(`${window.API_BASE}/hf/models/unload`, { model_id: modelId });
    } else if (provider === 'llama') {
        res = await _post(`${window.API_BASE}/llama/stop`);
    } else {
        showAlert(`Unload not supported for provider: ${provider}`, 'warning');
        return;
    }

    if (res.success) {
        if (_activeModel?.id === modelId) _saveActiveModel(null);
        showAlert(`✅ ${modelId} unloaded`, 'success');
        setTimeout(refreshModels, 1000);
    } else {
        showAlert(`❌ ${res.error || 'Unload failed'}`, 'danger');
    }
}

/** Mark a model as the active default for chat */
export function setActiveModel(provider, modelId, prefix) {
    _saveActiveModel({ provider, id: modelId, prefix });

    // Sync chat model selector
    const chatSel = document.getElementById('chat-model');
    if (chatSel) {
        // Try to find existing option
        const existing = [...chatSel.options].find(o => o.value === prefix);
        if (existing) {
            chatSel.value = prefix;
        } else {
            const opt = new Option(prefix, prefix);
            chatSel.appendChild(opt);
            chatSel.value = prefix;
        }
    }

    showAlert(`✅ Active model: ${prefix}`, 'success');
    refreshModels();
    window.refreshModelBanner?.();
}

/** Copy model prefix to clipboard */
export function copyModelPrefix(prefix) {
    navigator.clipboard.writeText(prefix)
        .then(() => showAlert(`✅ Copied: ${prefix}`, 'success'))
        .catch(() => showAlert('Copy failed', 'danger'));
}

/** Expose on window for inline onclick handlers */
window.loadModel       = loadModel;
window.unloadModel     = unloadModel;
window.setActiveModel  = setActiveModel;
window.copyModelPrefix = copyModelPrefix;
window.refreshModels   = refreshModels;

// ── Populate chat-model select ────────────────────────────────────────────────

/**
 * Populate the #chat-model select with all available models from all providers.
 * Called on boot and whenever a model is loaded/unloaded.
 *
 * Groups:
 *   - Foundry cached models  → value "foundry::id"
 *   - HuggingFace downloaded → value "hf::id"
 *   - llama.cpp GGUF files   → value "llama::path"
 *   - Ollama models          → value "ollama::name"
 */
export async function loadModels() {
    const sel = document.getElementById('chat-model');
    if (!sel) return;
    if (!sel.dataset.activeModelListener) {
        sel.addEventListener('change', () => {
            const model = _modelFromPrefix(sel.value);
            if (model) {
                _saveActiveModel(model);
                refreshModels();
                window.refreshModelBanner?.();
            }
        });
        sel.dataset.activeModelListener = '1';
    }

    const prev = sel.value;

    // Fetch all sources in parallel
    const [foundryCached, hfData, llamaStatus, llamaDisk, ollamaData] = await Promise.allSettled([
        fetch(`${window.API_BASE}/foundry/models/cached`).then(r => r.json()),
        fetch(`${window.API_BASE}/hf/models`).then(r => r.json()),
        fetch(`${window.API_BASE}/llama/status`).then(r => r.json()),
        fetch(`${window.API_BASE}/llama/models`).then(r => r.json()),
        fetch(`${window.API_BASE}/ollama/models`).then(r => r.json()),
    ]).then(results => results.map(r => r.status === 'fulfilled' ? r.value : { success: false }));

    // Rebuild select — keep the empty "auto" option
    sel.innerHTML = '<option value="" data-i18n="chat.model_auto">Auto-select</option>';

    // ── Foundry ──────────────────────────────────────────────────────────────
    const foundryModels = foundryCached.success ? (foundryCached.items || []) : [];
    if (foundryModels.length) {
        const grp = document.createElement('optgroup');
        grp.label = '— Microsoft Foundry (cached) —';
        foundryModels.forEach(m => {
            const id = m.id;
            const opt = new Option(m.name || m.alias || id, `foundry::${id}`);
            grp.appendChild(opt);
        });
        sel.appendChild(grp);
    }

    // ── HuggingFace ───────────────────────────────────────────────────────────
    // Show downloaded models (not just loaded) — user can load on demand
    const hfDownloaded = hfData.success ? (hfData.downloaded || []) : [];
    const hfLoaded     = new Set((hfData.success ? (hfData.loaded || []) : []).map(m => m.id));
    if (hfDownloaded.length) {
        const grp = document.createElement('optgroup');
        grp.label = '— HuggingFace (local) —';
        hfDownloaded.forEach(m => {
            const label = m.id + (hfLoaded.has(m.id) ? ' ✓' : '');
            const opt = new Option(label, `hf::${m.id}`);
            opt.dataset.hf = '1';
            grp.appendChild(opt);
        });
        sel.appendChild(grp);
    }

    // ── llama.cpp ─────────────────────────────────────────────────────────────
    const llamaModels = llamaDisk.success ? (llamaDisk.models || []) : [];
    if (llamaModels.length || (llamaStatus.success && llamaStatus.loading)) {
        const grp = document.createElement('optgroup');
        grp.label = '— llama.cpp —';
        if (llamaModels.length) {
            llamaModels.forEach(m => {
                const id = m.path || m.name;
                const opt = new Option(m.name || id, `llama::${id}`);
                grp.appendChild(opt);
            });
        } else {
            grp.appendChild(new Option('llama.cpp (loading…)', 'llama::llama-server'));
        }
        sel.appendChild(grp);
    }

    // ── Ollama ────────────────────────────────────────────────────────────────
    const ollamaModels = ollamaData.success ? (ollamaData.models || []) : [];
    if (ollamaModels.length) {
        const grp = document.createElement('optgroup');
        grp.label = '— Ollama —';
        ollamaModels.forEach(m => {
            const id = m.name || m.id;
            const opt = new Option(id, `ollama::${id}`);
            grp.appendChild(opt);
        });
        sel.appendChild(grp);
    }

    // Restore previous selection if still available
    const savedModel = prev || window._savedChatModel || _activeModel?.prefix || '';
    if (savedModel) {
        const exists = [...sel.options].some(o => o.value === savedModel);
        if (exists) sel.value = savedModel;
    }
}

// Expose loadModels globally — called by foundry.js, llama.js etc.
window.loadModels = loadModels;
