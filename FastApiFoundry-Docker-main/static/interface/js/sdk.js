/**
 * sdk.js — Примеры SDK
 *
 * Содержит:
 *  - loadExamples()           — загрузка списка примеров
 *  - loadSelectedExample()    — загрузка кода выбранного примера
 *  - runExample()             — выполнение примера через API
 *  - copyExampleToClipboard() — копирование кода в буфер
 */

import { showAlert } from './ui.js';

// ── Примеры ───────────────────────────────────────────────────────────────────

/**
 * Загружает список доступных примеров SDK в select #example-select.
 */
export async function loadExamples() {
    const select = document.getElementById('example-select');
    if (!select) return;
    try {
        const data = await fetch(`${window.API_BASE}/examples`).then(r => r.json());
        if (data.success && data.examples?.length) {
            select.innerHTML = '<option value="">Select an example...</option>'
                + data.examples.map(e => `<option value="${e.id}">${e.name}</option>`).join('');
        }
    } catch (e) {
        console.error('Failed to load examples:', e);
    }
}

/**
 * Загружает код выбранного примера в textarea #example-code.
 */
export async function loadSelectedExample() {
    const id = document.getElementById('example-select')?.value;
    const ta = document.getElementById('example-code');
    if (!id || !ta) return;
    try {
        const data = await fetch(`${window.API_BASE}/examples/${id}`).then(r => r.json());
        if (data.success) ta.value = data.code || '';
    } catch (e) {
        console.error('Failed to load example:', e);
    }
}

/**
 * Выполняет выбранный пример через POST /examples/{id}/run.
 * Результат отображается в #example-output.
 */
export async function runExample() {
    const id     = document.getElementById('example-select')?.value;
    const output = document.getElementById('example-output');
    if (!id) { showAlert('Select an example first', 'warning'); return; }
    if (!output) return;

    output.style.display = '';
    output.textContent = '⏳ Running...';
    try {
        const data = await fetch(`${window.API_BASE}/examples/${id}/run`, { method: 'POST' }).then(r => r.json());
        output.textContent = data.success ? (data.output || data.result) : `❌ ${data.error}`;
    } catch (e) {
        output.textContent = `❌ ${e.message}`;
    }
}

/** Копирует код примера в буфер обмена */
export function copyExampleToClipboard() {
    const code = document.getElementById('example-code')?.value;
    if (!code) return;
    navigator.clipboard.writeText(code).then(() => showAlert('Copied to clipboard', 'success'));
}
