// Admin Tab — Media management logic
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

function initAdminTabLogic() {
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
}

window.initAdminTab = initAdminTabLogic;
