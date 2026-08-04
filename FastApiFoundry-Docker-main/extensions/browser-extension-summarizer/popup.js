// popup.js
import { PROVIDERS } from './providers.js';
import { initI18n, t } from './js/i18n.js';

const infoEl = document.getElementById('active-info');

async function init() {
    await initI18n();
    chrome.storage.sync.get(['activeProvider', 'activeModel'], ({ activeProvider, activeModel }) => {
        if (activeProvider && activeModel) {
            const label = PROVIDERS[activeProvider]?.label || activeProvider;
            infoEl.className = 'info-block';
            infoEl.innerHTML = `
                <span class="label">${t('popup.provider')}: </span><span class="value">${label}</span><br>
                <span class="label">${t('popup.model')}: </span><span class="value">${activeModel}</span>
            `;
        } else {
            infoEl.className = 'info-block empty';
            infoEl.textContent = t('popup.no_provider');
        }
    });
}

init();

// Открываем providers.html в новой вкладке.
// chrome.runtime.getURL нужен чтобы получить полный chrome-extension:// URL —
// нельзя просто написать 'providers.html', браузер не поймёт.
document.getElementById('open-chat').addEventListener('click', () => {
    chrome.tabs.create({ url: chrome.runtime.getURL('chat.html') });
});

document.getElementById('open-debug').addEventListener('click', () => {
    chrome.tabs.create({ url: chrome.runtime.getURL('debug.html') });
});

document.getElementById('open-providers').addEventListener('click', () => {
    chrome.tabs.create({ url: chrome.runtime.getURL('providers.html') });
});

document.getElementById('open-rag').addEventListener('click', () => {
    chrome.tabs.create({ url: chrome.runtime.getURL('rag-storage.html') });
});
