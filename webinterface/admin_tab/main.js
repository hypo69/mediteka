// Admin Tab — RAG & Media management logic
// Инициализируется через window.initAdminTab() из admin/main.js

'use strict';

// ── Helpers ────────────────────────────────────────────────────────────────

function adminFetch(url, options = {}) {
  return window.api
    ? window.api.fetch(url, options)
    : fetch(url, options).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      });
}

function notify(msg, type = 'info') {
  if (typeof showNotification === 'function') {
    showNotification(msg, type);
  } else {
    console.log(`[${type}] ${msg}`);
  }
}

function setButtonState(btn, loading, originalText) {
  if (!btn) return;
  btn.disabled = loading;
  btn.textContent = loading ? '⏳ Выполняется...' : originalText;
}

// ── RAG STATUS ─────────────────────────────────────────────────────────────

async function loadAdminRagStatus() {
  const statusEl = document.getElementById('admin-rag-status');
  if (!statusEl) return;
  try {
    const data = await adminFetch('/api/media-admin/rag/status');
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

async function buildRagIndex() {
  const btn = document.getElementById('btn-admin-rag-build');
  const originalText = btn ? btn.textContent : '';
  setButtonState(btn, true, originalText);
  notify('Строю RAG-индекс. Это может занять несколько минут...', 'info');
  try {
    const data = await adminFetch('/api/media-admin/rag/build', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: '' })
    });
    if (data.success) {
      notify(`✅ RAG-индекс построен успешно. Документов: ${data.count}`, 'success');
    } else {
      notify('⚠️ Индекс построен с ошибкой', 'warning');
    }
    await loadAdminRagStatus();
  } catch (e) {
    notify('❌ Ошибка построения RAG-индекса: ' + e.message, 'danger');
  } finally {
    setButtonState(btn, false, originalText);
  }
}

// ── RAG SEARCH ─────────────────────────────────────────────────────────────

async function searchRagAdmin() {
  const queryInput = document.getElementById('admin-rag-query');
  const resultsEl = document.getElementById('admin-rag-results');
  const btn = document.getElementById('btn-admin-rag-search');
  const query = queryInput ? queryInput.value.trim() : '';
  if (!query) return;

  const originalText = btn ? btn.textContent : '';
  setButtonState(btn, true, originalText);
  if (resultsEl) resultsEl.innerHTML = '<div class="text-muted small">Поиск...</div>';

  try {
    const params = new URLSearchParams({ query, top_k: 10 });
    const data = await adminFetch('/api/media-admin/rag/search?' + params, { method: 'POST' });
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
    setButtonState(btn, false, originalText);
  }
}

// ── AUDIT ──────────────────────────────────────────────────────────────────

async function runAudit() {
  const btn = document.getElementById('btn-admin-audit');
  const bodyEl = document.getElementById('admin-audit-body');
  const originalText = btn ? btn.textContent : '';
  setButtonState(btn, true, originalText);
  if (bodyEl) bodyEl.innerHTML = '<div class="text-muted small">Выполняется аудит, ожидайте...</div>';

  try {
    const data = await adminFetch('/api/media-admin/audit', { method: 'POST' });
    const issues = data.issues || [];
    if (!issues.length) {
      if (bodyEl) bodyEl.innerHTML = '<div class="text-success small">✅ Проблем не обнаружено</div>';
      notify('✅ Аудит завершён: проблем не обнаружено', 'success');
    } else {
      const summary = `<div class="text-warning small fw-bold mb-1">⚠️ Найдено проблем: ${issues.length}</div>`;
      const issueList = issues.slice(0, 20).map(i => {
        const typeLabel = {
          missing_season: '❌ Отсутствует сезон',
          episodes: '⚠️ Нехватает серий',
          incomplete_files: '🕐 Незавершённые файлы',
          incomplete_metadata: '📋 Неполные метаданные',
          number: '🔢 Неверный номер'
        }[i.type] || i.type;
        return `<div class="border-bottom py-1 small"><span class="text-danger me-1">${typeLabel}</span><strong>${i.title || '—'}</strong>${i.season ? ` (Сезон ${i.season})` : ''}</div>`;
      }).join('');
      const moreText = issues.length > 20 ? `<div class="text-muted small mt-1">...и ещё ${issues.length - 20} проблем(ы)</div>` : '';
      if (bodyEl) bodyEl.innerHTML = summary + issueList + moreText;
      notify(`⚠️ Аудит завершён: найдено ${issues.length} проблем(ы)`, 'warning');
    }
  } catch (e) {
    if (bodyEl) bodyEl.innerHTML = `<div class="text-danger small">❌ Ошибка аудита: ${e.message}</div>`;
    notify('❌ Ошибка аудита: ' + e.message, 'danger');
  } finally {
    setButtonState(btn, false, originalText);
  }
}

