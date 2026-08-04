/**
 * ui.js — Вспомогательные функции интерфейса
 *
 * Содержит:
 *  - showAlert()          — всплывающие уведомления
 *  - updateChatModelBadge() — бейдж активной модели в шапке чата
 *  - updateModelStatus()  — заглушка для статуса модели
 *  - hideProgress()       — скрытие прогресс-бара загрузки
 *  - clearFoundryLogs()   — очистка лога Foundry
 *  - addLog()             — добавление записи в системный лог
 *  - refreshLogs()        — обновление логов с сервера
 *  - filterLogs()         — фильтрация логов по уровню
 */

// ── Уведомления ───────────────────────────────────────────────────────────────

/**
 * Показывает всплывающее уведомление Bootstrap.
 * Автоматически исчезает через 5 секунд.
 * @param {string} message - Текст уведомления
 * @param {'info'|'success'|'warning'|'danger'} type
 */
export function showAlert(message, type = 'info') {
    const container = document.getElementById('alert-container');
    if (!container) return;

    const el = document.createElement('div');
    el.className = `alert alert-${type} alert-dismissible fade show`;
    el.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    container.appendChild(el);

    setTimeout(() => {
        el.classList.remove('show');
        setTimeout(() => el.remove(), 150);
    }, 5000);
}

// ── Модель ────────────────────────────────────────────────────────────────────

/**
 * Updates the chat stats badge: model name, response time, token count.
 * @param {string} modelId
 * @param {{totalTokens?: number, elapsedMs?: number}} [stats]
 */
export function updateChatModelBadge(modelId, stats = {}) {
    const badge     = document.getElementById('chat-model-badge');
    const statWrap  = document.getElementById('chat-stats-badge');
    const timerEl   = document.getElementById('chat-timer');
    const timerVal  = document.getElementById('chat-timer-value');
    const tokBadge  = document.getElementById('chat-tokens-badge');
    const tokVal    = document.getElementById('chat-tokens-value');

    if (!badge) return;

    if (modelId) {
        badge.textContent = modelId.startsWith('hf::') ? '🤗 ' + modelId.slice(4) : modelId;
        if (statWrap) statWrap.style.display = '';
    } else {
        if (statWrap) statWrap.style.display = 'none';
        return;
    }

    if (stats.elapsedMs != null && timerEl && timerVal) {
        timerVal.textContent = (stats.elapsedMs / 1000).toFixed(1) + 's';
        timerEl.style.display = '';
    }

    if (stats.totalTokens != null && tokBadge && tokVal) {
        tokVal.textContent = stats.totalTokens;
        tokBadge.style.display = '';
    }
}

/** Заглушка — статус модели выводится только в консоль */
export function updateModelStatus(message, type) {
    console.log(`[Status: ${type}] ${message}`);
}

// ── Прогресс ──────────────────────────────────────────────────────────────────

/** Скрывает блок прогресс-бара загрузки модели */
export function hideProgress() {
    const el = document.getElementById('download-progress');
    if (el) el.style.display = 'none';
}

// ── Foundry логи ──────────────────────────────────────────────────────────────

/** Очищает блок логов Foundry на вкладке Foundry */
export function clearFoundryLogs() {
    const el = document.getElementById('foundry-logs');
    if (el) el.innerHTML = '<div class="text-muted text-center mt-5"><i class="bi bi-terminal"></i><br>Foundry logs cleared</div>';
}

// ── Log Viewer (Logs tab) ─────────────────────────────────────────────────────

/** @type {number|null} Auto-refresh interval id */
let _logRefreshTimer = null;

/** @type {number} Current pagination offset (lines from tail) */
let _logOffset = 0;

/** @type {boolean} Word-wrap state */
let _logWrap = false;

/** Level → Bootstrap text color class */
const _LEVEL_CLASS = {
    DEBUG:    'text-secondary',
    INFO:     'text-info',
    WARNING:  'text-warning',
    ERROR:    'text-danger',
    CRITICAL: 'text-danger fw-bold',
};

/**
 * Detect log level from a plain-text log line.
 * @param {string} line
 * @returns {string}
 */
function _detectLevel(line) {
    for (const lvl of ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']) {
        if (line.includes(lvl)) return lvl;
    }
    return 'INFO';
}

/**
 * Render a single log line as a colored <div>.
 * Highlights search term if provided.
 * @param {string} line
 * @param {string} search
 * @returns {HTMLElement}
 */
function _renderLine(line, search = '') {
    const level = _detectLevel(line);
    const cls   = _LEVEL_CLASS[level] || '';
    const el    = document.createElement('div');
    el.className = `log-line ${cls}`;

    if (search) {
        // Highlight search term (case-insensitive)
        const escaped = search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const html = line.replace(
            new RegExp(`(${escaped})`, 'gi'),
            '<mark>$1</mark>'
        );
        el.innerHTML = html;
    } else {
        el.textContent = line;
    }
    return el;
}

