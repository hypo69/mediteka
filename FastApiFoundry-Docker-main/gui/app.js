/**
 * REST API Client for Ai Assistant
 * Location: gui/frontend/app.js
 */

const API_BASE = 'http://localhost:9696/api/v1';

const i18n = {
    ru: {
        "app.title": "AI Помощник",
        "tabs.chat": "Чат",
        "tabs.status": "Статус",
        "tabs.settings": "Настройки",
        "section.status": "Состояние сервера",
        "section.prompt": "Запрос",
        "label.response": "Ответ",
        "btn.send": "Отправить",
        "placeholder.prompt": "Введите текст (Ctrl+Enter)...",
        "label.theme": "Темная тема",
        "status.online": "В СЕТИ",
        "status.offline": "ОФФЛАЙН"
    },
    en: {
        "app.title": "AI Assistant",
        "tabs.chat": "Chat",
        "tabs.status": "Status",
        "tabs.settings": "Settings",
        "section.status": "Backend Status",
        "section.prompt": "Prompt",
        "label.response": "Response",
        "btn.send": "Send",
        "placeholder.prompt": "Enter text (Ctrl+Enter)...",
        "label.theme": "Dark Mode",
        "status.online": "ONLINE",
        "status.offline": "OFFLINE"
    }
};

let currentLang = localStorage.getItem('lang') || 'ru';

function updateUI() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = i18n[currentLang][key];
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.placeholder = i18n[currentLang][key];
    });
}

async function checkHealth() {
    const statusBadge = document.getElementById('status-badge');
    const statusContent = document.getElementById('status-content');
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();
        statusBadge.className = 'badge rounded-pill bg-success ms-2';
        statusBadge.textContent = i18n[currentLang]['status.online'];
        statusContent.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        statusBadge.className = 'badge rounded-pill bg-danger ms-2';
        statusBadge.textContent = i18n[currentLang]['status.offline'];
    }
}

async function sendPrompt() {
    const input = document.getElementById('prompt-input');
    const output = document.getElementById('response-content');
    const spinner = document.getElementById('chat-spinner');
    const btn = document.getElementById('send-btn');

    const prompt = input.value.trim();
    if (!prompt) return;

    output.textContent = '';
    spinner.classList.remove('d-none');
    btn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, stream: true })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.slice(6).trim();
                    if (dataStr === '[DONE]') break;
                    try {
                        const json = JSON.parse(dataStr);
                        output.textContent += (json.response || json.text || "");
                    } catch (err) {}
                }
            }
        }
    } catch (err) {
        output.textContent = `Error: ${err.message}`;
    } finally {
        spinner.classList.add('d-none');
        btn.disabled = false;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // i18n init
    document.getElementById('lang-select').value = currentLang;
    document.getElementById('lang-select').onchange = (e) => {
        currentLang = e.target.value;
        localStorage.setItem('lang', currentLang);
        updateUI();
    };

    // Theme init
    const toggle = document.getElementById('theme-toggle');
    if (localStorage.getItem('theme') === 'dark') {
        document.documentElement.setAttribute('data-bs-theme', 'dark');
        toggle.checked = true;
    }
    toggle.onchange = (e) => {
        const theme = e.target.checked ? 'dark' : 'light';
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
    };

    document.getElementById('send-btn').onclick = sendPrompt;
    document.getElementById('prompt-input').onkeydown = (e) => {
        if (e.ctrlKey && e.key === 'Enter') sendPrompt();
    };

    updateUI();
    checkHealth();
    setInterval(checkHealth, 5000);
});