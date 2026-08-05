// RAG Tab logic
// Инициализируется через window.initRagTab() из admin/main.js

'use strict';

// Helpers
function ragFetch(url, options = {}) {
  return window.api
    ? window.api.fetch(url, options)
    : fetch(url, options).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      });
}

function notifyRag(msg, type = 'info') {
  if (typeof showNotification === 'function') {
    showNotification(msg, type);
  } else {
    console.log(`[${type}] ${msg}`);
  }
}

function setRagButtonState(btn, loading, originalText) {
  if (!btn) return;
  btn.disabled = loading;
  btn.textContent = loading ? '⏳ Выполняется...' : originalText;
}

// ── RAG STATUS ─────────────────────────────────────────────────────────────
async function loadRagStatus() {
  const statusEl = document.getElementById('admin-rag-status');
  if (!statusEl) return;
  try {
    const data = await ragFetch('/api/media-admin/rag/status');
    const db = data.database || {};
    const rag = data.rag_index || {};
    statusEl.innerHTML = `
      <span class="badge bg-secondary me-1">БД: <strong>${db.total_records || 0}</strong> записей</span>
      <span class="badge bg-info me-1">Фильмов: <strong>${db.by_type?.movie || 0}</strong></span>
      <span class="badge bg-primary me-1">Сериалов: <strong>${db.by_type?.series || 0}</strong></span>
      <span class="badge ${(rag.documents || 0) > 0 ? 'bg-success' : 'bg-warning text-dark'}">
        Индекс: <strong>${rag.documents || 0}</strong> doc
      </span>`;
  } catch (e) {
    if (statusEl) statusEl.innerHTML = `<span class="badge bg-danger">Ошибка: ${e.message}</span>`;
  }
}

// ── RAG BUILD ──────────────────────────────────────────────────────────────
async function buildRagIndexTab() {
  const btn = document.getElementById('btn-admin-rag-build');
  const originalText = btn ? btn.textContent : '';
  setRagButtonState(btn, true, originalText);
  notifyRag('Строю RAG-индекс. Это может занять несколько минут...', 'info');
  try {
    const data = await ragFetch('/api/media-admin/rag/build', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: '' })
    });
    if (data.success) {
      notifyRag(`✅ RAG-индекс построен успешно. Документов: ${data.count}`, 'success');
    } else {
      notifyRag('⚠️ Индекс построен с ошибкой', 'warning');
    }
    await loadRagStatus();
  } catch (e) {
    notifyRag('❌ Ошибка построения RAG-индекса: ' + e.message, 'danger');
  } finally {
    setRagButtonState(btn, false, originalText);
  }
}

// ── RAG JSON UPLOAD ────────────────────────────────────────────────────────
function showRagJsonModalTab() {
  const modalEl = document.getElementById('ragJsonModal');
  if (!modalEl) return;
  const modal = new bootstrap.Modal(modalEl);
  document.getElementById('rag-json-file').value = '';
  document.getElementById('rag-json-text').value = '';
  modal.show();
}

async function submitRagJsonTab() {
  const fileInput = document.getElementById('rag-json-file');
  const textInput = document.getElementById('rag-json-text');
  const btn = document.getElementById('btn-submit-rag-json');
  
  let jsonData = null;

  if (fileInput.files.length > 0) {
    const file = fileInput.files[0];
    try {
      const text = await file.text();
      jsonData = JSON.parse(text);
    } catch (e) {
      notifyRag('Ошибка чтения файла: ' + e.message, 'danger');
      return;
    }
  } else if (textInput.value.trim()) {
    try {
      jsonData = JSON.parse(textInput.value);
    } catch (e) {
      notifyRag('Ошибка парсинга JSON текста: ' + e.message, 'danger');
      return;
    }
  } else {
    notifyRag('Загрузите файл или вставьте JSON', 'warning');
    return;
  }

  if (!Array.isArray(jsonData)) {
    notifyRag('JSON должен быть массивом объектов (начинаться с [ и заканчиваться ])', 'warning');
    return;
  }

  const originalText = btn.textContent;
  setRagButtonState(btn, true, originalText);
  notifyRag('Запись JSON в RAG...', 'info');

  try {
    const data = await ragFetch('/api/media-admin/rag/add-json', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ documents: jsonData, key: '' })
    });
    notifyRag(`✅ Добавлено документов в RAG: ${data.added}`, 'success');
    const modalEl = document.getElementById('ragJsonModal');
    if (modalEl) {
      bootstrap.Modal.getInstance(modalEl)?.hide();
    }
    await loadRagStatus();
  } catch (e) {
    notifyRag('❌ Ошибка добавления в RAG: ' + e.message, 'danger');
  } finally {
    setRagButtonState(btn, false, originalText);
  }
}

