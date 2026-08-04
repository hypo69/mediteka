// -*- coding: utf-8 -*-
// =============================================================================
// Process Name: Support Chat Widget
// =============================================================================
// Description:
//   Floating support chat widget accessible from any tab via the navbar button.
//
//   Two panels:
//     User panel  — chat with the Telegram HelpDesk bot.
//                   Messages are sent to /api/v1/helpdesk/message and displayed
//                   in a chat bubble layout.
//     Admin panel — view all Telegram user dialogs, manage RAG profiles,
//                   check bot status. Shown only when bot is configured.
//
//   Widget state:
//     - Closed by default, toggled via supportToggleChat()
//     - Admin panel hidden by default, toggled via supportToggleAdminPanel()
//     - Admin sub-tabs: "dialogs" | "rag"
//
// File: js/support.js
// Project: AI Assistant (ai_assist)
// Version: 0.7.1
// Changes in 0.7.1:
//   - Converted from tab to floating chat widget
//   - Added user-facing chat panel with message send/receive
//   - Admin panel now inside the widget (dialogs + RAG profiles)
//   - Navbar button with unread indicator
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

// ── State ─────────────────────────────────────────────────────────────────────

let _supportDialogs   = {};
let _selectedChatId   = null;
let _widgetOpen       = false;
let _adminPanelOpen   = false;
let _adminTab         = 'dialogs';
let _chatMessages     = [];   // local chat history for user panel
let _botEnabled       = false;

// ── Widget toggle ─────────────────────────────────────────────────────────────

export function supportToggleChat() {
    _widgetOpen = !_widgetOpen;
    const widget = document.getElementById('support-widget');
    if (!widget) return;

    widget.style.display = _widgetOpen ? '' : 'none';

    if (_widgetOpen) {
        // Clear unread badge
        const badge = document.getElementById('support-unread-badge');
        if (badge) badge.style.display = 'none';

        // Load status and data
        supportLoadStatus();
        if (_adminPanelOpen) {
            if (_adminTab === 'dialogs') supportLoadDialogs();
            else supportLoadProfiles();
        }
    }
}

export function supportToggleAdminPanel() {
    _adminPanelOpen = !_adminPanelOpen;
    const userPanel  = document.getElementById('support-user-panel');
    const adminPanel = document.getElementById('support-admin-panel');
    if (!userPanel || !adminPanel) return;

    userPanel.style.display  = _adminPanelOpen ? 'none' : '';
    adminPanel.style.display = _adminPanelOpen ? '' : 'none';

    if (_adminPanelOpen) {
        supportAdminTab(_adminTab);
    }
}

export function supportAdminTab(tab) {
    _adminTab = tab;

    document.getElementById('sadmin-dialogs-tab')?.classList.toggle('active', tab === 'dialogs');
    document.getElementById('sadmin-rag-tab')?.classList.toggle('active', tab === 'rag');
    document.getElementById('sadmin-dialogs').style.display = tab === 'dialogs' ? '' : 'none';
    document.getElementById('sadmin-rag').style.display     = tab === 'rag'     ? '' : 'none';

    if (tab === 'dialogs') supportLoadDialogs();
    if (tab === 'rag')     { supportLoadProfiles(); supportLoadStatus(); }
}

// ── User chat ─────────────────────────────────────────────────────────────────

export async function supportSendMessage() {
    const input = document.getElementById('support-chat-input');
    const text  = input?.value.trim();
    if (!text) return;

    input.value = '';
    input.disabled = true;

    // Append user bubble immediately
    _chatMessages.push({ role: 'user', text, ts: new Date().toISOString() });
    _renderChatMessages();

    try {
        const data = await fetch(`${window.API_BASE}/helpdesk/message`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ message: text }),
        }).then(r => r.json());

        if (data.success && data.reply) {
            _chatMessages.push({ role: 'bot', text: data.reply, ts: new Date().toISOString() });
        } else if (!data.success) {
            _chatMessages.push({
                role: 'bot',
                text: data.error || 'Bot is unavailable. Check TELEGRAM_SUPPORT_TOKEN in .env.',
                ts:   new Date().toISOString(),
                error: true,
            });
        }
    } catch (e) {
        _chatMessages.push({
            role: 'bot',
            text: 'Connection error: ' + e.message,
            ts:   new Date().toISOString(),
            error: true,
        });
    } finally {
        input.disabled = false;
        input.focus();
        _renderChatMessages();
    }
}

