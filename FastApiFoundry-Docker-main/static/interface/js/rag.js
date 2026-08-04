/**
 * rag.js — Система RAG
 *
 * Содержит:
 *  - refreshRAGStatus()      — статус активной базы
 *  - ragLoadProfiles()       — список баз в ~/.ai-assist/rag
 *  - ragAddDirectory()       — добавить строку выбора директории
 *  - ragRemoveDirectory(idx) — удалить строку директории
 *  - ragOpenBrowserFor(idx)  — открыть браузер для конкретной строки
 *  - ragBuildIndex(force)    — собрать индексы для всех выбранных директорий
 *  - testRAGSearch()         — тестовый поиск
 *  - clearRAGChunks()        — очистить активный индекс
 *  - handleRAGToggle()       — переключатель Enable RAG
 */

import { showAlert } from './ui.js';

const RAG_API = `${window.location.origin}/api/v1/rag`;

// ── Статус ────────────────────────────────────────────────────────────────────

/**
 * Обновляет блок #rag-status — показывает активную базу и её параметры.
 */
export async function refreshRAGStatus() {
    const el = document.getElementById('rag-status');
    if (!el) return;
    try {
        const data = await fetch(`${RAG_API}/status`).then(r => r.json());
        if (!data.success) { el.innerHTML = `<div class="text-danger small">${data.error}</div>`; return; }

        el.innerHTML = `
            <table class="table table-sm mb-0">
                <tr><td>Status</td><td><span class="badge ${data.enabled ? 'bg-success' : 'bg-secondary'}">${data.enabled ? 'Enabled' : 'Disabled'}</span></td></tr>
                <tr><td>Index dir</td><td><code style="font-size:.75rem">${data.index_dir}</code></td></tr>
                <tr><td>Chunks</td><td>${data.total_chunks}</td></tr>
                <tr><td>Model</td><td><small>${data.model}</small></td></tr>
            </table>`;
    } catch (e) {
        if (el) el.innerHTML = `<div class="text-danger small">${e.message}</div>`;
    }
}

// ── Профили (базы в ~/.aiassistant/rag) ───────────────────────────────────────

/**
 * Загружает список RAG баз из ~/.ai-assist/rag и отрисовывает в #rag-profiles-list.
 * Каждая база показывает кнопки Activate, Disable и Delete.
 */
export async function ragLoadProfiles() {
    const list = document.getElementById('rag-profiles-list');
    if (!list) return;
    list.innerHTML = '<div class="text-center p-2"><div class="spinner-border spinner-border-sm"></div></div>';

    try {
        const data = await fetch(`${RAG_API}/profiles`).then(r => r.json());
        if (!data.profiles?.length) {
            list.innerHTML = '<div class="text-muted text-center p-3"><small>No RAG bases yet. Build one →</small></div>';
            return;
        }

        list.innerHTML = data.profiles.map(p => `
            <div class="d-flex align-items-center gap-2 px-3 py-2 border-bottom">
                <div class="flex-grow-1 overflow-hidden">
                    <strong style="font-size:.85rem">${_esc(p.title || p.name)}</strong>
                    <small class="text-muted d-block text-truncate">${_esc(p.description || p.source_dir || p.index_dir || '')}</small>
                    ${p.chunks ? `<small class="text-muted">${p.chunks} chunks</small>` : ''}
                </div>
                <span class="badge ${p.active ? 'bg-primary' : (p.has_index ? 'bg-success' : 'bg-warning')}">${p.active ? 'Active' : (p.has_index ? '✓' : '!')}</span>
                <button class="btn btn-sm btn-outline-primary" onclick="ragLoadProfile('${p.name}')" title="Activate this base">
                    <i class="bi bi-play-fill"></i>
                </button>
                ${p.active ? `<button class="btn btn-sm btn-outline-secondary" onclick="ragDeactivateProfiles()" title="Disable RAG">
                    <i class="bi bi-pause-fill"></i>
                </button>` : ''}
                <button class="btn btn-sm btn-outline-danger" onclick="ragDeleteProfile('${p.name}')" title="Delete">
                    <i class="bi bi-trash"></i>
                </button>
            </div>`).join('');
    } catch (e) {
        list.innerHTML = `<div class="text-danger p-2 small">${e.message}</div>`;
        console.error('ragLoadProfiles failed:', e);
    }
}

