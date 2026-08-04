/**
 * agent.js — AI Agent tab
 *
 * Contains:
 *  - agentLoadTools()       — load agent list and tools on tab open
 *  - agentRefreshTools()    — refresh tools for selected agent
 *  - agentRun()             — send text task to agent
 *  - agentOnSelectChange()  — switch UI when agent changes
 *  - agentClearMessages()   — clear message area
 *  - agentKsGenDemo()       — generate demo keystroke data
 *  - agentKsTrain()         — send train_model task for keystroke agent
 *  - agentKsPredict()       — send predict_user task for keystroke agent
 *  - agentKsRecordSession() — interactive keystroke recording
 */

import { showAlert } from './ui.js';

const AGENT_API = '/api/v1/agent';

// ── Helpers ───────────────────────────────────────────────────────────────────

function _msgs() { return document.getElementById('agent-messages'); }
function _agentName() { return document.getElementById('agent-name')?.value || 'rag'; }

function _appendUser(text) {
    const msgs = _msgs();
    if (!msgs) return;
    msgs.querySelector('#agent-empty-hint')?.remove();
    msgs.innerHTML += `<div class="mb-2"><span class="badge bg-primary">You</span> <span style="white-space:pre-wrap">${text}</span></div>`;
    msgs.scrollTop = msgs.scrollHeight;
}

function _appendThinking() {
    const id = `think-${Date.now()}`;
    const msgs = _msgs();
    if (msgs) {
        msgs.innerHTML += `<div id="${id}" class="mb-2 text-muted"><i class="bi bi-gear-fill spin"></i> Агент думает...</div>`;
        msgs.scrollTop = msgs.scrollHeight;
    }
    return id;
}

function _removeThinking(id) { document.getElementById(id)?.remove(); }

function _appendResult(d) {
    const msgs = _msgs();
    if (!msgs) return;

    // Tool calls
    for (const tc of (d.tool_calls || [])) {
        let resultText = tc.result || '';
        // Pretty-print JSON results
        try { resultText = JSON.stringify(JSON.parse(tc.result), null, 2); } catch (_) {}
        msgs.innerHTML += `
            <div class="mb-2 p-2 border rounded" style="background:#f0f4ff;font-size:.82rem">
                <i class="bi bi-gear"></i> <strong>${tc.tool}</strong>
                <code class="d-block mt-1 text-muted" style="font-size:.75rem">${JSON.stringify(tc.arguments).slice(0, 120)}…</code>
                <pre class="mt-1 mb-0" style="font-size:.78rem;max-height:140px;overflow-y:auto;white-space:pre-wrap">${resultText}</pre>
            </div>`;
    }

    // Final answer
    if (d.success) {
        msgs.innerHTML += `<div class="mb-3"><span class="badge bg-success">Agent</span> <span style="white-space:pre-wrap">${d.answer || ''}</span></div>`;
    } else {
        msgs.innerHTML += `<div class="mb-2 text-danger">❌ ${d.error || 'Unknown error'}</div>`;
    }
    if (d.note) {
        msgs.innerHTML += `<div class="mb-2 text-muted" style="font-size:.8rem">ℹ️ ${d.note}</div>`;
    }
    msgs.scrollTop = msgs.scrollHeight;
}

