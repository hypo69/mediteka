// Gemini Models & APIs management tab logic

async function initModelsTab() {
  const modelSelect = document.getElementById('models-tab-select');
  const saveBtn = document.getElementById('btn-models-tab-save');
  const keysListBody = document.getElementById('keys-list-body');
  const refreshKeysBtn = document.getElementById('btn-refresh-keys');
  const addKeyBtn = document.getElementById('btn-add-key');
  
  if (!modelSelect || !saveBtn || !keysListBody) return;

  // --- 1. Load Models list & Active model ---
  await loadTabModels(modelSelect, saveBtn);

  // --- 2. Load API keys ---
  await refreshKeysList(keysListBody);

  // --- 2.5 Load Foundry Configuration ---
  await loadFoundryConfig();

  // --- 3. Bind Event Handlers ---
  const saveFoundryBtn = document.getElementById('btn-save-foundry');
  if (saveFoundryBtn) {
    saveFoundryBtn.onclick = async () => {
      const enabled = document.getElementById('foundry-enabled')?.checked || false;
      const url = document.getElementById('foundry-url')?.value.trim() || '';
      const key = document.getElementById('foundry-key')?.value.trim() || '';
      const model = document.getElementById('foundry-model')?.value.trim() || '';
      
      saveFoundryBtn.disabled = true;
      try {
        await window.api.fetch('/api/foundry/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled, url, key, model })
        });
        showModelsNotification('Настройки Microsoft Foundry успешно сохранены', 'success');
        // Reload models selection as it might have changed
        await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error('Ошибка сохранения Foundry:', err);
        showModelsNotification('Ошибка сохранения: ' + err.message, 'danger');
      } finally {
        saveFoundryBtn.disabled = false;
      }
    };
  }
  saveBtn.onclick = async () => {
    const selectedModel = modelSelect.value;
    saveBtn.disabled = true;
    const originalText = saveBtn.textContent;
    saveBtn.textContent = 'Сохранение...';
    
    try {
      await window.api.fetch('/auth/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel })
      });
      showModelsNotification('Модель успешно обновлена на: ' + selectedModel, 'success');
      
      // Also update the selector on the other tab if it exists
      const otherModelSelect = document.getElementById('admin-model-select');
      if (otherModelSelect) {
        otherModelSelect.value = selectedModel;
      }
    } catch (err) {
      console.error('Ошибка сохранения модели:', err);
      showModelsNotification('Ошибка сохранения: ' + err.message, 'danger');
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = originalText;
    }
  };

  if (refreshKeysBtn) {
    refreshKeysBtn.onclick = () => refreshKeysList(keysListBody);
  }

  if (addKeyBtn) {
    addKeyBtn.onclick = async () => {
      const nameInput = document.getElementById('new-key-name');
      const valueInput = document.getElementById('new-key-value');
      if (!nameInput || !valueInput) return;

      const name = nameInput.value.trim();
      const apiKey = valueInput.value.trim();

      if (!name || !apiKey) {
        showModelsNotification('Заполните все поля!', 'warning');
        return;
      }

      addKeyBtn.disabled = true;
      try {
        await window.api.fetch('/api/keys', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, api_key: apiKey, status: 'active' })
        });
        showModelsNotification(`Ключ "${name}" успешно добавлен`, 'success');
        nameInput.value = '';
        valueInput.value = '';
        await refreshKeysList(keysListBody);
      } catch (err) {
        console.error('Ошибка добавления ключа:', err);
        showModelsNotification('Ошибка добавления: ' + err.message, 'danger');
      } finally {
        addKeyBtn.disabled = false;
      }
    };
  }
}