function _renderChatMessages() {
    const el = document.getElementById('support-chat-messages');
    if (!el) return;

    if (!_chatMessages.length) {
        el.innerHTML = `
            <div class="text-center text-muted mt-5" style="font-size:.85rem">
                <i class="bi bi-chat-square-dots fs-2 d-block mb-2 opacity-25"></i>
                <span data-i18n="support.chat_placeholder">Send a message to start a conversation</span>
            </div>`;
        return;
    }

    el.innerHTML = _chatMessages.map(m => {
        const isUser = m.role === 'user';
        const align  = isUser ? 'justify-content-end' : 'justify-content-start';
        const bg     = isUser ? 'bg-primary text-white' : (m.error ? 'bg-danger text-white' : 'bg-light');
        const ts     = m.ts ? new Date(m.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
        return `
        <div class="d-flex ${align} mb-2">
            <div style="max-width:80%">
                <div class="rounded px-3 py-2 ${bg}" style="font-size:.85rem;word-break:break-word">
                    ${_escHtml(m.text)}
                </div>
                <div class="text-muted mt-1" style="font-size:.65rem;text-align:${isUser ? 'right' : 'left'}">${ts}</div>
            </div>
        </div>`;
    }).join('');

    el.scrollTop = el.scrollHeight;
}

// ── Admin: Dialogs ────────────────────────────────────────────────────────────

export async function supportLoadDialogs() {
    try {
        const data = await fetch(`${window.API_BASE}/helpdesk/dialogs`).then(r => r.json());
        if (!data.success) return;
        _supportDialogs = data.dialogs || {};
        _renderUserList();
    } catch (e) {
        console.error('[support] loadDialogs error:', e);
    }
}

function _renderUserList() {
    const el = document.getElementById('support-users');
    if (!el) return;

    const chatIds = Object.keys(_supportDialogs);
    if (!chatIds.length) {
        el.innerHTML = '<div class="text-muted small p-2">No dialogs yet</div>';
        return;
    }

    el.innerHTML = chatIds.map(id => {
        const msgs     = _supportDialogs[id];
        const username = msgs[0]?.username || id;
        const active   = id === _selectedChatId ? 'bg-primary text-white' : '';
        return `<div class="p-2 border-bottom ${active}"
                     style="cursor:pointer" onclick="supportSelectUser('${id}')">
                    <div class="fw-semibold" style="font-size:.78rem">${_escHtml(username)}</div>
                    <div class="text-muted" style="font-size:.68rem">${msgs.length} msg</div>
                </div>`;
    }).join('');
}

export function supportSelectUser(chatId) {
    _selectedChatId = chatId;
    _renderUserList();
    _renderAdminMessages(chatId);
}

function _renderAdminMessages(chatId) {
    const el = document.getElementById('support-messages');
    if (!el) return;

    const msgs = _supportDialogs[chatId] || [];
    el.innerHTML = msgs.map(m => {
        const isUser = m.role === 'user';
        const align  = isUser ? 'justify-content-end' : 'justify-content-start';
        const bg     = isUser ? 'bg-primary text-white' : 'bg-light';
        const ts     = m.ts ? new Date(m.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
        return `<div class="d-flex ${align} mb-1">
                    <div class="rounded px-2 py-1 ${bg}" style="max-width:85%;font-size:.78rem;word-break:break-word">
                        ${_escHtml(m.text || '')}
                        <div class="opacity-50 mt-1" style="font-size:.65rem">${ts}</div>
                    </div>
                </div>`;
    }).join('');
    el.scrollTop = el.scrollHeight;
}

// ── Admin: RAG Profiles ───────────────────────────────────────────────────────

export async function supportLoadProfiles() {
    try {
        const data = await fetch(`${window.API_BASE}/helpdesk/rag-profiles`).then(r => r.json());
        if (!data.success) return;
        _renderProfiles(data.profiles || []);
    } catch (e) {
        console.error('[support] loadProfiles error:', e);
    }
}

function _renderProfiles(profiles) {
    const el = document.getElementById('support-profiles-list');
    if (!el) return;

    if (!profiles.length) {
        el.innerHTML = '<div class="text-muted small">No profiles found</div>';
        return;
    }

    el.innerHTML = profiles.map(p => {
        const badge = p.has_index
            ? '<span class="badge bg-success ms-1" style="font-size:.6rem">indexed</span>'
            : '<span class="badge bg-warning text-dark ms-1" style="font-size:.6rem">empty</span>';
        return `<div class="d-flex justify-content-between align-items-center mb-1">
                    <div>
                        <span class="fw-semibold small">${_escHtml(p.name)}</span>${badge}
                        ${p.description ? `<div class="text-muted" style="font-size:.7rem">${_escHtml(p.description)}</div>` : ''}
                    </div>
                    <button class="btn btn-sm btn-outline-danger py-0 px-1"
                            onclick="supportDeleteProfile('${_escHtml(p.name)}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>`;
    }).join('');
}

export async function supportCreateProfile() {
    const name = document.getElementById('support-new-profile-name')?.value.trim();
    const desc = document.getElementById('support-new-profile-desc')?.value.trim();
    if (!name) return;

    try {
        const data = await fetch(`${window.API_BASE}/helpdesk/rag-profiles`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ name, description: desc }),
        }).then(r => r.json());

        if (data.success) {
            document.getElementById('support-new-profile-name').value = '';
            document.getElementById('support-new-profile-desc').value = '';
            await supportLoadProfiles();
        }
    } catch (e) {
        console.error('[support] createProfile error:', e);
    }
}