async function _runTask(message) {
    const btn = document.getElementById('agent-btn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<div class="spinner-border spinner-border-sm"></div>'; }

    _appendUser(message);
    const thinkId = _appendThinking();

    try {
        const d = await fetch(`${AGENT_API}/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                agent:          _agentName(),
                model:          document.getElementById('agent-model')?.value.trim() || undefined,
                temperature:    parseFloat(document.getElementById('agent-temp')?.value || '0.3'),
                max_iterations: parseInt(document.getElementById('agent-max-iter')?.value || '5'),
            })
        }).then(r => r.json());

        _removeThinking(thinkId);
        _appendResult(d);
    } catch (e) {
        _removeThinking(thinkId);
        const msgs = _msgs();
        if (msgs) msgs.innerHTML += `<div class="mb-2 text-danger">❌ ${e.message}</div>`;
        console.error('Agent run failed:', e);
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-send"></i> Run'; }
    }
}

// ── Public: common ────────────────────────────────────────────────────────────

export function agentClearMessages() {
    const msgs = _msgs();
    if (msgs) msgs.innerHTML = `
        <div class="text-muted text-center p-4" id="agent-empty-hint">
            <i class="bi bi-robot" style="font-size:2rem"></i><br>
            <span>Send a task to the agent</span>
        </div>`;
}

export async function agentLoadTools() {
    try {
        const dl = await fetch(`${AGENT_API}/list`).then(r => r.json());
        const sel = document.getElementById('agent-name');
        if (sel && dl.success) {
            sel.innerHTML = dl.agents.map(a =>
                `<option value="${a.name}" title="${a.description}">${a.name}</option>`
            ).join('');
        }
    } catch (e) {
        console.error('Failed to load agent list:', e);
    }
    agentOnSelectChange();
}

export async function agentRefreshTools() {
    const el   = document.getElementById('agent-tools-list');
    const name = _agentName();
    if (!el) return;

    el.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm"></div></div>';
    try {
        const d = await fetch(`${AGENT_API}/${name}/tools`).then(r => r.json());
        if (!d.success) {
            el.innerHTML = `<div class="text-danger p-2">Error: ${d.detail || 'Unknown error'}</div>`;
            return;
        }
        el.innerHTML = d.tools.map(t => `
            <div class="px-3 py-2 border-bottom">
                <strong style="font-size:.8rem">${t}</strong>
                <div class="text-muted" style="font-size:.75rem">${d.descriptions?.[t] || ''}</div>
            </div>`).join('');
    } catch (e) {
        el.innerHTML = `<div class="text-danger p-2">${e.message}</div>`;
    }
}

/** Switch UI layout when agent selector changes */
export function agentOnSelectChange() {
    const name = _agentName();

    // Update badge
    const badge = document.getElementById('agent-active-badge');
    if (badge) badge.textContent = name;

    // Show/hide keystroke panel and text input
    const ksPanel   = document.getElementById('keystroke-panel');
    const textInput = document.getElementById('agent-text-input-row');
    if (name === 'keystroke') {
        ksPanel?.style && (ksPanel.style.display = '');
        textInput?.style && (textInput.style.display = 'none');
    } else {
        ksPanel?.style && (ksPanel.style.display = 'none');
        textInput?.style && (textInput.style.display = '');
    }

    agentRefreshTools();
}

export async function agentRun() {
    const input   = document.getElementById('agent-input');
    const message = input?.value.trim();
    if (!message) return;
    input.value = '';
    await _runTask(message);
}

// ── Public: keystroke agent ───────────────────────────────────────────────────

/** Generate demo training data for two users */
export function agentKsGenDemo() {
    // Alice: fast typist ~90-110ms, Bob: slow typist ~140-165ms
    function randSession(mean, spread, len = 20) {
        return Array.from({ length: len }, () =>
            Math.round(mean + (Math.random() - 0.5) * spread * 2)
        );
    }
    const demo = {
        alice: Array.from({ length: 5 }, () => randSession(100, 15)),
        bob:   Array.from({ length: 5 }, () => randSession(152, 15)),
    };
    const ta = document.getElementById('ks-users-data');
    if (ta) ta.value = JSON.stringify(demo, null, 2);

    // Also fill predict session with an alice-like session
    const ps = document.getElementById('ks-predict-session');
    if (ps) ps.value = JSON.stringify(randSession(100, 15));
}

/** Send train_model task to keystroke agent */
export async function agentKsTrain() {
    const raw = document.getElementById('ks-users-data')?.value.trim();
    if (!raw) { showAlert('Введите данные пользователей', 'warning'); return; }

    let users_data;
    try { users_data = JSON.parse(raw); } catch (_) {
        showAlert('Некорректный JSON в поле данных', 'danger'); return;
    }

    const msg = `Обучи модель идентификации по клавиатурному почерку на следующих данных: ${JSON.stringify(users_data)}`;
    await _runTask(msg);
}

/** Send predict_user task to keystroke agent */
export async function agentKsPredict() {
    const raw = document.getElementById('ks-predict-session')?.value.trim();
    if (!raw) { showAlert('Введите сессию для идентификации', 'warning'); return; }

    let session;
    try { session = JSON.parse(raw); } catch (_) {
        showAlert('Некорректный JSON в поле сессии', 'danger'); return;
    }

    const msg = `Определи пользователя по этой сессии нажатий клавиш: ${JSON.stringify(session)}`;
    await _runTask(msg);
}

/** Interactive keystroke recording: measure key-hold durations in a modal input */
export function agentKsRecordSession() {
    const durations = [];
    let pressTime = null;

    // Create overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center';
    overlay.innerHTML = `
        <div class="card" style="width:380px">
            <div class="card-header d-flex justify-content-between">
                <span><i class="bi bi-keyboard"></i> Recording keystrokes…</span>
                <button class="btn-close" id="ks-rec-close"></button>
            </div>
            <div class="card-body text-center">
                <p class="text-muted mb-2" style="font-size:.85rem">
                    Type any text below. Key-hold durations will be recorded.
                </p>
                <input id="ks-rec-input" class="form-control mb-3" placeholder="Type here..." autocomplete="off">
                <div class="mb-2">
                    Recorded: <strong id="ks-rec-count">0</strong> keystrokes
                </div>
                <button class="btn btn-success btn-sm" id="ks-rec-done">
                    <i class="bi bi-check-lg"></i> Use this session
                </button>
            </div>
        </div>`;
    document.body.appendChild(overlay);

    const recInput = overlay.querySelector('#ks-rec-input');
    recInput.focus();

    recInput.addEventListener('keydown', e => {
        pressTime = performance.now();
    });

    recInput.addEventListener('keyup', e => {
        if (pressTime !== null) {
            durations.push(Math.round(performance.now() - pressTime));
            pressTime = null;
            overlay.querySelector('#ks-rec-count').textContent = durations.length;
        }
    });

    overlay.querySelector('#ks-rec-done').addEventListener('click', () => {
        if (durations.length > 0) {
            const ps = document.getElementById('ks-predict-session');
            if (ps) ps.value = JSON.stringify(durations);
        }
        document.body.removeChild(overlay);
    });

    overlay.querySelector('#ks-rec-close').addEventListener('click', () => {
        document.body.removeChild(overlay);
    });
}

/** @deprecated kept for backward compat */
export async function runAgentExample() {}
