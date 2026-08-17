// RAG Tab logic
// Инициализируется через window.initRagTab() из admin/main.js

'use strict';

// Helpers
function ragFetch(url, options = {}) {
  return window.api
    ? window.api.fetch(url, options)
    : fetch(url, options).then(async r => {
        if (!r.ok) {
          let msg = r.statusText;
          try {
            const data = await r.json();
            if (data && data.detail) {
              if (typeof data.detail === 'string') {
                msg = data.detail;
              } else if (Array.isArray(data.detail)) {
                msg = data.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
              } else {
                msg = JSON.stringify(data.detail);
              }
            }
          } catch {}
          throw new Error(`${r.status} ${msg}`);
        }
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

let currentRagType = 'media';

// ── RAG MODE ────────────────────────────────────────────────────────────────
async function loadRagMode() {
  try {
    const data = await ragFetch('/api/admin/rag/config');
    if (data && data.mode) {
      const selector = document.getElementById('rag-mode-selector');
      if (selector) {
        selector.value = data.mode;
      }
    }
  } catch (e) {
    console.error("Ошибка загрузки режима RAG:", e);
  }
}

async function loadWebSearchEngine() {
  try {
    const data = await ragFetch('/api/admin/web-search/config');
    if (data && data.engine) {
      const selector = document.getElementById('web-search-engine-selector');
      if (selector) {
        selector.value = data.engine;
      }
    }
  } catch (e) {
    console.error("Ошибка загрузки сервера веб-поиска:", e);
  }
}

async function saveWebSearchEngine() {
  const selector = document.getElementById('web-search-engine-selector');
  const btn = document.getElementById('btn-save-web-engine');
  if (!selector || !btn) return;
  
  const engine = selector.value;
  const originalText = btn.textContent;
  setRagButtonState(btn, true, originalText);
  
  try {
    await ragFetch('/api/admin/web-search/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ engine: engine })
    });
    notifyRag(`✅ Сервер MCP поиска изменен на: ${engine}`, 'success');
  } catch (e) {
    notifyRag(`❌ Ошибка сохранения сервера веб-поиска: ${e.message}`, 'danger');
  } finally {
    setRagButtonState(btn, false, originalText);
  }
}

// ── RAG STATUS ─────────────────────────────────────────────────────────────
async function loadRagStatus() {
  const statusEl = document.getElementById('admin-rag-status');
  if (!statusEl) return;
  try {
    const data = await ragFetch(`/api/media-admin/rag/status?type=${currentRagType}`);
    const db = data.database || {};
    const rag = data.rag_index || {};
    
    if (currentRagType === 'chat') {
      statusEl.innerHTML = `
        <span class="badge bg-secondary me-1">Файлов диалогов: <strong>${db.total_records || 0}</strong></span>
        <span class="badge bg-info me-1">Ваших: <strong>${db.by_type?.user_saved || 0}</strong></span>
        <span class="badge ${(rag.documents || 0) > 0 ? 'bg-success' : 'bg-warning text-dark'}">
          Индекс Чат-RAG: <strong>${rag.documents || 0}</strong> doc
        </span>`;
    } else {
      statusEl.innerHTML = `
        <span class="badge bg-secondary me-1">БД: <strong>${db.total_records || 0}</strong> записей</span>
        <span class="badge bg-info me-1">Фильмов: <strong>${db.by_type?.movie || 0}</strong></span>
        <span class="badge bg-primary me-1">Сериалов: <strong>${db.by_type?.series || 0}</strong></span>
        <span class="badge ${(rag.documents || 0) > 0 ? 'bg-success' : 'bg-warning text-dark'}">
          Индекс: <strong>${rag.documents || 0}</strong> doc
        </span>`;
    }
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
    const data = await ragFetch(`/api/media-admin/rag/build?type=${currentRagType}`, {
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
  document.getElementById('rag-folder-input').value = '';
  document.getElementById('rag-json-text').value = '';
  const infoEl = document.getElementById('rag-upload-files-info');
  if (infoEl) {
    infoEl.classList.add('d-none');
    infoEl.textContent = '';
  }
  modal.show();
}

async function submitRagJsonTab() {
  const fileInput = document.getElementById('rag-json-file');
  const folderInput = document.getElementById('rag-folder-input');
  const textInput = document.getElementById('rag-json-text');
  const btn = document.getElementById('btn-submit-rag-json');
  
  let filesToProcess = [];
  if (fileInput.files.length > 0) {
    filesToProcess = Array.from(fileInput.files);
  } else if (folderInput.files.length > 0) {
    filesToProcess = Array.from(folderInput.files);
  }

  let documents = [];

  if (filesToProcess.length > 0) {
    notifyRag(`Чтение ${filesToProcess.length} файлов...`, 'info');
    for (const file of filesToProcess) {
      try {
        const text = await file.text();
        const extension = file.name.split('.').pop().toLowerCase();
        
        if (extension === 'json') {
          let parsed;
          try {
            parsed = JSON.parse(text);
          } catch (e) {
            console.warn(`Файл ${file.name} не является валидным JSON, пробуем как текст`, e);
            parsed = null;
          }
          
          if (Array.isArray(parsed)) {
            documents.push(...parsed);
          } else if (parsed && typeof parsed === 'object') {
            documents.push(parsed);
          } else {
            documents.push({
              id: `${file.name}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              text: text,
              meta: {
                title: file.name.replace(/\.[^/.]+$/, ""),
                type: 'document',
                disk_name: file.name
              }
            });
          }
        } else if (extension === 'txt' || extension === 'md') {
          documents.push({
            id: `${file.name}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            text: text,
            meta: {
              title: file.name.replace(/\.[^/.]+$/, ""),
              type: 'document',
              disk_name: file.name
            }
          });
        }
      } catch (e) {
        notifyRag(`Ошибка чтения файла ${file.name}: ${e.message}`, 'danger');
        return;
      }
    }
  } else if (textInput.value.trim()) {
    try {
      const parsed = JSON.parse(textInput.value);
      if (Array.isArray(parsed)) {
        documents = parsed;
      } else if (parsed && typeof parsed === 'object') {
        documents = [parsed];
      } else {
        notifyRag('JSON должен быть объектом или массивом объектов', 'warning');
        return;
      }
    } catch (e) {
      notifyRag('Ошибка парсинга JSON текста: ' + e.message, 'danger');
      return;
    }
  } else {
    notifyRag('Загрузите файлы/папку или вставьте JSON', 'warning');
    return;
  }

  if (documents.length === 0) {
    notifyRag('Не найдено валидных документов для добавления', 'warning');
    return;
  }

  const originalText = btn.textContent;
  setRagButtonState(btn, true, originalText);
  notifyRag(`Отправка ${documents.length} документов в RAG...`, 'info');

  try {
    const data = await ragFetch('/api/media-admin/rag/add-json', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ documents: documents, key: '' })
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
  const dirInput = document.getElementById('rag-server-dir-input');
  const serverDir = dirInput ? dirInput.value.trim() : '';
  
  if (!serverDir) {
    notifyRag('Укажите путь к папке на сервере', 'warning');
    return;
  }

  const originalText = btn.textContent;
  setRagButtonState(btn, true, originalText);
  notifyRag(`Сканирование ${serverDir}...`, 'info');

  try {
    const data = await ragFetch('/api/media-admin/rag/add-json-dir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: '', directories: [serverDir] })
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
  const thresholdInput = document.getElementById('rag-search-threshold');
  const query = queryInput ? queryInput.value.trim() : '';
  if (!query) return;

  const originalText = btn ? btn.textContent : '';
  setRagButtonState(btn, true, originalText);
  if (resultsEl) resultsEl.innerHTML = '<div class="text-muted small">Поиск...</div>';

  try {
    const threshold = thresholdInput ? thresholdInput.value : '0.3';
    const params = new URLSearchParams({ query, top_k: 10, type: currentRagType });
    const data = await ragFetch('/api/media-admin/rag/search?' + params, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query, top_k: 10, type: currentRagType })
    });
    let results = data.results || [];

    // Client-side filter for threshold as well to be absolutely sure
    results = results.filter(r => r.score >= parseFloat(threshold));

    if (!results.length) {
      if (resultsEl) resultsEl.innerHTML = '<div class="text-muted small py-3 text-center">Ничего не найдено с порогом схожести ≥ ' + threshold + '</div>';
      return;
    }

    if (resultsEl) {
      resultsEl.innerHTML = results.map((r, i) => `
        <div class="border-bottom py-2">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <span class="fw-semibold small">${escapeHtml(r.title)}</span>
              <span class="badge ${(r.media_type || r.type) === 'series' ? 'bg-info' : ((r.media_type || r.type) === 'chat_dialogue' ? 'bg-success' : 'bg-primary')} ms-1 badge-sm">
                ${(r.media_type || r.type) === 'series' ? 'Сериал' : ((r.media_type || r.type) === 'chat_dialogue' ? 'Диалог' : 'Фильм')}
              </span>
              <span class="text-muted small ms-1">${r.year || '—'} · ${r.disk_name || '—'}</span>
            </div>
            <div class="d-flex align-items-center gap-1">
              <span class="badge bg-success">${(r.score * 100).toFixed(1)}%</span>
              <button class="btn btn-xs btn-outline-secondary py-0 px-1 text-xs" style="font-size: 0.75rem;" onclick="toggleResultText(${i})">Текст</button>
            </div>
          </div>
          <div id="rag-result-chunk-${i}" class="mt-1 p-2 bg-light border rounded text-monospace text-xs d-none" style="white-space: pre-wrap; font-size: 0.8rem; font-family: monospace;">
            ${escapeHtml(r.text || 'Нет текста')}
          </div>
        </div>
      `).join('');
      // Store results globally to make toggle easy
      window.lastRagSearchResults = results;
    }
  } catch (e) {
    if (resultsEl) resultsEl.innerHTML = `<div class="text-danger small">❌ Ошибка: ${e.message}</div>`;
  } finally {
    setRagButtonState(btn, false, originalText);
  }
}

window.toggleResultText = function(index) {
  const el = document.getElementById(`rag-result-chunk-${index}`);
  if (el) {
    el.classList.toggle('d-none');
  }
};

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// ── RAG DOCUMENTS LISTING ──────────────────────────────────────────────────
let allRagDocuments = [];

async function loadRagDocuments(query = '') {
  const listEl = document.getElementById('admin-rag-docs-list');
  if (!listEl) return;
  listEl.innerHTML = '<div class="text-center text-muted py-4">⏳ Загрузка документов...</div>';
  
  try {
    const params = new URLSearchParams({ query, limit: 100, type: currentRagType });
    const data = await ragFetch('/api/media-admin/rag/documents?' + params);
    allRagDocuments = data.documents || [];
    
    if (!allRagDocuments.length) {
      listEl.innerHTML = '<div class="text-center text-muted py-4">Документы не найдены</div>';
      return;
    }

    listEl.innerHTML = allRagDocuments.map((doc, idx) => `
      <div class="list-group-item list-group-item-action p-2 d-flex justify-content-between align-items-center gap-2">
        <div class="overflow-hidden flex-grow-1">
          <div class="fw-semibold text-truncate text-sm" style="font-size: 0.9rem;">${escapeHtml(doc.title)}</div>
          <div class="text-muted text-xs text-truncate" style="font-size: 0.75rem;">
            ${(doc.media_type || doc.type) === 'series' ? 'Сериал' : ((doc.media_type || doc.type) === 'chat_dialogue' ? 'Диалог' : 'Фильм')} · ${doc.year || '—'} · ${doc.disk_name || '—'}
          </div>
        </div>
        <div class="d-flex gap-1 flex-shrink-0">
          <button class="btn btn-sm btn-outline-info" onclick="showRagDocDetail(${idx})">Смотреть</button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteRagDocDirect(${idx})">Удалить</button>
        </div>
      </div>
    `).join('');
  } catch (e) {
    listEl.innerHTML = `<div class="text-danger p-3 text-center">❌ Ошибка загрузки: ${e.message}</div>`;
  }
}

window.showRagDocDetail = function(idx) {
  const doc = allRagDocuments[idx];
  if (!doc) return;
  
  const mType = doc.media_type || doc.type;
  document.getElementById('ragDocViewTitle').textContent = doc.title;
  document.getElementById('ragDocViewBadgeDisk').textContent = 'Источник: ' + (doc.disk_name || '—');
  document.getElementById('ragDocViewBadgeType').textContent = 'Тип: ' + (mType === 'chat_dialogue' ? 'Диалог чата' : (mType === 'series' ? 'Сериал' : 'Фильм'));
  document.getElementById('ragDocViewBadgeYear').textContent = 'Дата/Год: ' + (doc.year || '—');
  document.getElementById('ragDocViewId').textContent = doc.id;
  
  const readOnlyContainer = document.getElementById('ragDocViewReadOnlyContainer');
  const editableContainer = document.getElementById('ragDocViewEditableContainer');
  const saveBtn = document.getElementById('btn-rag-doc-save');
  const deleteBtn = document.getElementById('btn-rag-doc-delete');
  
  if (currentRagType === 'chat') {
    if (readOnlyContainer) readOnlyContainer.classList.add('d-none');
    if (editableContainer) editableContainer.classList.remove('d-none');
    if (saveBtn) saveBtn.classList.remove('d-none');
    if (deleteBtn) {
      deleteBtn.classList.remove('d-none');
      deleteBtn.textContent = 'Удалить ответ';
    }
    
    document.getElementById('ragDocEditQuery').value = doc.query_raw || '';
    document.getElementById('ragDocEditChatText').value = doc.chat_text_raw || '';
    document.getElementById('ragDocEditVoiceText').value = doc.voice_text_raw || '';
    
    // Store current index globally to know what we are editing
    window.currentEditingDocIdx = idx;
  } else {
    if (readOnlyContainer) readOnlyContainer.classList.remove('d-none');
    if (editableContainer) editableContainer.classList.add('d-none');
    if (saveBtn) saveBtn.classList.add('d-none');
    if (deleteBtn) {
      deleteBtn.classList.remove('d-none');
      deleteBtn.textContent = 'Удалить документ';
    }
    
    document.getElementById('ragDocViewText').textContent = doc.text_full;
    window.currentEditingDocIdx = idx;
  }
  
  const modalEl = document.getElementById('ragDocViewModal');
  if (modalEl) {
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  }
};

async function saveRagDocChanges() {
  if (window.currentEditingDocIdx === undefined) return;
  const doc = allRagDocuments[window.currentEditingDocIdx];
  if (!doc) return;
  
  const saveBtn = document.getElementById('btn-rag-doc-save');
  const originalText = saveBtn.textContent;
  setRagButtonState(saveBtn, true, originalText);
  
  const query = document.getElementById('ragDocEditQuery').value.trim();
  const chat_text = document.getElementById('ragDocEditChatText').value.trim();
  const voice_text = document.getElementById('ragDocEditVoiceText').value.trim();
  
  try {
    const data = await ragFetch('/api/media-admin/rag/documents/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: doc.id,
        query,
        chat_text,
        voice_text
      })
    });
    
    if (data.status === 'ok') {
      notifyRag('✅ Документ RAG успешно обновлен на диске', 'success');
      
      // Hide modal
      const modalEl = document.getElementById('ragDocViewModal');
      if (modalEl) {
        bootstrap.Modal.getInstance(modalEl)?.hide();
      }
      
      // Refresh documents list
      loadRagDocuments();
    } else {
      notifyRag('⚠️ Ошибка обновления: ' + data.message, 'warning');
    }
  } catch (e) {
    notifyRag('❌ Ошибка сохранения изменений: ' + e.message, 'danger');
  } finally {
    setRagButtonState(saveBtn, false, originalText);
  }
}

async function deleteRagDoc() {
  if (window.currentEditingDocIdx === undefined) return;
  const doc = allRagDocuments[window.currentEditingDocIdx];
  if (!doc) return;

  const promptMsg = currentRagType === 'chat' 
    ? `Вы действительно хотите удалить этот ответ из RAG?\n\nВопрос: "${doc.title}"`
    : `Вы действительно хотите удалить этот документ из RAG?\n\nНазвание: "${doc.title}"`;

  if (!confirm(promptMsg)) {
    return;
  }

  const deleteBtn = document.getElementById('btn-rag-doc-delete');
  const originalText = deleteBtn.textContent;
  setRagButtonState(deleteBtn, true, originalText);

  try {
    const data = await ragFetch('/api/media-admin/rag/documents/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: doc.id,
        type: currentRagType
      })
    });

    if (data.status === 'ok') {
      notifyRag('✅ Документ RAG успешно удален', 'success');

      // Hide modal
      const modalEl = document.getElementById('ragDocViewModal');
      if (modalEl) {
        bootstrap.Modal.getInstance(modalEl)?.hide();
      }

      loadRagStatus();
      loadRagDocuments();
    } else {
      notifyRag('⚠️ Ошибка удаления: ' + data.message, 'warning');
    }
  } catch (e) {
    notifyRag('❌ Ошибка удаления: ' + e.message, 'danger');
  } finally {
    setRagButtonState(deleteBtn, false, originalText);
  }
}