/**
 * Активирует выбранную RAG базу — переключает index_dir в config.json
 * и перезагружает RAG систему.
 * @param {string} name
 */
export async function ragLoadProfile(name) {
    try {
        const data = await fetch(`${RAG_API}/profiles/load`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        }).then(r => r.json());

        if (data.success) {
            showAlert(`✅ RAG base '${name}' activated`, 'success');
            refreshRAGStatus();
        } else {
            showAlert(`❌ ${data.error}`, 'danger');
        }
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    }
}

/** Отключает RAG без удаления индексов. */
export async function ragDeactivateProfiles() {
    try {
        const data = await fetch(`${RAG_API}/profiles/deactivate`, { method: 'POST' }).then(r => r.json());
        if (data.success) {
            showAlert('✅ RAG disabled', 'success');
            ragLoadProfiles();
            refreshRAGStatus();
        } else {
            showAlert(`❌ ${data.error}`, 'danger');
        }
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    }
}

/**
 * Удаляет RAG базу из ~/.ai-assist/rag/<name>/.
 * @param {string} name
 */
export async function ragDeleteProfile(name) {
    if (!confirm(`Delete RAG base '${name}'?`)) return;
    try {
        const data = await fetch(`${RAG_API}/profiles/${encodeURIComponent(name)}`, { method: 'DELETE' }).then(r => r.json());
        if (data.success) { showAlert(`✅ Deleted '${name}'`, 'success'); ragLoadProfiles(); }
        else showAlert(`❌ ${data.error}`, 'danger');
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    }
}

// ── Выбор директорий (серверный браузер, мульти) ─────────────────────────────

let _ragBrowserModal = null;
let _ragBrowserCurrentPath = '';
let _ragBrowserTargetIdx = -1; // index of the directory row being edited
let _ragBrowserMode = 'build'; // 'build' | 'index' — determines where confirm writes the path

/**
 * Adds a new directory row and immediately opens the browser for it.
 */
export function ragAddDirectory() {
    const list = document.getElementById('rag-dirs-list');
    if (!list) return;
    const idx = list.children.length;
    const row = document.createElement('div');
    row.className = 'input-group rag-dir-row';
    row.dataset.idx = idx;
    row.innerHTML = `
        <input type="text" class="form-control font-monospace rag-dir-path"
               placeholder="Path will appear here..." readonly>
        <button class="btn btn-outline-secondary" type="button" onclick="ragOpenBrowserFor(${idx})">
            <i class="bi bi-folder2-open"></i>
        </button>
        <button class="btn btn-outline-danger" type="button" onclick="ragRemoveDirectory(${idx})">
            <i class="bi bi-x"></i>
        </button>`;
    list.appendChild(row);
    ragOpenBrowserFor(idx);
}

/**
 * Removes a directory row by its index.
 * @param {number} idx
 */
export function ragRemoveDirectory(idx) {
    const row = document.querySelector(`.rag-dir-row[data-idx="${idx}"]`);
    if (row) row.remove();
}

/**
 * Returns all non-empty directory paths from the list.
 * @returns {string[]}
 */
function ragGetSelectedDirs() {
    return [...document.querySelectorAll('.rag-dir-path')]
        .map(el => el.value.trim())
        .filter(Boolean);
}

/** Opens the directory browser modal for a specific row index. */
export async function ragOpenBrowserFor(idx) {
    _ragBrowserTargetIdx = idx;
    _ragBrowserMode = 'build';
    const modalEl = document.getElementById('ragBrowserModal');
    if (!modalEl) return;
    _ragBrowserModal = bootstrap.Modal.getOrCreateInstance(modalEl);
    _ragBrowserModal.show();
    await ragBrowseTo('');  // empty string → server returns Path.home()
}

