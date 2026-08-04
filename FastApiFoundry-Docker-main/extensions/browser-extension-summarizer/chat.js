// -*- coding: utf-8 -*-
// =============================================================================
// Process Name: Chat — чат через FastAPI Foundry
// =============================================================================
// Description:
//   Все запросы к AI идут ТОЛЬКО через локальный FastAPI сервер.
//   Никаких прямых вызовов к внешним провайдерам.
//
// File: chat.js
// Project: AI Assistant (ai_assist)
// Version: 0.8.0
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

import { initI18n, t } from './js/i18n.js';
import { sendRequest as geminiRequest }    from './connectors/gemini.js';
import { sendRequest as openrouterRequest } from './connectors/openrouter.js';
import { sendRequest as openaiRequest }     from './connectors/openai-compat.js';

// ── DOM ───────────────────────────────────────────────────────────────────────

const modelSelect = document.getElementById('model-select');
const messagesEl  = document.getElementById('messages');
const emptyState  = document.getElementById('empty-state');
const userInput   = document.getElementById('user-input');
const sendBtn     = document.getElementById('send-btn');
const clearBtn    = document.getElementById('clear-btn');
const ragBtn      = document.getElementById('rag-btn');
const errorBanner = document.getElementById('error-banner');

// ── Состояние ─────────────────────────────────────────────────────────────────

const messages = [];
let currentModel    = '';   // "providerId|modelId"
let currentEntry    = null; // запись из selectedModels
let currentJob      = null;

// ── Настройки ─────────────────────────────────────────────────────────────────

async function loadSettings() {
    const data = await chrome.storage.sync.get(['selectedModels', 'defaultModel']);
    const selected     = data.selectedModels || [];
    const defaultModel = data.defaultModel   || '';
    const badge        = document.getElementById('current-model-badge');

    if (!selected.length) {
        modelSelect.innerHTML = `<option value="">${t('chat.no_models')}</option>`;
        showError(t('chat.no_key_error'));
        return;
    }

    modelSelect.innerHTML = selected.map(m => {
        const key      = `${m.providerId}|${m.modelId}`;
        const isDefault = key === defaultModel;
        return `<option value="${key}"${isDefault ? ' selected' : ''}>${m.label || key}${isDefault ? ' ★' : ''}</option>`;
    }).join('');

    // Устанавливаем текущую модель
    const activeKey  = defaultModel || `${selected[0].providerId}|${selected[0].modelId}`;
    currentModel     = activeKey;
    currentEntry     = selected.find(m => `${m.providerId}|${m.modelId}` === activeKey) || selected[0];
    badge.textContent = currentEntry.label || activeKey;
    badge.style.display = '';

    modelSelect.addEventListener('change', () => {
        currentModel = modelSelect.value;
        currentEntry = selected.find(m => `${m.providerId}|${m.modelId}` === currentModel);
        badge.textContent = currentEntry?.label || currentModel;
    });
}

// ── FastAPI запрос ────────────────────────────────────────────────────────────

async function sendToAPI(history) {
    if (!currentEntry) throw new Error(t('chat.no_model_error'));

    const { providerId, modelId, apiKey, customUrl } = currentEntry;
    const msgs = history.map(m => ({ role: m.role, content: m.content }));

    if (providerId === 'gemini')     return geminiRequest(msgs, apiKey, modelId);
    if (providerId === 'openrouter') return openrouterRequest(msgs, apiKey, modelId);
    // ai_assist, custom и все OpenAI-совместимые — через openai-compat
    return openaiRequest(providerId, apiKey, modelId, msgs, customUrl);
}

// ── Рендер ────────────────────────────────────────────────────────────────────

