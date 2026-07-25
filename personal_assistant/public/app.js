// State Management
let currentPage = 1;
const itemsPerPage = 12;
let categoriesList = [];
let currentMediaItem = null;
let isEditMode = false;
let isNewItem = false;

// DOM Elements
const statTotal = document.getElementById('stat-total');
const statMovies = document.getElementById('stat-movies');
const statSeries = document.getElementById('stat-series');
const statCategories = document.getElementById('stat-categories');

const searchInput = document.getElementById('search-input');
const filterType = document.getElementById('filter-type');
const filterCategory = document.getElementById('filter-category');
const filterYear = document.getElementById('filter-year');
const btnResetFilters = document.getElementById('btn-reset-filters');

const mediaGrid = document.getElementById('media-grid');
const btnPrev = document.getElementById('btn-prev');
const btnNext = document.getElementById('btn-next');
const pageIndicator = document.getElementById('page-indicator');

const btnAddMedia = document.getElementById('btn-add-media');

// Modal Elements
const mediaModal = document.getElementById('media-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const modalBadgeType = document.getElementById('modal-badge-type');
const modalViewMode = document.getElementById('modal-view-mode');
const modalEditForm = document.getElementById('modal-edit-form');
const editModalHeaderTitle = document.getElementById('edit-modal-header-title');

// View Mode Elements
const modalTitleRu = document.getElementById('modal-title-ru');
const modalTitleOrig = document.getElementById('modal-title-orig');
const modalMetaYear = document.getElementById('modal-meta-year');
const modalMetaCategory = document.getElementById('modal-meta-category');
const modalMetaGenres = document.getElementById('modal-meta-genres');
const modalMetaRating = document.getElementById('modal-meta-rating');
const modalPlot = document.getElementById('modal-plot');
const modalCountry = document.getElementById('modal-country');
const modalDirectors = document.getElementById('modal-directors');
const modalCast = document.getElementById('modal-cast');
const modalSize = document.getElementById('modal-size');
const modalVerdict = document.getElementById('modal-verdict');
const modalReview = document.getElementById('modal-review');
const modalAtmosphere = document.getElementById('modal-atmosphere');
const modalWhyWatch = document.getElementById('modal-why-watch');
const modalMood = document.getElementById('modal-mood');
const modalCatchphrases = document.getElementById('modal-catchphrases');
const modalFacts = document.getElementById('modal-facts');
const modalSimilar = document.getElementById('modal-similar');
const modalEpisodesSection = document.getElementById('modal-episodes-section');
const modalEpisodesBody = document.getElementById('modal-episodes-body');

// Edit Form Inputs
const editTitle = document.getElementById('edit-title');
const editTitleRu = document.getElementById('edit-title-ru');
const editTitleOrig = document.getElementById('edit-title-orig');
const editType = document.getElementById('edit-type');
const editYear = document.getElementById('edit-year');
const editCategory = document.getElementById('edit-category');
const editGenres = document.getElementById('edit-genres');
const editRating = document.getElementById('edit-rating');
const editSize = document.getElementById('edit-size');
const editPath = document.getElementById('edit-path');
const editPlot = document.getElementById('edit-plot');
const editReview = document.getElementById('edit-review');
const editFinalVerdict = document.getElementById('edit-final-verdict');
const editDirectors = document.getElementById('edit-directors');
const editCountry = document.getElementById('edit-country');
const editCast = document.getElementById('edit-cast');
const editAtmosphere = document.getElementById('edit-atmosphere');
const editWhyWatch = document.getElementById('edit-why-watch');
const editMood = document.getElementById('edit-mood');
const editCatchphrases = document.getElementById('edit-catchphrases');
const editFacts = document.getElementById('edit-facts');
const editSimilar = document.getElementById('edit-similar');

// Modal Action Buttons
const btnDeleteMedia = document.getElementById('btn-delete-media');
const btnEditToggle = document.getElementById('btn-edit-toggle');
const btnSaveMedia = document.getElementById('btn-save-media');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
  fetchStats();
  fetchCategories();
  fetchMedia();

  // Event Listeners
  searchInput.addEventListener('input', debounce(() => { currentPage = 1; fetchMedia(); }, 400));
  filterType.addEventListener('change', () => { currentPage = 1; fetchMedia(); });
  filterCategory.addEventListener('change', () => { currentPage = 1; fetchMedia(); });
  filterYear.addEventListener('input', debounce(() => { currentPage = 1; fetchMedia(); }, 400));
  btnResetFilters.addEventListener('click', resetFilters);

  btnPrev.addEventListener('click', () => { if (currentPage > 1) { currentPage--; fetchMedia(); } });
  btnNext.addEventListener('click', () => { currentPage++; fetchMedia(); });

  btnAddMedia.addEventListener('click', openAddMediaModal);
  btnCloseModal.addEventListener('click', closeModal);
  mediaModal.addEventListener('click', (e) => { if (e.target === mediaModal) closeModal(); });

  btnEditToggle.addEventListener('click', toggleEditMode);
  btnSaveMedia.addEventListener('click', saveMediaData);
  btnDeleteMedia.addEventListener('click', deleteMediaItem);
});

