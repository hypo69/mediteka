// -*- coding: utf-8 -*-
// =============================================================================
// Process Name: API Keys / Providers tab — manage LLM provider keys
// =============================================================================
// Description:
//   Web app UI for managing provider API keys.
//   Keys are stored in .env via /api/v1/config/provider-keys.
//   Supports export/import using the shared ai-assistant-config format.
//
//   Key names (labels) are UI-only metadata stored in memory and in the
//   export file under the optional "keyNames" field. Default name: "Default".
//   The "Load models" button has been removed — model selection is handled
//   by the extension, not the web app.
//
// File: js/providers.js
// Project: AI Assistant (ai_assist)
// Version: 0.7.1
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

import {
    PROVIDERS,
    CONFIG_SCHEMA_NAME,
    CONFIG_SCHEMA_VERSION,
    validateConfigFile,
    normalizeProviderKeys,
} from './providers-registry.js';

// ── State ─────────────────────────────────────────────────────────────────────

// Active provider (in-memory, cosmetic — not persisted to server)
let _activeProvider = null;

// Key names: { [providerId]: string } — UI-only, persisted via export/import
let _keyNames = {};

// ── Helpers ───────────────────────────────────────────────────────────────────

function maskKey(k) {
    if (!k) return '••••••••';
    return k.length > 8 ? k.slice(0, 4) + '…' + k.slice(-4) : '••••••••';
}

function showStatus(el, msg, cls) {
    el.textContent = msg;
    el.className = `small ${cls}`;
    setTimeout(() => { el.textContent = ''; el.className = 'small'; }, 3000);
}

// ── Server API ────────────────────────────────────────────────────────────────

async function loadProviderKeys() {
    try {
        const res = await fetch(`${window.API_BASE}/config/provider-keys`).then(r => r.json());
        return res.success ? res.keys : {};
    } catch { return {}; }
}

async function saveProviderKey(provider, value) {
    return fetch(`${window.API_BASE}/config/provider-keys`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ keys: { [provider]: value } }),
    }).then(r => r.json());
}

// ── Provider card ─────────────────────────────────────────────────────────────