// ── REBUILD DB ─────────────────────────────────────────────────────────────

async function runRebuild() {
  const btn = document.getElementById('btn-admin-rebuild');
  const bodyEl = document.getElementById('admin-rebuild-body');
  const originalText = btn ? btn.textContent : '';

  if (!confirm('Консолидация БД удалит дубликаты. Продолжить?')) return;

  setButtonState(btn, true, originalText);
  if (bodyEl) bodyEl.innerHTML = '<div class="text-muted small">Восстановление БД...</div>';

  try {
    const data = await adminFetch('/api/media-admin/rebuild', { method: 'POST' });
    const msg = data.result || 'Готово';
    if (bodyEl) bodyEl.innerHTML = `<div class="text-success small">✅ ${msg}</div>`;
    notify('✅ ' + msg, 'success');
  } catch (e) {
    if (bodyEl) bodyEl.innerHTML = `<div class="text-danger small">❌ Ошибка: ${e.message}</div>`;
    notify('❌ Ошибка восстановления: ' + e.message, 'danger');
  } finally {
    setButtonState(btn, false, originalText);
  }
}

// ── FULL SCAN ──────────────────────────────────────────────────────────────

async function runFullScan() {
  const btn = document.getElementById('btn-admin-scan');
  const originalText = btn ? btn.textContent : '';
  setButtonState(btn, true, originalText);
  notify('🔍 Запуск полного сканирования медиатеки...', 'info');
  try {
    await adminFetch('/api/media-admin/scan', { method: 'POST' });
    notify('✅ Сканирование запущено в фоне. Проверьте статус через несколько минут.', 'success');
  } catch (e) {
    notify('❌ Ошибка запуска сканирования: ' + e.message, 'danger');
  } finally {
    setButtonState(btn, false, originalText);
  }
}

// ── INIT ───────────────────────────────────────────────────────────────────

async function toggleRag(enabled) {
  try {
    const data = await adminFetch('/api/admin/plugin/rag/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    });
    notify(`RAG плагин ${data.enabled ? 'включен' : 'отключен'}`, 'success');
  } catch (e) {
    notify('Ошибка переключения RAG: ' + e.message, 'danger');
    const toggle = document.getElementById('admin-rag-toggle');
    if (toggle) toggle.checked = !enabled; // revert
  }
}

async function initAdminTabRAG() {
  // Load initial toggle state
  try {
    const data = await adminFetch('/api/admin/plugin/rag/status');
    const toggle = document.getElementById('admin-rag-toggle');
    if (toggle) toggle.checked = data.enabled;
  } catch (e) {
    console.error('Failed to load RAG status', e);
  }

  // RAG build button
  const buildBtn = document.getElementById('btn-admin-rag-build');
  if (buildBtn) {
    buildBtn.addEventListener('click', buildRagIndex);
  }

  // RAG search button
  const searchBtn = document.getElementById('btn-admin-rag-search');
  if (searchBtn) {
    searchBtn.addEventListener('click', searchRagAdmin);
  }

  // RAG search on Enter
  const ragInput = document.getElementById('admin-rag-query');
  if (ragInput) {
    ragInput.addEventListener('keypress', e => {
      if (e.key === 'Enter') searchRagAdmin();
    });
  }

  // Audit button
  const auditBtn = document.getElementById('btn-admin-audit');
  if (auditBtn) {
    auditBtn.addEventListener('click', runAudit);
  }

  // Rebuild button
  const rebuildBtn = document.getElementById('btn-admin-rebuild');
  if (rebuildBtn) {
    rebuildBtn.addEventListener('click', runRebuild);
  }

  // Full scan button
  const scanBtn = document.getElementById('btn-admin-scan');
  if (scanBtn) {
    scanBtn.addEventListener('click', runFullScan);
  }

  // Load initial RAG status
  loadAdminRagStatus();
}

window.initAdminTab = initAdminTabRAG;