window.deleteRagDocDirect = async function(idx) {
  const doc = allRagDocuments[idx];
  if (!doc) return;

  const promptMsg = currentRagType === 'chat' 
    ? `Вы действительно хотите удалить этот ответ из RAG?\n\nВопрос: "${doc.title}"`
    : `Вы действительно хотите удалить этот документ из RAG?\n\nНазвание: "${doc.title}"`;

  if (!confirm(promptMsg)) {
    return;
  }

  notifyRag('Удаление документа...', 'info');

  try {
    const data = await ragFetch('/api/media-admin/rag/documents/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: doc.id,
        type: currentRagType
      })
    });

    if (data.status === 'ok') {
      notifyRag('✅ Документ RAG успешно удален', 'success');
      loadRagStatus();
      loadRagDocuments();
    } else {
      notifyRag('⚠️ Ошибка удаления: ' + data.message, 'warning');
    }
  } catch (e) {
    notifyRag('❌ Ошибка удаления: ' + e.message, 'danger');
  }
};

async function clearRagIndexTab() {
  const label = currentRagType === 'chat' ? 'Чат-RAG' : 'Медиа-RAG';
  if (!confirm(`Вы действительно хотите ПОЛНОСТЬЮ очистить индекс ${label}?\nВсе векторные эмбеддинги будут удалены.`)) {
    return;
  }

  const btn = document.getElementById('btn-admin-rag-clear');
  const originalText = btn ? btn.textContent : '';
  setRagButtonState(btn, true, originalText);
  notifyRag('Очистка RAG...', 'info');

  try {
    const data = await ragFetch(`/api/media-admin/rag/clear`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: currentRagType })
    });
    if (data.status === 'ok') {
      notifyRag(`✅ RAG успешно очищен: ${data.message}`, 'success');
    } else {
      notifyRag('⚠️ Ошибка при очистке RAG', 'warning');
    }
    await loadRagStatus();
    loadRagDocuments();
  } catch (e) {
    notifyRag('❌ Ошибка очистки RAG: ' + e.message, 'danger');
  } finally {
    setRagButtonState(btn, false, originalText);
  }
}