// Fetch Stats
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    statTotal.textContent = data.total || 0;
    
    const movieStat = data.types.find(t => t.media_type === 'movie');
    statMovies.textContent = movieStat ? movieStat.count : 0;

    const seriesStat = data.types.find(t => t.media_type === 'series');
    statSeries.textContent = seriesStat ? seriesStat.count : 0;

    statCategories.textContent = data.categories.length || 0;
  } catch (err) {
    console.error('Error fetching stats:', err);
  }
}

// Fetch Categories
async function fetchCategories() {
  try {
    const res = await fetch('/api/categories');
    categoriesList = await res.json();
    
    // Populate filter dropdown
    filterCategory.innerHTML = '<option value="">Все категории</option>';
    categoriesList.forEach(cat => {
      const option = document.createElement('option');
      option.value = cat;
      option.textContent = cat;
      filterCategory.appendChild(option);
    });
  } catch (err) {
    console.error('Error fetching categories:', err);
  }
}

// Fetch Media Items
async function fetchMedia() {
  showLoader();
  try {
    const search = searchInput.value;
    const type = filterType.value;
    const category = filterCategory.value;
    const year = filterYear.value;

    let url = `/api/media?page=${currentPage}&limit=${itemsPerPage}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (type) url += `&type=${type}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    if (year) url += `&year=${year}`;

    const res = await fetch(url);
    const data = await res.json();
    renderMediaGrid(data.items);
    updatePagination(data.pagination);
  } catch (err) {
    console.error('Error fetching media:', err);
    mediaGrid.innerHTML = `<div class="grid-loader"><i class="bi bi-exclamation-triangle" style="font-size: 2rem; color: var(--danger)"></i><p>Ошибка загрузки данных</p></div>`;
  }
}

// Reset Filters
function resetFilters() {
  searchInput.value = '';
  filterType.value = '';
  filterCategory.value = '';
  filterYear.value = '';
  currentPage = 1;
  fetchMedia();
}

// Show Loader
function showLoader() {
  mediaGrid.innerHTML = `
    <div class="grid-loader">
      <div class="spinner"></div>
      <p>Загрузка коллекции...</p>
    </div>
  `;
}

// Render Media Grid
function renderMediaGrid(items) {
  if (!items || items.length === 0) {
    mediaGrid.innerHTML = `
      <div class="grid-loader">
        <i class="bi bi-folder-x" style="font-size: 2.5rem; color: var(--text-muted)"></i>
        <p>Ничего не найдено</p>
      </div>
    `;
    return;
  }

  mediaGrid.innerHTML = '';
  items.forEach(item => {
    const card = document.createElement('div');
    card.className = `media-card ${item.media_type || 'movie'}`;
    card.addEventListener('click', () => openMediaDetail(item.id));

    const category = item.main_category || 'Без категории';
    const year = item.year ? `, ${item.year}` : '';
    const rating = item.rating ? `<i class="bi bi-star-fill text-warning"></i> ${item.rating}` : '<i class="bi bi-star text-muted"></i> -';
    const formattedSize = item.media_size ? `${item.media_size.toFixed(1)} ГБ` : '';
    const typeIconClass = item.media_type === 'series' ? 'bi-tv' : 'bi-film';

    card.innerHTML = `
      <div class="card-top">
        <span class="category-tag">${category}</span>
        <i class="bi ${typeIconClass} type-icon"></i>
      </div>
      <div class="card-middle">
        <h3 class="card-title" title="${item.title_ru || item.title}">${item.title_ru || item.title}</h3>
        <p class="card-subtitle">${item.title_orig || ''}${year}</p>
      </div>
      <div class="card-bottom">
        <span class="card-rating">${rating}</span>
        <span class="card-size">${formattedSize}</span>
      </div>
    `;
    mediaGrid.appendChild(card);
  });
}

// Update Pagination UI
function updatePagination(meta) {
  pageIndicator.textContent = `Страница ${meta.page} из ${meta.totalPages || 1}`;
  btnPrev.disabled = meta.page <= 1;
  btnNext.disabled = meta.page >= meta.totalPages;
}