function appendMessage(role, content) {
    emptyState.style.display = 'none';

    const wrap   = document.createElement('div');
    wrap.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'You' : '🤖';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    if (role === 'assistant') {
        const isHtml = /<[a-z][\s\S]*>/i.test(content);
        bubble.innerHTML = isHtml ? content : `<p>${content.replace(/\n/g, '<br>')}</p>`;
    } else {
        bubble.textContent = content;
    }

    wrap.appendChild(avatar);
    wrap.appendChild(bubble);
    messagesEl.appendChild(wrap);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showTyping() {
    emptyState.style.display = 'none';
    const wrap = document.createElement('div');
    wrap.className = 'message assistant';
    wrap.id = 'typing-wrap';
    wrap.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-bubble">
            <div class="typing-indicator"><span></span><span></span><span></span></div>
        </div>`;
    messagesEl.appendChild(wrap);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function removeTyping() { document.getElementById('typing-wrap')?.remove(); }

function showError(msg) {
    errorBanner.textContent = msg;
    errorBanner.style.display = '';
    setTimeout(() => { errorBanner.style.display = 'none'; }, 6000);
}

// ── Отправка ──────────────────────────────────────────────────────────────────

async function handleSend() {
    const text = userInput.value.trim();
    if (!text || sendBtn.disabled) return;
    if (!currentModel) { showError(t('chat.no_model_error')); return; }

    userInput.value = '';
    userInput.style.height = 'auto';
    sendBtn.disabled = true;
    errorBanner.style.display = 'none';

    messages.push({ role: 'user', content: text });
    appendMessage('user', text);
    showTyping();

    try {
        const reply = await sendToAPI(messages);
        removeTyping();
        messages.push({ role: 'assistant', content: reply });
        appendMessage('assistant', reply);
    } catch (e) {
        removeTyping();
        showError(e.message);
        messages.pop();
    } finally {
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// ── Авторастягивание textarea ─────────────────────────────────────────────────

userInput.addEventListener('input', () => {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 160) + 'px';
});

userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
});

sendBtn.addEventListener('click', handleSend);

// ── Очистка ───────────────────────────────────────────────────────────────────

clearBtn.addEventListener('click', () => {
    messages.length = 0;
    messagesEl.innerHTML = '';
    messagesEl.appendChild(emptyState);
    emptyState.style.display = '';
    ragBtn.style.display = 'none';
    currentJob = null;
});

// ── RAG ───────────────────────────────────────────────────────────────────────

ragBtn.addEventListener('click', async () => {
    if (!currentJob?.finalSummary) return;
    ragBtn.disabled = true;
    ragBtn.textContent = '…';

    const firstTab = currentJob.tabs?.[0];
    const title = firstTab?.title || document.title || 'Summary';
    const url   = firstTab?.url   || window.location.href;

    const result = await chrome.runtime.sendMessage({
        action: 'saveToRag', title, url, text: currentJob.finalSummary
    });

    if (result?.ok) {
        ragBtn.textContent = '✅ Saved';
        setTimeout(() => chrome.tabs.create({ url: chrome.runtime.getURL('rag-storage.html') }), 600);
    } else {
        ragBtn.textContent = '❌ Error';
        ragBtn.disabled = false;
    }
});

// ── Init ──────────────────────────────────────────────────────────────────────

async function init() {
    await initI18n();
    await loadSettings();

    const params    = new URLSearchParams(window.location.search);
    const factJobId = params.get('factcheck');
    const summJobId = params.get('summary');
    const jobId     = factJobId || summJobId;

    if (!jobId) { userInput.focus(); return; }

    showTyping();
    const interval = setInterval(async () => {
        const data = await chrome.storage.local.get(jobId);
        const job  = data[jobId];
        if (!job || job.status === 'running' || job.status === 'merging') return;

        clearInterval(interval);
        removeTyping();

        if (job.status === 'done' && job.finalSummary) {
            if (summJobId) {
                const mode = job.mode === 'single' ? 'Summarize this page' : 'Summarize all tabs';
                messages.push({ role: 'user', content: mode });
                appendMessage('user', mode);
            } else if (factJobId && job.selection) {
                messages.push({ role: 'user', content: job.selection });
                appendMessage('user', job.selection);
            }
            messages.push({ role: 'assistant', content: job.finalSummary });
            appendMessage('assistant', job.finalSummary);
            currentJob = job;
            ragBtn.style.display = '';
        } else if (job.status === 'error') {
            showError(job.error || 'Failed');
        }
    }, 400);
}

init();
