// ── TORRENTS.JS ───────────────────────────────────────────────────────────────

let allTorrents = [], selectedHash = null, showMissing = true;
let sortCol = 'name', sortAsc = true;

const STATE_LABELS = {
  missingFiles: '⛔ Файлы утеряны', downloading: '⬇ Загрузка',
  uploading: '⬆ Раздача', seeding: '🌱 Сидирование',
  pausedDL: '⏸ Пауза (DL)', pausedUP: '⏸ Пауза (UP)',
  checkingUP: '🔍 Проверка', checkingDL: '🔍 Проверка', error: '❌ Ошибка',
};

function fmtSize(b) {
  if (b >= 1e12) return (b/1e12).toFixed(2)+' ТБ';
  if (b >= 1e9)  return (b/1e9).toFixed(2)+' ГБ';
  if (b >= 1e6)  return (b/1e6).toFixed(1)+' МБ';
  return b+' Б';
}

function selectTorrent(hash) {
  selectedHash = hash;
  const t = allTorrents.find(x => x.hash === hash);
  if (!t) return;
  document.getElementById('manual-name').value = t.name;
  document.getElementById('manual-path').value = t.save_path || '';
  document.getElementById('manual-result').className = 'alert mt-2 d-none';
  // highlight
  document.querySelectorAll('.missing-row').forEach(r => r.classList.toggle('selected', r.dataset.hash === hash));
}

function renderMissing() {
  const missing = allTorrents.filter(t => t.state === 'missingFiles');
  document.getElementById('missing-count').textContent = missing.length;
  const tbody = document.getElementById('missing-body');
  const empty = document.getElementById('missing-empty');
  if (!missing.length) {
    tbody.innerHTML = ''; empty.classList.remove('d-none'); return;
  }
  empty.classList.add('d-none');
  tbody.innerHTML = missing.map(t => `
    <tr class="missing-row ${t.hash===selectedHash?'selected':''}" data-hash="${t.hash}" onclick="selectTorrent('${t.hash}')">
      <td class="ps-2 py-1">
        <div class="fw-semibold" style="font-size:.85rem">${t.name}</div>
        <div class="text-muted" style="font-size:.75rem">${fmtSize(t.size)}</div>
      </td>
    </tr>`).join('');
}

function renderAll() {
  let data = showMissing ? allTorrents.filter(t => t.state === 'missingFiles') : allTorrents;
  document.getElementById('all-count').textContent = allTorrents.length;
  data = [...data].sort((a,b) => {
    let va = a[sortCol], vb = b[sortCol];
    if (typeof va === 'string') { va = va.toLowerCase(); vb = vb.toLowerCase(); }
    return sortAsc ? (va>vb?1:-1) : (va<vb?1:-1);
  });
  document.getElementById('torrents-body').innerHTML = data.map(t => `
    <tr class="missing-row ${t.hash===selectedHash?'selected':''}" data-hash="${t.hash}" onclick="selectTorrent('${t.hash}')">
      <td>${t.name}</td>
      <td><span class="state-${t.state}">${STATE_LABELS[t.state]||t.state}</span></td>
      <td>
        <div class="progress"><div class="progress-bar" style="width:${t.progress}%"></div></div>
        <small>${t.progress}%</small>
      </td>
      <td>${fmtSize(t.size)}</td>
    </tr>`).join('');
}

async function loadTorrents() {
  try {
    const r = await fetch('/api/torrents');
    if (!r.ok) {
      const d = await r.json();
      document.getElementById('missing-empty').textContent = d.detail || 'Ошибка загрузки';
      document.getElementById('missing-empty').classList.remove('d-none');
      return;
    }
    allTorrents = await r.json();
    renderMissing();
    renderAll();
  } catch(e) {
    document.getElementById('missing-empty').textContent = 'Нет соединения с сервером';
    document.getElementById('missing-empty').classList.remove('d-none');
    console.error('loadTorrents:', e);
  }
}

// Сортировка
document.querySelectorAll('#torrents-table th[data-col]').forEach(th =>
  th.addEventListener('click', () => {
    const col = th.dataset.col;
    sortAsc = sortCol === col ? !sortAsc : true;
    sortCol = col;
    renderAll();
  })
);

// Фильтр
document.getElementById('btn-show-missing').addEventListener('click', () => {
  showMissing = true; renderAll();
  document.getElementById('btn-show-missing').classList.add('active');
  document.getElementById('btn-show-all').classList.remove('active');
});
document.getElementById('btn-show-all').addEventListener('click', () => {
  showMissing = false; renderAll();
  document.getElementById('btn-show-all').classList.add('active');
  document.getElementById('btn-show-missing').classList.remove('active');
});

document.getElementById('btn-refresh').addEventListener('click', loadTorrents);

// ── DIRS MANAGEMENT ───────────────────────────────────────────────────────────
let savedDirs = [];

async function loadDirs() {
  try {
    const r = await fetch('/api/torrents/dirs');
    savedDirs = await r.json();
    renderDirs();
  } catch(e) { console.error('loadDirs:', e); }
}

