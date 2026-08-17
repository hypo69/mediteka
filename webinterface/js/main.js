// ── MAIN.JS ───────────────────────────────────────────────────────────────────

import { initI18n, switchLang, applyTranslations } from './i18n.js';

// Make switchLang available globally for the language selector
window.switchLang = switchLang;
window.applyTranslations = applyTranslations;

// ── THEME MANAGEMENT ──────────────────────────────────────────────────────────
// Version 2.1 - Fixed DOM initialization and syntax errors

function initTheme() {
  const themeToggle = document.getElementById('theme-toggle');
  const savedTheme = localStorage.getItem('theme') || 'light';

  // Set initial theme
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  // Theme toggle handler
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
      updateThemeIcon(newTheme);
    });
  }
}

function updateThemeIcon(theme) {
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    if (theme === 'dark') {
      themeToggle.innerHTML = '<i class="bi bi-sun-fill"></i>';
      themeToggle.setAttribute('title', 'Светлая тема');
    } else {
      themeToggle.innerHTML = '<i class="bi bi-moon-fill"></i>';
      themeToggle.setAttribute('title', 'Темная тема');
    }
  }
}

// Initialize HELP content when help tab is loaded
document.addEventListener('DOMContentLoaded', async () => {
  console.log('Starting initialization...');
  
  // Initialize theme first
  initTheme();
  console.log('Theme initialized');
  
  // Initialize i18n first
  const savedLang = localStorage.getItem('app_language') || 'ru';
  await initI18n(savedLang);
  console.log('i18n initialized');
  
  // Setup language selector
  const langSelector = document.getElementById('lang-selector');
  if (langSelector) {
    langSelector.value = savedLang;
    langSelector.addEventListener('change', (e) => {
      switchLang(e.target.value);
    });
  }

  
  await initHelpContent();
  console.log('HELP system initialized');
  
  console.log('Loading tabs...');
  await Promise.all([
    loadTabContent('chat', '/html/chat/index.html'),
    loadTabContent('torrents', '/html/torrents/index.html'),
    loadTabContent('media', '/html/media/index.html'),
    loadTabContent('movie-search', '/html/movie-search/index.html'),
    loadTabContent('admin', '/html/admin/index.html'),
    loadTabContent('help', '/html/help/index.html'),
  ]);
  console.log('All tabs loaded');
  
  // Apply translations after all tabs are loaded
  applyTranslations();
  
  // Инициализация первой вкладки
  const chatTab = document.querySelector('[data-bs-target="#tab-chat"]');
  if (chatTab) {
    chatTab.classList.add('active');
    document.getElementById('tab-chat').classList.add('show', 'active');
  }
  console.log('Initialization complete');
});