window.switchRagType = function(type) {
  currentRagType = type;
  
  // Clear search results on switch
  const resultsEl = document.getElementById('admin-rag-results');
  if (resultsEl) {
    resultsEl.innerHTML = '<div class="text-center text-muted py-4">Введите запрос и нажмите «Найти» для проверки результатов</div>';
  }
  const queryInput = document.getElementById('admin-rag-query');
  if (queryInput) queryInput.value = '';

  loadRagStatus();
  loadRagDocuments();
};

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
  console.log('[RAG Tab] initRagTab called');
  
  // 1. Immediately load status and documents list
  loadRagStatus();
  loadRagDocuments();

  // 2. Load mode and engine settings
  try { loadRagMode(); } catch (e) {}
  try { loadWebSearchEngine(); } catch (e) {}

  // 3. Load initial toggle state
  try {
    const data = await ragFetch('/api/admin/plugin/rag/status');
    const toggle = document.getElementById('admin-rag-toggle');
    if (toggle && data && typeof data.enabled !== 'undefined') {
      toggle.checked = data.enabled;
    }
  } catch (e) {
    console.warn('[RAG Tab] Could not load plugin toggle status', e);
  }

  // 4. Bind radio buttons selector
  const mediaRadio = document.getElementById('rag-type-media');
  const chatRadio = document.getElementById('rag-type-chat');
  if (mediaRadio && chatRadio) {
    mediaRadio.onchange = () => { if (mediaRadio.checked) switchRagType('media'); };
    chatRadio.onchange = () => { if (chatRadio.checked) switchRagType('chat'); };
  }

  const buildBtn = document.getElementById('btn-admin-rag-build');
  if (buildBtn) buildBtn.onclick = async () => {
    await buildRagIndexTab();
    loadRagDocuments();
  };

  const ragJsonBtn = document.getElementById('btn-admin-rag-json');
  if (ragJsonBtn) ragJsonBtn.onclick = showRagJsonModalTab;

  const fileInput = document.getElementById('rag-json-file');
  const folderInput = document.getElementById('rag-folder-input');
  const infoEl = document.getElementById('rag-upload-files-info');

  const updateFileInfo = (inputSource) => {
    if (inputSource === 'files') {
      if (folderInput) folderInput.value = '';
      if (fileInput && fileInput.files.length > 0) {
        if (infoEl) {
          infoEl.textContent = `Выбрано файлов: ${fileInput.files.length}`;
          infoEl.classList.remove('d-none');
        }
      } else {
        if (infoEl) infoEl.classList.add('d-none');
      }
    } else if (inputSource === 'folder') {
      if (fileInput) fileInput.value = '';
      if (folderInput && folderInput.files.length > 0) {
        if (infoEl) {
          infoEl.textContent = `Выбрано файлов в папке: ${folderInput.files.length}`;
          infoEl.classList.remove('d-none');
        }
      } else {
        if (infoEl) infoEl.classList.add('d-none');
      }
    }
  };

  if (fileInput) fileInput.onchange = () => updateFileInfo('files');
  if (folderInput) folderInput.onchange = () => updateFileInfo('folder');

  const submitRagJsonBtn = document.getElementById('btn-submit-rag-json');
  if (submitRagJsonBtn) submitRagJsonBtn.onclick = async () => {
    await submitRagJsonTab();
    loadRagDocuments();
  };

  const submitRagDirBtn = document.getElementById('btn-submit-rag-dir');
  if (submitRagDirBtn) submitRagDirBtn.onclick = async () => {
    await submitRagDirTab();
    loadRagDocuments();
  };

  const searchBtn = document.getElementById('btn-admin-rag-search');
  if (searchBtn) searchBtn.onclick = searchRagTab;

  const ragInput = document.getElementById('admin-rag-query');
  if (ragInput) {
    ragInput.onkeypress = e => {
      if (e.key === 'Enter') searchRagTab();
    };
  }

  // Bind save document changes button
  const docSaveBtn = document.getElementById('btn-rag-doc-save');
  if (docSaveBtn) docSaveBtn.onclick = saveRagDocChanges;

  // Bind delete document button
  const docDeleteBtn = document.getElementById('btn-rag-doc-delete');
  if (docDeleteBtn) docDeleteBtn.onclick = deleteRagDoc;

  // Bind clear RAG button
  const clearBtn = document.getElementById('btn-admin-rag-clear');
  if (clearBtn) clearBtn.onclick = clearRagIndexTab;

  // Bind documents filter
  const filterBtn = document.getElementById('btn-admin-rag-docs-filter');
  const filterInput = document.getElementById('admin-rag-docs-filter');
  if (filterBtn && filterInput) {
    const applyFilter = () => {
      const q = filterInput.value.trim();
      loadRagDocuments(q);
    };
    filterBtn.onclick = applyFilter;
    filterInput.onkeypress = e => {
      if (e.key === 'Enter') applyFilter();
    };
  }

  // Bind RAG mode save button
  const saveModeBtn = document.getElementById('btn-save-rag-mode');
  if (saveModeBtn) {
    saveModeBtn.onclick = saveRagMode;
  }

  // Bind Web Search engine save button
  const saveEngineBtn = document.getElementById('btn-save-web-engine');
  if (saveEngineBtn) {
    saveEngineBtn.onclick = saveWebSearchEngine;
  }
};

// Auto-run if tab is present
if (document.getElementById('tab-rag') || document.getElementById('admin-rag-status')) {
  window.initRagTab();
}