/**
 * Fetch logs from API and render into #log-output.
 * @param {boolean} append - If true, prepend older lines (pagination).
 */
export async function refreshLogs(append = false) {
    const output  = document.getElementById('log-output');
    const status  = document.getElementById('log-status');
    const footer  = document.getElementById('log-footer-info');
    const moreBtn = document.getElementById('log-load-more');
    if (!output) return;

    const file   = document.getElementById('log-file-select')?.value  || '';
    const level  = document.getElementById('log-level-filter')?.value || '';
    const search = document.getElementById('log-search')?.value       || '';
    const lines  = document.getElementById('log-lines-count')?.value  || '200';

    const params = new URLSearchParams({ file, lines, level, search, offset: _logOffset });

    try {
        if (status) status.textContent = 'Loading…';
        const data = await fetch(`${window.API_BASE}/logs?${params}`).then(r => r.json());
        if (!data.success) throw new Error(data.detail || 'API error');

        if (!append) {
            output.innerHTML = '';
        }

        const frag = document.createDocumentFragment();
        for (const line of data.lines) {
            frag.appendChild(_renderLine(line, search));
        }

        if (append) {
            output.insertBefore(frag, output.firstChild);
        } else {
            output.appendChild(frag);
            output.scrollTop = output.scrollHeight;
        }

        if (status) status.textContent = `${file} — ${data.filtered_total} lines`;
        if (footer) footer.textContent = `Showing ${data.returned} of ${data.filtered_total} filtered (${data.total_lines} total)`;
        if (moreBtn) moreBtn.style.display = data.has_more ? '' : 'none';

    } catch (e) {
        if (status) status.textContent = `Error: ${e.message}`;
        console.error('Log fetch failed:', e);
    }
}

/** Load older lines (pagination). */
async function _loadMore() {
    const lines = parseInt(document.getElementById('log-lines-count')?.value || '200');
    _logOffset += lines;
    await refreshLogs(true);
}

/** Toggle auto-refresh every 5 s. */
function _toggleAutoRefresh(enabled) {
    clearInterval(_logRefreshTimer);
    if (enabled) {
        _logRefreshTimer = setInterval(() => refreshLogs(), 5000);
    }
}

/** Toggle word-wrap on log output. */
function _toggleWrap() {
    _logWrap = !_logWrap;
    const el = document.getElementById('log-output');
    if (el) el.classList.toggle('log-viewer--wrap', _logWrap);
}

/** Download current log file from server. */
function _downloadLog() {
    const file = document.getElementById('log-file-select')?.value || '';
    if (!file) return showAlert('No log file selected', 'warning');
    window.open(`${window.API_BASE}/logs/download?file=${encodeURIComponent(file)}`, '_blank');
}

/** Clear current log file via API. */
async function _clearLog() {
    const file = document.getElementById('log-file-select')?.value || '';
    if (!file) return showAlert('No log file selected', 'warning');
    if (!confirm(`Clear ${file}?`)) return;
    try {
        const data = await fetch(
            `${window.API_BASE}/logs/clear?file=${encodeURIComponent(file)}`,
            { method: 'POST' }
        ).then(r => r.json());
        if (data.success) {
            document.getElementById('log-output').innerHTML = '';
            showAlert(data.message, 'success');
        }
    } catch (e) {
        showAlert('Failed to clear log', 'danger');
    }
}

/** Populate file selector from /logs/files. */
async function _loadFileList() {
    const sel = document.getElementById('log-file-select');
    if (!sel) return;
    try {
        const data = await fetch(`${window.API_BASE}/logs/files`).then(r => r.json());
        if (!data.success) return;
        if (data.files.length) {
            sel.innerHTML = data.files.map(f =>
                `<option value="${f.name}">${f.name} (${f.size_kb} KB)</option>`
            ).join('');
        } else {
            sel.innerHTML = '<option value="">No log files yet</option>';
        }
        const dirInfo = document.getElementById('log-dir-info');
        if (dirInfo) dirInfo.textContent = data.log_dir || '';
    } catch (_) { /* keep default option */ }
}

/** Load log retention settings into the toolbar. */
async function _loadLogSettings() {
    try {
        const data = await fetch(`${window.API_BASE}/logs/settings`).then(r => r.json());
        if (!data.success) return;
        const settings = data.settings || {};
        const maxLines = document.getElementById('log-max-lines');
        const retention = document.getElementById('log-retention-days');
        const dirInfo = document.getElementById('log-dir-info');
        if (maxLines) maxLines.value = settings.max_lines_per_file || 5000;
        if (retention) retention.value = settings.retention_days || 7;
        if (dirInfo) dirInfo.textContent = settings.log_dir || '';
    } catch (e) {
        console.error('Log settings fetch failed:', e);
    }
}

