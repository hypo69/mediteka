/**
 * =============================================================================
 * Название процесса: Управление интерактивным чатом
 * =============================================================================
 * Описание:
 *   Обеспечение отправки сообщений, ведение истории диалога и интеграция
 *   настроек в config.json. Включение обработки асинхронных генераций ответов.
 *
 * File: chat.js
 * Project: Ai Assistant
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Version: 0.4.1
 * =============================================================================
 */

import { showAlert, updateChatModelBadge } from './ui.js';

let _timerInterval = null;
let _activeAbortController = null;
let _isSending = false;

// Локальная история сообщений (сохраняется на сервер по кнопке Stop/после завершения)
let _chatHistoryMessages = [];
let _historySessionId = null;

function _getOrCreateHistorySessionId() {
    // Возврат существующего ID сессии при наличии
    // Return of the existing session ID if present
    if (_historySessionId) return _historySessionId;
    try {
        _historySessionId = localStorage.getItem('aiAssistantChatHistorySessionId');
    } catch {}
    // Генерация нового UUID при отсутствии сохраненного
    // Generation of a new UUID if no stored one exists
    if (!_historySessionId) {
        try {
            _historySessionId = crypto.randomUUID();
        } catch {
            _historySessionId = `sess_${Date.now()}_${Math.random().toString(16).slice(2)}`;
        }
        try {
            localStorage.setItem('aiAssistantChatHistorySessionId', _historySessionId);
        } catch {}
    }
    return _historySessionId;
}

function setStopButtonEnabled(enabled) {
    const btn = document.getElementById('chat-stop-btn');
    // Изменение состояния активности кнопки остановки
    // Alteration of the stop button activity state
    if (btn) btn.disabled = !enabled;
}

