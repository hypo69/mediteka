// -*- coding: utf-8 -*-
// =============================================================================
// Process Name: Main web interface bootstrap for FastAPI Foundry
// =============================================================================
// Description:
//   Loads all partials, initializes i18n, connects to backend services.
//   Entry point for the SPA — imported as ES module from index.html.
//
// File: app.js
// Project: AI Assistant (ai_assist)
// Version: 0.8.0
// =============================================================================

import * as ui        from './js/ui.js';
import * as config    from './js/config.js';
import * as models    from './js/models.js?v=0.7.7';
import * as chat      from './js/chat.js';
import * as foundry   from './js/foundry.js';
import * as rag       from './js/rag.js';
import * as editor    from './js/editor.js';
import * as llama     from './js/llama.js';
import * as hf        from './js/hf.js';
import * as ollama    from './js/ollama.js';
import * as agent     from './js/agent.js';
import * as mcp       from './js/mcp.js';
import * as sdk       from './js/sdk.js';
import * as providers from './js/providers.js';
import * as support   from './js/support.js';
import * as opencode  from './js/opencode.js';
import { initI18n, switchLang } from './js/i18n.js';
import { refreshModelBanner } from './js/model-badge.js';

window.API_BASE = window.location.origin + '/api/v1';
window.CONFIG   = { foundry_url: null, default_model: null };

window.switchLang = switchLang;

Object.assign(window, ui, config, models, chat, foundry, rag, editor, llama, hf, ollama, agent, mcp, sdk, providers, support, opencode);

window.providersRefresh     = providers.initProviders;
window.systemRestartService = foundry.systemRestartService;
window.providersExport      = providers.exportToExtension;
window.providersImport      = (e) => { const f = e.target.files?.[0]; if (f) providers.importFromExtension(f); e.target.value = ''; };

// ── Loading overlay helpers ───────────────────────────────────────────────────

const _LOADING_FALLBACK = {
    'loading.init':     'Loading interface...',
    'loading.config':   'Loading configuration...',
    'loading.i18n':     'Initializing localization...',
    'loading.services': 'Connecting to services...',
    'loading.done':     'Ready',
};

function _loadingStatus(key) {
    const el = document.getElementById('app-loading-status');
    if (!el) return;
    const text = (typeof i18next !== 'undefined' && i18next.isInitialized)
        ? i18next.t(key)
        : (_LOADING_FALLBACK[key] || key);
    el.textContent = text;
    el.setAttribute('data-i18n', key);
}

function _hideLoading() {
    const overlay = document.getElementById('app-loading-overlay');
    if (!overlay) return;
    overlay.classList.add('fade-out');
    setTimeout(() => overlay.remove(), 380);
}

// ── Partial loader ────────────────────────────────────────────────────────────

async function fetchPartial(path) {
    try {
        const r = await fetch(path);
        return r.ok ? await r.text() : '';
    } catch (e) {
        console.error(`[partials] Failed to load ${path}:`, e);
        return '';
    }
}

async function loadAllPartials() {
    const base = '/static/interface/partials';

    const slots = [
        ['slot-navbar',   `${base}/_navbar.html`],
        ['slot-tabs-nav', `${base}/_tabs_nav.html`],
    ];
    for (const [id, path] of slots) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = await fetchPartial(path);
    }

    const tabContent = document.getElementById('mainTabsContent');
    if (tabContent) {
        const tabs = [
            `${base}/_tab_models.html`,
            `${base}/_tab_foundry.html`,
            `${base}/_tab_hf.html`,
            `${base}/_tab_llama.html`,
            `${base}/_tab_ollama.html`,
            `${base}/_tab_rag.html`,
            `${base}/_tab_opencode.html`,
            `${base}/_tab_chat.html`,
            `${base}/_tab_settings_shell.html`,
            `${base}/_tab_editor.html`,
            `${base}/_tab_mcp.html`,
            `${base}/_tab_agent.html`,
            `${base}/_tab_providers.html`,
            `${base}/_tab_support.html`,
            `${base}/_tab_logs.html`,
            `${base}/_tab_docs.html`,
        ];
        const htmlParts = await Promise.all(tabs.map(fetchPartial));
        tabContent.innerHTML = htmlParts.join('');
    }

    const settingsBody = document.getElementById('settings-card-body');
    if (settingsBody) {
        const sections = [
            `${base}/_tab_settings_server.html`,
            `${base}/_tab_settings_dirs.html`,
            `${base}/_tab_settings_foundry.html`,
            `${base}/_tab_settings_models.html`,
            `${base}/_tab_settings_rag.html`,
            `${base}/_tab_settings_opencode.html`,
            `${base}/_tab_settings_security.html`,
            `${base}/_tab_settings_logging.html`,
            `${base}/_tab_settings_dev.html`,
        ];
        const sectionParts = await Promise.all(sections.map(fetchPartial));
        const statusEl = settingsBody.querySelector('#settings-status');
        sectionParts.forEach(html => {
            if (html) statusEl.insertAdjacentHTML('beforebegin', html);
        });
    }

    const modals = [
        `${base}/_modal_llama_picker.html`,
        `${base}/_modal_add_model.html`,
        `${base}/_support_widget.html`,
    ];
    const modalHtml = await Promise.all(modals.map(fetchPartial));
    modalHtml.forEach(html => { if (html) document.body.insertAdjacentHTML('beforeend', html); });
}