// Загрузка контента вкладки
async function loadTabContent(tabName, url) {
  try {
    console.log(`Loading tab ${tabName} from ${url}...`);
    const response = await fetch(url);
    console.log(`Response status: ${response.status} for ${tabName}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    const container = document.getElementById(`tab-${tabName}`);
    container.innerHTML = html;
    console.log(`Content set for tab ${tabName}, length: ${html.length}`);
    
    // Загрузка JS файла вкладки
    const script = document.createElement('script');
    script.src = `/html/${tabName}/main.js?v=20260811`;
    if (tabName === 'admin') {
      script.type = 'module';
    }
    script.onload = () => {
      console.log(`✓ Загружен JS вкладки: ${tabName}`);
      // Call init function if exists
      if (window[`init${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Tab`]) {
        window[`init${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Tab`]();
      }
      // Apply translations to newly loaded tab content
      window.applyTranslations?.();
    };
    script.onerror = () => console.error(`✗ Ошибка загрузки JS вкладки ${tabName}`);
    container.appendChild(script);
    
    console.log(`✓ Загружена вкладка: ${tabName}`);
  } catch (e) {
    console.error(`✗ Ошибка загрузки вкладки ${tabName}:`, e);
    document.getElementById(`tab-${tabName}`).innerHTML = 
      `<div class="alert alert-danger">Ошибка загрузки вкладки: ${e.message}</div>`;
  }
}

// Обработка переключения вкладок
document.getElementById('mainTabs')?.addEventListener('shown.bs.tab', (e) => {
  const target = e.target.dataset.bsTarget.replace('#tab-', '');
  console.log(`Переключение на вкладку: ${target}`);
});

// Модуль для работы с API
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
  }
};

// ── HELP SYSTEM ───────────────────────────────────────────────────────────────
// HELP content stored in JavaScript (will be populated from help tab)

window.HELP_CONTENT = {};

// Initialize HELP content when help tab is loaded
async function initHelpContent() {
  // Overview
  window.HELP_CONTENT['overview'] = `
    <h4>📋 Обзор проекта</h4>
    <p>mediteka — это интегрированная среда разработки для работы с AI-моделями Gemini, управлением медиатекой и торрентами.</p>
    <h5>Основные возможности</h5>
    <ul>
      <li><strong>Чат</strong> — взаимодействие с AI через API Gemini</li>
      <li><strong>Торренты</strong> — управление торрентами через qBittorrent API</li>
      <li><strong>Медиатека</strong> — сканирование и классификация медиа через TMDB + Gemini</li>
      <li><strong>Управление</strong> — полный набор инструментов для администрирования</li>
    </ul>
    <h5>Структура проекта</h5>
    <pre>gemini-simplechat/
├── html/                 # Веб-интерфейс
├── plugins/              # Плагины
├── src/                  # Исходный код
└── doc/                  # Документация</pre>
  `;

  // Code Rules
  window.HELP_CONTENT['code_rules'] = `
    <h4>⚙️ Правила кодирования (CODE_RULES)</h4>
    <p>Проект использует Engineering Standard для поддержания качества кода.</p>
    <h5>Ключевые принципы</h5>
    <ul>
      <li><strong>Читаемость важнее краткости</strong></li>
      <li><strong>Принцип единственной ответственности</strong></li>
      <li><strong>Явное лучше неявного</strong></li>
      <li><strong>Ранний возврат и отказоустойчивость</strong></li>
    </ul>
    <h5>Запрещено использовать None</h5>
    <p>Вместо <code>None</code> использовать:</p>
    <ul>
      <li>Числа: <code>0</code> или <code>0.0</code></li>
      <li>Строки: <code>''</code> (пустая строка)</li>
      <li>Булевы: <code>false</code></li>
      <li>Коллекции: <code>[]</code> или <code>{}</code></li>
    </ul>
  `;

  // Architecture
  window.HELP_CONTENT['architecture'] = `
    <h4>🏗️ Архитектура</h4>
    <h5>Технологический стек</h5>
    <ul>
      <li><strong>FastAPI</strong> — веб-фреймворк для Python</li>
      <li><strong>UVicorn</strong> — ASGI сервер</li>
      <li><strong>Bootstrap 5</strong> — UI фреймворк</li>
      <li><strong>SQLite</strong> — база данных</li>
    </ul>
    <h5>AI интеграции</h5>
    <ul>
      <li><strong>Google Gemini</strong> — генерация контента</li>
      <li><strong>TMDB API</strong> — база данных фильмов и сериалов</li>
      <li><strong>RAG</strong> — семантический поиск</li>
    </ul>
  `;

  // FastAPI
  window.HELP_CONTENT['fastapi'] = `
    <h4>🚀 FastAPI</h4>
    <h5>Роутеры</h5>
    <table class="table table-sm">
      <tr><td><code>/api/chat</code></td><td>Взаимодействие с Gemini AI</td></tr>
      <tr><td><code>/api/media-admin</code></td><td>Управление медиатекой</td></tr>
      <tr><td><code>/api/torrents</code></td><td>Управление торрентами</td></tr>
    </table>
    <h5>Конфигурация</h5>
    <p>Файл: <code>src/fastapi/config.json</code></p>
  `;

  // Media
  window.HELP_CONTENT['media'] = `
    <h4>🎬 Медиатека</h4>
    <h5>Компоненты</h5>
    <ul>
      <li><strong>MediaScanner</strong> — сканирование файловой системы</li>
      <li><strong>TMDBClient</strong> — запросы к TMDB API</li>
      <li><strong>MediaAuditor</strong> — проверка целостности</li>
      <li><strong>GenreClassifier</strong> — классификация медиа</li>
    </ul>
    <h5>База данных</h5>
    <p>Файл: <code>plugins/media_organizer/media.db</code></p>
  `;

  // qBittorrent
  window.HELP_CONTENT['qbittorrent'] = `
    <h4>🧲 qBittorrent</h4>
    <h5>Возможности</h5>
    <ul>
      <li>Просмотр всех торрентов</li>
      <li>Управление путями файлов</li>
      <li>Автопоиск утерянных файлов</li>
      <li>Перемещение и recheck</li>
    </ul>
    <h5>Конфигурация</h5>
    <p>Файл: <code>src/fastapi/config.json</code></p>
  `;

  // Gemini
  window.HELP_CONTENT['gemini'] = `
    <h4>🧠 Gemini AI</h4>
    <h5>Использование</h5>
    <ul>
      <li>Генерация метаданных для медиа</li>
      <li>Классификация по жанрам</li>
      <li>Генерация описаний и рецензий</li>
      <li>Поиск по RAG-индексу</li>
    </ul>
    <h5>Управление ключами</h5>
    <p>Файл: <code>src/secrets/gemini_keys.json</code></p>
  `;

  // Configuration
  window.HELP_CONTENT['configuration'] = `
    <h4>⚙️ Конфигурация</h4>
    <h5>Файлы конфигурации</h5>
    <table class="table table-sm">
      <tr><td><code>.env</code></td><td>Секреты (API ключи, пароли)</td></tr>
      <tr><td><code>src/fastapi/config.json</code></td><td>Публичные настройки</td></tr>
      <tr><td><code>plugins/media_organizer/media_paths.txt</code></td><td>Пути к медиатеке</td></tr>
    </table>
  `;

  // CLI Commands
  window.HELP_CONTENT['cli_commands'] = `
    <h4>⌨️ Командная строка</h4>
    <p>Все команды медиатеки доступны в CLI и веб-интерфейсе.</p>
    
    <h5>run_media_organizer.py</h5>
    <p>Полный функционал управления медиатекой:</p>
    <table class="table table-sm">
      <tr><td><code>--disk 1</code></td><td>Имя диска (например: 1, 2, 3)</td></tr>
      <tr><td><code>--path E: L:</code></td><td>Пути для сканирования</td></tr>
      <tr><td><code>--key имя_ключа</code></td><td>Ключ Gemini API</td></tr>
      <tr><td><code>--title</code></td><td>Генерация отчёта из БД</td></tr>
      <tr><td><code>--audit</code></td><td>Только аудит (без сканирования)</td></tr>
      <tr><td><code>--rebuild</code></td><td>Восстановление из JSON</td></tr>
      <tr><td><code>--rebuild-db</code></td><td>Консолидация дублей в БД</td></tr>
      <tr><td><code>--rebuild-rag</code></td><td>Перестройка RAG-индекса</td></tr>
    </table>
    
    <h5>series_collector.py</h5>
    <p>Сбор и анализ эпизодов:</p>
    <table class="table table-sm">
      <tr><td><code>--scan</code></td><td>Сканирование сериалов</td></tr>
      <tr><td><code>--duplicates</code></td><td>Проверка дубликатов</td></tr>
      <tr><td><code>--integrity</code></td><td>Проверка целостности</td></tr>
      <tr><td><code>--report</code></td><td>Генерация отчёта</td></tr>
      <tr><td><code>--all</code></td><td>Все проверки сразу</td></tr>
    </table>
    
    <h5>Примеры:</h5>
    <pre><code>
# Полное сканирование диска 1
py run_media_organizer.py --disk 1 --path E: L:

# Только аудит без сканирования
py run_media_organizer.py --disk 2 --audit

# Генерация отчёта из БД
py run_media_organizer.py --disk 1 --title

# Консолидация дублей
py run_media_organizer.py --rebuild-db

# Сканирование сериалов
py series_collector.py --scan

# Все проверки сразу
py series_collector.py --all
    </code></pre>
  `;

  console.log('HELP content initialized');
}

// Show help modal
function showHelpModal(key) {
  const content = window.HELP_CONTENT[key] || '<p>Информация не найдена</p>';
  document.getElementById('help-modal-content').innerHTML = content;
  
  const modal = new bootstrap.Modal(document.getElementById('help-modal'));
  modal.show();
}

// Show help tooltip/popover for element
function showHelpTooltip(element, content) {
  const options = {
    title: 'Помощь',
    content: content,
    html: true,
    placement: 'top',
    trigger: 'hover focus'
  };
  
  const popover = new bootstrap.Popover(element, options);
  popover.show();
}