function buildProviderCard(providerId, cfg, currentKey, customUrl) {
    const hasKey   = !!currentKey;
    const isActive = _activeProvider === providerId;
    const keyName  = _keyNames[providerId] || 'Default';

    const card = document.createElement('div');
    card.className = 'card mb-3 provider-card';
    card.dataset.provider = providerId;

    card.innerHTML = `
        <div class="card-header provider-card-header d-flex align-items-center gap-2"
             style="cursor:pointer;user-select:none">
            <span class="fw-semibold small flex-grow-1">${cfg.label}</span>
            <span class="provider-badge badge ${isActive ? 'bg-success' : 'bg-secondary'}">
                ${isActive ? 'Активен' : 'Не активен'}
            </span>
            <span class="chevron" style="font-size:11px;color:#adb5bd;transition:transform .2s${hasKey || isActive ? ';transform:rotate(180deg)' : ''}">▼</span>
        </div>
        <div class="card-body provider-card-body" style="display:${hasKey || isActive ? '' : 'none'}">
            <div class="form-label small mb-2">
                API ключи${cfg.hint ? ` — <a href="https://${cfg.hint}" target="_blank" class="text-primary">${cfg.hint}</a>` : ''}
            </div>
            <div class="keys-list mb-2"></div>
            <div class="input-group input-group-sm add-key-row">
                <input type="password" class="form-control new-key-input" placeholder="${cfg.placeholder}">
                <button class="btn btn-outline-secondary btn-sm toggle-new-key" type="button">👁</button>
                <button class="btn btn-outline-secondary add-key-btn" type="button">+ Добавить ключ</button>
            </div>
            ${providerId === 'custom' ? `
                <label class="form-label small mt-3 mb-1">Базовый URL</label>
                <input type="text" class="form-control form-control-sm url-input"
                    placeholder="http://localhost:9696/v1"
                    value="${customUrl || 'http://localhost:9696/v1'}">
                <div class="url-status small mt-1"></div>
            ` : ''}
        </div>
    `;

    const header   = card.querySelector('.provider-card-header');
    const body     = card.querySelector('.provider-card-body');
    const chevron  = card.querySelector('.chevron');
    const badge    = card.querySelector('.provider-badge');
    const keysList = card.querySelector('.keys-list');
    const newInput = card.querySelector('.new-key-input');

    // Toggle card open/close
    header.addEventListener('click', () => {
        const open = body.style.display !== 'none';
        body.style.display = open ? 'none' : '';
        chevron.style.transform = open ? '' : 'rotate(180deg)';
    });

    // Show/hide API key value
    card.querySelector('.toggle-new-key').addEventListener('click', () => {
        newInput.type = newInput.type === 'password' ? 'text' : 'password';
    });

    // Custom provider: save URL on blur
    if (providerId === 'custom') {
        const urlInput  = card.querySelector('.url-input');
        const urlStatus = card.querySelector('.url-status');
        urlInput.addEventListener('blur', async () => {
            const res = await saveProviderKey('custom_url', urlInput.value.trim());
            if (res.success) showStatus(urlStatus, '✓ Сохранено', 'text-success');
        });
    }

    // Keys state: array of { value, name }
    const keysState = currentKey ? [{ value: currentKey, name: keyName }] : [];

    function markAllInactive() {
        document.querySelectorAll('.provider-card .provider-badge').forEach(b => {
            b.className = 'provider-badge badge bg-secondary';
            b.textContent = 'Не активен';
        });
    }

    function renderKeys() {
        keysList.innerHTML = '';
        keysState.forEach((entry, i) => {
            const isThisActive = _activeProvider === providerId && i === 0;
            const block = document.createElement('div');
            block.className = 'mb-2';

            block.innerHTML = `
                <div class="key-item d-flex align-items-center gap-2 p-2 border rounded
                     ${isThisActive ? 'border-primary bg-light' : ''}" style="font-size:13px">
                    <input type="text" class="form-control form-control-sm key-name-input"
                           value="${entry.name || 'Default'}"
                           placeholder="Default"
                           style="max-width:120px;font-size:12px"
                           title="Key name">
                    <span class="key-masked text-muted font-monospace"
                          style="font-size:11px;flex-shrink:0">${maskKey(entry.value)}</span>
                    <button class="btn btn-primary btn-sm set-active-btn ms-auto"
                            style="white-space:nowrap"
                            ${isThisActive ? 'disabled' : ''}>
                        ${isThisActive ? 'Активен' : 'Сделать активным'}
                    </button>
                    <button class="btn btn-outline-danger btn-sm remove-key-btn">✕</button>
                </div>
            `;

            const keyItem      = block.querySelector('.key-item');
            const nameInput    = block.querySelector('.key-name-input');
            const setActiveBtn = block.querySelector('.set-active-btn');

            // Persist key name on blur; stop click from toggling card
            nameInput.addEventListener('blur', () => {
                entry.name = nameInput.value.trim() || 'Default';
                _keyNames[providerId] = entry.name;
            });
            nameInput.addEventListener('click', e => e.stopPropagation());

            setActiveBtn.addEventListener('click', () => {
                _activeProvider = providerId;
                markAllInactive();
                badge.className = 'provider-badge badge bg-success';
                badge.textContent = 'Активен';
                keyItem.classList.add('border-primary', 'bg-light');
                setActiveBtn.disabled = true;
                setActiveBtn.textContent = 'Активен';
            });

            block.querySelector('.remove-key-btn').addEventListener('click', async () => {
                keysState.splice(i, 1);
                await saveProviderKey(providerId, keysState.length ? keysState[0].value : '');
                renderKeys();
                if (!keysState.length) body.style.display = 'none';
            });

            keysList.appendChild(block);
        });
    }

    renderKeys();

    card.querySelector('.add-key-btn').addEventListener('click', async () => {
        const val = newInput.value.trim();
        if (!val) return;
        keysState.push({ value: val, name: 'Default' });
        await saveProviderKey(providerId, val);
        newInput.value = '';
        body.style.display = '';
        chevron.style.transform = 'rotate(180deg)';
        renderKeys();
    });

    return card;
}

