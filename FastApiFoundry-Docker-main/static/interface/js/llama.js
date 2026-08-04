/**
 * Модуль интеграции с llama.cpp
 * Version: 0.4.1
 */

const LLAMA_API = '/api/v1/llama';

export async function toggleLlamaService(on) {
    const label = document.getElementById('llama-toggle-label');
    const sw    = document.getElementById('llama-toggle-switch');
    if (on) {
        if (label) label.textContent = 'Starting\u2026';
        if (sw) sw.disabled = true;  // lock toggle during startup
        await llamaStart();
        // llamaStart() handles its own polling — status updated there
        if (sw) sw.disabled = false;
    } else {
        if (label) label.textContent = 'Stopping\u2026';
        await llamaStop();
        await llamaCheckStatus();
    }
}

export async function llamaCheckStatus() {
    const el = document.getElementById('llama-status-body');
    if (!el) return;
    try {
        const response = await fetch(`${LLAMA_API}/status`);
        if (!response.ok) throw new Error('Network response was not ok');
        const d = await response.json();

        // Restore port from config.json if field is empty
        const portEl = document.getElementById('llama-port');
        if (portEl && !portEl.value) {
            const cfg = await fetch(`${window.API_BASE}/config`).then(r => r.json());
            portEl.value = cfg.config?.llama_cpp?.port || 9780;
        }

        // Restore model_path from config.json if field is empty
        const modelPathEl = document.getElementById('llama-model-path');
        if (modelPathEl && !modelPathEl.value) {
            try {
                const cfg = await fetch(`${window.API_BASE}/config`).then(r => r.json());
                const cfgPath = cfg.config?.llama_cpp?.model_path || '';
                if (cfgPath) modelPathEl.value = cfgPath;
            } catch (_) {}
        }

        // Update URL in Usage block
        const port = portEl?.value || 9780;
        const urlCode = document.getElementById('llama-openai-url');
        if (urlCode) urlCode.textContent = d.openai_url || `http://127.0.0.1:${port}/v1`;

        const sw    = document.getElementById('llama-toggle-switch');
        const label = document.getElementById('llama-toggle-label');
        if (sw) sw.checked = !!d.running;
        if (label) label.textContent = d.running ? 'Stop llama.cpp' : 'Start llama.cpp';

        let badge;
        if (d.running) {
            badge = '<span class="badge bg-success">Running</span>';
        } else if (d.loading) {
            badge = '<span class="badge bg-warning text-dark"><span class="spinner-border spinner-border-sm me-1" style="width:.7em;height:.7em"></span>Loading model...</span>';
            // Keep toggle ON while model is loading
            if (sw) sw.checked = true;
            if (label) label.textContent = 'Loading...';
        } else {
            badge = '<span class="badge bg-secondary">Stopped</span>';
        }

        const errorRow = d.last_error
            ? `<tr><td colspan="2"><div class="alert alert-danger mb-0 mt-2 p-2" style="font-size:.8rem">
                   <i class="bi bi-exclamation-triangle-fill me-1"></i><strong>Error:</strong><br>
                   <code style="white-space:pre-wrap;word-break:break-all">${d.last_error}</code>
               </div></td></tr>`
            : '';

        el.innerHTML = `
            <table class="table table-sm mb-0">
                <tr><td>Status</td><td>${badge}</td></tr>
                <tr><td>PID</td><td>${d.pid || '\u2014'}</td></tr>
                <tr><td>URL</td><td><code>${d.url || 'N/A'}</code></td></tr>
                ${errorRow}
            </table>`;
    } catch(e) {
        console.error('Llama status check failed:', e);
        el.innerHTML = `<div class="text-danger"><small>${e.message}</small></div>`;
    }
}

