/**
 * Название процесса: Интеграция с HuggingFace
 * Описание: Управление моделями HuggingFace, загрузка, выгрузка и генерация.
 * Version: 0.4.1
 * Date: 17 апреля 2026
 */

import { showAlert, updateChatModelBadge } from './ui.js';

const HF_API = '/api/v1/hf';

export async function hfCheckStatus() {
    const el = document.getElementById('hf-status-body');
    if (!el) return;
    el.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm"></div></div>';
    try {
        const d = await fetch(`${HF_API}/status`).then(r => r.json());
        const ok  = v => v ? '<span class="badge bg-success">OK</span>' : '<span class="badge bg-danger">Missing</span>';
        const warn = document.getElementById('hf-token-warning');
        if (warn) warn.style.display = d.hf_token_set ? 'none' : '';
        el.innerHTML = `
            <table class="table table-sm mb-0">
                <tr><td>transformers</td><td>${ok(d.transformers?.available)} ${d.transformers?.version||''}</td></tr>
                <tr><td>huggingface_hub</td><td>${ok(d.huggingface_hub?.available)} ${d.huggingface_hub?.version||''}</td></tr>
                <tr><td>torch</td><td>${ok(d.torch?.available)} ${d.torch?.version||''}</td></tr>
                <tr><td>CUDA</td><td>${d.torch?.cuda ? '<span class="badge bg-success">Available</span>' : '<span class="badge bg-secondary">CPU only</span>'}</td></tr>
                <tr><td>HF Token</td><td>${d.hf_token_set
                    ? '<span class="badge bg-success">Set ✓</span>'
                    : '<span class="badge bg-warning">Not set — go to API Keys tab</span>'}</td></tr>
            </table>
            ${!d.transformers?.available ? `<div class="alert alert-warning mt-2 mb-0 p-2"><small>Run: <code>${d.install_cmd}</code></small></div>` : ''}`;
    } catch(e) { 
        el.innerHTML = `<div class="text-danger"><small>${e.message}</small></div>`; 
        console.error('HuggingFace status check failed:', e);
    }
}

// ── Hub Models ─────────────────────────────────────────────────────

let _hubData = null;
let _hubTab  = 'my';

export async function hfLoadHubModels() {
    const listEl = document.getElementById('hf-hub-list');
    if (!listEl) return;
    listEl.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm"></div> Loading from Hub...</div>';
    try {
        _hubData = await fetch(`${HF_API}/hub/models`).then(r => r.json());
        if (!_hubData.success && _hubData.error === 'HF_TOKEN not set') {
            listEl.innerHTML = `<div class="alert alert-warning m-2 p-2">
                ⚠️ HF Token не задан.<br>
                <small>1. Перейдите во вкладку <strong>API Keys</strong><br>
                2. Найдите <strong>HuggingFace</strong> и добавьте токен<br>
                3. Вернитесь сюда и нажмите Load</small>
            </div>`;
            // Показываем публичные модели даже без токена
            hfSwitchHubTab('public');
            return;
        }
        hfSwitchHubTab(_hubTab);
    } catch(e) {
        listEl.innerHTML = `<div class="text-danger p-3">${e.message}</div>`;
        console.error('HuggingFace hub models load failed:', e);
    }
}

