// ── MOVIE-SEARCH.JS ──────────────────────────────────────────────────────────

let searchResults = [];

window['initMovie-searchTab'] = function() {
  console.log('initMovie-searchTab initialized');
  
  const btnSearch = document.getElementById('btn-movie-search');
  const queryInput = document.getElementById('movie-search-query');
  const trackerFilter = document.getElementById('movie-search-tracker-filter');
  const sortSelect = document.getElementById('movie-search-sort');
  const btnRefreshDownloads = document.getElementById('btn-refresh-downloads');

  if (btnSearch) {
    btnSearch.addEventListener('click', performMovieSearch);
  }
  if (queryInput) {
    queryInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') performMovieSearch();
    });
  }

  // Filter/Sort change triggers re-render
  if (trackerFilter) trackerFilter.addEventListener('change', renderSearchResults);
  if (sortSelect) sortSelect.addEventListener('change', renderSearchResults);

  if (btnRefreshDownloads) {
    btnRefreshDownloads.addEventListener('click', updateActiveDownloads);
  }

  // Initial downloads update and start polling
  updateActiveDownloads();
  setInterval(updateActiveDownloads, 5000);
};

// Perform Rutracker/NNMClub Search
async function performMovieSearch() {
  const queryInput = document.getElementById('movie-search-query');
  const statusDiv = document.getElementById('movie-search-status');
  const statusText = document.getElementById('movie-search-status-text');
  const resultsDiv = document.getElementById('movie-search-results');
  
  const query = queryInput.value.trim();
  if (!query) return;

  searchResults = [];
  statusDiv.classList.remove('d-none');
  resultsDiv.innerHTML = '';

  try {
    const url = `/api/torrents/search?query=${encodeURIComponent(query)}`;
    const data = await window.api.fetch(url);
    searchResults = data || [];
    renderSearchResults();
  } catch (err) {
    resultsDiv.innerHTML = `
      <div class="alert alert-danger m-3">
        <strong>Ошибка поиска:</strong> ${err.message}
      </div>
    `;
  } finally {
    statusDiv.classList.add('d-none');
  }
}

// Helper to extract video qualities (1080p, 4k, etc.) from torrent title
function parseQualities(title) {
  const t = title.toLowerCase();
  const badges = [];
  if (t.includes('2160') || t.includes('4k') || t.includes('uhd')) badges.push({ text: '4K UHD', class: 'bg-danger' });
  else if (t.includes('1080') || t.includes('fhd')) badges.push({ text: '1080p', class: 'bg-primary' });
  else if (t.includes('720') || t.includes('hd')) badges.push({ text: '720p', class: 'bg-info text-dark' });

  if (t.includes('bdrip') || t.includes('blu-ray') || t.includes('bluray')) badges.push({ text: 'BDRip', class: 'bg-success' });
  else if (t.includes('web-dl') || t.includes('webdl') || t.includes('webrip')) badges.push({ text: 'WEB-DL', class: 'bg-secondary' });

  if (t.includes('hevc') || t.includes('x265') || t.includes('h.265')) badges.push({ text: 'HEVC/x265', class: 'bg-dark' });
  
  return badges;
}

