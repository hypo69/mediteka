/**
 * mcp.js — Управление MCP PowerShell серверами
 *
 * Содержит:
 *  - mcpLoadServers()         — загрузка списка серверов
 *  - mcpStart(name)           — запуск сервера
 *  - mcpStop(name)            — остановка сервера
 *  - startAllMCPServers()     — запуск всех серверов
 *  - stopAllMCPServers()      — остановка всех серверов
 *  - refreshMCPServers()      — алиас mcpLoadServers
 *  - mcpOpenSettingsEditor()  — открыть редактор settings.json
 *  - mcpSaveSettings()        — сохранить settings.json
 *  - mcpCloseSettingsEditor() — закрыть редактор
 */

import { showAlert } from './ui.js';

const MCP_API = '/api/v1/mcp-powershell';

// ── Список серверов ───────────────────────────────────────────────────────────

/**
 * Загружает список MCP серверов и отрисовывает в #mcp-servers-list.
 * Каждый сервер показывает статус и кнопку Start/Stop.
 */
export async function mcpLoadServers() {
    const list = document.getElementById('mcp-servers-list');
    if (!list) return;
    list.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm"></div></div>';

    try {
        const data = await fetch(`${MCP_API}/servers`).then(r => r.json());
        if (!data.success) {
            list.innerHTML = `<div class="text-danger p-3">${data.detail || 'Error loading servers'}</div>`;
            return;
        }
        if (!data.servers.length) {
            list.innerHTML = '<div class="text-muted text-center p-4">No MCP servers configured in settings.json</div>';
            return;
        }

        list.innerHTML = data.servers.map(srv => {
            const running = srv.status === 'running';
            return `
                <div class="d-flex align-items-center gap-3 px-3 py-2 border-bottom" id="mcp-row-${srv.name}">
                    <div class="flex-grow-1">
                        <strong style="font-size:.9rem">${srv.name}</strong>
                        <small class="text-muted d-block">${srv.description || ''}</small>
                    </div>
                    <span class="badge ${running ? 'bg-success' : 'bg-secondary'}">
                        ${running ? '● Running' : '○ Stopped'}
                    </span>
                    ${running
                        ? `<button class="btn btn-sm btn-danger" onclick="mcpStop('${srv.name}')"><i class="bi bi-stop-fill"></i> Stop</button>`
                        : `<button class="btn btn-sm btn-success" onclick="mcpStart('${srv.name}')"><i class="bi bi-play-fill"></i> Start</button>`
                    }
                </div>`;
        }).join('');
    } catch (e) {
        list.innerHTML = `<div class="text-danger p-3">Error: ${e.message}</div>`;
        console.error('MCP load servers failed:', e);
    }
}

/** Алиас для кнопки Refresh */
export const refreshMCPServers = mcpLoadServers;

// ── Управление серверами ──────────────────────────────────────────────────────

/**
 * Запускает MCP сервер по имени.
 * @param {string} name
 */
export async function mcpStart(name) {
    try {
        const d = await fetch(`${MCP_API}/servers/${name}/start`, { method: 'POST' }).then(r => r.json());
        showAlert(d.success ? `✅ ${d.message}` : `❌ ${d.detail || d.message}`, d.success ? 'success' : 'danger');
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
        console.error('MCP start failed:', e);
    }
    setTimeout(mcpLoadServers, 800);
}

/**
 * Останавливает MCP сервер по имени.
 * @param {string} name
 */
export async function mcpStop(name) {
    try {
        const d = await fetch(`${MCP_API}/servers/${name}/stop`, { method: 'POST' }).then(r => r.json());
        showAlert(d.success ? `✅ ${d.message}` : `❌ ${d.detail || d.message}`, d.success ? 'success' : 'danger');
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
        console.error('MCP stop failed:', e);
    }
    setTimeout(mcpLoadServers, 800);
}

/** Запускает все серверы последовательно */
export async function startAllMCPServers() {
    try {
        const data = await fetch(`${MCP_API}/servers`).then(r => r.json());
        for (const srv of (data.servers || [])) {
            if (srv.status !== 'running') await mcpStart(srv.name);
        }
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    }
}

/** Останавливает все серверы последовательно */
export async function stopAllMCPServers() {
    try {
        const data = await fetch(`${MCP_API}/servers`).then(r => r.json());
        for (const srv of (data.servers || [])) {
            if (srv.status === 'running') await mcpStop(srv.name);
        }
    } catch (e) {
        showAlert(`❌ ${e.message}`, 'danger');
    }
}

// ── Редактор settings.json ────────────────────────────────────────────────────

/**
 * Открывает редактор settings.json MCP серверов.
 * Загружает текущие настройки в textarea #mcp-settings-editor.
 */
export async function mcpOpenSettingsEditor() {
    const ta   = document.getElementById('mcp-settings-editor');
    const btns = document.getElementById('mcp-settings-btns');
    const st   = document.getElementById('mcp-settings-status');
    if (!ta) return;

    try {
        const d = await fetch(`${MCP_API}/settings`).then(r => r.json());
        ta.value = JSON.stringify(d.settings, null, 2);
        if (ta)   ta.style.display   = '';
        if (btns) btns.style.display = '';
        if (st)   st.style.display   = 'none';
    } catch (e) {
        if (st) { st.className = 'alert alert-danger py-1 px-2'; st.textContent = `❌ ${e.message}`; st.style.display = ''; }
        console.error('MCP open settings editor failed:', e);
    }
}

/**
 * Сохраняет отредактированный settings.json.
 * Валидирует JSON перед отправкой.
 */
export async function mcpSaveSettings() {
    const ta = document.getElementById('mcp-settings-editor');
    const st = document.getElementById('mcp-settings-status');
    if (!ta) return;

    try {
        const settings = JSON.parse(ta.value); // Бросит SyntaxError если JSON невалидный
        const d = await fetch(`${MCP_API}/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ settings })
        }).then(r => r.json());

        if (st) { st.className = `alert ${d.success ? 'alert-success' : 'alert-danger'} py-1 px-2`; st.textContent = d.success ? '✅ Saved' : `❌ ${d.detail || d.message}`; st.style.display = ''; }
        if (d.success) mcpLoadServers();
    } catch (e) {
        if (st) { st.className = 'alert alert-danger py-1 px-2'; st.textContent = `❌ ${e instanceof SyntaxError ? 'Invalid JSON: ' + e.message : e.message}`; st.style.display = ''; }
        console.error('MCP save settings failed:', e);
    }
}

/** Скрывает редактор settings.json */
export function mcpCloseSettingsEditor() {
    document.getElementById('mcp-settings-editor')?.style && (document.getElementById('mcp-settings-editor').style.display = 'none');
    document.getElementById('mcp-settings-btns')?.style   && (document.getElementById('mcp-settings-btns').style.display   = 'none');
}