// Helper to load models list
async function loadTabModels(modelSelect, saveBtn) {
  modelSelect.innerHTML = '';
  let models = [];
  
  try {
    const modelsData = await window.api.fetch('/api/chat/models');
    models = modelsData.models || [];
  } catch (err) {
    console.error('Ошибка загрузки моделей:', err);
    showModelsNotification('Ошибка загрузки моделей AI: ' + err.message, 'danger');
  }

  if (models.length === 0) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'Нет доступных моделей';
    modelSelect.appendChild(option);
    saveBtn.disabled = true;
  } else {
    models.forEach(modelName => {
      const option = document.createElement('option');
      option.value = modelName;
      option.textContent = modelName;
      modelSelect.appendChild(option);
    });
    saveBtn.disabled = false;
  }

  try {
    const settingsData = await window.api.fetch('/auth/settings');
    if (settingsData && settingsData.model) {
      modelSelect.value = settingsData.model;
    }
  } catch (err) {
    console.error('Ошибка загрузки настроек AI пользователя:', err);
  }
}

// Helper to refresh keys list table
async function refreshKeysList(container) {
  try {
    container.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Загрузка ключей...</td></tr>';
    const keysData = await window.api.fetch('/api/keys');
    const keys = keysData.keys || [];

    if (keys.length === 0) {
      container.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Список ключей пуст</td></tr>';
      return;
    }

    container.innerHTML = '';
    keys.forEach(key => {
      const row = document.createElement('tr');

      // 1. Name
      const tdName = document.createElement('td');
      tdName.innerHTML = `<strong>${key.name}</strong>`;
      row.appendChild(tdName);

      // 2. Key masked
      const tdKey = document.createElement('td');
      tdKey.className = 'font-monospace text-muted small';
      tdKey.textContent = key.api_key_masked;
      row.appendChild(tdKey);

      // 3. Status badge
      const tdStatus = document.createElement('td');
      const isEnabled = key.status === 'active';
      const statusClass = isEnabled ? 'bg-success' : 'bg-secondary';
      const statusText = isEnabled ? 'Активен' : 'Отключен';
      tdStatus.innerHTML = `<span class="badge ${statusClass}">${statusText}</span>`;
      row.appendChild(tdStatus);

      // 4. Quota status
      const tdQuota = document.createElement('td');
      if (key.exhausted) {
        let resetText = 'Лимит';
        if (key.reset_in_seconds) {
          const hours = Math.floor(key.reset_in_seconds / 3600);
          const mins = Math.floor((key.reset_in_seconds % 3600) / 60);
          resetText = `Сброс через ${hours}ч ${mins}м`;
        }
        tdQuota.innerHTML = `<span class="badge bg-danger d-block mb-1" title="Превышен лимит запросов в сутки">${resetText}</span>`;
      } else {
        tdQuota.innerHTML = `<span class="badge bg-success d-block mb-1">OK</span>`;
      }
      row.appendChild(tdQuota);

      // 5. Actions buttons
      const tdActions = document.createElement('td');
      tdActions.className = 'text-end';

      // Toggle status button
      const btnToggle = document.createElement('button');
      btnToggle.className = `btn btn-xs btn-sm me-1 ${isEnabled ? 'btn-outline-secondary' : 'btn-outline-success'}`;
      btnToggle.textContent = isEnabled ? 'Откл' : 'Вкл';
      btnToggle.onclick = () => toggleKeyStatus(key.name, isEnabled ? 'disabled' : 'active', container);
      tdActions.appendChild(btnToggle);

      // Reset Quota button (if exhausted)
      if (key.exhausted) {
        const btnReset = document.createElement('button');
        btnReset.className = 'btn btn-xs btn-outline-warning btn-sm me-1';
        btnReset.innerHTML = 'Сброс';
        btnReset.title = 'Сбросить 24-часовой бан квоты';
        btnReset.onclick = () => resetKeyQuota(key.name, container);
        tdActions.appendChild(btnReset);
      }

      // Delete button
      const btnDelete = document.createElement('button');
      btnDelete.className = 'btn btn-xs btn-outline-danger btn-sm';
      btnDelete.textContent = 'Удалить';
      btnDelete.onclick = () => deleteKey(key.name, container);
      tdActions.appendChild(btnDelete);

      row.appendChild(tdActions);
      container.appendChild(row);
    });

  } catch (err) {
    console.error('Ошибка загрузки ключей:', err);
    container.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-danger">Ошибка: ${err.message}</td></tr>`;
  }
}

