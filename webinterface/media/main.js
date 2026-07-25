// ── MEDIA.JS ──────────────────────────────────────────────────────────────────

// HELP content for media tab options
const MEDIA_HELP = {
  media_paths: {
    title: '📁 Пути сканирования',
    content: `
      <p>Список директорий для сканирования медиатеки.</p>
      <h5>Как настроить:</h5>
      <ol>
        <li>Открыть <code>plugins/media_organizer/media_paths.txt</code></li>
        <li>Добавить путь на каждой строке</li>
        <li>Сохранить файл</li>
      </ol>
      <h5>Поддерживаемые форматы:</h5>
      <ul>
        <li><code>D:\Series</code> — абсолютные пути Windows</li>
        <li><code>/mnt/series</code> — абсолютные пути Linux/Mac</li>
      </ul>
    `
  },
  media_summary: {
    title: '📺 Сводка по сериалам',
    content: `
      <p>Таблица всех сериалов из базы данных media.db.</p>
      <h5>Колонки:</h5>
      <ul>
        <li><strong>Сериал</strong> — название сериала</li>
        <li><strong>Сезонов</strong> — количество сезонов</li>
        <li><strong>Эпизодов</strong> — количество эпизодов</li>
        <li><strong>Размер</strong> — общий размер в GB</li>
      </ul>
    `
  },
  media_duplicates: {
    title: '⚠️ Дубликаты сезонов',
    content: `
      <p>Проверка на дубликаты по сезонам в разных сериалах.</p>
      <h5>Что проверяет:</h5>
      <ul>
        <li>Одинаковые названия сезонов в разных сериалах</li>
        <li>Одинаковые номера сезонов в разных сериалах</li>
      </ul>
      <h5>Рекомендации:</h5>
      <ul>
        <li>Проверить правильность названий</li>
        <li>Переименовать дубликаты</li>
      </ul>
    `
  },
  media_integrity: {
    title: '🔎 Целостность',
    content: `
      <p>Проверка целостности данных в базе и на диске.</p>
      <h5>Что проверяет:</h5>
      <ul>
        <li>Наличие файлов на диске</li>
        <li>Совпадение количества серий</li>
        <li>Состояние торрентов (если qBittorrent настроен)</li>
      </ul>
    `
  },
  media_report: {
    title: '📄 Последний отчёт',
    content: `
      <p>Отчёт о последнем сканировании медиатеки.</p>
      <h5>Формат:</h5>
      <ul>
        <li>Markdown файл с описанием всех медиа</li>
        <li>Разделение на сериалы и фильмы</li>
        <li>Сортировка по категориям</li>
      </ul>
      <h5>Расположение:</h5>
      <p><code>plugins/media_organizer/media_reports/</code></p>
    `
  }
};

// Initialize HELP content
document.addEventListener('DOMContentLoaded', () => {
  // Copy to window.HELP_CONTENT for modal
  window.HELP_CONTENT = window.HELP_CONTENT || {};
  Object.assign(window.HELP_CONTENT, MEDIA_HELP);
  
  console.log('Media HELP initialized');
});

// Fetch helper
async function mediaFetch(url, opts = {}) {
  const r = await fetch(url, opts);
  if (!r.ok) {
    let msg = r.statusText;
    try { const d = await r.json(); msg = d.detail || msg; } catch {}
    throw new Error(`${r.status} ${msg}`);
  }
  return r.json();
}

let mediaPaths = [];

async function loadMediaPaths() {
  mediaPaths = await mediaFetch('/api/media/paths');
  renderMediaPaths();
}

function renderMediaPaths() {
  const el = document.getElementById('media-paths-list');
  if (!mediaPaths.length) {
    el.innerHTML = '<div class="text-muted small" id="media-paths-empty">Нет путей</div>';
    return;
  }
  el.innerHTML = mediaPaths.map((p, i) => `
    <div class="d-flex align-items-center gap-1 py-1 border-bottom">
      <input class="form-check-input mt-0 media-path-check" type="checkbox" value="${p}" checked id="mp-${i}">
      <label class="form-check-label font-monospace small flex-grow-1 mb-0" for="mp-${i}" style="cursor:pointer">${p}</label>
      <button class="btn btn-outline-danger btn-sm p-0 lh-1" onclick="deleteMediaPath('${p.replace(/'/g,"\\'")}')">−</button>
    </div>
  `).join('');
}

