/**
 * model-badge.js — Global active model banner with resource monitor
 *
 * Renders the selected model from the chat dropdown.
 * Updates #active-model-banner above the tab bar.
 *
 * File: js/model-badge.js
 * Project: FastApiFoundry (Docker)
 * Version: 0.6.0
 * Author: hypo69
 * Copyright: © 2026 hypo69
 */

/**
 * Fetch the currently active model info.
 * Source of truth: #chat-model dropdown value.
 */
async function _fetchActiveModel() {
    const stats = await _sysStats();

    // Primary source: what the user selected in the chat dropdown
    const selectedModel = document.getElementById('chat-model')?.value || '';

    if (selectedModel.startsWith('llama::')) {
        const rawId = selectedModel.slice('llama::'.length);
        const name = rawId.split(/[\/\\]/).pop() || 'llama.cpp model';
        return { name, size: null, backend: 'llama.cpp', ...stats };
    }

    if (selectedModel.startsWith('hf::')) {
        return { name: selectedModel.slice(4), size: null, backend: 'HuggingFace 🤗', ...stats };
    }

    if (selectedModel) {
        return { name: selectedModel, size: _lookupSize(selectedModel), backend: 'Foundry', ...stats };
    }

    return null;
}

/** Fetch system stats from /api/v1/system/stats. */
async function _sysStats() {
    try {
        const s = await fetch(`${window.API_BASE}/system/stats`).then(r => r.json());
        if (s.success) {
            return {
                ram_mb:       s.ram_used_mb,
                ram_avail_mb: s.ram_available_mb,
                ram_total_mb: s.ram_total_mb,
                ram_pct:      s.ram_pct,
                cpu_pct:      s.cpu_pct,
                disk_used_gb: s.disk_used_gb,
                disk_total_gb:s.disk_total_gb,
                disk_pct:     s.disk_pct,
                proc_ram_mb:  s.proc_ram_mb,
                proc_cpu_pct: s.proc_cpu_pct,
                proc_threads: s.proc_threads,
                gpus:         s.gpus || [],
            };
        }
    } catch (_) {}
    return {
        ram_mb: null, ram_avail_mb: null, ram_total_mb: null, ram_pct: null,
        cpu_pct: null,
        disk_used_gb: null, disk_total_gb: null, disk_pct: null,
        proc_ram_mb: null, proc_cpu_pct: null, proc_threads: null,
        gpus: [],
    };
}

/** Look up model size from the Foundry available list (window._foundryModels cache). */
function _lookupSize(modelId) {
    const list = window._foundryModelsCache || [];
    return list.find(m => m.id === modelId)?.size || null;
}

/** Render the banner content. */
function _renderBanner(info) {
    const banner = document.getElementById('active-model-banner');
    if (!banner) return;

    if (!info) {
        banner.innerHTML = `
            <span class="text-muted small">
                <i class="bi bi-cpu me-1"></i>
                <span data-i18n="banner.no_model">No model loaded</span>
            </span>`;
        banner.className = 'active-model-banner active-model-banner--idle';
        return;
    }

    const sizePart  = info.size  ? ` <span class="badge bg-secondary ms-1">${info.size}</span>` : '';
    const backendPart = `<span class="badge bg-primary ms-2">${info.backend}</span>`;

    const fmt1 = v => v != null ? Number(v).toFixed(1) : null;
    const pct   = v => v != null ? `${Number(v).toFixed(1)}%` : null;

    let statsPart = '';

    if (info.ram_mb != null) {
        const used  = (info.ram_mb / 1024).toFixed(1);
        const total = info.ram_total_mb ? ` / ${(info.ram_total_mb / 1024).toFixed(1)}` : '';
        const p     = info.ram_pct != null ? ` (${info.ram_pct.toFixed(0)}%)` : '';
        statsPart += `<span class="active-model-stat"><i class="bi bi-memory me-1"></i>${used}${total} GB RAM${p}</span>`;
    }

    if (info.cpu_pct != null) {
        statsPart += `<span class="active-model-stat"><i class="bi bi-speedometer2 me-1"></i>${pct(info.cpu_pct)} CPU</span>`;
    }

    if (info.disk_used_gb != null) {
        const total = info.disk_total_gb ? ` / ${info.disk_total_gb.toFixed(0)}` : '';
        const p     = info.disk_pct != null ? ` (${info.disk_pct.toFixed(0)}%)` : '';
        statsPart += `<span class="active-model-stat"><i class="bi bi-hdd me-1"></i>${info.disk_used_gb.toFixed(1)}${total} GB${p}</span>`;
    }

    if (info.proc_ram_mb != null) {
        statsPart += `<span class="active-model-stat"><i class="bi bi-box me-1"></i>${(info.proc_ram_mb / 1024).toFixed(2)} GB proc</span>`;
    }

    (info.gpus || []).forEach(g => {
        const used  = (g.ram_used_mb / 1024).toFixed(1);
        const total = g.ram_total_mb ? ` / ${(g.ram_total_mb / 1024).toFixed(1)}` : '';
        const p     = g.ram_pct != null ? ` (${g.ram_pct.toFixed(0)}%)` : '';
        const util  = g.gpu_pct != null ? ` · ${g.gpu_pct}% util` : '';
        statsPart += `<span class="active-model-stat"><i class="bi bi-gpu-card me-1"></i>${g.name}: ${used}${total} GB${p}${util}</span>`;
    });

    banner.innerHTML = `
        <span class="active-model-label">
            <i class="bi bi-robot me-2"></i>
            <strong>${info.name}</strong>${sizePart}${backendPart}
        </span>
        ${statsPart ? `<span class="active-model-stats">${statsPart}</span>` : ''}`;
    banner.className = 'active-model-banner active-model-banner--active';
}

/** Poll and update the banner. */
async function _poll() {
    try {
        const info = await _fetchActiveModel();
        _renderBanner(info);
    } catch (e) {
        console.warn('[model-badge] poll error:', e);
    }
}

/** Initialize banner once without polling model providers. */
export function initModelBanner() {
    _poll();
}

/**
 * Force immediate refresh.
 * If modelInfo is provided, renders it directly without polling.
 * @param {{ name: string, backend: string, size?: string }|null} [modelInfo]
 */
export function refreshModelBanner(modelInfo) {
    if (modelInfo) {
        _renderBanner(modelInfo);
        return;
    }
    _poll();
}