async function saveChatHistory({ aborted = false, error = null, model = '' } = {}) {
    // Прекращение выполнения при пустой истории сообщений
    // Termination of execution if the message history is empty
    if (!_chatHistoryMessages.length) return;

    try {
        const session_id = _getOrCreateHistorySessionId();
        const payload = {
            session_id,
            model,
            aborted,
            messages: _chatHistoryMessages
        };

        const resp = await fetch(`${window.API_BASE}/chat/history/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await resp.json();
        // Уведомление об успешном сохранении истории
        // Notification of successful history saving
        if (data.success) {
            if (error) showAlert(`History saved (${data.file})`, 'warning');
            else showAlert(`History saved (${data.file})`, 'success');
        } else {
            showAlert(`History save failed: ${data.error || 'unknown error'}`, 'danger');
        }
    } catch (e) {
        console.error('Save chat history failed:', e);
    }
}

// ── Settings → config.json ────────────────────────────────────────────────────

function patchConfig(patch) {
    fetch(`${window.API_BASE}/config`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch)
    }).catch(() => {});
}

// Вызывается из config.js после loadConfig() — восстанавливает поля чата
export function applyChatConfig(foundryAi) {
    // Отмена операции при отсутствии объекта настроек
    // Cancellation of the operation if the settings object is missing
    if (!foundryAi) return;
    const tempEl  = document.getElementById('temperature');
    const tempVal = document.getElementById('temp-value');
    const tokEl   = document.getElementById('max-tokens');
    const modelEl = document.getElementById('chat-model');

    if (tempEl  && foundryAi.temperature != null) { tempEl.value  = foundryAi.temperature; }
    if (tempVal && foundryAi.temperature != null) { tempVal.textContent = foundryAi.temperature; }
    if (tokEl   && foundryAi.max_tokens  != null) { tokEl.value   = foundryAi.max_tokens; }

    // Восстановление выбранной модели после загрузки списка
    // Restoration of the selected model after the list loading
    if (foundryAi.default_model) {
        window._savedChatModel = foundryAi.default_model;
        // Немедленный выбор значения при заполненном селекте
        // Immediate selection of the value if the select is populated
        if (modelEl) {
            const opt = [...modelEl.options].find(o => o.value === foundryAi.default_model);
            if (opt) modelEl.value = foundryAi.default_model;
        }
    }
}

// ── UI helpers ────────────────────────────────────────────────────────────────

function appendMessage(role, text) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    container.querySelector('.text-muted.text-center')?.remove();

    const div = document.createElement('div');
    div.className = `mb-3 d-flex ${role === 'user' ? 'justify-content-end' : 'justify-content-start'}`;
    div.innerHTML = `
        <div class="px-3 py-2 rounded-3 ${role === 'user' ? 'bg-primary text-white' : 'bg-light border'}"
             style="max-width:80%;white-space:pre-wrap;font-size:.9rem;word-break:break-word">
            ${role === 'assistant' ? '<small class="text-muted d-block mb-1"><i class="bi bi-robot"></i> AI</small>' : ''}
            ${escapeHtml(text)}
        </div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function setThinking(on) {
    document.getElementById('chat-thinking')?.remove();
    if (!on) return;
    const container = document.getElementById('chat-messages');
    if (!container) return;
    const div = document.createElement('div');
    div.id = 'chat-thinking';
    div.className = 'mb-3 d-flex justify-content-start';
    div.innerHTML = `<div class="px-3 py-2 rounded-3 bg-light border">
        <span class="spinner-border spinner-border-sm me-2"></span>
        <small class="text-muted">Генерация ответа...</small></div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(t) {
    return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function startTimer() {
    const t0 = Date.now();
    clearInterval(_timerInterval);
    // Store start time for elapsed calculation on response
    window._chatTimerStart = t0;
    _timerInterval = setInterval(() => {
        const val = document.getElementById('chat-timer-value');
        if (val) val.textContent = ((Date.now() - t0) / 1000).toFixed(1) + 's';
        const timerEl = document.getElementById('chat-timer');
        if (timerEl) timerEl.style.display = '';
    }, 100);
}

function stopTimer() { clearInterval(_timerInterval); }

// ── Public API ────────────────────────────────────────────────────────────────

export async function sendMessage() {
    const input = document.getElementById('chat-input');
    const model = document.getElementById('chat-model')?.value;

    if (!input?.value.trim()) return;
    if (!model) { showAlert('Выберите модель в Chat Settings', 'warning'); return; }

    const message = input.value.trim();
    if (_isSending) {
        showAlert('Request is already running. Stop it first.', 'warning');
        return;
    }

    input.value = '';
    input.disabled = true;
    _isSending = true;
    setStopButtonEnabled(true);
    _activeAbortController = new AbortController();

    appendMessage('user', message);
    _chatHistoryMessages.push({ role: 'user', content: message });
    setThinking(true);
    startTimer();
    let aborted = false;
    let responseError = null;

    try {
        const r = await fetch(`${window.API_BASE}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt:                  message,
                model,
                temperature:             parseFloat(document.getElementById('temperature')?.value || '0.7'),
                max_tokens:              parseInt(document.getElementById('max-tokens')?.value    || '2048'),
                use_rag:                 document.getElementById('use-rag')?.checked || false,
                translate_model_dialog:  document.getElementById('translate-dialog')?.checked ?? true,
                user_language:           document.getElementById('user-language')?.value || null,
            }),
            signal: _activeAbortController.signal,
        });

        const data = await r.json();
        setThinking(false);
        stopTimer();

        if (data.success) {
            appendMessage('assistant', data.content);
            const elapsedMs = Date.now() - (window._chatTimerStart || Date.now());
            const totalTokens = data.usage?.total_tokens ?? null;
            updateChatModelBadge(model, { elapsedMs, totalTokens });
            _chatHistoryMessages.push({ role: 'assistant', content: data.content });
            // Save model as default in config.json
            patchConfig({ 'foundry_ai.default_model': model });
        } else {
            const errText = `❌ ${data.error || 'Ошибка генерации'}`;
            appendMessage('assistant', errText);
            _chatHistoryMessages.push({ role: 'assistant', content: errText });
            responseError = errText;
        }
    } catch (err) {
        setThinking(false);
        stopTimer();
        if (err?.name === 'AbortError') {
            aborted = true;
            const cancelText = '⏹ Request canceled';
            appendMessage('assistant', cancelText);
            _chatHistoryMessages.push({ role: 'assistant', content: cancelText });
        } else {
            const netErr = `❌ Ошибка сети: ${err.message}`;
            appendMessage('assistant', netErr);
            _chatHistoryMessages.push({ role: 'assistant', content: netErr });
            responseError = netErr;
        }
    } finally {
        // В любом исходе сохраняем историю
        await saveChatHistory({
            aborted,
            error: responseError,
            model
        });

        input.disabled = false;
        _activeAbortController = null;
        _isSending = false;
        setStopButtonEnabled(false);
        input.focus();
    }
}

export function stopSendingRequest() {
    if (_activeAbortController) {
        _activeAbortController.abort();
    }
}

export function clearChat() {
    const c = document.getElementById('chat-messages');
    if (c) c.innerHTML = `<div class="text-muted text-center">
        <i class="bi bi-chat-square-dots"></i><br>Start a conversation with AI</div>`;

    // Hide stats badge
    const statWrap = document.getElementById('chat-stats-badge');
    if (statWrap) statWrap.style.display = 'none';
    const timerEl = document.getElementById('chat-timer');
    if (timerEl) timerEl.style.display = 'none';
    const tokBadge = document.getElementById('chat-tokens-badge');
    if (tokBadge) tokBadge.style.display = 'none';

    _chatHistoryMessages = [];
    _activeAbortController = null;
    _isSending = false;
    setStopButtonEnabled(false);
}

export function handleChatKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        window.sendMessage?.();
    }
}

export function updateTempValue(val) {
    const el = document.getElementById('temp-value');
    if (el) el.textContent = val;
    patchConfig({ 'foundry_ai.temperature': parseFloat(val) });
}