function renderDirs() {
  const container = document.getElementById('dirs-list');
  const empty     = document.getElementById('dirs-empty');
  if (!savedDirs.length) {
    container.innerHTML = '';
    container.appendChild(empty);
    empty.classList.remove('d-none');
    return;
  }
  empty.classList.add('d-none');
  // Сохраняем текущее состояние чекбоксов перед перерисовкой
  const prevChecked = {};
  document.querySelectorAll('.dir-check').forEach(c => { prevChecked[c.value] = c.checked; });
  container.innerHTML = savedDirs.map((d, i) => {
    const checked = d in prevChecked ? prevChecked[d] : true;
    return `
    <div class="d-flex align-items-center gap-2 py-1 border-bottom">
      <input class="form-check-input mt-0 dir-check" type="checkbox" value="${d}" ${checked ? 'checked' : ''} id="dir-${i}">
      <label class="form-check-label font-monospace flex-grow-1 small mb-0" for="dir-${i}"
             style="word-break:break-all;cursor:pointer">${d}</label>
      <button class="btn btn-outline-danger btn-sm p-0 lh-1" style="width:22px;height:22px;font-size:.9rem;line-height:1" onclick="deleteDir(this)"
              data-path="${d.replace(/"/g,'&quot;')}">−</button>
    </div>`;
  }).join('');
}

async function addDir() {
  const input = document.getElementById('new-dir-input');
  const val   = input.value.trim();
  if (!val || savedDirs.includes(val)) { input.value = ''; return; }
  const newDirs = [...savedDirs, val];
  await fetch('/api/torrents/dirs', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({dirs: newDirs})
  });
  savedDirs = newDirs;
  renderDirs();
  input.value = '';
}

async function deleteDir(btn) {
  const path = btn.dataset.path;
  await fetch('/api/torrents/dirs?' + new URLSearchParams({path}), {method: 'DELETE'});
  savedDirs = savedDirs.filter(d => d !== path);
  renderDirs();
}

function getCheckedDirs() {
  return [...document.querySelectorAll('.dir-check:checked')].map(c => c.value);
}

document.getElementById('btn-add-dir').addEventListener('click', addDir);
document.getElementById('new-dir-input').addEventListener('keypress', e => { if (e.key === 'Enter') addDir(); });
document.getElementById('btn-select-all').addEventListener('click', () => {
  const checks = [...document.querySelectorAll('.dir-check')];
  const allChecked = checks.every(c => c.checked);
  checks.forEach(c => c.checked = !allChecked);
});

// ── Автопоиск ─────────────────────────────────────────────────────────────────
async function doRelocate(dirs) {
  const banner = document.getElementById('relocate-result');
  banner.className = 'alert alert-info mt-2';
  banner.textContent = '⏳ Индексирую файлы, это может занять время…';
  try {
    const r = await fetch('/api/torrents/relocate', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({dirs})
    });
    const d = await r.json();
    banner.className = `alert mt-2 ${r.ok ? 'alert-success' : 'alert-danger'}`;
    banner.textContent = r.ok ? d.result : d.detail;
  } catch { banner.className = 'alert alert-danger mt-2'; banner.textContent = 'Ошибка соединения.'; }
  await loadTorrents();
}

document.getElementById('btn-relocate').addEventListener('click', () => {
  const dirs = getCheckedDirs();
  if (!dirs.length) { alert('Отметьте папки для поиска'); return; }
  doRelocate(dirs);
});

document.getElementById('btn-relocate-selected').addEventListener('click', () => {
  if (!selectedHash) { alert('Выберите торрент из списка'); return; }
  const dirs = getCheckedDirs();
  if (!dirs.length) { alert('Отметьте папки для поиска'); return; }
  doRelocate(dirs);
});

// ── Ручное управление ─────────────────────────────────────────────────────────
async function showManualResult(ok, text) {
  const el = document.getElementById('manual-result');
  el.className = `alert mt-2 ${ok ? 'alert-success' : 'alert-danger'}`;
  el.textContent = text;
}

document.getElementById('btn-set-location').addEventListener('click', async () => {
  if (!selectedHash) { alert('Выберите торрент'); return; }
  const location = document.getElementById('manual-path').value.trim();
  if (!location) { alert('Введите путь'); return; }
  try {
    const r = await fetch('/api/torrents/set-location', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({hash: selectedHash, location})
    });
    const d = await r.json();
    showManualResult(r.ok, r.ok ? '✅ Путь установлен, recheck запущен' : d.detail);
    if (r.ok) await loadTorrents();
  } catch(e) { showManualResult(false, 'Ошибка соединения.'); }
});

document.getElementById('btn-recheck-manual').addEventListener('click', async () => {
  if (!selectedHash) { alert('Выберите торрент'); return; }
  try {
    const r = await fetch(`/api/torrents/recheck/${selectedHash}`, {method: 'POST'});
    showManualResult(r.ok, r.ok ? '🔁 Recheck запущен' : 'Ошибка');
    if (r.ok) setTimeout(loadTorrents, 2000);
  } catch(e) { showManualResult(false, 'Ошибка соединения.'); }
});

// Загрузка при открытии вкладки
document.querySelector('[data-bs-target="#tab-torrents"]')?.addEventListener('shown.bs.tab', () => {
  loadTorrents();
  loadDirs();
});
