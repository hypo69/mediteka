// -*- coding: utf-8 -*-
// =============================================================================
// Process Name: Providers & Models page
// =============================================================================
// Description:
//   Страница настройки провайдеров AI.
//   Таб 1 — список всех провайдеров с API ключами и моделями.
//   Таб 2 — настройки суммаризатора (язык, провайдер, модель).
//
// File: providers-page.js
// Project: AI Assistant (ai_assist)
// Version: 0.8.0
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

import { PROVIDERS, CONFIG_SCHEMA_NAME, CONFIG_SCHEMA_VERSION,
         validateConfigFile, wrapProviderKeysAsArrays, normalizeProviderKeys } from './providers-registry.js';
import { LANGUAGES } from './prompts/index.js';
import { initI18n, t } from './js/i18n.js';

// ── Состояние ─────────────────────────────────────────────────────────────────

let syncData = {
    providerKeys:   {},   // { [providerId]: string[] }
    activeKeyIndex: {},   // { [providerId]: number }
    providerModels: {},   // { [providerId]: [{id,label}] }  — в local storage
    customModels:   {},   // { [providerId]: [{id,label}] }  — вручную добавленные
    activeProvider: null,
    activeModel:    null,
    summaryLang:    'auto',
    summaryProvider: '',
    summaryModel:    '',
};

// ── Tabs ──────────────────────────────────────────────────────────────────────

document.querySelectorAll('.ext-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.ext-tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
        btn.classList.add('active');
        document.getElementById(`tab-${btn.dataset.tab}`).style.display = '';
    });
});

// ── Persist helpers ───────────────────────────────────────────────────────────

async function saveSync(patch) {
    Object.assign(syncData, patch);
    await chrome.storage.sync.set(patch);
}

async function saveLocal(patch) {
    await chrome.storage.local.set(patch);
}

// ── Provider list render ──────────────────────────────────────────────────────

function maskedKey(key) {
    if (!key || key.length < 8) return '••••••••';
    return key.slice(0, 4) + '••••' + key.slice(-4);
}

function renderProviders() {
    const container = document.getElementById('provider-list');
    container.innerHTML = '';

    for (const [providerId, cfg] of Object.entries(PROVIDERS)) {
        const keys      = syncData.providerKeys[providerId] || [];
        const keyArr    = Array.isArray(keys) ? keys : (keys ? [keys] : []);
        const activeIdx = syncData.activeKeyIndex[providerId] ?? 0;
        const models    = [
            ...(syncData.providerModels[providerId] || []),
            ...(syncData.customModels[providerId]   || []),
        ];
        const isActive  = syncData.activeProvider === providerId;

        const card = document.createElement('div');
        card.className = 'card mb-2';
        card.innerHTML = `
            <div class="card-header provider-card-header d-flex align-items-center gap-2"
                 data-provider="${providerId}">
                <span class="fw-semibold small flex-grow-1">${cfg.label}</span>
                ${isActive ? `<span class="badge bg-primary">${t('providers.active')}</span>` : ''}
                <span class="chevron">▼</span>
            </div>
            <div class="card-body p-2 provider-body" id="body-${providerId}" style="display:none">

                <!-- Keys -->
                <div class="small fw-semibold mb-1">${t('providers.api_keys')}</div>
                <div class="keys-list" id="keys-${providerId}"></div>
                <div class="add-key-row">
                    <input type="password" class="form-control form-control-sm new-key-input"
                           placeholder="${cfg.placeholder || 'API key…'}" data-provider="${providerId}">
                    <button class="btn btn-sm btn-outline-secondary add-key-btn"
                            data-provider="${providerId}">${t('providers.add_key')}</button>
                </div>
                ${cfg.hint ? `<div class="form-text mt-1">🔑 <a href="https://${cfg.hint}" target="_blank">${cfg.hint}</a></div>` : ''}
                ${providerId === 'custom' || providerId === 'ai_assist' ? `
                <div class="mt-2">
                    <label class="form-label small mb-1">${t('providers.base_url')}</label>
                    <input type="text" class="form-control form-control-sm custom-url-input"
                           value="${syncData.providerKeys['custom_url'] || (providerId === 'ai_assist' ? 'http://localhost:9696' : '')}"
                           placeholder="http://localhost:9696">
                </div>` : ''}

                <!-- Models -->
                <div class="d-flex align-items-center gap-2 mt-2 mb-1">
                    <span class="small fw-semibold flex-grow-1">Models</span>
                    <button class="btn btn-sm btn-outline-secondary load-models-btn"
                            data-provider="${providerId}">${t('providers.load_models')}</button>
                    <button class="btn btn-sm btn-outline-secondary set-active-btn"
                            data-provider="${providerId}">${isActive ? t('providers.active') : t('providers.set_active')}</button>
                </div>
                <div class="model-list" id="models-${providerId}"></div>
                <div class="add-model-row">
                    <input type="text" class="form-control form-control-sm new-model-input"
                           placeholder="${t('providers.add_model_placeholder')}" data-provider="${providerId}">
                    <button class="btn btn-sm btn-outline-secondary add-model-btn"
                            data-provider="${providerId}">${t('providers.add_model')}</button>
                </div>
            </div>
        `;
        container.appendChild(card);

        // Render keys
        renderKeys(providerId, keyArr, activeIdx);
        // Render models
        renderModels(providerId, models);
    }

    bindProviderEvents();
}