// Helper to format bytes to human readable sizes
function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Render search results with filter & sort options applied
function renderSearchResults() {
  const resultsDiv = document.getElementById('movie-search-results');
  const trackerFilter = document.getElementById('movie-search-tracker-filter').value;
  const sortVal = document.getElementById('movie-search-sort').value;

  if (searchResults.length === 0) {
    resultsDiv.innerHTML = `
      <div class="text-center text-muted p-5 border rounded bg-light" id="movie-search-empty">
        <i class="bi bi-search h1 d-block mb-3 text-secondary"></i>
        <span>Раздачи не найдены. Попробуйте изменить запрос.</span>
      </div>
    `;
    return;
  }

  // Filter
  let filtered = [...searchResults];
  if (trackerFilter !== 'all') {
    filtered = filtered.filter(item => item.source === trackerFilter);
  }

  // Sort
  if (sortVal === 'seeds') {
    filtered.sort((a, b) => (b.seeds || 0) - (a.seeds || 0));
  } else if (sortVal === 'size-desc') {
    filtered.sort((a, b) => (b.size_bytes || 0) - (a.size_bytes || 0));
  } else if (sortVal === 'size-asc') {
    filtered.sort((a, b) => (a.size_bytes || 0) - (b.size_bytes || 0));
  }

  if (filtered.length === 0) {
    resultsDiv.innerHTML = `
      <div class="text-center text-muted p-5 border rounded bg-light">
        <span>Нет результатов, соответствующих выбранным фильтрам.</span>
      </div>
    `;
    return;
  }

  resultsDiv.innerHTML = filtered.map(t => {
    const badges = parseQualities(t.title);
    const badgeHtml = badges.map(b => `<span class="badge ${b.class} me-1">${b.text}</span>`).join('');
    const seedClass = t.seeds > 50 ? 'text-success fw-bold' : (t.seeds > 10 ? 'text-warning' : 'text-muted');
    const sourceBadge = t.source === 'rutracker' ? 'bg-success' : 'bg-primary';

    return `
      <div class="list-group-item list-group-item-action p-3 mb-2 border rounded shadow-sm">
        <div class="d-flex w-100 justify-content-between align-items-start mb-2">
          <h6 class="mb-1 fw-bold text-wrap pe-3">
            <a href="${t.view_url}" target="_blank" class="text-decoration-none text-dark hover-primary">${t.title}</a>
          </h6>
          <span class="badge ${sourceBadge} text-uppercase">${t.source}</span>
        </div>
        <div class="mb-2">
          ${badgeHtml}
        </div>
        <div class="d-flex justify-content-between align-items-center mt-3">
          <div class="small text-muted">
            <span class="me-3">💾 <strong>${t.size_human}</strong></span>
            <span class="me-3">▲ <span class="${seedClass}">${t.seeds || 0}</span></span>
            <span>▼ ${t.peers || 0}</span>
          </div>
          <button class="btn btn-sm btn-outline-success download-movie-btn d-flex align-items-center gap-1"
                  data-url="${t.download_url}" data-source="${t.source}" data-title="${encodeURIComponent(t.title)}">
            <i class="bi bi-download"></i> 📥 Скачать
          </button>
        </div>
      </div>
    `;
  }).join('');

  // Wire up download events
  resultsDiv.querySelectorAll('.download-movie-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const targetBtn = e.currentTarget;
      const url = targetBtn.getAttribute('data-url');
      const source = targetBtn.getAttribute('data-source');
      const title = decodeURIComponent(targetBtn.getAttribute('data-title'));

      targetBtn.disabled = true;
      targetBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Добавление...';

      try {
        const response = await fetch('/api/torrents/download', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, source, title })
        });
        
        if (response.ok) {
          targetBtn.className = 'btn btn-sm btn-success d-flex align-items-center gap-1';
          targetBtn.innerHTML = '<i class="bi bi-check-circle"></i> Добавлено';
          // Immediately refresh downloads panel
          setTimeout(updateActiveDownloads, 1000);
        } else {
          const errData = await response.json();
          alert('Ошибка при добавлении: ' + (errData.detail || response.statusText));
          targetBtn.disabled = false;
          targetBtn.className = 'btn btn-sm btn-outline-success d-flex align-items-center gap-1';
          targetBtn.innerHTML = '<i class="bi bi-download"></i> 📥 Скачать';
        }
      } catch (err) {
        alert('Ошибка: ' + err.message);
        targetBtn.disabled = false;
        targetBtn.className = 'btn btn-sm btn-outline-success d-flex align-items-center gap-1';
        targetBtn.innerHTML = '<i class="bi bi-download"></i> 📥 Скачать';
      }
    });
  });
}

// Fetch active downloads from qBittorrent and update UI
async function updateActiveDownloads() {
  const listDiv = document.getElementById('active-downloads-list');
  const emptyDiv = document.getElementById('active-downloads-empty');
  
  if (!listDiv) return;

  try {
    const data = await window.api.fetch('/api/torrents');
    
    // Filter for active downloading state (non-complete and non-paused/stopped)
    const activeStates = ['downloading', 'stalledDL', 'checkingDL', 'forcedDL', 'downloadingMetadata', 'checkingResumeData'];
    const active = data.filter(t => activeStates.includes(t.state) || (t.state === 'pausedDL' && t.progress < 100));

    if (active.length === 0) {
      listDiv.innerHTML = '';
      emptyDiv.classList.remove('d-none');
      return;
    }

    emptyDiv.classList.add('d-none');
    listDiv.innerHTML = active.map(t => {
      // Choose state color class
      let stateColor = 'bg-primary';
      if (t.state === 'stalledDL') stateColor = 'bg-warning text-dark';
      if (t.state.includes('checking')) stateColor = 'bg-info text-dark';
      
      return `
        <div class="list-group-item p-2">
          <div class="d-flex justify-content-between align-items-start mb-1">
            <span class="small fw-bold text-truncate pe-2" style="max-width: 80%;">${t.name}</span>
            <span class="badge ${stateColor} style="font-size: 0.7rem;">${t.state}</span>
          </div>
          <div class="progress mb-1" style="height: 6px;">
            <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" 
                 style="width: ${t.progress}%" aria-valuenow="${t.progress}" aria-valuemin="0" aria-valuemax="100"></div>
          </div>
          <div class="d-flex justify-content-between align-items-center" style="font-size: 0.75rem; color: #6c757d;">
            <span>${t.progress}% (${formatBytes(t.size)})</span>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Failed to update active downloads:', err);
  }
}
