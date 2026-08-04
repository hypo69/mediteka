// -*- coding: utf-8 -*-
// =============================================================================
// Process Name: RAG Storage page logic
// =============================================================================
// Description:
//   Управление списком сохранённых страниц для RAG-индексации.
//   Загружает записи из chrome.storage через background, позволяет
//   выбирать, удалять и отправлять их на FastAPI /api/v1/rag/build.
//
// File: rag-storage.js
// Project: AI Assistant (ai_assist)
// Version: 0.8.0
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

import { initI18n, t } from './js/i18n.js';

const entriesArea  = document.getElementById('entries-area');
const emptyState   = document.getElementById('empty-state');
const statusBar    = document.getElementById('status-bar');
const serverUrlEl  = document.getElementById('server-url');

let entries = [];

// ── Helpers ──────────────────────────────────────────────────────────────────

function setStatus(msg, isError = false) {
    statusBar.textContent = msg;
    statusBar.style.color = isError ? '#842029' : '#0f5132';
}

function selectedIds() {
    return [...document.querySelectorAll('.entry-checkbox:checked')].map(cb => cb.dataset.id);
}

function formatDate(ts) {
    return new Date(ts).toLocaleString();
}

// ── Render ────────────────────────────────────────────────────────────────────

function render() {
    // Удаляем все карточки, оставляем empty-state
    document.querySelectorAll('.entry-card').forEach(el => el.remove());

    if (!entries.length) {
        emptyState.style.display = '';
        return;
    }
    emptyState.style.display = 'none';

    for (const entry of entries) {
        const badgeClass = entry.status === 'ready' ? 'badge-ready'
                         : entry.status === 'error' ? 'badge-error'
                         : 'badge-pending';
        const badgeLabel = entry.status === 'ready'   ? t('rag.status_ready')
                         : entry.status === 'error'   ? t('rag.status_error')
                         : t('rag.status_pending');

        const card = document.createElement('div');
        card.className = 'entry-card';
        card.dataset.id = entry.id;
        card.innerHTML = `
            <input type="checkbox" class="form-check-input entry-checkbox mt-1" data-id="${entry.id}">
            <div class="entry-meta">
                <div class="entry-title" title="${entry.title}">${entry.title || entry.url}</div>
                <div class="entry-url">${entry.url}</div>
                <div class="entry-date">${formatDate(entry.savedAt)}</div>
            </div>
            <span class="badge-status ${badgeClass}">${badgeLabel}</span>
        `;

        // Клик по карточке — переключает чекбокс
        card.addEventListener('click', e => {
            if (e.target.type === 'checkbox') return;
            const cb = card.querySelector('.entry-checkbox');
            cb.checked = !cb.checked;
            card.classList.toggle('selected', cb.checked);
        });

        card.querySelector('.entry-checkbox').addEventListener('change', e => {
            card.classList.toggle('selected', e.target.checked);
        });

        entriesArea.appendChild(card);
    }
}

// ── Load ──────────────────────────────────────────────────────────────────────

async function loadEntries() {
    setStatus(t('common.loading'));
    const response = await chrome.runtime.sendMessage({ action: 'getRagEntries' });
    entries = response?.entries || [];
    render();
    setStatus(entries.length ? `${entries.length} ${t('rag.entries_count')}` : '');
}

// ── Actions ───────────────────────────────────────────────────────────────────

document.getElementById('btn-select-all').addEventListener('click', () => {
    document.querySelectorAll('.entry-checkbox').forEach(cb => {
        cb.checked = true;
        cb.closest('.entry-card').classList.add('selected');
    });
});

document.getElementById('btn-deselect-all').addEventListener('click', () => {
    document.querySelectorAll('.entry-checkbox').forEach(cb => {
        cb.checked = false;
        cb.closest('.entry-card').classList.remove('selected');
    });
});

document.getElementById('btn-delete').addEventListener('click', async () => {
    const ids = selectedIds();
    if (!ids.length) { setStatus(t('rag.nothing_selected'), true); return; }

    for (const id of ids) {
        await chrome.runtime.sendMessage({ action: 'deleteRagEntry', id });
    }
    await loadEntries();
    setStatus(`${t('rag.deleted')} ${ids.length}`);
});

document.getElementById('btn-send').addEventListener('click', async () => {
    const ids = selectedIds();
    if (!ids.length) { setStatus(t('rag.nothing_selected'), true); return; }

    const serverUrl = serverUrlEl.value.trim().replace(/\/$/, '');
    if (!serverUrl) { setStatus(t('rag.no_server_url'), true); return; }

    // Сохраняем URL для следующего раза
    chrome.storage.sync.set({ ragServerUrl: serverUrl });

    setStatus(t('rag.sending'));
    const result = await chrome.runtime.sendMessage({ action: 'sendToRag', ids, serverUrl });

    if (result.ok) {
        setStatus(`✅ ${t('rag.sent_ok')} ${result.sent}`);
    } else {
        const errMsg = result.errors?.join('; ') || result.error || 'unknown error';
        setStatus(`❌ ${errMsg}`, true);
    }
});

// ── Init ──────────────────────────────────────────────────────────────────────

async function init() {
    await initI18n();

    // Восстанавливаем сохранённый URL сервера
    const { ragServerUrl } = await chrome.storage.sync.get('ragServerUrl');
    if (ragServerUrl) serverUrlEl.value = ragServerUrl;

    await loadEntries();
}

init();