// Open Media Detail Modal
async function openMediaDetail(id) {
  isNewItem = false;
  isEditMode = false;
  btnDeleteMedia.classList.remove('hidden');
  btnEditToggle.classList.remove('hidden');
  btnSaveMedia.classList.add('hidden');
  modalViewMode.classList.remove('hidden');
  modalEditForm.classList.add('hidden');
  btnEditToggle.innerHTML = '<i class="bi bi-pencil"></i> Редактировать';

  try {
    const res = await fetch(`/api/media/${id}`);
    if (!res.ok) throw new Error('Failed to fetch item details');
    currentMediaItem = await res.json();
    await populateModalView(currentMediaItem);
    mediaModal.classList.remove('hidden');
  } catch (err) {
    alert('Не удалось загрузить подробности: ' + err.message);
  }
}

// Populate Modal in View Mode
async function populateModalView(item) {
  modalBadgeType.textContent = item.media_type === 'series' ? 'Сериал' : item.media_type === 'movie' ? 'Фильм' : item.media_type;
  modalBadgeType.className = `media-type-badge ${item.media_type || 'movie'}`;

  modalTitleRu.textContent = item.title_ru || item.title || 'Без названия';
  modalTitleOrig.textContent = `${item.title_orig || ''} ${item.year ? `(${item.year})` : ''}`;
  
  modalMetaYear.innerHTML = `<i class="bi bi-calendar"></i> ${item.year || '-'}`;
  modalMetaCategory.innerHTML = `<i class="bi bi-folder2"></i> ${item.main_category || 'Без категории'}`;
  modalMetaGenres.innerHTML = `<i class="bi bi-hash"></i> ${item.genres || '-'}`;
  modalMetaRating.innerHTML = `<i class="bi bi-star-fill text-warning"></i> ${item.rating || '-/10'}`;

  modalPlot.textContent = item.plot || 'Описание отсутствует.';
  modalCountry.textContent = item.country || '-';
  modalDirectors.textContent = item.directors || '-';
  modalCast.textContent = item.cast || '-';
  modalSize.textContent = item.media_size ? `${item.media_size.toFixed(2)} ГБ` : '-';

  // Handle RAG verdicts
  modalVerdict.textContent = item.final_verdict || '';
  if (item.final_verdict) {
    modalVerdict.parentElement.classList.remove('hidden');
  } else {
    modalVerdict.parentElement.classList.add('hidden');
  }
  modalReview.textContent = item.review || '';

  modalAtmosphere.textContent = item.atmosphere || '-';
  modalWhyWatch.textContent = item.why_watch || '-';
  modalMood.textContent = item.mood || '-';
  modalCatchphrases.textContent = item.catchphrases || '-';
  modalFacts.textContent = item.facts || '-';
  modalSimilar.textContent = item.similar || '-';

  // Fetch and Render Episodes dynamically if this is a series
  if (item.media_type === 'series') {
    modalEpisodesBody.innerHTML = '<tr><td colspan="3" class="text-center">Загрузка серий...</td></tr>';
    modalEpisodesSection.classList.remove('hidden');
    try {
      const epRes = await fetch(`/api/media/${item.id || item.parent_id || 0}/episodes`);
      if (epRes.ok) {
        const episodes = await epRes.json();
        if (Array.isArray(episodes) && episodes.length > 0) {
          modalEpisodesBody.innerHTML = '';
          episodes.forEach(ep => {
            const row = document.createElement('tr');
            row.innerHTML = `
              <td>${ep.season_number || ep.season || '-'}</td>
              <td>${ep.episode_number || ep.episode || '-'}</td>
              <td>${ep.title || ep.title_ru || 'Без названия'}</td>
            `;
            modalEpisodesBody.appendChild(row);
          });
        } else {
          modalEpisodesBody.innerHTML = '<tr><td colspan="3" class="text-center">Нет загруженных эпизодов</td></tr>';
        }
      } else {
        modalEpisodesSection.classList.add('hidden');
      }
    } catch (e) {
      modalEpisodesSection.classList.add('hidden');
    }
  } else {
    modalEpisodesSection.classList.add('hidden');
  }
}

// Open Add Media Modal
function openAddMediaModal() {
  isNewItem = true;
  isEditMode = true;
  currentMediaItem = {};
  
  editModalHeaderTitle.textContent = 'Добавить медиа в библиотеку';
  btnDeleteMedia.classList.add('hidden');
  btnEditToggle.classList.add('hidden');
  btnSaveMedia.classList.remove('hidden');
  modalViewMode.classList.add('hidden');
  modalEditForm.classList.remove('hidden');

  // Reset all inputs
  resetFormInputs();
  
  modalBadgeType.textContent = 'NEW';
  modalBadgeType.className = 'media-type-badge movie';
  mediaModal.classList.remove('hidden');
}