export function hfSwitchHubTab(tab) {
    _hubTab = tab;
    document.getElementById('hf-my-tab')?.classList.toggle('active', tab === 'my');
    document.getElementById('hf-public-tab')?.classList.toggle('active', tab === 'public');
    if (!_hubData) return;
    const listEl = document.getElementById('hf-hub-list');
    if (!listEl) return;
    const models  = tab === 'my' ? (_hubData.user_models || []) : (_hubData.public_models || []);

    if (!models.length) {
        listEl.innerHTML = tab === 'my'
            ? '<div class="text-muted text-center p-3"><small>No models in your account</small></div>'
            : '<div class="text-muted text-center p-3"><small>No public models</small></div>';
        return;
    }

    listEl.innerHTML = models.map(m => {
        const note    = m.note    ? `<span class="text-muted"> — ${m.note}</span>`    : '';
        const size    = m.size    ? `<span class="badge bg-light text-dark me-1">${m.size}</span>` : '';
        const priv    = m.private ? '<span class="badge bg-secondary me-1">private</span>' : '';
        const pipe    = m.pipeline ? `<span class="badge bg-info me-1">${m.pipeline}</span>` : '';
        return `
        <div class="d-flex align-items-center justify-content-between px-3 py-2 border-bottom">
            <div class="overflow-hidden">
                <div style="font-size:.85rem;font-weight:600">${m.id}${note}</div>
                <div>${priv}${pipe}${size}</div>
            </div>
            <div class="d-flex gap-1 ms-2 flex-shrink-0">
                <button class="btn btn-sm btn-outline-secondary" title="Open on HuggingFace"
                    onclick="window.open('https://huggingface.co/${m.id}','_blank')">
                    <i class="bi bi-box-arrow-up-right"></i>
                </button>
                <button class="btn btn-sm btn-success"
                    onclick="hfSelectAndDownload('${m.id}')">
                    <i class="bi bi-download"></i>
                </button>
            </div>
        </div>`;
    }).join('');

    // Показываем инструкцию для публичных моделей
    if (tab === 'public') {
        listEl.insertAdjacentHTML('beforeend', `
            <div class="alert alert-info m-2 p-2" style="font-size:.8rem">
                <strong>ℹ️ Как использовать публичные модели:</strong><br>
                • <strong>Без лицензии</strong> (Phi, Qwen, TinyLlama, DeepSeek): нажмите ↓ — скачается сразу<br>
                • <strong>С лицензией</strong> (Gemma, Llama, Mistral): сначала примите лицензию на 
                <a href="https://huggingface.co" target="_blank">huggingface.co</a> → кнопка ↗ откроет страницу модели<br>
                • HF Token должен быть задан в Settings для закрытых моделей
            </div>`);
    }
}

export function hfSelectAndDownload(modelId) {
    const hfDownloadIdEl = document.getElementById('hf-download-id');
    if (hfDownloadIdEl) hfDownloadIdEl.value = modelId;
    hfDownload();
}

export async function hfRefreshModels() {
    try {
        const d = await fetch(`${HF_API}/models`).then(r => r.json());
        const dlEl = document.getElementById('hf-downloaded-list');
        const ldEl = document.getElementById('hf-loaded-list');

        if (!dlEl || !ldEl) return;

        if (!d.downloaded?.length) {
            dlEl.innerHTML = '<div class="text-muted text-center p-3"><small>No models downloaded yet</small></div>';
        } else {
            dlEl.innerHTML = d.downloaded.map(m => `
                <div class="d-flex align-items-center justify-content-between px-3 py-2 border-bottom">
                    <div>
                        <strong style="font-size:.85rem">${m.id}</strong>
                        <small class="text-muted d-block">${m.size_mb} MB</small>
                    </div>
                    <div class="d-flex gap-1">
                        ${m.loaded
                            ? `<button class="btn btn-sm btn-outline-danger" onclick="hfUnload('${m.id}')">Unload</button>`
                            : `<button class="btn btn-sm btn-outline-success" onclick="hfLoad('${m.id}')">Load</button>`
                        }
                    </div>
                </div>`).join('');
        }

        if (!d.loaded?.length) {
            ldEl.innerHTML = '<div class="text-muted text-center p-3"><small>No models in memory</small></div>';
        } else {
            ldEl.innerHTML = d.loaded.map(m => `
                <div class="d-flex align-items-center justify-content-between px-3 py-2 border-bottom">
                    <span style="font-size:.85rem">${m.id}</span>
                    <button class="btn btn-sm btn-outline-danger" onclick="hfUnload('${m.id}')">Unload</button>
                </div>`).join('');
        }

        // Заполняем chat model select скачанными моделями
        await hfUpdateChatModelSelect();
    } catch(e) { console.error('HuggingFace refresh models failed:', e); }
}