function renderKeys(providerId, keyArr, activeIdx) {
    const container = document.getElementById(`keys-${providerId}`);
    if (!container) return;
    container.innerHTML = keyArr.map((key, idx) => `
        <div class="key-item ${idx === activeIdx ? 'key-active' : ''}" data-provider="${providerId}" data-idx="${idx}">
            <span class="key-masked">${maskedKey(key)}</span>
            <span class="key-chosen-model ${!syncData.activeModel ? 'key-no-model' : ''}">
                ${idx === activeIdx && syncData.activeModel ? syncData.activeModel : ''}
            </span>
            <button class="btn btn-xs btn-outline-secondary use-key-btn" data-provider="${providerId}" data-idx="${idx}">use</button>
            <button class="btn btn-xs btn-outline-danger del-key-btn" data-provider="${providerId}" data-idx="${idx}">✕</button>
        </div>
    `).join('');
}

function renderModels(providerId, models) {
    const container = document.getElementById(`models-${providerId}`);
    if (!container) return;
    const selected     = syncData.selectedModels || [];
    const defaultModel = syncData.defaultModel || '';
    container.innerHTML = models.map(m => {
        const key       = `${providerId}|${m.id}`;
        const isSelected = selected.find(s => s.providerId === providerId && s.modelId === m.id);
        const isDefault  = defaultModel === key;
        return `
        <div class="model-item ${isSelected ? 'selected' : ''}" data-provider="${providerId}" data-model="${m.id}">
            <span class="model-label">${m.label || m.id}</span>
            ${isSelected ? `<span class="badge bg-success" style="font-size:10px">✓ added</span>` : ''}
            ${isDefault  ? `<span class="badge bg-primary" style="font-size:10px">★ default</span>` : ''}
            ${isSelected && !isDefault ? `<button class="btn btn-xs btn-outline-primary set-default-btn" data-key="${key}" style="font-size:10px;padding:1px 5px">★ set default</button>` : ''}
            <span class="model-remove" data-provider="${providerId}" data-model="${m.id}">✕</span>
        </div>`;
    }).join('');

    // Кнопка set default
    container.querySelectorAll('.set-default-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            await saveSync({ defaultModel: btn.dataset.key });
            renderModels(providerId, models);
        });
    });
}

// ── Provider events ───────────────────────────────────────────────────────────