export async function llamaStop() {
    try {
        const response = await fetch(`${LLAMA_API}/stop`, { method: 'POST' });
        const d = await response.json();
        if (d.success) {
            alert('✅ ' + (d.message || 'Stopped'));
        } else {
            throw new Error(d.error || 'Stop failed');
        }
        await llamaCheckStatus();
    } catch(e) {
        console.error('Llama stop failed:', e);
        alert('❌ ' + e.message);
    }
}
// ── llama.cpp Tab ─────────────────────────────────────────────────────

export async function llamaStart() {
    let modelPath = document.getElementById('llama-model-path')?.value.trim();
    const port      = parseInt(document.getElementById('llama-port')?.value || '9780');
    const statusEl  = document.getElementById('llama-start-status');

    // Fallback: load model_path from config.json if field is empty
    if (!modelPath) {
        try {
            const cfg = await fetch(`${window.API_BASE}/config`).then(r => r.json());
            modelPath = cfg.config?.llama_cpp?.model_path || '';
            const modelPathEl = document.getElementById('llama-model-path');
            if (modelPathEl && modelPath) modelPathEl.value = modelPath;
        } catch (_) {}
    }

    if (!modelPath) {
        showAlert('Select a model first', 'warning');
        return;
    }

    // Save port to config.json
    fetch(`${window.API_BASE}/config`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ 'llama_cpp.port': port })
    }).catch(() => {});

    const showStatus = (html) => {
        if (!statusEl) return;
        statusEl.style.display = '';
        statusEl.innerHTML = html;
    };

    showStatus('<div class="alert alert-info p-2"><div class="spinner-border spinner-border-sm me-2"></div>Sending start request...</div>');

    let startData;
    try {
        const response = await fetch(`${LLAMA_API}/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                model_path:   modelPath,
                copy_to_models: true,
                port,
                ctx_size:     parseInt(document.getElementById('llama-ctx')?.value     || '4096'),
                threads:      parseInt(document.getElementById('llama-threads')?.value || '0'),
                n_gpu_layers: parseInt(document.getElementById('llama-ngl')?.value     || '0'),
            })
        });
        startData = await response.json();
    } catch(e) {
        showStatus(`<div class="alert alert-danger p-2">❌ Network error: ${e.message}</div>`);
        await llamaCheckStatus();
        return;
    }

    if (!startData.success) {
        showStatus(`<div class="alert alert-danger p-2">❌ ${startData.error}</div>`);
        await llamaCheckStatus();
        return;
    }

    // Process launched — now poll /health until server is ready
    const pid        = startData.pid;
    const openaiUrl  = startData.openai_url;
    const modelName  = startData.model;
    const timeoutMs  = 60_000;
    const startedAt  = Date.now();
    let   elapsed    = 0;

    showStatus(`<div class="alert alert-info p-2"><div class="spinner-border spinner-border-sm me-2"></div>
        Waiting for llama-server to become ready (PID: ${pid})...<br>
        <small>Model: <code>${modelName}</code> &nbsp; This may take up to 60s</small>
    </div>`);

    while (elapsed < timeoutMs) {
        await new Promise(r => setTimeout(r, 2000));
        elapsed = Date.now() - startedAt;

        const st = await fetch(`${LLAMA_API}/status`).then(r => r.json()).catch(() => ({}));

        if (st.running) {
            // Success
            showStatus(`<div class="alert alert-success p-2">✅ Running (PID: ${pid})<br>
                <small>Model: <code>${modelName}</code><br>OpenAI URL: <code>${openaiUrl}</code></small>
            </div>`);
            const urlEl = document.getElementById('llama-openai-url');
            if (urlEl) urlEl.textContent = openaiUrl;
            await llamaCheckStatus();
            if (window.loadModels) window.loadModels();
            return;
        }

        // Process died — show error immediately
        if (st.last_error) {
            showStatus(`<div class="alert alert-danger p-2">❌ Server failed to start:<br>
                <code style="white-space:pre-wrap;font-size:.8rem">${st.last_error}</code>
            </div>`);
            await llamaCheckStatus();
            return;
        }

        // Still starting — update elapsed
        const sec = Math.round(elapsed / 1000);
        showStatus(`<div class="alert alert-info p-2"><div class="spinner-border spinner-border-sm me-2"></div>
            Waiting for llama-server... ${sec}s / 60s<br>
            <small>Model: <code>${modelName}</code></small>
        </div>`);
    }

    // Timeout
    showStatus(`<div class="alert alert-warning p-2">⚠️ Timeout: server did not respond in 60s.<br>
        <small>Check logs or try starting manually.</small>
    </div>`);
    await llamaCheckStatus();
}

export async function llamaCopyToModels() {
    const modelPath = document.getElementById('llama-model-path')?.value.trim();
    const statusEl  = document.getElementById('llama-start-status');
    if (!modelPath) {
        showAlert('Select a model first', 'warning');
        return;
    }
    if (statusEl) {
        statusEl.style.display = '';
        statusEl.innerHTML = '<div class="alert alert-info p-2"><div class="spinner-border spinner-border-sm me-2"></div>Copying to ~/models...</div>';
    }
    try {
        const response = await fetch(`${LLAMA_API}/models/copy`, {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({model_path: modelPath})
        });
        const d = await response.json();
        if (d.success) {
            const msg = d.status === 'already_exists' ? 'Already in ~/models' : `Copied (${d.size_gb} GB)`;
            if (statusEl) {
                statusEl.innerHTML = `<div class="alert alert-success p-2">✅ ${msg}<br><small><code>${d.path}</code></small></div>`;
            }
            const llamaModelPathEl = document.getElementById('llama-model-path');
            if (llamaModelPathEl) llamaModelPathEl.value = d.path;
            llamaScanModels();
        } else {
            if (statusEl) {
                statusEl.innerHTML = `<div class="alert alert-danger p-2">❌ ${d.error}</div>`;
            }
        }
    } catch(e) {
        if (statusEl) {
            statusEl.innerHTML = `<div class="alert alert-danger p-2">❌ ${e.message}</div>`;
        }
        console.error('Llama copy to models failed:', e);
    }
}

export async function llamaScanModels() {
    const listEl = document.getElementById('llama-models-list');
    if (!listEl) return;
    listEl.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm"></div> Scanning...</div>';
    try {
        const response = await fetch(`${LLAMA_API}/models`);
        const d = await response.json();
        if (!d.models?.length) {
            listEl.innerHTML = '<div class="text-muted text-center p-3"><small>No .gguf files found</small></div>';
            return;
        }
        listEl.innerHTML = d.models.map(m => `
            <div class="d-flex align-items-center justify-content-between px-3 py-2 border-bottom">
                <div>
                    <strong style="font-size:.85rem">${m.name}</strong>
                    <small class="text-muted d-block">${m.path} &nbsp;·&nbsp; ${m.size_gb} GB</small>
                </div>
                <button class="btn btn-sm btn-outline-primary" onclick="llamaSelectModel('${m.path.replace(/\\/g,'\\\\')}')">Use</button>
            </div>`).join('');
    } catch(e) {
        listEl.innerHTML = `<div class="text-danger p-3"><small>${e.message}</small></div>`;
        console.error('Llama scan models failed:', e);
    }
}

export function llamaSelectModel(path) {
    const modelPathEl = document.getElementById('llama-model-path');
    if (modelPathEl) modelPathEl.value = path;
}

let _llamaPickerModal = null;

export function llamaOpenPicker() {
    if (!_llamaPickerModal) {
        _llamaPickerModal = new bootstrap.Modal(document.getElementById('llamaPickerModal'));
    }
    const cur = document.getElementById('llama-model-path')?.value;
    if (cur) {
        const pickerManualEl = document.getElementById('llama-picker-manual');
        if (pickerManualEl) pickerManualEl.value = cur;
    }
    _llamaPickerModal.show();
    llamaPickerScan();
}

export function llamaPickerConfirmManual() {
    const path = document.getElementById('llama-picker-manual')?.value.trim();
    if (!path) return;
    const modelPathEl = document.getElementById('llama-model-path');
    if (modelPathEl) modelPathEl.value = path;
    _llamaPickerModal?.hide();
}

export async function llamaPickerScan() {
    const listEl = document.getElementById('llama-picker-list');
    const extraDir = document.getElementById('llama-picker-search-dir')?.value.trim();
    if (!listEl) return;
    listEl.innerHTML = '<div class="text-center p-4"><div class="spinner-border"></div><div class="mt-2">Scanning...</div></div>';

    try {
        const url = extraDir ? `${LLAMA_API}/models?extra_dir=${encodeURIComponent(extraDir)}` : `${LLAMA_API}/models`;
        const d = await fetch(url).then(r => r.json());

        if (!d.models?.length) {
            listEl.innerHTML = '<div class="text-muted text-center p-4">No .gguf files found.<br><small>Enter a directory above and click Scan.</small></div>';
            return;
        }

        listEl.innerHTML = d.models.map(m => `
            <div class="d-flex align-items-center gap-3 px-3 py-2 border-bottom llama-picker-row"
                 style="cursor:pointer" onclick="llamaPickerSelect('${m.path.replace(/\\/g,'\\\\').replace(/'/g,"\\'")}')"
                 onmouseover="this.style.background='#f0f4ff'" onmouseout="this.style.background=''">
                <i class="bi bi-file-earmark-binary text-primary fs-5"></i>
                <div class="flex-grow-1 overflow-hidden">
                    <div class="fw-semibold text-truncate" style="font-size:.9rem">${m.name}</div>
                    <div class="text-muted" style="font-size:.75rem">${m.path}</div>
                </div>
                <span class="badge bg-secondary">${m.size_gb} GB</span>
                <button class="btn btn-sm btn-primary" onclick="event.stopPropagation();llamaPickerSelect('${m.path.replace(/\\/g,'\\\\').replace(/'/g,"\\'")}')">Select</button>
            </div>`).join('');
    } catch(e) {
        listEl.innerHTML = `<div class="text-danger p-3">${e.message}</div>`;
        console.error('Llama picker scan failed:', e);
    }
}

export function llamaPickerSelect(path) {
    const modelPathEl = document.getElementById('llama-model-path');
    if (modelPathEl) modelPathEl.value = path;
    const pickerManualEl = document.getElementById('llama-picker-manual');
    if (pickerManualEl) pickerManualEl.value = path;
    _llamaPickerModal?.hide();
}

export function llamaCopyUrl() {
    const urlEl = document.getElementById('llama-openai-url');
    if (!urlEl) return;
    const url = urlEl.textContent;
    navigator.clipboard.writeText(url).then(() => showAlert('✅ Copied: ' + url, 'success'));
}

// Переключение llama.cpp модели из чата/селектов:
// выгружаем старый llama.cpp сервер (он заменяется при новом start)
// и ждём, пока /llama/status станет running.
export async function llamaSwitchChatModel(modelPath) {
    if (!modelPath) throw new Error('llama modelPath is required');

    const startResp = await fetch(`${LLAMA_API}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            model_path: modelPath,
            copy_to_models: true
        })
    }).then(r => r.json());

    if (!startResp.success) {
        throw new Error(startResp.error || 'Failed to start llama.cpp');
    }

    const startedAt = Date.now();
    const timeoutMs = 120_000;

    while (Date.now() - startedAt < timeoutMs) {
        const st = await fetch(`${LLAMA_API}/status`).then(r => r.json());
        if (st.success && st.running) return true;
        await new Promise(resolve => setTimeout(resolve, 2000));
    }

    throw new Error('Timed out waiting for llama.cpp to become running');
}
// ... остальные функции llama извлеченные из HTML