/** Opens the directory browser for the "Index Directory" tab. */
export async function ragOpenDirBrowser() {
    _ragBrowserMode = 'index';
    const modalEl = document.getElementById('ragBrowserModal');
    if (!modalEl) return;
    _ragBrowserModal = bootstrap.Modal.getOrCreateInstance(modalEl);
    _ragBrowserModal.show();
    await ragBrowseTo('');  // empty string → server returns Path.home()
}

/** @deprecated Use ragAddDirectory() instead */
export async function ragOpenBrowser() { ragAddDirectory(); }

/** Навигация в директорию path. */
export async function ragBrowseTo(path) {
    const list  = document.getElementById('rag-browser-list');
    const pathEl = document.getElementById('rag-browser-path');
    const upBtn  = document.getElementById('rag-browser-up');
    if (!list) return;
    list.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm"></div></div>';
    try {
        const data = await fetch(`${RAG_API}/browse?path=${encodeURIComponent(path)}`).then(r => r.json());
        if (!data.success) { list.innerHTML = `<div class="text-danger p-3 small">${data.error}</div>`; return; }
        _ragBrowserCurrentPath = data.current;
        if (pathEl) pathEl.textContent = data.current;
        if (upBtn)  upBtn.disabled = !data.parent;
        const label = document.getElementById('rag-browser-selected-label');
        if (label) label.textContent = data.current;
        if (!data.dirs.length) {
            list.innerHTML = '<div class="text-muted text-center p-3 small">No subdirectories</div>';
            return;
        }
        list.innerHTML = data.dirs.map(d =>
            `<div class="d-flex align-items-center px-3 py-2 border-bottom rag-dir-item"
                 style="cursor:pointer" data-path="${d.path.replace(/"/g, '&quot;')}">
                <i class="bi bi-folder-fill text-warning me-2"></i>
                <span class="small">${d.name}</span>
            </div>`
        ).join('');
        list.querySelectorAll('.rag-dir-item').forEach(el =>
            el.addEventListener('click', () => ragBrowseTo(el.dataset.path))
        );
    } catch (e) {
        list.innerHTML = `<div class="text-danger p-3 small">${e.message}</div>`;
    }
}

/** Переход на уровень выше. */
export async function ragBrowserUp() {
    const data = await fetch(`${RAG_API}/browse?path=${encodeURIComponent(_ragBrowserCurrentPath)}`).then(r => r.json()).catch(() => ({}));
    if (data.parent) await ragBrowseTo(data.parent);
}

/** Подтверждает выбор текущей директории и записывает в целевую строку. */
export function ragBrowserConfirm() {
    const selected = _ragBrowserCurrentPath;
    if (!selected) return;

    if (_ragBrowserMode === 'index') {
        // Write into the "Index Directory" tab input
        const inp = document.getElementById('rag-dir-path');
        if (inp) inp.value = selected;
    } else {
        // Write path into the target build-row input
        const row = document.querySelector(`.rag-dir-row[data-idx="${_ragBrowserTargetIdx}"]`);
        if (row) {
            const input = row.querySelector('.rag-dir-path');
            if (input) input.value = selected;
        }
        const status = document.getElementById('rag-dir-status');
        if (status) {
            status.style.display = '';
            status.innerHTML = `<div class="alert alert-success p-2 mb-0 small">✅ Added: <strong>${selected}</strong></div>`;
        }
    }

    if (_ragBrowserModal) _ragBrowserModal.hide();
}

// ── Сборка индекса ────────────────────────────────────────────────────────────

/**
 * Builds RAG index for each selected directory sequentially.
 * @param {boolean} force - rebuild even if index already exists
 */
