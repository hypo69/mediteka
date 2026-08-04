// ui-manager.js
// Управление UI: индикаторы на страницах и открытие вкладки результата.

class UIManager {
    /**
     * Показ небольшого индикатора-тоста на странице.
     * Используется чтобы дать обратную связь пока идёт суммаризация.
     * @param {number} tabId
     * @param {string} message
     */
    static showIndicator(tabId, message) {
        chrome.scripting.executeScript({
            target: { tabId },
            func: (msg) => {
                let el = document.getElementById('__ai_summarizer_indicator__');
                if (!el) {
                    el = document.createElement('div');
                    el.id = '__ai_summarizer_indicator__';
                    el.style.cssText = [
                        'position:fixed', 'bottom:20px', 'right:20px',
                        'background:rgba(0,0,0,0.85)', 'color:#fff',
                        'padding:10px 16px', 'border-radius:8px',
                        'font:14px system-ui,sans-serif', 'z-index:2147483647',
                        'box-shadow:0 4px 12px rgba(0,0,0,0.3)',
                        'pointer-events:none', 'max-width:300px'
                    ].join(';');
                    document.body.appendChild(el);
                }
                el.textContent = msg;
            },
            args: [message]
        }, () => { if (chrome.runtime.lastError) {} });
    }

    /**
     * Удаление индикатора со страницы.
     * @param {number} tabId
     */
    static hideIndicator(tabId) {
        chrome.scripting.executeScript({
            target: { tabId },
            func: () => {
                const el = document.getElementById('__ai_summarizer_indicator__');
                if (el) el.remove();
            }
        }, () => { if (chrome.runtime.lastError) {} });
    }

    /**
     * Открытие вкладки чата с результатом суммаризации.
     *
     * ПОЧЕМУ chat.html ВМЕСТО summary.html:
     *   Результат суммаризации попадает в чат как сообщение ассистента.
     *   Пользователь может сразу задать уточняющие вопросы по теме.
     *   summary.html был отдельной страницей только для отображения —
     *   чат делает то же самое и даёт больше возможностей.
     *
     * ПОЧЕМУ НЕ ПЕРЕИСПОЛЬЗУЕМ СУЩЕСТВУЮЩУЮ ВКЛАДКУ:
     *   Каждый job — отдельный результат. Переиспользование вкладки
     *   затёрло бы предыдущий диалог пользователя.
     *
     * @param {string} jobId  ключ в chrome.storage.local с данными задачи
     * @returns {Promise<number>} tabId открытой вкладки
     */
    static async openSummaryTab(jobId) {
        const url = chrome.runtime.getURL(`chat.html?summary=${jobId}`);
        const tab = await chrome.tabs.create({ url, active: true });
        return tab.id;
    }
}

export { UIManager };