// API action helpers
async function toggleKeyStatus(name, newStatus, container) {
  try {
    await window.api.fetch(`/api/keys/${name}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    showModelsNotification(`Статус ключа "${name}" изменен на ${newStatus === 'active' ? 'активный' : 'отключенный'}`, 'success');
    await refreshKeysList(container);
  } catch (err) {
    console.error('Ошибка переключения статуса ключа:', err);
    showModelsNotification('Ошибка изменения статуса: ' + err.message, 'danger');
  }
}

async function resetKeyQuota(name, container) {
  try {
    await window.api.fetch(`/api/keys/${name}/reset-quota`, { method: 'POST' });
    showModelsNotification(`Квота для ключа "${name}" успешно сброшена`, 'success');
    await refreshKeysList(container);
  } catch (err) {
    console.error('Ошибка сброса квоты:', err);
    showModelsNotification('Ошибка сброса квоты: ' + err.message, 'danger');
  }
}

async function deleteKey(name, container) {
  if (!confirm(`Вы уверены, что хотите удалить ключ "${name}"?`)) return;
  try {
    await window.api.fetch(`/api/keys/${name}`, { method: 'DELETE' });
    showModelsNotification(`Ключ "${name}" успешно удален`, 'success');
    await refreshKeysList(container);
  } catch (err) {
    console.error('Ошибка удаления ключа:', err);
    showModelsNotification('Ошибка удаления: ' + err.message, 'danger');
  }
}

// Notification helper
function showModelsNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
  notification.style.zIndex = '9999';
  notification.style.maxWidth = '400px';
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 5000);
}

async function loadFoundryConfig() {
  try {
    const config = await window.api.fetch('/api/foundry/config');
    const enabledInput = document.getElementById('foundry-enabled');
    const urlInput = document.getElementById('foundry-url');
    const keyInput = document.getElementById('foundry-key');
    const modelInput = document.getElementById('foundry-model');
    
    if (enabledInput) enabledInput.checked = config.enabled || false;
    if (urlInput) urlInput.value = config.url || '';
    if (keyInput) keyInput.value = config.key || '';
    if (modelInput) modelInput.value = config.model || '';
  } catch (err) {
    console.error('Ошибка загрузки настроек Foundry:', err);
  }
}

// ── System Instruction Editor ─────────────────────────────────────────────

async function loadSystemInstruction() {
  const editor = document.getElementById('system-instruction-editor');
  if (!editor) return;
  
  editor.value = 'Загрузка...';
  editor.disabled = true;
  
  try {
    const data = await window.api.fetch('/api/admin/system_instruction');
    editor.value = data.content || '';
    editor.disabled = false;
  } catch (err) {
    console.error('Ошибка загрузки системной инструкции:', err);
    editor.value = '';
    editor.disabled = false;
    showModelsNotification('Ошибка загрузки системной инструкции: ' + err.message, 'danger');
  }
}

async function saveSystemInstruction() {
  const editor = document.getElementById('system-instruction-editor');
  const saveBtn = document.getElementById('btn-save-instruction');
  if (!editor || !saveBtn) return;

  const originalHtml = saveBtn.innerHTML;
  saveBtn.disabled = true;
  saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Сохранение...';

  try {
    await window.api.fetch('/api/admin/system_instruction', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: editor.value })
    });
    showModelsNotification('✅ Системная инструкция успешно сохранена', 'success');
  } catch (err) {
    console.error('Ошибка сохранения системной инструкции:', err);
    showModelsNotification('Ошибка сохранения: ' + err.message, 'danger');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerHTML = originalHtml;
  }
}

// Hook system instruction editor after initModelsTab
const _origInitModelsTab = window.initModelsTab;
window.initModelsTab = async function() {
  await _origInitModelsTab();
  
  // Load system instruction
  await loadSystemInstruction();

  // Bind save/reload buttons
  const saveBtn = document.getElementById('btn-save-instruction');
  const reloadBtn = document.getElementById('btn-reload-instruction');

  if (saveBtn) {
    saveBtn.onclick = saveSystemInstruction;
  }
  if (reloadBtn) {
    reloadBtn.onclick = loadSystemInstruction;
  }
};