// ── Boot ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    _loadingStatus('loading.init');
    await loadAllPartials();

    _loadingStatus('loading.config');
    const cfg  = await config.loadConfig();
    const lang = cfg?.config?.app?.language || '';

    _loadingStatus('loading.i18n');
    await initI18n(lang);

    _loadingStatus('loading.services');

    document.addEventListener('change', e => {
        if (e.target.name === 'startup-model-mode') {
            const row = document.getElementById('startup-custom-model-row');
            if (row) row.style.display = e.target.value === 'custom' ? '' : 'none';
        }
    });

    window.refreshModelBanner = refreshModelBanner;

    await Promise.allSettled([
        hf.hfCheckStatus?.(),
        hf.hfRefreshModels?.(),
        llama.llamaCheckStatus?.(),
        llama.llamaScanModels?.(),
        ollama.ollamaCheckStatus?.(),
        ollama.ollamaLoadModels?.(),
        rag.refreshRAGStatus?.(),
        models.refreshModels?.(),
        foundry.checkSystemStatus?.(),
    ]);

    refreshModelBanner();

    _loadingStatus('loading.done');
    setTimeout(_hideLoading, 200);

    document.getElementById('mainTabsContent')?.addEventListener('keypress', e => {
        if (e.target.id === 'chat-input' && e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            window.sendMessage?.();
        }
        if (e.target.id === 'agent-input' && e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            window.agentRun?.();
        }
    });

    document.getElementById('models-tab')?.addEventListener('shown.bs.tab',    () => { window.refreshModels?.(); });
    document.getElementById('foundry-tab')?.addEventListener('shown.bs.tab',   () => { window.listCachedFoundryModels?.(); window.listFoundryModels?.(); });
    document.getElementById('editor-tab')?.addEventListener('shown.bs.tab',    () => { window.loadEnv?.(); window.loadConfigJson?.(); });
    document.getElementById('llama-tab')?.addEventListener('shown.bs.tab',     () => { window.llamaCheckStatus?.(); window.llamaScanModels?.(); window.ollamaCheckStatus?.(); window.ollamaLoadModels?.(); });
    document.getElementById('ollama-tab')?.addEventListener('shown.bs.tab',    () => { window.ollamaCheckStatus?.(); window.ollamaLoadModels?.(); });
    document.getElementById('hf-tab')?.addEventListener('shown.bs.tab',        () => { window.hfCheckStatus?.(); window.hfRefreshModels?.(); });
    document.getElementById('rag-tab')?.addEventListener('shown.bs.tab',       () => { window.refreshRAGStatus?.(); window.ragLoadProfiles?.(); });
    document.getElementById('opencode-tab')?.addEventListener('shown.bs.tab',  () => { window.refreshOpenCodeStatus?.(); });
    document.getElementById('agent-tab')?.addEventListener('shown.bs.tab',     () => { window.agentLoadTools?.(); });
    document.getElementById('mcp-tab')?.addEventListener('shown.bs.tab',       () => { window.mcpLoadServers?.(); });
    document.getElementById('settings-tab')?.addEventListener('shown.bs.tab',  () => { window.loadConfigFields?.(); window.refreshLogHealth?.(); });
    document.getElementById('providers-tab')?.addEventListener('shown.bs.tab', () => { window.providersRefresh?.(); });
    document.getElementById('support-tab')?.addEventListener('shown.bs.tab', () => {
        window.supportLoadStatus?.();
        window.supportLoadDialogs?.();
        window.supportLoadProfiles?.();
    });
    let _logViewerInited = false;
    document.getElementById('logs-tab')?.addEventListener('shown.bs.tab', () => {
        if (!_logViewerInited) { window.initLogViewer?.(); _logViewerInited = true; }
        else { window.refreshLogs?.(); }
    });

});