function bindProviderEvents() {
    // Toggle card — только по клику на chevron
    document.querySelectorAll('.chevron').forEach(chevron => {
        chevron.addEventListener('click', (e) => {
            e.stopPropagation();
            const header     = chevron.closest('.provider-card-header');
            const providerId = header.dataset.provider;
            const body       = document.getElementById(`body-${providerId}`);
            const open       = body.style.display !== 'none';
            body.style.display = open ? 'none' : '';
            chevron.classList.toggle('open', !open);
        });
    });

    // Add key
    document.querySelectorAll('.add-key-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const providerId = btn.dataset.provider;
            const input = document.querySelector(`.new-key-input[data-provider="${providerId}"]`);
            const key   = input.value.trim();
            if (!key) return;
            const keys = [...(syncData.providerKeys[providerId] || []), key];
            await saveSync({ providerKeys: { ...syncData.providerKeys, [providerId]: keys } });
            input.value = '';
            renderProviders();
        });
    });

    // Delete key
    document.querySelectorAll('.del-key-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const { provider, idx } = btn.dataset;
            const keys = [...(syncData.providerKeys[provider] || [])];
            keys.splice(Number(idx), 1);
            await saveSync({ providerKeys: { ...syncData.providerKeys, [provider]: keys } });
            renderProviders();
        });
    });

    // Use key
    document.querySelectorAll('.use-key-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const { provider, idx } = btn.dataset;
            await saveSync({ activeKeyIndex: { ...syncData.activeKeyIndex, [provider]: Number(idx) } });
            renderProviders();
        });
    });

    // Load models
    document.querySelectorAll('.load-models-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const providerId = btn.dataset.provider;
            const cfg        = PROVIDERS[providerId];
            const keys       = syncData.providerKeys[providerId] || [];
            const keyArr     = Array.isArray(keys) ? keys : (keys ? [keys] : []);
            const activeIdx  = syncData.activeKeyIndex[providerId] ?? 0;
            const apiKey     = keyArr[activeIdx] || '';
            const customUrl  = document.querySelector(`.custom-url-input`)?.value || syncData.providerKeys['custom_url'] || '';

            btn.disabled = true;
            btn.textContent = t('providers.loading_models');
            try {
                const models = await cfg.fetchModels(apiKey, { customUrl });
                const updated = { ...syncData.providerModels, [providerId]: models };
                syncData.providerModels = updated;
                await saveLocal({ providerModels: updated });
                renderModels(providerId, [
                    ...models,
                    ...(syncData.customModels[providerId] || [])
                ]);
                btn.textContent = `✅ ${models.length} ${t('providers.models_loaded')}`;
            } catch (ex) {
                btn.textContent = `❌ ${ex.message}`;
            } finally {
                btn.disabled = false;
                setTimeout(() => { btn.textContent = t('providers.load_models'); }, 3000);
            }
        });
    });

    // Set active provider
    document.querySelectorAll('.set-active-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const providerId = btn.dataset.provider;
            await saveSync({ activeProvider: providerId });
            renderProviders();
        });
    });

    // Select model — привязываем модель к провайдеру и добавляем в selectedModels
    document.querySelectorAll('.model-item').forEach(item => {
        item.addEventListener('click', async (e) => {
            if (e.target.classList.contains('model-remove')) return;
            const { provider, model } = item.dataset;
            const cfg     = PROVIDERS[provider];
            const keys    = syncData.providerKeys[provider] || [];
            const keyArr  = Array.isArray(keys) ? keys : (keys ? [keys] : []);
            const keyIdx  = syncData.activeKeyIndex[provider] ?? 0;
            const apiKey  = keyArr[keyIdx] || '';
            const customUrl = syncData.providerKeys['custom_url'] || '';

            // Добавляем в selectedModels если ещё нет
            const selected = syncData.selectedModels || [];
            const exists   = selected.find(m => m.modelId === model && m.providerId === provider);
            if (!exists) {
                selected.push({ providerId: provider, modelId: model, label: `${cfg.label} · ${model}`, apiKey, customUrl, keyIdx });
            }

            // Если это первая модель — ставим дефолтной
            const defaultModel = syncData.defaultModel || (selected.length === 1 ? `${provider}|${model}` : syncData.defaultModel);

            await saveSync({
                activeProvider: provider,
                activeModel:    model,
                selectedModels: selected,
                defaultModel
            });
            renderModels(provider, [
                ...(syncData.providerModels[provider] || []),
                ...(syncData.customModels[provider]   || [])
            ]);
        });
    });

    // Remove model
    document.querySelectorAll('.model-remove').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const { provider, model } = btn.dataset;
            const custom   = (syncData.customModels[provider]   || []).filter(m => m.id !== model);
            const fetched  = (syncData.providerModels[provider] || []).filter(m => m.id !== model);
            const selected = (syncData.selectedModels || []).filter(m => !(m.providerId === provider && m.modelId === model));
            const key      = `${provider}|${model}`;
            const defaultModel = syncData.defaultModel === key ? (selected[0] ? `${selected[0].providerId}|${selected[0].modelId}` : '') : syncData.defaultModel;

            syncData.customModels[provider]   = custom;
            syncData.providerModels[provider] = fetched;
            await saveSync({ customModels: syncData.customModels, selectedModels: selected, defaultModel });
            await saveLocal({ providerModels: syncData.providerModels });
            renderModels(provider, [...fetched, ...custom]);
        });
    });

    // Add model manually
    document.querySelectorAll('.add-model-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const providerId = btn.dataset.provider;
            const input = document.querySelector(`.new-model-input[data-provider="${providerId}"]`);
            const id    = input.value.trim();
            if (!id) return;
            const custom  = [...(syncData.customModels[providerId] || []), { id, label: id }];
            await saveSync({ customModels: { ...syncData.customModels, [providerId]: custom } });
            input.value = '';
            renderModels(providerId, [
                ...(syncData.providerModels[providerId] || []),
                ...custom
            ]);
        });
    });

    // Save custom URL
    document.querySelectorAll('.custom-url-input').forEach(input => {
        input.addEventListener('change', async () => {
            await saveSync({ providerKeys: { ...syncData.providerKeys, custom_url: input.value.trim() } });
        });
    });
}

// ── Summarizer tab ────────────────────────────────────────────────────────────