/** Save log retention settings. */
async function _saveLogSettings() {
    const maxLines = parseInt(document.getElementById('log-max-lines')?.value || '5000', 10);
    const retention = parseInt(document.getElementById('log-retention-days')?.value || '7', 10);
    try {
        const data = await fetch(`${window.API_BASE}/logs/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                max_lines_per_file: maxLines,
                retention_days: retention,
                level: 'WARNING',
            }),
        }).then(r => r.json());
        if (!data.success) throw new Error(data.detail || 'API error');
        showAlert('Log settings saved', 'success');
        await _loadFileList();
        await refreshLogs();
    } catch (e) {
        showAlert(`Failed to save log settings: ${e.message}`, 'danger');
    }
}

/**
 * Initialize log viewer — attach all event listeners.
 * Called once when the Logs tab becomes active.
 */
export function initLogViewer() {
    _loadLogSettings();
    _loadFileList().then(() => refreshLogs());

    // Reset offset on any filter change
    const resetAndRefresh = () => { _logOffset = 0; refreshLogs(); };

    document.getElementById('log-file-select')  ?.addEventListener('change', resetAndRefresh);
    document.getElementById('log-level-filter') ?.addEventListener('change', resetAndRefresh);
    document.getElementById('log-lines-count')  ?.addEventListener('change', resetAndRefresh);
    document.getElementById('log-refresh-btn')  ?.addEventListener('click',  resetAndRefresh);

    // Search with debounce
    let _searchTimer;
    document.getElementById('log-search')?.addEventListener('input', () => {
        clearTimeout(_searchTimer);
        _searchTimer = setTimeout(resetAndRefresh, 400);
    });
    document.getElementById('log-search-clear')?.addEventListener('click', () => {
        const el = document.getElementById('log-search');
        if (el) { el.value = ''; resetAndRefresh(); }
    });

    document.getElementById('log-auto-refresh') ?.addEventListener('change', e => _toggleAutoRefresh(e.target.checked));
    document.getElementById('log-wrap-toggle')  ?.addEventListener('click',  _toggleWrap);
    document.getElementById('log-scroll-bottom')?.addEventListener('click',  () => {
        const el = document.getElementById('log-output');
        if (el) el.scrollTop = el.scrollHeight;
    });
    document.getElementById('log-load-more')    ?.addEventListener('click',  _loadMore);
    document.getElementById('log-download-btn') ?.addEventListener('click',  _downloadLog);
    document.getElementById('log-clear-btn')    ?.addEventListener('click',  _clearLog);
    document.getElementById('log-save-settings-btn')?.addEventListener('click', _saveLogSettings);
}

/** @deprecated Use initLogViewer() instead. */
export function filterLogs() { refreshLogs(); }
export function downloadLogs() { _downloadLog(); }
export async function clearLogFile() { await _clearLog(); }
export function addLog(message, level = 'info') {
    const el = document.getElementById('log-output');
    if (el) el.appendChild(_renderLine(`[${new Date().toLocaleTimeString()}] ${message}`));
}

/** @type {number|null} ID интервала мигания заголовка */
let _flashingInterval = null;
/** @type {string} Исходный заголовок страницы */
let _originalTitle = document.title;

/**
 * Запускает мигание заголовка вкладки браузера.
 * @param {string} message - Текст для мигания.
 */
export function startFlashingTitle(message = '⚠️ ВНИМАНИЕ!') {
    if (_flashingInterval) return;
    _originalTitle = document.title;
    let isOriginal = true;
    _flashingInterval = setInterval(() => {
        document.title = isOriginal ? message : _originalTitle;
        isOriginal = !isOriginal;
    }, 1000);
}

/**
 * Останавливает мигание заголовка вкладки и возвращает исходный текст.
 */
export function stopFlashingTitle() {
    if (!_flashingInterval) return;
    clearInterval(_flashingInterval);
    _flashingInterval = null;
    document.title = _originalTitle;
}

/**
 * Автоматически закрывает модальное окно HITL при получении таймаута от сервера.
 * @param {string} permissionId - ID запроса.
 */
export function handleHitlTimeout(permissionId) {
    const modal = document.getElementById(`hitl-modal-${permissionId}`);
    if (modal) {
        modal.remove();
        showAlert(`Время ожидания подтверждения ${permissionId} истекло`, 'warning');
        stopFlashingTitle();
    }
}

/**
 * Воспроизводит звуковое уведомление для нового запроса HITL.
 */
export function playHitlNotification() {
    const audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3');
    audio.volume = 0.5;
    audio.play().catch(err => console.debug('Sound notification blocked or failed:', err));
}