// ── Local server API key ────────────────────────────────────────────────────

/**
 * Load current API key status from the server and update the UI.
 * Called on tab open and after generate/remove actions.
 *
 * Returns:
 *   void
 */
async function _localApiKeyRefresh() {
    const badge   = document.getElementById('local-api-key-status-badge');
    const preview = document.getElementById('local-api-key-preview');
    const input   = document.getElementById('local-api-key-value');
    const removeBtn = document.getElementById('local-api-key-remove-btn');

    try {
        const res = await fetch(`${window.API_BASE}/security/api-key/status`).then(r => r.json());
        if (res.configured) {
            if (badge)  { badge.className = 'badge bg-success'; badge.textContent = 'Active'; }
            if (preview) preview.style.display = '';
            if (removeBtn) removeBtn.style.display = '';
            // Show masked preview — actual value only shown after generate
            if (input && !input.dataset.plaintext) input.value = res.preview || '••••••••••••••••';
        } else {
            if (badge)  { badge.className = 'badge bg-secondary'; badge.textContent = 'Not set'; }
            if (preview) preview.style.display = 'none';
            if (removeBtn) removeBtn.style.display = 'none';
        }
    } catch {
        if (badge) { badge.className = 'badge bg-danger'; badge.textContent = 'Error'; }
    }
}

/**
 * Generate a new server API key and display it in plain text once.
 *
 * Returns:
 *   void
 */
export async function localApiKeyGenerate() {
    const msg   = document.getElementById('local-api-key-msg');
    const input = document.getElementById('local-api-key-value');
    const eye   = document.getElementById('local-api-key-eye');

    if (msg) { msg.textContent = 'Generating…'; msg.className = 'small text-muted'; }

    try {
        const res = await fetch(`${window.API_BASE}/security/api-key/generate`, { method: 'POST' })
            .then(r => r.json());

        if (res.success) {
            // Show the new key in plain text — user must copy it now
            if (input) {
                input.value = res.api_key;
                input.type  = 'text';
                input.dataset.plaintext = '1';
                if (eye) eye.className = 'bi bi-eye-slash';
            }
            if (msg) {
                msg.textContent = '✅ Key generated. Copy it now — it will be masked after reload.';
                msg.className = 'small text-success';
            }
            await _localApiKeyRefresh();
        } else {
            if (msg) { msg.textContent = `❌ ${res.error}`; msg.className = 'small text-danger'; }
        }
    } catch (e) {
        if (msg) { msg.textContent = `❌ ${e.message}`; msg.className = 'small text-danger'; }
    }
}

/**
 * Remove the server API key (disables protection).
 *
 * Returns:
 *   void
 */
export async function localApiKeyRemove() {
    if (!confirm('Remove the API key? This will disable key-based protection.')) return;
    const msg = document.getElementById('local-api-key-msg');
    const input = document.getElementById('local-api-key-value');
    try {
        const res = await fetch(`${window.API_BASE}/security/api-key`, { method: 'DELETE' })
            .then(r => r.json());
        if (res.success) {
            if (input) { input.value = ''; delete input.dataset.plaintext; }
            if (msg) { msg.textContent = '✅ Key removed.'; msg.className = 'small text-success'; }
            await _localApiKeyRefresh();
        } else {
            if (msg) { msg.textContent = `❌ ${res.error}`; msg.className = 'small text-danger'; }
        }
    } catch (e) {
        if (msg) { msg.textContent = `❌ ${e.message}`; msg.className = 'small text-danger'; }
    }
}

/** Toggle visibility of the local API key input field. */
export function localApiKeyToggleVisibility() {
    const input = document.getElementById('local-api-key-value');
    const eye   = document.getElementById('local-api-key-eye');
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
    if (eye) eye.className = input.type === 'password' ? 'bi bi-eye' : 'bi bi-eye-slash';
}