function renderSummarizerTab() {
    // Language
    const langSelect = document.getElementById('summary-lang');
    langSelect.innerHTML = LANGUAGES
        .map(l => `<option value="${l.value}"${l.value === syncData.summaryLang ? ' selected' : ''}>${l.label}</option>`)
        .join('');
    langSelect.addEventListener('change', () => saveSync({ summaryLang: langSelect.value }));

    // Summary provider
    const provSelect = document.getElementById('summary-provider');
    provSelect.innerHTML = `<option value="">${t('providers.use_active_provider')}</option>` +
        Object.entries(PROVIDERS).map(([id, cfg]) =>
            `<option value="${id}"${id === syncData.summaryProvider ? ' selected' : ''}>${cfg.label}</option>`
        ).join('');
    provSelect.addEventListener('change', () => {
        saveSync({ summaryProvider: provSelect.value, summaryModel: '' });
        renderSummaryModelSelect(provSelect.value);
    });

    renderSummaryModelSelect(syncData.summaryProvider);
}

function renderSummaryModelSelect(providerId) {
    const modelSelect = document.getElementById('summary-model');
    const models = providerId
        ? [...(syncData.providerModels[providerId] || []), ...(syncData.customModels[providerId] || [])]
        : [];

    modelSelect.innerHTML = `<option value="">${t('providers.use_active_model')}</option>` +
        models.map(m =>
            `<option value="${m.id}"${m.id === syncData.summaryModel ? ' selected' : ''}>${m.label || m.id}</option>`
        ).join('');
    modelSelect.addEventListener('change', () => saveSync({ summaryModel: modelSelect.value }));
}

// ── Export / Import ───────────────────────────────────────────────────────────

document.getElementById('export-btn').addEventListener('click', () => {
    const payload = {
        schema:         CONFIG_SCHEMA_NAME,
        version:        CONFIG_SCHEMA_VERSION,
        exportedAt:     new Date().toISOString(),
        exportedFrom:   'extension',
        providerKeys:   normalizeProviderKeys(syncData.providerKeys),
        customModels:   syncData.customModels,
        activeProvider: syncData.activeProvider,
        activeModel:    syncData.activeModel,
        activeKeyIndex: syncData.activeKeyIndex,
        providerModels: syncData.providerModels,
        summaryLang:    syncData.summaryLang,
        summaryProvider: syncData.summaryProvider,
        summaryModel:   syncData.summaryModel,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = `ai-assistant-config-${Date.now()}.json`;
    a.click();
});

document.getElementById('import-btn').addEventListener('click', () => {
    document.getElementById('import-file').click();
});

document.getElementById('import-file').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
        const text = await file.text();
        const obj  = JSON.parse(text);
        const err  = validateConfigFile(obj);
        if (err) throw new Error(err);

        const wrapped = wrapProviderKeysAsArrays(obj.providerKeys || {});
        await saveSync({
            providerKeys:    wrapped,
            customModels:    obj.customModels   || {},
            activeProvider:  obj.activeProvider || null,
            activeModel:     obj.activeModel    || null,
            activeKeyIndex:  obj.activeKeyIndex || {},
            summaryLang:     obj.summaryLang    || 'auto',
            summaryProvider: obj.summaryProvider || '',
            summaryModel:    obj.summaryModel   || '',
        });
        if (obj.providerModels) {
            syncData.providerModels = obj.providerModels;
            await saveLocal({ providerModels: obj.providerModels });
        }
        renderProviders();
        renderSummarizerTab();
    } catch (ex) {
        alert(`Import failed: ${ex.message}`);
    }
    e.target.value = '';
});

// ── Init ──────────────────────────────────────────────────────────────────────

async function init() {
    await initI18n();

    const [sync, local] = await Promise.all([
        chrome.storage.sync.get([
            'providerKeys', 'activeKeyIndex', 'customModels',
            'activeProvider', 'activeModel',
            'selectedModels', 'defaultModel',
            'summaryLang', 'summaryProvider', 'summaryModel'
        ]),
        chrome.storage.local.get(['providerModels'])
    ]);

    syncData = {
        providerKeys:    sync.providerKeys    || {},
        activeKeyIndex:  sync.activeKeyIndex  || {},
        customModels:    sync.customModels    || {},
        activeProvider:  sync.activeProvider  || null,
        activeModel:     sync.activeModel     || null,
        selectedModels:  sync.selectedModels  || [],
        defaultModel:    sync.defaultModel    || '',
        summaryLang:     sync.summaryLang     || 'auto',
        summaryProvider: sync.summaryProvider || '',
        summaryModel:    sync.summaryModel    || '',
        providerModels:  local.providerModels || {},
    };

    renderProviders();
    renderSummarizerTab();
}

init();