async function addMediaPath() {
  const input = document.getElementById('media-path-input');
  const val = input.value.trim();
  if (!val) return;
  try {
    mediaPaths = await mediaFetch('/api/media/paths', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({path: val})
    });
    input.value = '';
    renderMediaPaths();
  } catch(e) {
    console.error('addMediaPath:', e);
  }
}

async function deleteMediaPath(path) {
  mediaPaths = await mediaFetch('/api/media/paths?' + new URLSearchParams({path}), {method: 'DELETE'});
  renderMediaPaths();
}

document.getElementById('btn-media-add-path')?.addEventListener('click', addMediaPath);
document.getElementById('media-path-input')?.addEventListener('keypress', e => { if (e.key==='Enter') addMediaPath(); });

// Сканирование
document.getElementById('btn-series-scan')?.addEventListener('click', async () => {
  const btn = document.getElementById('btn-series-scan');
  btn.disabled = true; btn.textContent = '⏳ Сканирую...';
  try {
    await mediaFetch('/api/media-admin/series/scan', {method: 'POST'});
    // Запросить статус...
  } catch(e) { console.error(e); }
  finally { btn.disabled = false; btn.textContent = '🔍 Сканировать сериалы'; }
});

// Сводка
async function loadMediaSummary() {
  const rows = await mediaFetch('/api/media/series/summary');
  const tbody = document.getElementById('media-summary-body');
  const empty = document.getElementById('media-summary-empty');
  document.getElementById('media-series-count').textContent = rows.length;
  if (!rows.length) { tbody.innerHTML = ''; empty.classList.remove('d-none'); return; }
  empty.classList.add('d-none');
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td class="ps-2">${r.series_title}</td>
      <td class="text-center">${r.total_seasons || '—'}</td>
      <td class="text-center">${r.total_episodes}</td>
      <td class="text-center">${((r.total_size_mb || 0) / 1024).toFixed(1)} GB</td>
    </tr>
  `).join('');
}

document.getElementById('btn-media-load-summary')?.addEventListener('click', loadMediaSummary);

// Дубликаты
document.getElementById('btn-check-dups')?.addEventListener('click', async () => {
  const el = document.getElementById('dup-body');
  el.innerHTML = '<span class="text-muted">⏳ Проверяю...</span>';
  try {
    const dups = await mediaFetch('/api/media/series/duplicates');
    if (!dups.length) { el.innerHTML = '<span class="integrity-ok">✅ Дублей нет</span>'; return; }
    el.innerHTML = dups.map(d => `
      <div class="mb-1"><strong>${d.series_title}</strong> — Сезон ${d.season}</div>
    `).join('');
  } catch(e) { el.innerHTML = `<span class="integrity-warn">❌ ${e.message}</span>`; }
});

// Целостность
document.getElementById('btn-check-integrity')?.addEventListener('click', async () => {
  const el = document.getElementById('integrity-body');
  el.innerHTML = '<span class="text-muted">⏳ Проверяю...</span>';
  try {
    const issues = await mediaFetch('/api/media/series/integrity');
    if (!issues.length) { el.innerHTML = '<span class="integrity-ok">✅ Всё в порядке</span>'; return; }
    el.innerHTML = issues.map(iss => `
      <div class="integrity-warn">⚠️ ${iss.series}</div>
    `).join('');
  } catch(e) { el.innerHTML = `<span class="integrity-warn">❌ ${e.message}</span>`; }
});

// Отчёт
document.getElementById('btn-load-series-report')?.addEventListener('click', async () => {
  const log = document.getElementById('media-log');
  try {
    const data = await mediaFetch('/api/media/series/report/content');
    log.textContent = data.content || '(пусто)';
  } catch(e) { log.textContent = e.message; }
});

// Загрузка при открытии вкладки
document.querySelector('[data-bs-target="#tab-media"]')?.addEventListener('shown.bs.tab', () => {
  loadMediaPaths();
  loadMediaSummary();
});
// ── RAG FUNCTIONS ───────────────────────────────────────────────────────────

// Загрузка статуса RAG
async function loadRagStatus() {
  try {
    const data = await mediaFetch('/api/media-admin/rag/status');
    const db = data.database || {};
    const rag = data.rag_index || {};

    document.getElementById('rag-docs-count').textContent = rag.documents || 0;
    document.getElementById('rag-db-records').textContent = db.total_records || 0;
    document.getElementById('rag-index-docs').textContent = rag.documents || 0;
    document.getElementById('rag-movies-count').textContent = db.by_type?.movie || 0;
    document.getElementById('rag-series-count').textContent = db.by_type?.series || 0;

    return data;
  } catch(e) {
    console.error('loadRagStatus:', e);
    return null;
  }
}

// Загрузка списка API ключей
async function loadApiKeys() {
  try {
    const data = await mediaFetch('/api/keys');
    const select = document.getElementById('rag-key-select');
    select.innerHTML = '<option value="">API Key</option>';
    data.keys?.forEach(k => {
      const opt = document.createElement('option');
      opt.value = k.name;
      opt.textContent = k.name;
      select.appendChild(opt);
    });
  } catch(e) {
    console.error('loadApiKeys:', e);
  }
}

// Построение RAG индекса
document.getElementById('btn-rag-build')?.addEventListener('click', async () => {
  const btn = document.getElementById('btn-rag-build');
  const keySelect = document.getElementById('rag-key-select');
  const key = keySelect?.value || '';

  btn.disabled = true;
  btn.textContent = '⏳ Строю индекс...';

  try {
    const data = await mediaFetch('/api/media-admin/rag/build', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({key})
    });
    alert(`✅ Готово! Документов в индексе: ${data.count}`);
    loadRagStatus();
  } catch(e) {
    alert(`❌ Ошибка: ${e.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = '🔨 Построить индекс';
  }
});