async function hfWaitForModelLoaded(modelId, timeoutMs = 120000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
        const d = await fetch(`${HF_API}/models`).then(r => r.json());
        const loadedIds = (d.loaded || []).map(m => m.id);
        if (d.success !== false && loadedIds.includes(modelId)) return true;
        await new Promise(resolve => setTimeout(resolve, 3000));
    }
    return false;
}

// Аналог логики переключения в Foundry: выгрузить предыдущие HF модели и загрузить выбранную
export async function hfSwitchLocalModel(modelId) {
    if (!modelId) return;

    const device = document.getElementById('hf-gen-device')?.value || 'auto';

    try {
        showAlert(`HF switch: unloading previous models...`, 'info');

        // Останавливаем llama.cpp сервер, чтобы не держать несколько подсистем одновременно
        try {
            await fetch(`${window.API_BASE}/llama/stop`, { method: 'POST' }).then(r => r.json());
        } catch (e) {
            // Не критично
        }

        // Сначала выгружаем все загруженные Foundry модели, чтобы в памяти была только одна активная подсистема.
        try {
            const foundryLoaded = await fetch(`${window.API_BASE}/foundry/models/loaded`).then(r => r.json());
            const loadedFoundryIds = (foundryLoaded.models || []).map(m => m.id);
            for (const foundryId of loadedFoundryIds) {
                const u = await fetch(`${window.API_BASE}/foundry/models/unload`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model_id: foundryId })
                }).then(r => r.json());
                if (!u.success) {
                    console.warn(`Foundry unload failed for ${foundryId}:`, u.error);
                }
            }
        } catch (e) {
            console.warn('Foundry unload before HF switch failed:', e);
        }

        const d = await fetch(`${HF_API}/models`).then(r => r.json());
        const loadedIds = (d.loaded || []).map(m => m.id);

        for (const loadedId of loadedIds) {
            if (loadedId === modelId) continue;
            const u = await fetch(`${HF_API}/models/unload`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_id: loadedId })
            }).then(r => r.json());

            if (!u.success) {
                console.warn(`HF unload failed for ${loadedId}:`, u.error);
                showAlert(`Unload failed for ${loadedId}: ${u.error || 'unknown'}`, 'warning');
            }
        }

        // Загружаем выбранную (если еще не в памяти)
        if (!loadedIds.includes(modelId)) {
            const l = await fetch(`${HF_API}/models/load`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_id: modelId, device })
            }).then(r => r.json());

            if (!l.success) {
                throw new Error(l.error || `Failed to load ${modelId}`);
            }
        }

        const ready = await hfWaitForModelLoaded(modelId);
        if (!ready) {
            showAlert(`HF model ${modelId} did not become ready in time. Check logs.`, 'warning');
        } else {
            showAlert(`HF model switched to: ${modelId}`, 'success');
        }

        await hfRefreshModels();
        await hfUpdateChatModelSelect();

        const sel = document.getElementById('hf-downloaded-model-select');
        if (sel) sel.value = modelId;
    } catch (e) {
        console.error('HF switch failed:', e);
        showAlert(`HF switch failed: ${e.message}`, 'danger');
    }
}