export async function ragBuildIndex(force = false) {
    const dirs = ragGetSelectedDirs();
    if (!dirs.length) { showAlert('Add at least one source directory', 'warning'); return; }

    const statusEl = document.getElementById('rag-build-status');
    const buildBtn = document.getElementById('rag-build-btn');
    const model      = document.getElementById('rag-build-model')?.value || 'sentence-transformers/all-mpnet-base-v2';
    const chunk_size = parseInt(document.getElementById('rag-build-chunk')?.value  || '1000');
    const overlap    = parseInt(document.getElementById('rag-build-overlap')?.value || '50');

    if (buildBtn) buildBtn.disabled = true;
    if (statusEl) {
        statusEl.style.display = '';
        statusEl.innerHTML = `<div class="alert alert-info p-2"><div class="spinner-border spinner-border-sm me-2"></div>Building ${dirs.length} index(es)...</div>`;
    }

    const results = [];
    for (const sourceDir of dirs) {
        try {
            const data = await fetch(`${RAG_API}/build`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ docs_dir: sourceDir, output_dir: '', model, chunk_size, overlap, force })
            }).then(r => r.json());
            results.push({ dir: sourceDir, ...data });
        } catch (e) {
            results.push({ dir: sourceDir, success: false, error: e.message });
        }
    }

    if (statusEl) {
        const lines = results.map(r =>
            r.success
                ? `<div>✅ <strong>${r.name || r.dir}</strong>: ${r.chunks} chunks</div>`
                : `<div>❌ <strong>${r.dir}</strong>: ${r.error}</div>`
        ).join('');
        statusEl.innerHTML = `<div class="alert ${results.every(r => r.success) ? 'alert-success' : 'alert-warning'} p-2">${lines}</div>`;
    }

    if (results.some(r => r.success)) { ragLoadProfiles(); refreshRAGStatus(); }
    if (buildBtn) buildBtn.disabled = false;
}

/**
 * Indexes files from a locally selected directory (via <input webkitdirectory>).
 * Sends all files one-by-one through /rag/index/stream with SSE progress.
 */
export async function ragIndexDirectoryFiles() {
    const input   = document.getElementById('rag-dir-input');
    const btn     = document.getElementById('rag-dir-index-btn');
    const statusEl = document.getElementById('rag-dir-index-status');
    if (!input?.files?.length) { showAlert('Выберите папку', 'warning'); return; }

    if (btn) btn.disabled = true;
    if (statusEl) statusEl.innerHTML = '';

    const files = Array.from(input.files);
    let anyOk = false;

    for (const file of files) {
        const fileId = `rag-dir-prog-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        if (statusEl) {
            statusEl.insertAdjacentHTML('beforeend',
                `<div id="${fileId}" class="border rounded p-2 mb-1 small">
                    <strong>${_esc(file.webkitRelativePath || file.name)}</strong>
                    <div id="${fileId}-body" class="mt-1">${_progressHtml('…', 5)}</div>
                </div>`);
        }

        const body = new FormData();
        body.append('file', file);

        try {
            const resp = await fetch(`${RAG_API}/index/stream`, { method: 'POST', body });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const reader = resp.body.getReader();
            const dec = new TextDecoder();
            let buf = '';
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buf += dec.decode(value, { stream: true });
                const lines = buf.split('\n');
                buf = lines.pop();
                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    let ev; try { ev = JSON.parse(line.slice(6)); } catch { continue; }
                    _applyProgressEvent(fileId, ev);
                    if (ev.stage === 'done') anyOk = true;
                }
            }
        } catch (e) {
            const b = document.getElementById(`${fileId}-body`);
            if (b) b.innerHTML = `<span class="text-danger">❌ ${_esc(e.message)}</span>`;
        }
    }

    if (btn) btn.disabled = false;
    if (anyOk) { refreshRAGStatus(); ragLoadDocuments(); input.value = ''; }
}

// ── Загрузка архива в активный индекс ────────────────────────────────────────

/** @param {string} msg @param {number} pct @param {string} cls */
function _progressHtml(msg, pct, cls = 'bg-primary') {
    return `
        <div class="small mb-1">${msg}</div>
        <div class="progress" style="height:6px">
            <div class="progress-bar ${cls}" style="width:${pct}%"></div>
        </div>`;
}

/**
 * Uploads files/archives one-by-one via SSE endpoint /rag/index/stream.
 * Shows per-stage progress: extract → chunk → embed (progress bar) → index → done.
 */
export async function ragUploadArchive() {
    const input  = document.getElementById('rag-upload-archive');
    const btn    = document.getElementById('rag-upload-btn');
    const status = document.getElementById('rag-upload-status');
    if (!input?.files?.length) { showAlert('Выберите файл(ы) для загрузки', 'warning'); return; }

    if (btn) btn.disabled = true;
    if (status) { status.style.display = ''; status.innerHTML = ''; }

    const files = Array.from(input.files);
    let anyOk = false;

    for (const file of files) {
        // Container for this file's progress
        const fileId = `rag-prog-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        if (status) {
            status.insertAdjacentHTML('beforeend',
                `<div id="${fileId}" class="border rounded p-2 mb-2 small">
                    <strong>${_esc(file.name)}</strong>
                    <div id="${fileId}-body" class="mt-1">${_progressHtml('…', 5)}</div>
                </div>`);
        }

        const body = new FormData();
        body.append('file', file);

        try {
            const resp = await fetch(`${RAG_API}/index/stream`, { method: 'POST', body });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

            const reader = resp.body.getReader();
            const dec    = new TextDecoder();
            let buf = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buf += dec.decode(value, { stream: true });
                const lines = buf.split('\n');
                buf = lines.pop();
                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    let ev;
                    try { ev = JSON.parse(line.slice(6)); } catch { continue; }
                    _applyProgressEvent(fileId, ev);
                    if (ev.stage === 'done') anyOk = true;
                }
            }
        } catch (e) {
            const body = document.getElementById(`${fileId}-body`);
            if (body) body.innerHTML = `<span class="text-danger">❌ ${_esc(e.message)}</span>`;
        }
    }

    if (btn) btn.disabled = false;
    if (anyOk) { refreshRAGStatus(); ragLoadDocuments(); input.value = ''; }
}