// Поиск по RAG
document.getElementById('btn-rag-search')?.addEventListener('click', async () => {
  const input = document.getElementById('rag-search-input');
  const query = input.value.trim();
  const category = document.getElementById('rag-search-category').value;
  const mediaType = document.getElementById('rag-search-type').value;
  const keySelect = document.getElementById('rag-key-select');
  const key = keySelect?.value || '';

  if (!query) return;

  const btn = document.getElementById('btn-rag-search');
  const resultsDiv = document.getElementById('rag-search-results');

  btn.disabled = true;
  btn.textContent = '⏳ Ищу...';
  resultsDiv.innerHTML = '<div class="text-muted">Поиск...</div>';

  try {
    const data = await mediaFetch('/api/media-admin/rag/search?' + new URLSearchParams({
      query,
      top_k: 10,
      key
    }), {method: 'POST'});

    const results = data.results || [];

    if (!results.length) {
      resultsDiv.innerHTML = '<div class="text-muted p-3">Ничего не найдено</div>';
      return;
    }

    // Фильтрация по категории и типу
    let filtered = results;
    if (category) {
      filtered = filtered.filter(r => r.category === category);
    }
    if (mediaType) {
      filtered = filtered.filter(r => r.type === mediaType);
    }

    if (!filtered.length) {
      resultsDiv.innerHTML = '<div class="text-muted p-3">По заданным фильтрам ничего не найдено</div>';
      return;
    }

    resultsDiv.innerHTML = filtered.map(r => `
      <div class="border-bottom py-2">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <strong>${r.title}</strong>
            <span class="badge bg-${r.type === 'series' ? 'info' : 'primary'} ms-2">${r.type === 'series' ? 'Сериал' : 'Фильм'}</span>
            <span class="badge bg-secondary ms-1">${r.category || '—'}</span>
            <span class="text-muted small ms-2">${r.year || '—'} | ${r.disk_name || '—'}</span>
          </div>
          <span class="badge bg-success">${(r.score * 100).toFixed(1)}%</span>
        </div>
      </div>
    `).join('');

  } catch(e) {
    resultsDiv.innerHTML = `<div class="text-danger">❌ Ошибка: ${e.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = '🔍 Поиск';
  }
});

// Поиск по Enter
document.getElementById('rag-search-input')?.addEventListener('keypress', e => {
  if (e.key === 'Enter') document.getElementById('btn-rag-search').click();
});

// Инициализация RAG при загрузке вкладки
document.querySelector('[data-bs-target="#tab-media"]')?.addEventListener('shown.bs.tab', () => {
  loadApiKeys();
  loadRagStatus();
});