export async function supportDeleteProfile(name) {
    try {
        await fetch(`${window.API_BASE}/helpdesk/rag-profiles/${name}`, { method: 'DELETE' });
        await supportLoadProfiles();
    } catch (e) {
        console.error('[support] deleteProfile error:', e);
    }
}

// ── Status ────────────────────────────────────────────────────────────────────

export async function supportLoadStatus() {
    try {
        const data = await fetch(`${window.API_BASE}/helpdesk/config`).then(r => r.json());
        if (!data.success) return;

        _botEnabled = !!data.enabled;

        // Bot status bar in user panel
        const dot   = document.getElementById('support-bot-dot');
        const label = document.getElementById('support-bot-label');
        if (dot)   dot.className   = `badge ${_botEnabled ? 'bg-success' : 'bg-secondary'}`;
        if (label) label.textContent = _botEnabled ? 'Bot active' : 'Bot disabled';

        // Admin badge in RAG sub-panel
        const badge = document.getElementById('support-status-badge');
        if (badge) {
            badge.innerHTML = _botEnabled
                ? '<span class="badge bg-success">🟢 Bot active</span>'
                : '<span class="badge bg-secondary">⚫ Bot disabled</span>';
        }

        const profileEl = document.getElementById('support-rag-profile-name');
        if (profileEl) profileEl.textContent = data.rag_profile || '—';

        // Show admin gear button only when bot is configured
        const adminBtn = document.getElementById('support-admin-btn');
        if (adminBtn) adminBtn.style.display = _botEnabled ? '' : 'none';

    } catch (e) {
        console.error('[support] loadStatus error:', e);
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _escHtml(s) {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// ── Window exports (for inline onclick handlers) ──────────────────────────────

window.supportToggleChat        = supportToggleChat;
window.supportToggleAdminPanel  = supportToggleAdminPanel;
window.supportAdminTab          = supportAdminTab;
window.supportSendMessage       = supportSendMessage;
window.supportSelectUser        = supportSelectUser;
window.supportDeleteProfile     = supportDeleteProfile;
window.supportCreateProfile     = supportCreateProfile;
