// -*- coding: utf-8 -*-
// =============================================================================
// Process Name: Simple Chat — чат с localhost:9696
// =============================================================================
// Description:
//   Минимальный чат-клиент для FastAPI AI Assistant.
//   Все запросы идут только через http://localhost:9696/api/v1
//
// File: chat.js
// Project: AI Assistant (ai_assist)
// Version: 0.8.0
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

const API_BASE = 'http://localhost:9696/api/v1';

const modelSelect = document.getElementById('model-select');
const messagesEl  = document.getElementById('messages');
const emptyState  = document.getElementById('empty-state');
const userInput   = document.getElementById('user-input');
const sendBtn     = document.getElementById('send-btn');
const clearBtn    = document.getElementById('clear-btn');
const errorBanner = document.getElementById('error-banner');

const messages = [];

// ── Загрузка моделей ──────────────────────────────────────────────────────────

async function loadModels() {
    try {
        const res  = await fetch(`${API_BASE}/models`);
        const data = await res.json();
        const models = data.models || [];

        if (!models.length) {
            modelSelect.innerHTML = '<option value="">No models</option>';
            return;
        }

        modelSelect.innerHTML = models.map(m => {
            const id = m.id || m.model_id || m;
            return `<option value="${id}">${id}</option>`;
        }).join('');

        // Восстановить последнюю выбранную модель
        chrome.storage.local.get('lastModel', ({ lastModel }) => {
            if (lastModel && [...modelSelect.options].some(o => o.value === lastModel)) {
                modelSelect.value = lastModel;
            }
        });
    } catch {
        modelSelect.innerHTML = '<option value="foundry::default">foundry::default</option>';
    }
}

modelSelect.addEventListener('change', () => {
    chrome.storage.local.set({ lastModel: modelSelect.value });
});

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
        bubble.innerHTML = `<p>${content.replace(/\n/g, '<br>')}</p>`;
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

    const model = modelSelect.value;
    if (!model) { showError('No model selected'); return; }

    userInput.value = '';
    userInput.style.height = 'auto';
    sendBtn.disabled = true;
    errorBanner.style.display = 'none';

    messages.push({ role: 'user', content: text });
    appendMessage('user', text);
    showTyping();

    try {
        const res = await fetch(`${API_BASE}/ai/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: messages.map(m => ({ role: m.role, content: m.content })),
                model
            })
        });

        const data = await res.json();
        removeTyping();

        const reply = data.choices?.[0]?.message?.content
                   || data.content
                   || data.error
                   || 'No response';

        messages.push({ role: 'assistant', content: reply });
        appendMessage('assistant', reply);
    } catch (e) {
        removeTyping();
        showError(`Connection error: ${e.message}`);
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

clearBtn.addEventListener('click', () => {
    messages.length = 0;
    messagesEl.innerHTML = '';
    messagesEl.appendChild(emptyState);
    emptyState.style.display = '';
});

// ── Init ──────────────────────────────────────────────────────────────────────

loadModels();
userInput.focus();
