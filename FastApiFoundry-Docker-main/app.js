/**
 * =============================================================================
 * Process Name: UI Logic and API Interaction
 * =============================================================================
 * Description:
 *   Management of UI state and communication with the FastAPI backend.
 *   Includes Server-Sent Events (SSE) streaming support for prompt generation.
 *
 * File: app.js
 * Project: Ai Assistant
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

const API_BASE = 'http://localhost:9696/api/v1';

/**
 * Localization System
 */
const i18n = {
    ru: {
        "app.title": "AI Помощник",
        "tabs.chat": "Чат",
        "tabs.status": "Статус",
        "tabs.settings": "Настройки",
        "section.status": "Состояние сервера",
        "section.prompt": "Ваш запрос",
        "label.response": "Ответ системы",
        "btn.send": "Отправить",
        "placeholder.prompt": "Введите ваш запрос здесь (Ctrl+Enter)...",
        "status.online": "В сети",
        "status.offline": "Оффлайн",
        "status.waiting": "Ожидание запроса...",
        "label.theme": "Темная тема"
    },
    en: {
        "app.title": "AI Assistant",
        "tabs.chat": "Chat",
        "tabs.status": "Status",
        "tabs.settings": "Settings",
        "section.status": "Backend Status",
        "section.prompt": "AI Prompt",
        "label.response": "Response",
        "btn.send": "Send",
        "placeholder.prompt": "Type your request here (Ctrl+Enter)...",
        "status.online": "Online",
        "status.offline": "Offline",
        "status.waiting": "Waiting for request...",
        "label.theme": "Dark Mode"
    }
};

let currentLang = 'ru';

function setLanguage(lang) {
    currentLang = lang;
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (i18n[lang][key]) el.innerText = i18n[lang][key];
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (i18n[lang][key]) el.placeholder = i18n[lang][key];
    });
}

/**
 * Check of backend health status.
 */
async function checkStatus() {
    const statusElem = document.getElementById('status-content');
    const badge = document.getElementById('status-badge');

    try {
        const res = await fetch(`${API_BASE}/health`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        
        const data = await res.json();
        statusElem.innerText = JSON.stringify(data, null, 2);
        
        badge.innerText = i18n[currentLang]["status.online"];
        badge.className = 'badge rounded-pill ms-2 text-uppercase badge-online';
    } catch (err) {
        statusElem.innerText = `Connection error: ${err.message}`;
        badge.innerText = i18n[currentLang]["status.offline"];
        badge.className = 'badge rounded-pill ms-2 text-uppercase badge-offline';
    }
}

/**
 * Processing of streaming response from the API.
 *
 * ПОЧЕМУ READABLESTREAM:
 *   Обеспечение отображения текста по мере его генерации моделью (Streaming),
 *   что значительно улучшает UX по сравнению с ожиданием полного JSON.
 */
async function sendPrompt() {
    const input = document.getElementById('prompt-input');
    const resultElem = document.getElementById('response-content');
    const sendBtn = document.getElementById('send-btn');
    const spinner = document.getElementById('chat-spinner');
    const prompt = input.value.trim();
    
    if (!prompt) return;

    // UI state reset
    resultElem.innerText = '';
    input.disabled = true;
    sendBtn.disabled = true;
    spinner.classList.remove('d-none');
    
    try {
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, stream: true }) // Requesting stream
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        // Setup of streaming reader
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulatedText = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            
            // Parsing of SSE format "data: {...}"
            const lines = chunk.split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const jsonStr = line.replace('data: ', '').trim();
                        if (jsonStr === '[DONE]') break;
                        
                        const data = JSON.parse(jsonStr);
                        // Concatenation of received tokens
                        accumulatedText += (data.response || data.text || "");
                        resultElem.innerText = accumulatedText;
                        
                        // Auto-scroll to bottom
                        resultElem.scrollTop = resultElem.scrollHeight;
                    } catch (e) {
                        // Ignore partial JSON chunks
                    }
                }
            }
        }
    } catch (err) {
        resultElem.innerText = `Error: ${err.message}`;
    } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        spinner.classList.add('d-none');
        input.focus();
    }
}

/**
 * Initialization on DOM ready.
 */
window.addEventListener('DOMContentLoaded', () => {
    // Init i18n
    setLanguage('ru');
    document.getElementById('lang-select').addEventListener('change', (e) => setLanguage(e.target.value));
    document.getElementById('response-content').innerText = i18n[currentLang]["status.waiting"];

    // Theme Logic
    const themeToggle = document.getElementById('theme-toggle');
    themeToggle.addEventListener('change', (e) => {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
    });

    checkStatus();
    
    document.getElementById('send-btn').addEventListener('click', sendPrompt);
    document.getElementById('prompt-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            sendPrompt();
        }
    });
});