/**
 * Updates the per-file progress block based on a pipeline SSE event.
 * @param {string} fileId
 * @param {{stage:string, message?:string, done?:number, total?:number, chunks?:number}} ev
 */
function _applyProgressEvent(fileId, ev) {
    const el = document.getElementById(`${fileId}-body`);
    if (!el) return;
    const stageIcons = { extract: '📄', chunk: '✂️', embed: '🧠', index: '💾', done: '✅', error: '❌' };
    const icon = stageIcons[ev.stage] || '•';
    switch (ev.stage) {
        case 'extract':
            el.innerHTML = _progressHtml(`${icon} ${ev.message}`, ev.done ? 40 : 10);
            break;
        case 'chunk':
            el.innerHTML = _progressHtml(`${icon} ${ev.message}`, 50);
            break;
        case 'embed': {
            const pct = ev.total ? Math.round((ev.done / ev.total) * 40) + 50 : 55;
            el.innerHTML = _progressHtml(`${icon} ${ev.message}`, pct);
            break;
        }
        case 'index':
            el.innerHTML = _progressHtml(`${icon} ${ev.message}`, 95);
            break;
        case 'done':
            el.innerHTML = `<span class="text-success fw-semibold">✅ ${_esc(ev.message)}</span>`
                + (ev.chunks ? ` <span class="badge bg-success ms-1">${ev.chunks} chunks</span>` : '')
                + (ev.chars  ? ` <span class="text-muted">${ev.chars.toLocaleString()} chars</span>` : '');
            break;
        case 'error':
            el.innerHTML = `<span class="text-danger">❌ ${_esc(ev.message)}</span>`;
            break;
    }
}
// ── Поиск ─────────────────────────────────────────────────────────────────────

/**
 * Тестовый поиск по активной RAG базе.
 * Читает запрос из #rag-test-query.
 */