export async function hfDownload() {
    const modelId  = document.getElementById('hf-download-id')?.value.trim();
    const statusEl = document.getElementById('hf-download-status');
    if (!modelId) {
        showAlert('Enter model ID', 'warning');
        return;
    }
    if (statusEl) {
        statusEl.style.display = '';
        statusEl.innerHTML = `
            <div class="alert alert-info p-2">
                <div class="d-flex align-items-center gap-2 mb-2">
                    <div class="spinner-border spinner-border-sm"></div>
                    <strong>Downloading ${modelId}...</strong>
                </div>
                <div class="progress mb-1" style="height:6px">
                    <div id="hf-dl-bar" class="progress-bar progress-bar-striped progress-bar-animated"
                         style="width:0%"></div>
                </div>
                <small id="hf-dl-label" class="text-muted">Connecting...</small>
            </div>`;
    }
    try {
        const params = new URLSearchParams({ model_id: modelId });
        const es = new EventSource(`${HF_API}/models/download/stream?${params}`);
        await new Promise((resolve, reject) => {
            es.onmessage = (e) => {
                const ev = JSON.parse(e.data);
                if (ev.type === 'file_start' || ev.type === 'file_done') {
                    const pct = Math.round((ev.file_index / ev.total_files) * 100);
                    const bar = document.getElementById('hf-dl-bar');
                    const lbl = document.getElementById('hf-dl-label');
                    if (bar) bar.style.width = pct + '%';
                    if (lbl) lbl.textContent =
                        `[${ev.file_index}/${ev.total_files}] ${ev.filename}`;
                } else if (ev.type === 'done') {
                    es.close();
                    if (statusEl) {
                        statusEl.innerHTML = ev.success
                            ? `<div class="alert alert-success p-2">✅ Downloaded to: <code>${ev.path}</code></div>`
                            : `<div class="alert alert-danger p-2">❌ ${ev.error}
                                ${ev.error?.includes('license') || ev.error?.includes('401') || ev.error?.includes('403')
                                    ? `<br><small>→ <a href="https://huggingface.co/${modelId}" target="_blank">Accept license on huggingface.co</a></small>`
                                    : ''}
                               </div>`;
                    }
                    if (ev.success) hfRefreshModels();
                    resolve();
                } else if (ev.type === 'error') {
                    es.close();
                    if (statusEl) statusEl.innerHTML =
                        `<div class="alert alert-danger p-2">❌ ${ev.error}</div>`;
                    reject(new Error(ev.error));
                }
            };
            es.onerror = () => {
                es.close();
                reject(new Error('SSE connection error'));
            };
        });
    } catch(e) {
        if (statusEl) statusEl.innerHTML = `<div class="alert alert-danger p-2">❌ ${e.message}</div>`;
        console.error('HuggingFace download failed:', e);
    }
}

export async function hfLoad(modelId) {
    const device = document.getElementById('hf-gen-device')?.value || 'auto';
    // Показываем спиннер на кнопке
    const btn = document.querySelector(`[onclick="hfLoad('${modelId}')"]`);
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>'; }
    try {
        const d = await fetch(`${HF_API}/models/load`, {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({model_id: modelId, device})
        }).then(r => r.json());
        if (!d.success) showAlert(`❌ ${d.error}`, 'danger');
        hfRefreshModels();
        hfUpdateChatModelSelect();
    } catch (e) {
        showAlert(`❌ Failed to load model: ${e.message}`, 'danger');
        console.error('HuggingFace load model failed:', e);
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = 'Load'; } // Restore button text
    }
}

export async function hfUnload(modelId) {
    const btn = document.querySelector(`[onclick="hfUnload('${modelId}')"]`);
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>'; }
    try {
        const d = await fetch(`${HF_API}/models/unload`, {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({model_id: modelId})
        }).then(r => r.json());
        if (!d.success) showAlert(`❌ ${d.error}`, 'danger');
        hfRefreshModels();
        hfUpdateChatModelSelect();
    } catch (e) {
        showAlert(`❌ Failed to unload model: ${e.message}`, 'danger');
        console.error('HuggingFace unload model failed:', e);
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = 'Unload'; } // Restore button text
    }
}

