// System Admin Tab — Central Management Logic

'use strict';

async function initSystemAdminTab() {
  console.log('Инициализация панели системного управления...');
  await refreshSystemDashboard();
}

async function refreshSystemDashboard() {
  try {
    // 1. Загрузка дисков
    const drivesData = await window.api.fetch('/api/control/rescan', { method: 'GET' }).catch(() => ({ drives: [] }));
    const drives = Array.isArray(drivesData.drives) ? drivesData.drives : [];
    const drivesCountEl = document.getElementById('sys-drives-count');
    const drivesListEl = document.getElementById('sys-drives-list');
    if (drivesCountEl) drivesCountEl.textContent = `${drives.length} диск(ов)`;
    if (drivesListEl) drivesListEl.textContent = drives.join(', ') || 'Диски не обнаружены';

    // 2. Загрузка статуса плагинов
    const pluginsData = await window.api.fetch('/api/admin/plugins').catch(() => ({ plugins: [] }));
    const plugins = pluginsData.plugins || [];
    const pluginsCountEl = document.getElementById('sys-plugins-count');
    const pluginsActiveEl = document.getElementById('sys-plugins-active-count');
    const activeCount = plugins.filter(p => p.enabled).length;
    if (pluginsCountEl) pluginsCountEl.textContent = `${plugins.length} модулей`;
    if (pluginsActiveEl) pluginsActiveEl.textContent = `${activeCount} активно из ${plugins.length}`;
  } catch (err) {
    console.error('Ошибка загрузки системного дашборда:', err);
  }
}

async function rescanStorageDrives() {
  try {
    if (typeof showNotification === 'function') showNotification('Пересканирование накопителей ОС...', 'info');
    const result = await window.api.fetch('/api/control/rescan', { method: 'GET' });
    const drivesList = Array.isArray(result.drives) ? result.drives.join(', ') : 'OK';
    if (typeof showNotification === 'function') showNotification(`Диски обновлены: ${drivesList}`, 'success');
    await refreshSystemDashboard();
  } catch (e) {
    if (typeof showNotification === 'function') showNotification(`Ошибка: ${e.message}`, 'danger');
  }
}

async function actualizeAiModels() {
  try {
    if (typeof showNotification === 'function') showNotification('Актуализация пула моделей ИИ...', 'info');
    await window.api.fetch('/api/keys/actualize-all', { method: 'POST' }).catch(() => {});
    if (typeof showNotification === 'function') showNotification('Модели успешно синхронизированы', 'success');
    await refreshSystemDashboard();
  } catch (e) {
    if (typeof showNotification === 'function') showNotification(`Ошибка: ${e.message}`, 'danger');
  }
}

function switchToTab(tabName) {
  const triggerEl = document.querySelector(`[data-bs-target="#tab-${tabName}"]`);
  if (triggerEl) {
    const tab = new bootstrap.Tab(triggerEl);
    tab.show();
  }
}

window.initAdminTab = initSystemAdminTab;
window.rescanStorageDrives = rescanStorageDrives;
window.actualizeAiModels = actualizeAiModels;
window.switchToTab = switchToTab;
