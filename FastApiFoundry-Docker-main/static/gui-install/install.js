/**
 * =============================================================================
 * Process Name: GUI Installer — Step-by-step wizard logic
 * =============================================================================
 * Description:
 *   Drives the installation wizard at /install.
 *   Each step calls /api/v1/install/* endpoints to perform and check actions.
 *
 * File: static/gui-install/install.js
 * Project: AI Assistant (ai_assist)
 * Version: 0.7.1
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

'use strict';

const STEPS = [
  { id: 'welcome',    label: 'Добро пожаловать' },
  { id: 'env',        label: '.env'              },
  { id: 'tesseract',  label: 'Tesseract'         },
  { id: 'foundry',    label: 'Foundry'           },
  { id: 'ollama',     label: 'Ollama'            },
  { id: 'models',     label: 'Модели'            },
  { id: 'finish',     label: 'Готово'            },
];

let current = 0;

// --- render ---

function renderSteps() {
  const el = document.getElementById('steps');
  el.innerHTML = STEPS.map((s, i) => {
    const cls = i < current ? 'done' : i === current ? 'active' : '';
    const icon = i < current ? '✓' : i + 1;
    return `<div class="step-dot ${cls}">
      <div class="dot">${icon}</div>
      <div class="step-label">${s.label}</div>
    </div>`;
  }).join('');
}

function renderNav() {
  document.getElementById('btn-back').style.display   = current > 0 ? '' : 'none';
  document.getElementById('btn-next').style.display   = current < STEPS.length - 1 ? '' : 'none';
  document.getElementById('btn-finish').style.display = current === STEPS.length - 1 ? '' : 'none';
}

async function renderContent() {
  const el = document.getElementById('step-content');
  el.innerHTML = '<div class="spinner"></div> Загрузка...';
  el.innerHTML = await RENDERERS[STEPS[current].id]();
}

function render() {
  renderSteps();
  renderNav();
  renderContent();
}

// --- navigation ---

function nextStep() {
  if (current < STEPS.length - 1) { current++; render(); }
}

function prevStep() {
  if (current > 0) { current--; render(); }
}

function finish() {
  window.location.href = '/';
}

// --- api helpers ---

async function api(path, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch('/api/v1/install' + path, opts);
  return r.json();
}

function toast(msg, type = 'ok') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast show ${type}`;
  setTimeout(() => { el.className = 'toast'; }, 3000);
}

function appendLog(id, text, cls = '') {
  const el = document.getElementById(id);
  if (!el) return;
  const line = document.createElement('div');
  if (cls) line.className = cls;
  line.textContent = text;
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
}

// --- step renderers ---

const RENDERERS = {

  welcome: async () => {
    const status = await api('/status');
    const rows = [
      ['Python',        status.python        || '—', status.python        ? 'ok' : 'error'],
      ['pip',           status.pip           || '—', status.pip           ? 'ok' : 'warn' ],
      ['venv',          status.venv          ? 'готов' : 'не найден', status.venv ? 'ok' : 'warn'],
      ['requirements',  status.requirements  ? 'установлены' : 'не установлены', status.requirements ? 'ok' : 'warn'],
    ];
    return `
      <h2>👋 Добро пожаловать</h2>
      <p>Мастер установки AI Assistant. Проверяем базовое окружение:</p>
      <div class="status-block">
        ${rows.map(([label, val, cls]) => `
          <div class="status-row">
            <span class="status-icon ${cls}">${cls === 'ok' ? '✓' : cls === 'warn' ? '⚠' : '✗'}</span>
            <span class="status-label">${label}</span>
            <span class="status-value">${val}</span>
          </div>`).join('')}
      </div>
      <p>Нажмите <strong>Далее</strong> для продолжения.</p>`;
  },

  env: async () => {
    const data = await api('/env');
    return `
      <h2>⚙️ Настройка .env</h2>
      <p>Укажите ключевые переменные окружения. Файл <code>.env</code> ${data.exists ? 'уже существует' : 'будет создан'}.</p>
      <div class="field">
        <label>FOUNDRY_BASE_URL</label>
        <input id="env-foundry-url" value="${data.foundry_url || 'http://localhost:50477/v1'}" placeholder="http://localhost:50477/v1">
        <div class="hint">URL Foundry Local (оставьте по умолчанию если не знаете)</div>
      </div>
      <div class="field">
        <label>HF_TOKEN <span style="color:#475569">(опционально)</span></label>
        <input id="env-hf-token" type="password" value="${data.hf_token || ''}" placeholder="hf_...">
        <div class="hint">Токен HuggingFace для закрытых моделей (Gemma, Llama)</div>
      </div>
      <div class="field">
        <label>HF_MODELS_DIR <span style="color:#475569">(опционально)</span></label>
        <input id="env-hf-dir" value="${data.hf_models_dir || ''}" placeholder="D:\\models">
        <div class="hint">Директория для хранения HuggingFace моделей</div>
      </div>
      <button class="btn-action" onclick="saveEnv()">💾 Сохранить .env</button>
      <div id="env-log" class="log-output" style="margin-top:12px;min-height:40px"></div>`;
  },

  tesseract: async () => {
    const data = await api('/tesseract');
    return `
      <h2>🔍 Tesseract OCR</h2>
      <p>Tesseract нужен для извлечения текста из изображений (OCR). ${data.installed ? '✅ Уже установлен.' : '⚠️ Не найден.'}</p>
      <div class="status-block">
        <div class="status-row">
          <span class="status-icon ${data.installed ? 'ok' : 'warn'}">${data.installed ? '✓' : '⚠'}</span>
          <span class="status-label">tesseract</span>
          <span class="status-value">${data.version || 'не найден'}</span>
        </div>
        <div class="status-row">
          <span class="status-icon ${data.path ? 'ok' : 'warn'}">${data.path ? '✓' : '⚠'}</span>
          <span class="status-label">Путь</span>
          <span class="status-value">${data.path || '—'}</span>
        </div>
      </div>
      ${!data.installed ? `<button class="btn-action" onclick="installTesseract()">⬇️ Установить Tesseract</button>` : ''}
      <p style="margin-top:12px;color:#475569;font-size:0.85rem">Можно пропустить — OCR будет недоступен, остальные функции работают.</p>
      <div id="tess-log" class="log-output" style="margin-top:12px;min-height:40px"></div>`;
  },

  foundry: async () => {
    const data = await api('/foundry');
    return `
      <h2>🤖 Microsoft Foundry Local</h2>
      <p>Foundry Local — основной AI бэкенд для ONNX моделей. ${data.installed ? '✅ Установлен.' : '⚠️ Не найден.'}</p>
      <div class="status-block">
        <div class="status-row">
          <span class="status-icon ${data.installed ? 'ok' : 'warn'}">${data.installed ? '✓' : '⚠'}</span>
          <span class="status-label">foundry CLI</span>
          <span class="status-value">${data.version || 'не найден'}</span>
        </div>
        <div class="status-row">
          <span class="status-icon ${data.running ? 'ok' : 'warn'}">${data.running ? '✓' : '⚠'}</span>
          <span class="status-label">Сервис</span>
          <span class="status-value">${data.running ? 'запущен' : 'не запущен'}</span>
        </div>
      </div>
      ${!data.installed ? `<button class="btn-action" onclick="installFoundry()">⬇️ Установить через winget</button>` : ''}
      ${data.installed && !data.running ? `<button class="btn-action" onclick="startFoundry()">▶️ Запустить сервис</button>` : ''}
      <p style="margin-top:12px;color:#475569;font-size:0.85rem">Можно пропустить — доступны HuggingFace, llama.cpp и Ollama бэкенды.</p>
      <div id="foundry-log" class="log-output" style="margin-top:12px;min-height:40px"></div>`;
  },

  ollama: async () => {
    const data = await api('/ollama');
    return `
      <h2>🧠 Ollama</h2>
      <p>Ollama — локальный AI backend для моделей Qwen, Llama, Mistral, Gemma и DeepSeek. ${data.installed ? '✅ Установлен.' : '⚠️ Не найден.'}</p>
      <div class="status-block">
        <div class="status-row">
          <span class="status-icon ${data.installed ? 'ok' : 'warn'}">${data.installed ? '✓' : '⚠'}</span>
          <span class="status-label">ollama CLI</span>
          <span class="status-value">${data.version || 'не найден'}</span>
        </div>
        <div class="status-row">
          <span class="status-icon ${data.running ? 'ok' : 'warn'}">${data.running ? '✓' : '⚠'}</span>
          <span class="status-label">Сервер</span>
          <span class="status-value">${data.running ? 'запущен' : 'не запущен'}</span>
        </div>
        <div class="status-row">
          <span class="status-icon ok">✓</span>
          <span class="status-label">API URL</span>
          <span class="status-value">${data.url || 'http://localhost:11434'}</span>
        </div>
      </div>
      ${!data.installed ? `<button class="btn-action" onclick="installOllama()">⬇️ Установить через winget</button>` : ''}
      <p style="margin-top:12px;color:#475569;font-size:0.85rem">Если winget отсутствует, установщик попробует поставить Microsoft App Installer автоматически.</p>
      <div id="ollama-log" class="log-output" style="margin-top:12px;min-height:40px"></div>`;
  },

  models: async () => {
    const data = await api('/models');
    return `
      <h2>📦 Модели по умолчанию</h2>
      <p>Загрузите стартовую модель для быстрого начала работы.</p>
      <div class="field">
        <label>Выберите модель</label>
        <select id="model-select">
          ${(data.available || []).map(m => `<option value="${m.id}">${m.name} (${m.size})</option>`).join('')}
        </select>
        <div class="hint">Модели загружаются через Foundry Local</div>
      </div>
      <button class="btn-action" onclick="downloadModel()">⬇️ Загрузить модель</button>
      <p style="margin-top:12px;color:#475569;font-size:0.85rem">Можно пропустить и загрузить модели позже через веб-интерфейс.</p>
      <div id="model-log" class="log-output" style="margin-top:12px;min-height:60px"></div>`;
  },

  finish: async () => {
    return `
      <h2>🎉 Установка завершена!</h2>
      <p>AI Assistant готов к работе. Нажмите <strong>Завершить</strong> для перехода в интерфейс.</p>
      <div class="status-block">
        <div class="status-row">
          <span class="status-icon ok">✓</span>
          <span class="status-label">Веб-интерфейс</span>
          <span class="status-value"><a href="/" style="color:#818cf8">http://localhost:9696</a></span>
        </div>
        <div class="status-row">
          <span class="status-icon ok">✓</span>
          <span class="status-label">API</span>
          <span class="status-value"><a href="/docs" style="color:#818cf8">http://localhost:9696/docs</a></span>
        </div>
        <div class="status-row">
          <span class="status-icon ok">✓</span>
          <span class="status-label">Health</span>
          <span class="status-value"><a href="/api/v1/health" style="color:#818cf8">/api/v1/health</a></span>
        </div>
      </div>`;
  },
};

// --- action handlers ---

async function saveEnv() {
  const body = {
    foundry_url:   document.getElementById('env-foundry-url').value,
    hf_token:      document.getElementById('env-hf-token').value,
    hf_models_dir: document.getElementById('env-hf-dir').value,
  };
  appendLog('env-log', '💾 Сохраняю .env...');
  const r = await api('/env', 'POST', body);
  appendLog('env-log', r.success ? '✅ .env сохранён' : `❌ ${r.error}`, r.success ? 'log-ok' : 'log-err');
  if (r.success) toast('.env сохранён', 'ok');
}

async function installTesseract() {
  appendLog('tess-log', '⬇️ Запускаю установку Tesseract...');
  const r = await api('/tesseract/install', 'POST');
  appendLog('tess-log', r.success ? '✅ Tesseract установлен' : `❌ ${r.error}`, r.success ? 'log-ok' : 'log-err');
}

async function installFoundry() {
  appendLog('foundry-log', '⬇️ Устанавливаю Foundry через winget...');
  const r = await api('/foundry/install', 'POST');
  appendLog('foundry-log', r.success ? '✅ Foundry установлен' : `❌ ${r.error}`, r.success ? 'log-ok' : 'log-err');
}

async function startFoundry() {
  appendLog('foundry-log', '▶️ Запускаю foundry service start...');
  const r = await api('/foundry/start', 'POST');
  appendLog('foundry-log', r.success ? '✅ Сервис запущен' : `❌ ${r.error}`, r.success ? 'log-ok' : 'log-err');
}

async function installOllama() {
  appendLog('ollama-log', '⬇️ Устанавливаю Ollama через winget...');
  const r = await api('/ollama/install', 'POST');
  appendLog('ollama-log', r.success ? '✅ Установка Ollama запущена' : `❌ ${r.error}`, r.success ? 'log-ok' : 'log-err');
}

async function downloadModel() {
  const modelId = document.getElementById('model-select')?.value;
  if (!modelId) return;
  appendLog('model-log', `⬇️ Загружаю ${modelId}...`);
  const r = await api('/models/download', 'POST', { model_id: modelId });
  appendLog('model-log', r.success ? `✅ ${modelId} загружен` : `❌ ${r.error}`, r.success ? 'log-ok' : 'log-err');
}

// --- init ---
render();