// Добавляем загруженные HF модели в селект чата
export async function hfUpdateChatModelSelect() {
    try {
        const d = await fetch(`${HF_API}/models`).then(r => r.json());
        const sel = document.getElementById('chat-model');
        if (!sel) return;

        const current = sel.value;
        // Удаляем старые HF опции
        [...sel.options].filter(o => o.dataset.hf).forEach(o => o.remove());
        const downloaded = Array.isArray(d.downloaded) ? d.downloaded : [];
        if (downloaded.length) {
            const group = document.createElement('optgroup');
            group.label = '— HuggingFace (local) —';
            downloaded.forEach(m => {
                const loadedLabel = m.loaded ? ' (loaded)' : '';
                const opt = new Option(`🤗 ${m.id}${loadedLabel}`, `hf::${m.id}`);
                opt.dataset.hf = '1';
                group.appendChild(opt);
            });
            sel.appendChild(group);
        }

        // Восстанавливаем выбор, если он всё ещё доступен
        if (current) {
            const exists = [...sel.options].some(o => o.value === current);
            if (exists) sel.value = current;
        }
    } catch(e) { console.error('HuggingFace update chat model select failed:', e); }
}

export async function hfGenerate() {
    const modelId = document.getElementById('hf-gen-model')?.value.trim();
    const prompt  = document.getElementById('hf-gen-prompt')?.value.trim();
    const tokens  = parseInt(document.getElementById('hf-gen-tokens')?.value || '256');
    const temp    = parseFloat(document.getElementById('hf-gen-temp')?.value || '0.7');
    const device  = document.getElementById('hf-gen-device')?.value || 'auto';
    const outEl   = document.getElementById('hf-gen-output');
    if (!modelId || !prompt) {
        showAlert('Fill in Model ID and Prompt', 'warning');
        return;
    }
    if (outEl) {
        outEl.style.display = '';
        outEl.textContent = '⏳ Generating...';
    }
    try {
        const d = await fetch(`${HF_API}/generate`, {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({model_id: modelId, prompt, max_new_tokens: tokens, temperature: temp, device: device})
        }).then(r => r.json());
        if (outEl) outEl.textContent = d.success ? d.content : `❌ ${d.error}`;
    } catch(e) { 
        if (outEl) outEl.textContent = `❌ ${e.message}`; 
        console.error('HuggingFace generate failed:', e);
    }
}

// Save HF token via provider-keys endpoint (used by API Keys tab)
export async function saveHFToken(token) {
    if (!token) {
        showAlert('Введите токен', 'warning');
        return;
    }
    try {
        const r = await fetch(`${window.API_BASE}/config/provider-keys`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ keys: { huggingface: token } }),
        });
        const d = await r.json();
        if (d.success) showAlert('✅ Токен сохранён в .env', 'success');
        else showAlert('Ошибка: ' + (d.detail || d.error), 'danger');
    } catch(e) {
        showAlert('Ошибка запроса: ' + e, 'danger');
        console.error('Save HF token failed:', e);
    }
}

// Load HF settings into Settings tab
export async function loadHFConfigFields(cfg) {
    const hf = cfg?.huggingface || {};
    const el = id => document.getElementById(id);
    if (el('config-hf-models-dir')) el('config-hf-models-dir').value = hf.models_dir || './models/hf';
    if (el('config-hf-device'))     el('config-hf-device').value     = hf.device     || 'auto';
    if (el('config-hf-max-tokens')) el('config-hf-max-tokens').value = hf.default_max_new_tokens || 512;

    // Load HF_TOKEN from .env (never from config.json)
    try {
        const envData = await fetch('/api/v1/config/env-raw').then(r => r.json());
        if (envData.success && el('config-hf-token')) {
            const match = envData.content.match(/^HF_TOKEN=(.*)$/m);
            el('config-hf-token').value = match ? match[1].trim() : '';
        }
    } catch (e) {
        console.error('Failed to load HF_TOKEN from .env:', e);
    }
}

export function collectHFConfigFields() {
    const el = id => document.getElementById(id);
    // token is intentionally excluded — it lives in .env only
    return {
        models_dir:             el('config-hf-models-dir')?.value || './models/hf',
        device:                 el('config-hf-device')?.value     || 'auto',
        default_max_new_tokens: parseInt(el('config-hf-max-tokens')?.value || '512'),
        default_temperature:    0.7
    };
}