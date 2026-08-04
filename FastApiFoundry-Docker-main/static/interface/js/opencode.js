const API = () => `${window.API_BASE}/opencode`;

function setAlert(message, type = 'info') {
    const el = document.getElementById('opencode-alert');
    if (!el) return;
    el.className = `alert alert-${type} mt-3 py-2`;
    el.style.display = '';
    el.textContent = message;
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value ?? '-';
}

function extractAssistantText(message) {
    const parts = message?.parts || [];
    const text = parts
        .filter(part => part?.type === 'text' && part.text)
        .map(part => part.text)
        .join('\n')
        .trim();
    return text || '';
}

async function readJson(url, options = {}) {
    const res = await fetch(url, options);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.error || res.statusText);
    return data;
}

export async function refreshOpenCodeStatus() {
    try {
        const data = await readJson(`${API()}/status`);
        const health = data.health || {};
        const badge = document.getElementById('opencode-status-badge');
        if (badge) {
            badge.className = `badge ${health.success ? 'bg-success' : 'bg-danger'}`;
            badge.textContent = health.success ? 'Online' : 'Offline';
        }
        setText('opencode-base-url', data.settings?.base_url || health.base_url);
        setText('opencode-version', health.version || data.settings?.target_version || '-');
        setText('opencode-pid', health.running_pid || '-');
        setText('opencode-provider', data.settings?.provider_id || '-');
        setText('opencode-model', data.settings?.model_id || '-');
        setText('opencode-api-base-url', data.settings?.api_base_url || '-');
        const link = document.getElementById('opencode-doc-link');
        if (link) link.href = data.docs_url || '#';
        if (!health.success) setAlert(health.error || 'OpenCode is offline', 'warning');
    } catch (e) {
        setAlert(`Status error: ${e.message}`, 'danger');
    }
}

export async function startOpenCode() {
    setAlert('Starting OpenCode...', 'info');
    const data = await readJson(`${API()}/start`, { method: 'POST' });
    setAlert(data.message || (data.success ? 'Started' : data.error), data.success ? 'success' : 'danger');
    await refreshOpenCodeStatus();
}

export async function stopOpenCode() {
    const data = await readJson(`${API()}/stop`, { method: 'POST' });
    setAlert(data.message || data.error, data.success ? 'success' : 'warning');
    await refreshOpenCodeStatus();
}

export async function loadOpenCodeProviders() {
    const box = document.getElementById('opencode-providers');
    if (box) box.textContent = 'Loading...';
    try {
        const data = await readJson(`${API()}/providers`);
        const providers = data.all || data.providers || [];
        const connected = new Set(data.connected || []);
        if (!box) return;
        box.innerHTML = providers.length
            ? providers.map(p => `<div class="d-flex justify-content-between border-bottom py-1"><span>${p.id || p.name}</span><span class="badge ${connected.has(p.id) ? 'bg-success' : 'bg-secondary'}">${connected.has(p.id) ? 'connected' : 'available'}</span></div>`).join('')
            : '<span class="text-muted">No providers returned.</span>';
    } catch (e) {
        if (box) box.textContent = e.message;
    }
}

export async function loadOpenCodeSessions() {
    const box = document.getElementById('opencode-sessions');
    if (box) box.textContent = 'Loading...';
    try {
        const data = await readJson(`${API()}/sessions`);
        const sessions = Array.isArray(data.sessions) ? data.sessions : [];
        if (!box) return;
        box.innerHTML = sessions.length
            ? sessions.map(s => `<button class="btn btn-sm btn-outline-secondary me-1 mb-1" onclick="document.getElementById('opencode-session-id').value='${s.id || ''}'">${s.title || s.id}</button>`).join('')
            : '<span class="text-muted">No sessions.</span>';
    } catch (e) {
        if (box) box.textContent = e.message;
    }
}

export async function sendOpenCodeMessage() {
    const out = document.getElementById('opencode-output');
    if (out) out.textContent = 'Sending...';
    const body = {
        prompt: document.getElementById('opencode-prompt')?.value || '',
        session_id: document.getElementById('opencode-session-id')?.value || '',
        provider_id: document.getElementById('opencode-provider-id')?.value || '',
        model_id: document.getElementById('opencode-model-id')?.value || '',
        agent: document.getElementById('opencode-agent')?.value || '',
        system: document.getElementById('opencode-system')?.value || '',
    };
    try {
        const data = await readJson(`${API()}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (data.session_id) document.getElementById('opencode-session-id').value = data.session_id;
        const assistantText = extractAssistantText(data.message);
        if (out) out.textContent = assistantText || JSON.stringify(data.message || data, null, 2);
        await loadOpenCodeSessions();
    } catch (e) {
        if (out) out.textContent = e.message;
    }
}