/** Copy local API key value to clipboard. */
export function localApiKeyCopy() {
    const input = document.getElementById('local-api-key-value');
    if (!input?.value) return;
    navigator.clipboard.writeText(input.value)
        .then(() => {
            const msg = document.getElementById('local-api-key-msg');
            if (msg) { msg.textContent = '✅ Copied to clipboard.'; msg.className = 'small text-success'; }
        })
        .catch(() => {});
}

// Expose for inline onclick handlers
window.localApiKeyGenerate         = localApiKeyGenerate;
window.localApiKeyRemove           = localApiKeyRemove;
window.localApiKeyToggleVisibility = localApiKeyToggleVisibility;
window.localApiKeyCopy             = localApiKeyCopy;

// ── Render all cards ──────────────────────────────────────────────────────────

export async function initProviders() {
    const list = document.getElementById('providers-list');
    if (!list) return;

    list.innerHTML = '<div class="text-muted text-center p-3"><small>Загрузка…</small></div>';

    // Load local server key status in parallel with provider keys
    const [keys] = await Promise.all([
        loadProviderKeys(),
        _localApiKeyRefresh(),
    ]);
    list.innerHTML = '';

    for (const [id, cfg] of Object.entries(PROVIDERS)) {
        list.appendChild(buildProviderCard(id, cfg, keys[id] || '', keys['custom_url'] || ''));
    }
}

// ── Export to shared format ───────────────────────────────────────────────────

export async function exportToExtension() {
    const confirmed = confirm(
        '⚠️ Предупреждение безопасности\n\n' +
        'Экспортируемый файл будет содержать ВСЕ ваши API ключи в открытом виде.\n\n' +
        'Не передавайте этот файл третьим лицам и не загружайте в облако.\n\nПродолжить?'
    );
    if (!confirmed) return;

    const res = await fetch(`${window.API_BASE}/config/extension-export`).then(r => r.json());
    if (!res.success) { alert('Export failed'); return; }

    const payload = {
        schema:         CONFIG_SCHEMA_NAME,
        version:        CONFIG_SCHEMA_VERSION,
        exportedAt:     new Date().toISOString(),
        exportedFrom:   'app',
        providerKeys:   res.providerKeys   || {},
        customModels:   res.customModels   || {},
        activeProvider: res.activeProvider || null,
        activeModel:    res.activeModel    || null,
        // keyNames is an optional v2 extension — ignored by older clients
        keyNames: Object.keys(_keyNames).length ? _keyNames : undefined,
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), {
        href:     url,
        download: `ai-assistant-config-${new Date().toISOString().slice(0, 10)}.json`,
    });
    a.click();
    URL.revokeObjectURL(url);
}

// ── Import from shared format ─────────────────────────────────────────────────

export async function importFromExtension(file) {
    let cfg;
    try { cfg = JSON.parse(await file.text()); }
    catch { alert('✗ Неверный JSON файл'); return; }

    const isLegacyV1 = cfg.version === 1 && typeof cfg.providerKeys === 'object' && !cfg.schema;
    const err = isLegacyV1 ? null : validateConfigFile(cfg);
    if (err) { alert(`✗ Неизвестный формат: ${err}`); return; }

    const confirmed = confirm(
        `Импортировать ключи?\n\nЭкспортировано: ${cfg.exportedAt || 'неизвестно'}\n` +
        `Источник: ${cfg.exportedFrom || 'неизвестно'}\n\nКлючи будут записаны в .env.`
    );
    if (!confirmed) return;

    // Restore key names if present
    if (cfg.keyNames && typeof cfg.keyNames === 'object') {
        Object.assign(_keyNames, cfg.keyNames);
    }

    const normalizedKeys = normalizeProviderKeys(cfg.providerKeys);

    const res = await fetch(`${window.API_BASE}/config/extension-import`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
            providerKeys:   normalizedKeys,
            customModels:   cfg.customModels   || {},
            activeProvider: cfg.activeProvider || null,
            activeModel:    cfg.activeModel    || null,
        }),
    }).then(r => r.json());

    if (res.success) {
        alert(`✓ Импортированы ключи для: ${res.imported.join(', ') || 'нет'}`);
        await initProviders();
    } else {
        alert('✗ Ошибка импорта');
    }
}
