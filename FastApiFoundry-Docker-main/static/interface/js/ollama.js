/**
 * =============================================================================
 * Process Name: Ollama Provider UI Module
 * =============================================================================
 * Description:
 *   Web UI for managing Ollama local model server.
 *   Handles status checks, model listing, pull and delete operations.
 *
 * File: js/ollama.js
 * Project: FastApiFoundry (Docker)
 * Version: 0.6.0
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

const OLLAMA_API = '/api/v1/ollama';

// ── Status ────────────────────────────────────────────────────────────────────

export async function ollamaCheckStatus() {
    const el = document.getElementById('ollama-status-body');
    if (!el) return;
    try {
        const d = await fetch(`${OLLAMA_API}/status`).then(r => r.json());

        const badge = d.running
            ? '<span class="badge bg-success">Running</span>'
            : '<span class="badge bg-secondary">Stopped</span>';

        el.innerHTML = `
            <table class="table table-sm mb-0">
                <tr><td>Status</td><td>${badge}</td></tr>
                <tr><td>Version</td><td>${d.version || '—'}</td></tr>
                <tr><td>URL</td><td><code>${d.url || 'N/A'}</code></td></tr>
                <tr><td>OpenAI URL</td><td><code>${d.openai_url || 'N/A'}</code></td></tr>
            </table>`;

        // Update OpenAI URL in usage block
        const urlEl = document.getElementById('ollama-openai-url');
        if (urlEl) urlEl.textContent = d.openai_url || 'http://localhost:11434/v1';
    } catch (e) {
        console.error('Ollama status check failed:', e);
        if (el) el.innerHTML = `<div class="text-danger"><small>${e.message}</small></div>`;
    }
}

// ── Models list ───────────────────────────────────────────────────────────────

export async function ollamaLoadModels() {
    const listEl = document.getElementById('ollama-models-list');
    if (!listEl) return;
    listEl.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm"></div> Loading...</div>';
    try {
        const d = await fetch(`${OLLAMA_API}/models`).then(r => r.json());
        if (!d.success) {
            listEl.innerHTML = `<div class="alert alert-warning m-2 p-2"><small>${d.error || 'Ollama not running'}</small></div>`;
            return;
        }
        if (!d.models?.length) {
            listEl.innerHTML = '<div class="text-muted text-center p-3"><small>No models. Pull one below.</small></div>';
            return;
        }
        listEl.innerHTML = d.models.map(m => `
            <div class="d-flex align-items-center justify-content-between px-3 py-2 border-bottom">
                <div>
                    <strong style="font-size:.85rem">${m.name}</strong>
                    <small class="text-muted d-block">${m.size_gb} GB &nbsp;·&nbsp; ${m.digest}</small>
                </div>
                <button class="btn btn-sm btn-outline-danger"
                        onclick="ollamaDeleteModel('${m.name}')">
                    <i class="bi bi-trash"></i>
                </button>
            </div>`).join('');
    } catch (e) {
        listEl.innerHTML = `<div class="text-danger p-3"><small>${e.message}</small></div>`;
        console.error('Ollama load models failed:', e);
    }
}

// ── Pull model ────────────────────────────────────────────────────────────────

export async function ollamaPullModel() {
    const input   = document.getElementById('ollama-pull-input');
    const statusEl = document.getElementById('ollama-pull-status');
    const model   = input?.value.trim();

    if (!model) {
        showAlert('Enter a model name, e.g. qwen2.5:0.5b', 'warning');
        return;
    }

    if (statusEl) {
        statusEl.style.display = '';
        statusEl.innerHTML = `<div class="alert alert-info p-2">
            <div class="spinner-border spinner-border-sm me-2"></div>
            Pulling <code>${model}</code>… This may take several minutes.
        </div>`;
    }

    try {
        const d = await fetch(`${OLLAMA_API}/models/pull`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ model }),
        }).then(r => r.json());

        if (d.success) {
            if (statusEl) statusEl.innerHTML = `<div class="alert alert-success p-2">✅ Pulled: <code>${model}</code></div>`;
            if (input) input.value = '';
            await ollamaLoadModels();
        } else {
            if (statusEl) statusEl.innerHTML = `<div class="alert alert-danger p-2">❌ ${d.error}</div>`;
        }
    } catch (e) {
        if (statusEl) statusEl.innerHTML = `<div class="alert alert-danger p-2">❌ ${e.message}</div>`;
        console.error('Ollama pull failed:', e);
    }
}

// ── Delete model ──────────────────────────────────────────────────────────────

export async function ollamaDeleteModel(model) {
    if (!confirm(`Delete model "${model}"?`)) return;
    try {
        const d = await fetch(`${OLLAMA_API}/models/delete`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ model }),
        }).then(r => r.json());

        if (d.success) {
            showAlert(`✅ Deleted: ${model}`, 'success');
            await ollamaLoadModels();
        } else {
            showAlert(`❌ ${d.error}`, 'danger');
        }
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
        console.error('Ollama delete failed:', e);
    }
}

// ── Copy OpenAI URL ───────────────────────────────────────────────────────────

export function ollamaCopyUrl() {
    const urlEl = document.getElementById('ollama-openai-url');
    if (!urlEl) return;
    navigator.clipboard.writeText(urlEl.textContent)
        .then(() => showAlert('✅ Copied: ' + urlEl.textContent, 'success'));
}
