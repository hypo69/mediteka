// Admin Interface Main JS
import { initI18n, switchLang, applyTranslations } from '../js/i18n.js';

window.switchLang = switchLang;
window.applyTranslations = applyTranslations;

// Admin password (hardcoded for security)
const ADMIN_PASSWORD = 'onela';

// API module
window.api = {
  async fetch(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
      let msg = response.statusText;
      try {
        const data = await response.json();
        msg = data.detail || msg;
      } catch {}
      throw new Error(`${response.status} ${msg}`);
    }
    return response.json();
  },
  
  // User management API
  users: {
    async list() {
      return this.fetch('/api/admin/users');
    },
    
    async update(userId, data) {
      return this.fetch(`/api/admin/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },
    
    async delete(userId) {
      return this.fetch(`/api/admin/users/${userId}`, {
        method: 'DELETE'
      });
    }
  }
};

// HELP content
window.HELP_CONTENT = {};

// Password protection state
let isPasswordProtected = false;
let hasEnteredPassword = false;

document.addEventListener('DOMContentLoaded', async () => {
  console.log('Admin interface initializing...');
  
  // Check if password protection is enabled
  isPasswordProtected = false; // Disabled since backend handles security
  
  if (isPasswordProtected) {
    showPasswordModal();
  } else {
    document.getElementById('admin-interface').style.display = 'block';
    initInterface();
  }
  
  console.log('Admin interface ready');
});

async function initInterface() {
  // Initialize i18n
  const savedLang = localStorage.getItem('app_language') || 'ru';
  await initI18n(savedLang);
  
  // Setup language selector
  const langSelector = document.getElementById('lang-selector');
  if (langSelector) {
    langSelector.value = savedLang;
    langSelector.addEventListener('change', (e) => {
      switchLang(e.target.value);
    });
  }

  
  // Initialize HELP content
  initHelpContent();
  
  // Load all tabs
  await Promise.all([
    loadTabContent('chat', '/html/chat/index.html'),
    loadTabContent('torrents', '/html/torrents/index.html'),
    loadTabContent('media', '/html/media/index.html'),
    loadTabContent('admin', '/html/admin_tab/index.html'),
    loadTabContent('help', '/html/help/index.html'),
  ]);
  
  // Apply translations
  applyTranslations();
  
  console.log('Admin interface ready');
}

function showPasswordModal() {
  const modal = new bootstrap.Modal(document.getElementById('passwordModal'));
  modal.show();
  
  const loginBtn = document.getElementById('login-btn');
  const passwordInput = document.getElementById('admin-password');
  const passwordError = document.getElementById('password-error');
  
  passwordInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') verifyPassword();
  });
  
  loginBtn?.addEventListener('click', verifyPassword);
}

async function verifyPassword() {
  const passwordInput = document.getElementById('admin-password');
  const passwordError = document.getElementById('password-error');
  const password = passwordInput?.value;
  
  if (password === ADMIN_PASSWORD) {
    // Password correct
    hasEnteredPassword = true;
    
    // Hide error
    passwordError?.classList.add('d-none');
    
    // Close modal
    const modalElement = document.getElementById('passwordModal');
    const modal = bootstrap.Modal.getInstance(modalElement);
    modal?.hide();
    
    // Show interface
    document.getElementById('admin-interface').style.display = 'block';
    
    // Initialize interface
    await initInterface();
  } else {
    // Password incorrect
    passwordError?.classList.remove('d-none');
    if (passwordError) {
      passwordError.textContent = 'Неверный пароль';
    }
    
    // Clear input
    if (passwordInput) {
      passwordInput.value = '';
      passwordInput.focus();
    }
  }
}

async function loadTabContent(tabName, url) {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    const container = document.getElementById(`tab-${tabName}`);
    container.innerHTML = html;
    
    // Load JS for the tab
    const script = document.createElement('script');
    script.src = `/html/${tabName}/main.js?v=20260725`;
    script.onload = () => {
      if (window[`init${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Tab`]) {
        window[`init${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Tab`]();
      }
      applyTranslations();
    };
    script.onerror = () => console.error(`Error loading JS for ${tabName}`);
    container.appendChild(script);
  } catch (e) {
    console.error(`Error loading tab ${tabName}:`, e);
    document.getElementById(`tab-${tabName}`).innerHTML = 
      `<div class="alert alert-danger">Ошибка загрузки: ${e.message}</div>`;
  }
}

// Initialize HELP content
function initHelpContent() {
  window.HELP_CONTENT = {
    'overview': `<h4>📋 Обзор проекта</h4><p>ai-mediteka — интегрированная среда для AI и медиатеки.</p>`,
    'scan': `<h4>🔍 Сканирование</h4><p>Полное сканирование медиатеки с классификацией.</p>`,
    'audit': `<h4>🗂 Аудит БД</h4><p>Сверка таблицы media с файлами на диске.</p>`,
    'rebuild': `<h4>🔧 Восстановление</h4><p>Восстановление БД из JSON.</p>`,
    'rag': `<h4>🧠 RAG-индекс</h4><p>Семантический поиск по медиатеке.</p>`,
    'media_paths': `<h4>📁 Пути сканирования</h4><p>Добавьте пути к медиафайлам.</p>`,
    'media_summary': `<h4>📺 Сводка по сериалам</h4><p>Статистика по сериалам.</p>`,
    'media_duplicates': `<h4>⚠️ Дубликаты</h4><p>Поиск дубликатов сезонов.</p>`,
    'media_integrity': `<h4>🔎 Целостность</h4><p>Проверка целостности файлов.</p>`,
    'media_report': `<h4>📄 Отчёт</h4><p>Генерация отчёта по медиатеке.</p>`,
    'code_rules': `<h4>⚙️ CODE_RULES</h4><p>Правила кодирования проекта.</p>`,
    'architecture': `<h4>🏗️ Архитектура</h4><p>Технологический стек проекта.</p>`,
    'fastapi': `<h4>🚀 FastAPI</h4><p>API роутеры и эндпоинты.</p>`,
    'media': `<h4>🎬 Медиатека</h4><p>Управление медиатекой.</p>`,
    'qbittorrent': `<h4>🧲 qBittorrent</h4><p>Управление торрентами.</p>`,
    'gemini': `<h4>🧠 Gemini AI</h4><p>Интеграция с Gemini.</p>`,
    'configuration': `<h4>⚙️ Конфигурация</h4><p>Настройки проекта.</p>`,
    'cli_commands': `<h4>⌨️ CLI команды</h4><p>Командная строка.</p>`,
  };
}

function showHelpModal(key) {
  const content = window.HELP_CONTENT[key] || '<p>Информация не найдена</p>';
  document.getElementById('help-modal-content').innerHTML = content;
  const modal = new bootstrap.Modal(document.getElementById('help-modal'));
  modal.show();
}

// Функция назначения категорий торрентам
async function assignCategoriesFromDB() {
  try {
    showNotification('Назначение категорий...', 'info');
    const result = await window.api.fetch('/api/torrents/assign-categories', { method: 'POST' });
    showNotification(result.result || 'Категории назначены', 'success');
  } catch (e) {
    showNotification('Ошибка: ' + e.message, 'danger');
  }
}

// Уведомления
function showNotification(message, type = 'info') {
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