// Reset Form Inputs
function resetFormInputs() {
  editTitle.value = '';
  editTitleRu.value = '';
  editTitleOrig.value = '';
  editType.value = 'movie';
  editYear.value = new Date().getFullYear();
  editCategory.value = '';
  editGenres.value = '';
  editRating.value = '';
  editSize.value = '';
  editPath.value = '';
  editPlot.value = '';
  editReview.value = '';
  editFinalVerdict.value = '';
  editDirectors.value = '';
  editCountry.value = '';
  editCast.value = '';
  editAtmosphere.value = '';
  editWhyWatch.value = '';
  editMood.value = '';
  editCatchphrases.value = '';
  editFacts.value = '';
  editSimilar.value = '';
}

// Populate Edit Form Inputs
function populateFormInputs(item) {
  editTitle.value = item.title || '';
  editTitleRu.value = item.title_ru || '';
  editTitleOrig.value = item.title_orig || '';
  editType.value = item.media_type || 'movie';
  editYear.value = item.year || '';
  editCategory.value = item.main_category || '';
  editGenres.value = item.genres || '';
  editRating.value = item.rating || '';
  editSize.value = item.media_size || '';
  editPath.value = item.path || '';
  editPlot.value = item.plot || '';
  editReview.value = item.review || '';
  editFinalVerdict.value = item.final_verdict || '';
  editDirectors.value = item.directors || '';
  editCountry.value = item.country || '';
  editCast.value = item.cast || '';
  editAtmosphere.value = item.atmosphere || '';
  editWhyWatch.value = item.why_watch || '';
  editMood.value = item.mood || '';
  editCatchphrases.value = item.catchphrases || '';
  editFacts.value = item.facts || '';
  editSimilar.value = item.similar || '';
}

// Toggle Edit/View Mode in Modal
function toggleEditMode() {
  isEditMode = !isEditMode;
  if (isEditMode) {
    editModalHeaderTitle.textContent = 'Редактирование записи';
    btnEditToggle.innerHTML = '<i class="bi bi-eye"></i> Просмотр';
    btnSaveMedia.classList.remove('hidden');
    modalViewMode.classList.add('hidden');
    modalEditForm.classList.remove('hidden');
    populateFormInputs(currentMediaItem);
  } else {
    btnEditToggle.innerHTML = '<i class="bi bi-pencil"></i> Редактировать';
    btnSaveMedia.classList.add('hidden');
    modalViewMode.classList.remove('hidden');
    modalEditForm.classList.add('hidden');
    populateModalView(currentMediaItem);
  }
}

// Save Media (Create / Update)
async function saveMediaData() {
  if (!editTitle.value) {
    alert('Пожалуйста, заполните основное название');
    return;
  }

  const payload = {
    title: editTitle.value,
    title_ru: editTitleRu.value,
    title_orig: editTitleOrig.value,
    media_type: editType.value,
    year: editYear.value ? parseInt(editYear.value) : null,
    main_category: editCategory.value,
    genres: editGenres.value,
    rating: editRating.value,
    media_size: editSize.value ? parseFloat(editSize.value) : null,
    path: editPath.value,
    plot: editPlot.value,
    review: editReview.value,
    final_verdict: editFinalVerdict.value,
    directors: editDirectors.value,
    country: editCountry.value,
    cast: editCast.value,
    atmosphere: editAtmosphere.value,
    why_watch: editWhyWatch.value,
    mood: editMood.value,
    catchphrases: editCatchphrases.value,
    facts: editFacts.value,
    similar: editSimilar.value
  };

  const method = isNewItem ? 'POST' : 'PUT';
  const url = isNewItem ? '/api/media' : `/api/media/${currentMediaItem.id}`;

  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error('Не удалось сохранить изменения');

    alert(isNewItem ? 'Медиа успешно добавлено!' : 'Изменения сохранены!');
    closeModal();
    fetchMedia();
    fetchStats();
    fetchCategories();
  } catch (err) {
    alert('Ошибка при сохранении: ' + err.message);
  }
}

// Delete Media Item
async function deleteMediaItem() {
  if (!currentMediaItem || !currentMediaItem.id) return;
  
  const confirmDelete = confirm(`Вы уверены, что хотите удалить "${currentMediaItem.title_ru || currentMediaItem.title}"?`);
  if (!confirmDelete) return;

  try {
    const res = await fetch(`/api/media/${currentMediaItem.id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete');

    alert('Запись удалена');
    closeModal();
    fetchMedia();
    fetchStats();
    fetchCategories();
  } catch (err) {
    alert('Ошибка при удалении: ' + err.message);
  }
}

// Close Modal
function closeModal() {
  mediaModal.classList.add('hidden');
  currentMediaItem = null;
  isEditMode = false;
  isNewItem = false;
}

// Debounce helper
function debounce(fn, delay) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), delay);
  };
}