async function submitRagDirTab() {
  const btn = document.getElementById('btn-submit-rag-dir');
  const originalText = btn.textContent;
  setRagButtonState(btn, true, originalText);
  notifyRag('Сканирование .files_for_rag...', 'info');

  try {
    const data = await ragFetch('/api/media-admin/rag/add-json-dir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: '' })
    });
    if (data.status === 'ok') {
      notifyRag(`✅ Из папки добавлено документов: ${data.added} (${data.files.join(', ') || 'нет файлов'})`, 'success');
      const modalEl = document.getElementById('ragJsonModal');
      if (modalEl) bootstrap.Modal.getInstance(modalEl)?.hide();
      await loadRagStatus();
    } else {
      notifyRag(`⚠️ Ошибка: ${data.message}`, 'warning');
    }
  } catch (e) {
    notifyRag('❌ Ошибка сканирования директории: ' + e.message, 'danger');
  } finally {
    setRagButtonState(btn, false, originalText);
  }
}

// ── RAG SEARCH ─────────────────────────────────────────────────────────────
async function searchRagTab() {
  const queryInput = document.getElementById('admin-rag-query');
  const resultsEl = document.getElementById('admin-rag-results');
  const btn = document.getElementById('btn-admin-rag-search');
  const query = queryInput ? queryInput.value.trim() : '';
  if (!query) return;

  const originalText = btn ? btn.textContent : '';
  setRagButtonState(btn, true, originalText);
  if (resultsEl) resultsEl.innerHTML = '<div class="text-muted small">Поиск...</div>';

  try {
    const params = new URLSearchParams({ query, top_k: 10 });
    const data = await ragFetch('/api/media-admin/rag/search?' + params, { method: 'POST' });
    const results = data.results || [];

    if (!results.length) {
      if (resultsEl) resultsEl.innerHTML = '<div class="text-muted small">Ничего не найдено</div>';
      return;
    }

    if (resultsEl) {
      resultsEl.innerHTML = results.map(r => `
        <div class="d-flex justify-content-between align-items-center border-bottom py-1">
          <div>
            <span class="fw-semibold small">${r.title}</span>
            <span class="badge ${r.type === 'series' ? 'bg-info' : 'bg-primary'} ms-1 badge-sm">${r.type === 'series' ? 'Сериал' : 'Фильм'}</span>
            <span class="text-muted small ms-1">${r.year || '—'} · ${r.disk_name || '—'}</span>
          </div>
          <span class="badge bg-success">${(r.score * 100).toFixed(1)}%</span>
        </div>
      `).join('');
    }
  } catch (e) {
    if (resultsEl) resultsEl.innerHTML = `<div class="text-danger small">❌ Ошибка: ${e.message}</div>`;
  } finally {
    setRagButtonState(btn, false, originalText);
  }
}

window.toggleRag = async function(enabled) {
  try {
    const data = await ragFetch('/api/admin/plugin/rag/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    });
    notifyRag(`RAG плагин ${data.enabled ? 'включен' : 'отключен'}`, 'success');
  } catch (e) {
    notifyRag('Ошибка переключения RAG: ' + e.message, 'danger');
    const toggle = document.getElementById('admin-rag-toggle');
    if (toggle) toggle.checked = !enabled; // revert
  }
};

window.initRagTab = async function() {
  // Load initial toggle state
  try {
    const data = await ragFetch('/api/admin/plugin/rag/status');
    const toggle = document.getElementById('admin-rag-toggle');
    if (toggle) toggle.checked = data.enabled;
  } catch (e) {
    console.error('Failed to load RAG status', e);
  }

  const buildBtn = document.getElementById('btn-admin-rag-build');
  if (buildBtn) buildBtn.addEventListener('click', buildRagIndexTab);

  const ragJsonBtn = document.getElementById('btn-admin-rag-json');
  if (ragJsonBtn) ragJsonBtn.addEventListener('click', showRagJsonModalTab);

  const submitRagJsonBtn = document.getElementById('btn-submit-rag-json');
  if (submitRagJsonBtn) submitRagJsonBtn.addEventListener('click', submitRagJsonTab);

  const submitRagDirBtn = document.getElementById('btn-submit-rag-dir');
  if (submitRagDirBtn) submitRagDirBtn.addEventListener('click', submitRagDirTab);

  const searchBtn = document.getElementById('btn-admin-rag-search');
  if (searchBtn) searchBtn.addEventListener('click', searchRagTab);

  const ragInput = document.getElementById('admin-rag-query');
  if (ragInput) {
    ragInput.addEventListener('keypress', e => {
      if (e.key === 'Enter') searchRagTab();
    });
  }

  loadRagStatus();
};