export async function testRAGSearch() {
    const query = document.getElementById('rag-test-query')?.value.trim();
    if (!query) { showAlert('Enter a search query', 'warning'); return; }

    try {
        const data = await fetch(`${RAG_API}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, top_k: 3 })
        }).then(r => r.json());

        const outputEl  = document.getElementById('rag-search-output');
        const resultsEl = document.getElementById('rag-test-results');
        if (outputEl && resultsEl && data.success) {
            resultsEl.style.display = '';
            outputEl.innerHTML = data.results.map(r =>
                `<p><strong>Score:</strong> ${r.score.toFixed(3)}<br><strong>Content:</strong> ${r.content}</p>`
            ).join('<hr>');
            showAlert(`Found ${data.results.length} results`, 'success');
        } else if (!data.success) {
            showAlert(`❌ ${data.error}`, 'danger');
        }
    } catch (e) {
        showAlert('RAG search failed', 'danger');
    }
}

// ── Прочее ────────────────────────────────────────────────────────────────────

/** Очищает активный RAG индекс (кнопка в Settings) */
export async function clearRAGChunks() {
    if (!confirm('Clear the active RAG index? This cannot be undone.')) return;
    try {
        const data = await fetch(`${RAG_API}/clear`, { method: 'POST' }).then(r => r.json());
        showAlert(data.success ? '✅ RAG index cleared' : `❌ ${data.error}`, data.success ? 'success' : 'danger');
        if (data.success) refreshRAGStatus();
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    }
}

/** Уведомление при переключении чекбокса Enable RAG */
export function handleRAGToggle(checkbox) {
    showAlert(`RAG system ${checkbox.checked ? 'enabled' : 'disabled'}. Save configuration to apply.`, 'info');
}

// ── Text Extractor ──────────────────────────────────────────────────────────────────────────────────

/**
 * Renders extraction results into the preview textarea.
 * @param {Array} files - array of {filename, text, size, type} objects
 * @param {string} sourceName - display name (filename or URL)
 */
function showExtractionPreview(files, sourceName) {
    const resultEl  = document.getElementById('ext-result');
    const textEl    = document.getElementById('ext-result-text');
    const metaEl    = document.getElementById('ext-result-meta');
    if (!resultEl || !textEl) return;

    const totalChars = files.reduce((s, f) => s + (f.text || '').length, 0);
    const combined   = files.map(f => {
        const header = files.length > 1 ? `=== ${f.filename} ===\n` : '';
        return header + (f.text || '');
    }).join('\n\n');

    if (metaEl) metaEl.textContent = `${sourceName} — ${files.length} file(s), ${totalChars.toLocaleString()} chars`;
    textEl.value = combined;
    resultEl.style.display = '';
}

/**
 * Extracts text from the selected file via POST /api/v1/rag/extract/file.
 */
export async function extractFromFile() {
    const input = document.getElementById('ext-file-input');
    const btn   = document.getElementById('ext-file-btn');
    if (!input?.files?.length) { showAlert('Select a file first', 'warning'); return; }

    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    if (btn) btn.disabled = true;
    try {
        const data = await fetch(`${RAG_API}/extract/file`, { method: 'POST', body: formData }).then(r => r.json());
        if (data.success) {
            showExtractionPreview(data.files, file.name);
            showAlert(`✅ Extracted ${data.total_chars?.toLocaleString() || 0} chars from ${file.name}`, 'success');
        } else {
            showAlert(`❌ ${data.error}`, 'danger');
        }
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    } finally {
        if (btn) btn.disabled = false;
    }
}

/**
 * Extracts text from a URL via POST /api/v1/rag/extract/url.
 */
export async function extractFromURL() {
    const urlInput = document.getElementById('ext-url-input');
    const btn      = document.getElementById('ext-url-btn');
    const url      = urlInput?.value.trim();
    if (!url) { showAlert('Enter a URL first', 'warning'); return; }

    const jsEnabled     = document.getElementById('ext-js-enabled')?.checked || false;
    const imagesEnabled = document.getElementById('ext-images-enabled')?.checked || false;

    if (btn) btn.disabled = true;
    try {
        const data = await fetch(`${RAG_API}/extract/url`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url,
                enable_javascript: jsEnabled,
                process_images: imagesEnabled,
                web_page_timeout: 30,
            }),
        }).then(r => r.json());

        if (data.success) {
            showExtractionPreview(data.files, url);
            showAlert(`✅ Extracted ${data.total_chars?.toLocaleString() || 0} chars from URL`, 'success');
        } else {
            showAlert(`❌ ${data.error}`, 'danger');
        }
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    } finally {
        if (btn) btn.disabled = false;
    }
}

/** Copies extracted text to clipboard. */
export function copyExtractedText() {
    const textEl = document.getElementById('ext-result-text');
    if (!textEl?.value) return;
    navigator.clipboard.writeText(textEl.value)
        .then(() => showAlert('✅ Copied to clipboard', 'success'))
        .catch(() => showAlert('❌ Clipboard access denied', 'danger'));
}

// ── Инициализация ─────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    refreshRAGStatus();
    ragLoadProfiles();
    ragLoadDocuments();
});

// ── Document Manager ──────────────────────────────────────────────────────────

/**
 * Load and render the document list from /api/v1/rag/documents.
 */
export async function ragLoadDocuments() {
    const listEl  = document.getElementById('rag-documents-list');
    const countEl = document.getElementById('rag-doc-count');
    const statsEl = document.getElementById('rag-doc-stats');
    if (!listEl) return;

    listEl.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm"></div></div>';

    try {
        const [docsData, statsData] = await Promise.all([
            fetch(`${RAG_API}/documents`).then(r => r.json()),
            fetch(`${RAG_API}/documents/stats`).then(r => r.json()).catch(() => null),
        ]);

        if (!docsData.success) {
            listEl.innerHTML = `<div class="text-danger p-3 small">${docsData.error}</div>`;
            return;
        }

        if (countEl) countEl.textContent = docsData.total;

        if (statsEl && statsData?.success) {
            const s = statsData;
            const compactBtn = document.getElementById('rag-compact-btn');
            if (compactBtn) compactBtn.style.display = s.compact_recommended ? '' : 'none';
            statsEl.innerHTML =
                `Документов: <strong>${s.documents}</strong> &nbsp;| ` +
                `Активных чанков: <strong>${s.active_chunks}</strong> &nbsp;| ` +
                `Векторов FAISS: <strong>${s.faiss_vectors}</strong>` +
                (s.compact_recommended ? ' &nbsp;<span class="badge bg-warning text-dark">Рекомендуется Compact</span>' : '');
        }

        if (!docsData.documents.length) {
            listEl.innerHTML = '<div class="text-muted text-center p-3"><small>Нет документов. Добавьте первый →</small></div>';
            return;
        }

        listEl.innerHTML = docsData.documents.map(d => `
            <div class="d-flex align-items-center gap-2 px-3 py-2 border-bottom">
                <div class="flex-grow-1 overflow-hidden">
                    <strong style="font-size:.85rem">${_esc(d.title)}</strong>
                    <small class="text-muted d-block text-truncate">${d.source_path || ''}</small>
                    <small class="text-muted">${d.chunk_count ?? 0} chunks &middot; ${_fmtDate(d.updated_at)}</small>
                </div>
                <button class="btn btn-sm btn-outline-secondary" onclick="ragEditDocument(${d.id})" title="Edit">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-info" onclick="ragReindexDocument(${d.id})" title="Force reindex">
                    <i class="bi bi-arrow-repeat"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="ragDeleteDocument(${d.id})" title="Delete">
                    <i class="bi bi-trash"></i>
                </button>
            </div>`).join('');
    } catch (e) {
        listEl.innerHTML = `<div class="text-danger p-3 small">${e.message}</div>`;
    }
}

/** Open the Add Document modal. */
export function ragShowAddModal() {
    document.getElementById('rag-doc-edit-id').value = '';
    document.getElementById('rag-doc-title').value = '';
    document.getElementById('rag-doc-content').value = '';
    document.getElementById('rag-doc-source').value = '';
    document.getElementById('rag-doc-char-count').textContent = '0 chars';
    document.getElementById('ragDocModalTitle').textContent = 'Add Document';
    bootstrap.Modal.getOrCreateInstance(document.getElementById('ragDocModal')).show();
}

/** Load document data into the modal for editing. */
export async function ragEditDocument(id) {
    try {
        const data = await fetch(`${RAG_API}/documents/${id}`).then(r => r.json());
        if (!data.success) { showAlert(`❌ ${data.error}`, 'danger'); return; }
        const d = data.document;
        document.getElementById('rag-doc-edit-id').value = d.id;
        document.getElementById('rag-doc-title').value = d.title;
        document.getElementById('rag-doc-content').value = d.content;
        document.getElementById('rag-doc-source').value = d.source_path || '';
        document.getElementById('rag-doc-char-count').textContent = d.content.length + ' chars';
        document.getElementById('ragDocModalTitle').textContent = 'Edit Document';
        bootstrap.Modal.getOrCreateInstance(document.getElementById('ragDocModal')).show();
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    }
}

/** Save (add or update) document from modal. */
export async function ragSaveDocument() {
    const id      = document.getElementById('rag-doc-edit-id').value;
    const title   = document.getElementById('rag-doc-title').value.trim();
    const content = document.getElementById('rag-doc-content').value.trim();
    const source  = document.getElementById('rag-doc-source').value.trim();
    const btn     = document.getElementById('rag-doc-save-btn');

    if (!title || !content) { showAlert('Заполните title и content', 'warning'); return; }

    if (btn) btn.disabled = true;
    try {
        const isEdit = Boolean(id);
        const url    = isEdit ? `${RAG_API}/documents/${id}` : `${RAG_API}/documents`;
        const method = isEdit ? 'PUT' : 'POST';
        const body   = isEdit ? { title, content } : { title, content, source_path: source };

        const data = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        }).then(r => r.json());

        if (data.success) {
            const msg = isEdit
                ? (data.changed ? `✅ Обновлено, ${data.chunks_added} чанков` : '✅ Без изменений (контент не изменился)')
                : `✅ Добавлено (id=${data.doc_id}), ${data.chunks_added} чанков`;
            showAlert(msg, 'success');
            bootstrap.Modal.getOrCreateInstance(document.getElementById('ragDocModal')).hide();
            ragLoadDocuments();
            refreshRAGStatus();
        } else {
            showAlert(`❌ ${data.error}`, 'danger');
        }
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    } finally {
        if (btn) btn.disabled = false;
    }
}

/** Force reindex a single document. */
export async function ragReindexDocument(id) {
    try {
        const data = await fetch(`${RAG_API}/documents/${id}/reindex`, { method: 'POST' }).then(r => r.json());
        showAlert(data.success ? `✅ Переиндексировано, ${data.chunks_added} чанков` : `❌ ${data.error}`, data.success ? 'success' : 'danger');
        if (data.success) { ragLoadDocuments(); refreshRAGStatus(); }
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    }
}

/** Delete a document after confirmation. */
export async function ragDeleteDocument(id) {
    if (!confirm('Удалить документ и его чанки?')) return;
    try {
        const data = await fetch(`${RAG_API}/documents/${id}`, { method: 'DELETE' }).then(r => r.json());
        showAlert(data.success ? '✅ Удалён' : `❌ ${data.error}`, data.success ? 'success' : 'danger');
        if (data.success) { ragLoadDocuments(); refreshRAGStatus(); }
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    }
}

/** Compact FAISS index (remove dead vectors). */
export async function ragCompactIndex() {
    if (!confirm('Перестроить FAISS индекс? Может занять несколько секунд.')) return;
    try {
        const data = await fetch(`${RAG_API}/compact`, { method: 'POST' }).then(r => r.json());
        showAlert(
            data.success
                ? `✅ Compact: ${data.vectors_before} → ${data.vectors_after} векторов`
                : `❌ ${data.error}`,
            data.success ? 'success' : 'danger'
        );
        if (data.success) { ragLoadDocuments(); refreshRAGStatus(); }
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _esc(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function _fmtDate(iso) {
    if (!iso) return '';
    try { return new Date(iso).toLocaleString(); } catch { return iso; }
}
