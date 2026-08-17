// TV Player & Assistant Main JS
import { initI18n, switchLang, applyTranslations } from '../js/i18n.js';

window.switchLang = switchLang;
window.applyTranslations = applyTranslations;

// ── API MODULE ───────────────────────────────────────────────────────────────
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
  
  // Auth module
  auth: {
    async check() {
      try {
        const response = await fetch('/auth/check');
        return await response.json();
      } catch {
        return { authenticated: false };
      }
    },
    
    loginWithGoogle() {
      window.location.href = '/auth/google?next=' + encodeURIComponent(window.location.pathname + window.location.search);
    },
    
    async register(email, password, name) {
      return window.api.fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name })
      });
    },

    async verify(email, code) {
      return window.api.fetch('/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code })
      });
    },

    async loginEmail(email, password) {
      return window.api.fetch('/auth/login/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
    },
    
    logout() {
      return fetch('/auth/logout', { method: 'POST' });
    }
  }
};

// Notification helper
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
  notification.style.zIndex = '9999';
  notification.style.maxWidth = '400px';
  notification.textContent = message;
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.remove();
  }, 4000);
}

// ── MEDIA STREAMING & PLAYBACK ───────────────────────────────────────────────
let mediaFiles = [];
let currentIndex = -1;

// Загрузка медиафайлов
async function loadMediaFiles() {
  try {
    const response = await fetch('/api/media/by-category');
    const data = await response.json();
    
    if (data.error) {
      console.error('Error loading media files:', data.error);
      return;
    }
    
    mediaFiles = [];
    if (data.movies) {
      Object.values(data.movies).forEach(list => mediaFiles.push(...list));
    }
    if (data.series) {
      Object.values(data.series).forEach(list => mediaFiles.push(...list));
    }
    
    if (currentIndex >= 0 && currentIndex < mediaFiles.length) {
      openFile(currentIndex);
    }
    
    renderFileInfo();
    sendPlaylistUpdate();
  } catch (e) {
    console.error('Failed to load media files:', e);
    document.getElementById('file-name').textContent = 'Ошибка загрузки файлов';
  }
}

// Открытие файла
function openFile(index) {
  if (index < 0 || index >= mediaFiles.length) return;
  
  currentIndex = index;
  const file = mediaFiles[index];
  const video = document.getElementById('video');
  if (!video) return;
  
  const rawPath = file.path || file;
  if (typeof rawPath === 'string' && (rawPath.includes('youtube.com') || rawPath.includes('youtu.be'))) {
    playYouTubeUrl(rawPath);
    return;
  }
  
  video.style.display = 'block';
  const iframe = document.getElementById('youtube-player');
  if (iframe) iframe.style.display = 'none';

  const filePath = encodeURIComponent(rawPath);
  video.src = `/api/media/stream?path=${filePath}`;
  
  document.getElementById('file-name').textContent = file.name || 'Файл не найден';
  document.getElementById('file-meta').textContent = 
    `${file.year ? file.year + ' • ' : ''}${file.type === 'series' ? 'Сериал' : 'Фильм'}`;
  
  video.play().catch(() => {
    console.log('Autoplay blocked - waiting for user interaction');
  });
  
  renderFileInfo();
  showControls();
}

function playYouTubeUrl(url) {
  const videoWrapper = document.querySelector('.video-wrapper');
  const video = document.getElementById('video');
  if (video) {
    video.pause();
    video.style.display = 'none';
  }
  
  let iframe = document.getElementById('youtube-player');
  if (!iframe) {
    iframe = document.createElement('iframe');
    iframe.id = 'youtube-player';
    iframe.width = '100%';
    iframe.height = '100%';
    iframe.frameBorder = '0';
    iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
    iframe.allowFullscreen = true;
    iframe.style.borderRadius = '8px';
    videoWrapper.appendChild(iframe);
  }
  
  iframe.style.display = 'block';
  let videoId = '';
  try {
    const urlObj = new URL(url);
    if (url.includes('youtube.com')) {
      videoId = urlObj.searchParams.get('v');
    } else if (url.includes('youtu.be')) {
      videoId = urlObj.pathname.substring(1);
    }
  } catch (e) { console.error(e); }

  if (videoId) {
    iframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1&controls=1`;
  }
  
  document.getElementById('file-name').textContent = 'YouTube Video';
  document.getElementById('file-meta').textContent = 'YouTube';
  showControls();
}

function playPrev() {
  if (currentIndex > 0) {
    openFile(currentIndex - 1);
  }
}

function playNext() {
  if (currentIndex < mediaFiles.length - 1) {
    openFile(currentIndex + 1);
  }
}

function togglePlay() {
  const video = document.getElementById('video');
  if (!video) return;
  
  if (video.paused) {
    video.play().catch(() => {});
  } else {
    video.pause();
  }
}

function renderFileInfo() {
  if (currentIndex >= 0 && currentIndex < mediaFiles.length) {
    const file = mediaFiles[currentIndex];
    document.getElementById('file-name').textContent = file.name || 'Файл не найден';
    document.getElementById('file-meta').textContent = 
      `${file.year ? file.year + ' • ' : ''}${file.type === 'series' ? 'Сериал' : 'Фильм'}`;
  }
}

// ── WEBSOCKET CONTROL & SYNC ─────────────────────────────────────────────
let ws = null;
let cachedUserEmail = 'default';

async function initControlWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  let email = cachedUserEmail;
  try {
    const authRes = await fetch('/auth/check');
    if (authRes.ok) {
      const authData = await authRes.json();
      if (authData.authenticated && authData.email) {
        email = authData.email.trim().toLowerCase();
        cachedUserEmail = email;
      } else {
        email = 'default';
        cachedUserEmail = email;
      }
    } else {
      console.warn(`Auth check response not OK (${authRes.status}), using cached email: ${email}`);
    }
  } catch (e) {
    console.error('Failed to check auth for websocket room, using cached email:', e);
  }
  
  const wsUrl = `${protocol}//${window.location.host}/api/control/ws?role=player&room=${encodeURIComponent(email)}`;
  console.log('Connecting control WS to:', wsUrl);
  
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('Player WebSocket control connected');
    sendStatusUpdate();
    sendPlaylistUpdate();
  };

  ws.onmessage = (event) => {
    try {
      const cmd = JSON.parse(event.data);
      handleRemoteCommand(cmd);
    } catch (e) {
      console.error('Error handling remote command:', e);
    }
  };

  ws.onclose = () => {
    console.log('Player WebSocket control closed. Reconnecting in 3s...');
    setTimeout(initControlWebSocket, 3000);
  };

  ws.onerror = (err) => {
    console.error('Player WebSocket error:', err);
  };
}

function handleRemoteCommand(cmd) {
  const video = document.getElementById('video');
  if (!video || !cmd || !cmd.action) return;

  switch (cmd.action) {
    case 'play':
      video.play().catch(console.error);
      break;
    case 'pause':
      video.pause();
      break;
    case 'toggle_play':
      if (video.paused) video.play().catch(console.error);
      else video.pause();
      break;
    case 'seek':
      if (typeof cmd.seconds === 'number') video.currentTime = cmd.seconds;
      break;
    case 'set_volume':
      if (typeof cmd.level === 'number') video.volume = Math.max(0, Math.min(1, cmd.level));
      break;
    case 'play_file':
      if (typeof cmd.index === 'number') openFile(cmd.index);
      break;
    case 'play_file_by_path':
      if (cmd.path) {
        if (typeof cmd.path === 'string' && (cmd.path.includes('youtube.com') || cmd.path.includes('youtu.be'))) {
          playYouTubeUrl(cmd.path);
        } else {
          const idx = mediaFiles.findIndex(f => f.path === cmd.path);
          if (idx !== -1) openFile(idx);
        }
      }
      break;
    case 'next':
      playNext();
      break;
    case 'prev':
      playPrev();
      break;
  }
}

function sendStatusUpdate() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  const video = document.getElementById('video');
  if (!video) return;
  const currentFile = currentIndex >= 0 ? mediaFiles[currentIndex] : null;

  ws.send(JSON.stringify({
    event: 'status_update',
    isPlaying: !video.paused && !video.ended,
    currentTime: video.currentTime || 0,
    duration: video.duration || 0,
    volume: video.volume,
    muted: video.muted,
    fileName: currentFile ? currentFile.name : 'Файл не выбран',
    currentIndex: currentIndex
  }));
}

function sendPlaylistUpdate() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  const filesSummary = mediaFiles.map((f, i) => ({
    index: i,
    name: f.name,
    type: f.type,
    year: f.year
  }));

  ws.send(JSON.stringify({
    event: 'playlist_update',
    files: filesSummary
  }));
}

// ── AUTO-HIDING CONTROLS ─────────────────────────────────────────────────────
let hideTimeout = null;

function isAnyOverlayOpen() {
  const chatPopup = document.getElementById('chat-popup');
  const chatOpen = chatPopup && chatPopup.classList.contains('show');
  
  const loginModal = document.getElementById('loginModal');
  const loginOpen = loginModal && loginModal.classList.contains('show');
  
  const settingsModal = document.getElementById('settingsModal');
  const settingsOpen = settingsModal && settingsModal.classList.contains('show');
  
  return chatOpen || loginOpen || settingsOpen;
}

function showControls() {
  const panel = document.getElementById('controls-panel');
  const container = document.getElementById('player-container');
  if (panel) panel.classList.remove('controls-hidden');
  if (container) container.classList.remove('cursor-hidden');
  
  resetHideTimer();
}

function resetHideTimer() {
  if (hideTimeout) clearTimeout(hideTimeout);
  
  const video = document.getElementById('video');
  if (!video || video.paused || isAnyOverlayOpen()) {
    return;
  }
  
  hideTimeout = setTimeout(() => {
    const panel = document.getElementById('controls-panel');
    const container = document.getElementById('player-container');
    if (panel) panel.classList.add('controls-hidden');
    if (container) container.classList.add('cursor-hidden');
  }, 3000);
}

// ── AUTHENTICATION & PORTED CABINET ──────────────────────────────────────────
async function initAuth() {
  try {
    const loginTriggerBtn = document.getElementById('login-trigger-btn');
    const googleSignInBtn = document.getElementById('google-signin-btn');
    const userProfile = document.getElementById('user-profile');
    const userName = document.getElementById('user-name');
    const logoutBtn = document.getElementById('logout-btn');

    // Modal forms
    const formLogin = document.getElementById('form-login');
    const formRegister = document.getElementById('form-register');
    const formVerify = document.getElementById('form-verify');
    const authAlert = document.getElementById('auth-alert');

    // Toggle register / login forms
    const goToRegister = document.getElementById('go-to-register');
    const goToLogin = document.getElementById('go-to-login');
    const verifyCancel = document.getElementById('verify-cancel');

    let currentVerifyEmail = '';

    function showError(msg) {
      if (authAlert) {
        authAlert.textContent = msg;
        authAlert.classList.remove('d-none');
      }
    }

    function hideError() {
      authAlert?.classList.add('d-none');
    }

    function switchForm(mode) {
      hideError();
      document.getElementById('auth-form-login')?.classList.add('d-none');
      document.getElementById('auth-form-register')?.classList.add('d-none');
      document.getElementById('auth-form-verify')?.classList.add('d-none');

      if (mode === 'login') {
        document.getElementById('auth-form-login')?.classList.remove('d-none');
      } else if (mode === 'register') {
        document.getElementById('auth-form-register')?.classList.remove('d-none');
      } else if (mode === 'verify') {
        document.getElementById('auth-form-verify')?.classList.remove('d-none');
      }
    }

    goToRegister?.addEventListener('click', (e) => {
      e.preventDefault();
      switchForm('register');
    });

    goToLogin?.addEventListener('click', (e) => {
      e.preventDefault();
      switchForm('login');
    });

    verifyCancel?.addEventListener('click', (e) => {
      e.preventDefault();
      switchForm('login');
    });

    // Submit Login
    formLogin?.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideError();
      const email = document.getElementById('login-email').value;
      const password = document.getElementById('login-password').value;
      
      try {
        await window.api.auth.loginEmail(email, password);
        window.location.reload();
      } catch (err) {
        console.error(err);
        if (err.message.includes('403') || err.message.includes('не подтверждена')) {
          currentVerifyEmail = email;
          switchForm('verify');
        } else {
          showError(err.message || 'Ошибка входа');
        }
      }
    });

    // Submit Register
    formRegister?.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideError();
      const name = document.getElementById('register-name').value;
      const email = document.getElementById('register-email').value;
      const password = document.getElementById('register-password').value;

      try {
        await window.api.auth.register(email, password, name);
        currentVerifyEmail = email;
        switchForm('verify');
      } catch (err) {
        console.error(err);
        showError(err.message || 'Ошибка регистрации');
      }
    });

    // Submit Verify
    formVerify?.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideError();
      const code = document.getElementById('verify-code').value;

      try {
        await window.api.auth.verify(currentVerifyEmail, code);
        switchForm('login');
        showNotification('Почта подтверждена! Теперь вы можете войти.', 'success');
      } catch (err) {
        console.error(err);
        showError(err.message || 'Неверный код подтверждения');
      }
    });

    async function updateAuthUI(authData) {
      const logoutBtnModal = document.getElementById('logout-btn-modal');
      const avatarContainer = document.getElementById('user-avatar-container');
      
      if (authData.authenticated) {
        userProfile?.classList.remove('d-none');
        loginTriggerBtn?.classList.add('d-none');
        logoutBtn?.classList.remove('d-none');
        logoutBtnModal?.classList.remove('d-none');
        document.querySelectorAll('.auth-only').forEach(el => el.classList.remove('d-none'));
        
        if (authData.name) {
          if (userName) userName.textContent = authData.name;
        } else if (authData.email) {
          if (userName) userName.textContent = authData.email.split('@')[0];
        }
        
        if (avatarContainer) {
          if (authData.picture) {
            avatarContainer.innerHTML = `<img src="${authData.picture}" class="rounded-circle" width="32" height="32" title="${authData.name || ''}">`;
          } else {
            avatarContainer.innerHTML = `<i class="bi bi-person-circle fs-4 text-light" title="${authData.name || ''}"></i>`;
          }
        }
        
        setupCabinet();
        setupSettings();
      } else {
        userProfile?.classList.add('d-none');
        loginTriggerBtn?.classList.remove('d-none');
        logoutBtn?.classList.add('d-none');
        logoutBtnModal?.classList.add('d-none');
        document.querySelectorAll('.auth-only').forEach(el => el.classList.add('d-none'));
        if (avatarContainer) avatarContainer.innerHTML = '';
      }
    }
    
    const authData = await window.api.auth.check();
    console.log('authData check result:', authData);
    if (authData.authenticated && authData.email) {
      cachedUserEmail = authData.email.trim().toLowerCase();
    }
    await updateAuthUI(authData);
    
    googleSignInBtn?.addEventListener('click', () => {
      console.log('Google Sign-In button clicked');
      window.api.auth.loginWithGoogle();
    });
    
    const handleLogout = async () => {
      try {
        await window.api.auth.logout();
        window.location.reload();
      } catch (e) {
        console.error('Logout failed:', e);
      }
    };

    logoutBtn?.addEventListener('click', handleLogout);
    document.getElementById('logout-btn-modal')?.addEventListener('click', handleLogout);
  } catch (err) {
    console.error('Error during initAuth:', err);
  }
}

// Cabinet Info Loader
async function setupCabinet() {
  const avatar = document.getElementById('cab-avatar');
  const nameEl = document.getElementById('cab-name');
  const emailEl = document.getElementById('cab-email');
  const roleEl = document.getElementById('cab-role');
  const dateEl = document.getElementById('cab-created-at');
  
  const linkedDiv = document.getElementById('tg-status-linked');
  const unlinkedDiv = document.getElementById('tg-status-unlinked');
  const tgUserEl = document.getElementById('cab-tg-username');
  
  const genBtn = document.getElementById('btn-gen-link-token');
  const codeArea = document.getElementById('tg-link-code-area');
  const codeEl = document.getElementById('tg-link-code');

  try {
    const data = await window.api.fetch('/auth/cabinet');
    if (avatar && data.picture) avatar.src = data.picture;
    if (nameEl) nameEl.textContent = data.name || 'Без имени';
    if (emailEl) emailEl.textContent = data.email;
    if (roleEl) {
      roleEl.textContent = data.role === 'admin' ? 'Администратор' : 'Пользователь';
      roleEl.className = data.role === 'admin' ? 'badge bg-danger' : 'badge bg-secondary';
    }
    if (dateEl && data.created_at) {
      const date = new Date(data.created_at);
      dateEl.textContent = 'Дата регистрации: ' + date.toLocaleDateString('ru-RU');
    }

    if (data.telegram_username) {
      linkedDiv?.classList.remove('d-none');
      unlinkedDiv?.classList.add('d-none');
      if (tgUserEl) tgUserEl.textContent = data.telegram_username.startsWith('@') ? data.telegram_username : `@${data.telegram_username}`;
    } else {
      linkedDiv?.classList.add('d-none');
      unlinkedDiv?.classList.remove('d-none');
    }
  } catch (e) {
    console.error('Failed to load cabinet data:', e);
  }

  genBtn?.addEventListener('click', async () => {
    try {
      const res = await window.api.fetch('/auth/link-token', { method: 'POST' });
      if (res.token) {
        if (codeEl) codeEl.textContent = res.token;
        codeArea?.classList.remove('d-none');
        showNotification('Код привязки успешно сгенерирован', 'success');
      }
    } catch (e) {
      showNotification('Не удалось получить код привязки: ' + e.message, 'danger');
    }
  });
}

// ── PORTED SETTINGS ──────────────────────────────────────────────────────────
async function setupSettings() {
  const form = document.getElementById('settings-form');
  const themeSelect = document.getElementById('settings-theme');
  const langSelect = document.getElementById('settings-lang');
  const ttsCheckbox = document.getElementById('settings-tts');
  const instructionText = document.getElementById('settings-instruction');

  try {
    const settings = await window.api.fetch('/auth/settings');
    if (themeSelect && settings.theme) themeSelect.value = settings.theme;
    if (langSelect && settings.language) langSelect.value = settings.language;
    if (ttsCheckbox) ttsCheckbox.checked = settings.tts_enabled === 1;
    if (instructionText && settings.system_instruction) instructionText.value = settings.system_instruction;
  } catch (e) {
    console.error('Failed to load settings:', e);
  }

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const payload = {
        theme: themeSelect?.value || 'dark',
        language: langSelect?.value || 'ru',
        tts_enabled: ttsCheckbox?.checked ? 1 : 0,
        system_instruction: instructionText?.value || ''
      };
      await window.api.fetch('/auth/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      showNotification('Настройки сохранены', 'success');
      
      if (window.switchLang) {
        window.switchLang(payload.language);
      }
    } catch (e) {
      showNotification('Ошибка сохранения настроек: ' + e.message, 'danger');
    }
  });
}

// ── QUICK ACCESS SETUP ───────────────────────────────────────────────────────
function setupQuickAccess() {
  const btnBookmark = document.getElementById('btn-bookmark');
  const btnHomepage = document.getElementById('btn-homepage');
  const modalBody = document.getElementById('quick-access-modal-body');
  const modalTitle = document.getElementById('quickAccessModalLabel');
  
  // Use bootstrap global object from the page
  const qaModal = new bootstrap.Modal(document.getElementById('quickAccessModal'));

  btnBookmark?.addEventListener('click', () => {
    modalTitle.textContent = 'Добавить в закладки';
    modalBody.innerHTML = `
      <div class="text-center mb-3">
        <i class="bi bi-bookmark-plus text-warning" style="font-size: 3rem;"></i>
      </div>
      <p class="mb-3">Для быстрого доступа к плееру добавьте эту страницу в закладки вашего браузера:</p>
      
      <div class="card bg-secondary text-white border-0 p-3 mb-3" style="background-color: #2d3238 !important;">
        <h6 class="fw-bold mb-2 text-warning"><i class="bi bi-laptop me-2"></i> На компьютере (PC / Mac)</h6>
        <p class="small mb-0">Нажмите комбинацию клавиш <strong>Ctrl + D</strong> (или <strong>Cmd + D</strong> на macOS).</p>
      </div>

      <div class="card bg-secondary text-white border-0 p-3 mb-3" style="background-color: #2d3238 !important;">
        <h6 class="fw-bold mb-2 text-warning"><i class="bi bi-phone me-2"></i> На смартфоне (iOS / Android)</h6>
        <p class="small mb-0">Нажмите на иконку «Поделиться» (Share) в меню браузера и выберите <strong>«На экран "Домой"»</strong> (Add to Home Screen) или <strong>«Добавить закладку»</strong>.</p>
      </div>

      <div class="card bg-secondary text-white border-0 p-3 mb-0" style="background-color: #2d3238 !important;">
        <h6 class="fw-bold mb-2 text-warning"><i class="bi bi-tv me-2"></i> На телевизоре (Smart TV)</h6>
        <p class="small mb-0">Откройте меню браузера с помощью пульта управления (кнопка с тремя точками или шестеренкой) и выберите пункт <strong>«Добавить в закладки»</strong> или <strong>«Добавить на главный экран»</strong>.</p>
      </div>
    `;
    
    // Try native bookmark fallback
    try {
      if (window.sidebar && window.sidebar.addPanel) { // Firefox
        window.sidebar.addPanel(document.title, window.location.href, '');
      } else if (window.external && ('AddFavorite' in window.external)) { // IE
        window.external.AddFavorite(window.location.href, document.title);
      }
    } catch(e) {}

    qaModal.show();
  });

  btnHomepage?.addEventListener('click', () => {
    modalTitle.textContent = 'Сделать стартовой';
    modalBody.innerHTML = `
      <div class="text-center mb-3">
        <i class="bi bi-house-door text-info" style="font-size: 3rem;"></i>
      </div>
      <p class="mb-3">Настройте автоматическое открытие плеера при запуске вашего устройства:</p>

      <div class="card bg-secondary text-white border-0 p-3 mb-3" style="background-color: #2d3238 !important;">
        <h6 class="fw-bold mb-2 text-info"><i class="bi bi-tv me-2"></i> На телевизоре (Smart TV)</h6>
        <p class="small mb-0">Откройте меню настроек браузера на телевизоре, найдите раздел <strong>«При запуске»</strong> (On Startup) или <strong>«Стартовая страница»</strong> и укажите <strong>«Использовать текущую страницу»</strong>.</p>
      </div>
      
      <div class="card bg-secondary text-white border-0 p-3 mb-3" style="background-color: #2d3238 !important;">
        <h6 class="fw-bold mb-2 text-info"><i class="bi bi-browser-chrome me-2"></i> Google Chrome / Яндекс.Браузер</h6>
        <p class="small mb-0">Перейдите в Настройки → <strong>«Запуск»</strong> (On Startup) → выберите <strong>«Ранее открытые вкладки»</strong> или добавьте адрес этого сайта в <strong>«Заданные страницы»</strong>.</p>
      </div>

      <div class="card bg-secondary text-white border-0 p-3 mb-0" style="background-color: #2d3238 !important;">
        <h6 class="fw-bold mb-2 text-info"><i class="bi bi-compass me-2"></i> Safari (macOS)</h6>
        <p class="small mb-0">Перейдите в Настройки (Preferences) → вкладка <strong>«Основные»</strong> (General) → нажмите кнопку <strong>«Текущая страница»</strong> в поле «Домашняя страница».</p>
      </div>
    `;
    qaModal.show();
  });
}

// ── CHAT POPUP ───────────────────────────────────────────────────────────────
function initChatPopup() {
  const chatToggleBtn = document.getElementById('chat-toggle-btn');
  const chatPopup = document.getElementById('chat-popup');
  const chatCloseBtn = document.getElementById('chat-close-btn');
  const chatPopupSend = document.getElementById('chat-popup-send');
  const chatPopupInput = document.getElementById('chat-popup-input');
  const chatPopupMessages = document.getElementById('chat-popup-messages');
  const chatPopupMic = document.getElementById('chat-popup-mic');
  
  const chatPopupSettingsBtn = document.getElementById('chat-popup-settings-btn');
  const chatPopupSettingsPanel = document.getElementById('chat-popup-settings-panel');
  const chatPopupTemp = document.getElementById('chat-popup-temp');
  const chatPopupTempVal = document.getElementById('chat-popup-temp-val');
  const chatPopupTopP = document.getElementById('chat-popup-topp');
  const chatPopupTopPVal = document.getElementById('chat-popup-topp-val');
  const chatPopupTopK = document.getElementById('chat-popup-topk');
  const chatPopupTopKVal = document.getElementById('chat-popup-topk-val');

  if (chatPopupSettingsBtn && chatPopupSettingsPanel) {
    chatPopupSettingsBtn.addEventListener('click', (e) => {
      e.preventDefault();
      chatPopupSettingsPanel.classList.toggle('d-none');
    });
  }

  // Update slider label values dynamically
  if (chatPopupTemp && chatPopupTempVal) {
    chatPopupTemp.addEventListener('input', () => {
      chatPopupTempVal.textContent = chatPopupTemp.value;
    });
  }
  if (chatPopupTopP && chatPopupTopPVal) {
    chatPopupTopP.addEventListener('input', () => {
      chatPopupTopPVal.textContent = chatPopupTopP.value;
    });
  }
  if (chatPopupTopK && chatPopupTopKVal) {
    chatPopupTopK.addEventListener('input', () => {
      chatPopupTopKVal.textContent = chatPopupTopK.value;
    });
  }

  // Init Bootstrap tooltips in popup settings
  try {
    if (chatPopupSettingsPanel) {
      const tooltipTriggerList = [].slice.call(chatPopupSettingsPanel.querySelectorAll('[data-bs-toggle="tooltip"]'));
      tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
      });
    }
  } catch (e) {
    console.warn('Bootstrap tooltips failed to init:', e);
  }

  if (chatToggleBtn && chatPopup) {
    chatToggleBtn.addEventListener('click', (e) => {
      e.preventDefault();
      chatPopup.classList.toggle('show');
      if (chatPopup.classList.contains('show')) {
        chatPopupInput.focus();
      }
      showControls();
    });
  }

  if (chatCloseBtn && chatPopup) {
    chatCloseBtn.addEventListener('click', (e) => {
      e.preventDefault();
      chatPopup.classList.remove('show');
      showControls();
    });
  }

  if (chatPopupSend) {
    chatPopupSend.addEventListener('click', async () => {
      const msg = chatPopupInput.value.trim();
      if (!msg) return;
      
      addPopupMessage('user', msg);
      chatPopupInput.value = '';
      chatPopupSend.disabled = true;
      chatPopupSend.textContent = '⏳';
      
      const generationConfig = {
        temperature: parseFloat(chatPopupTemp?.value || '1.0'),
        top_p: parseFloat(chatPopupTopP?.value || '0.95'),
        top_k: parseInt(chatPopupTopK?.value || '40', 10)
      };
      
      try {
        const reply = await window.chatService.sendChatMessage(msg, null, [], generationConfig);
        addPopupMessage('bot', reply.text);
        window.chatService.speak(reply.voice || reply.text);
      } catch (e) {
        addPopupMessage('bot', 'Ошибка: ' + e.message);
      } finally {
        chatPopupSend.disabled = false;
        chatPopupSend.textContent = 'OK';
      }
    });
  }
  
  if (chatPopupInput) {
    chatPopupInput.addEventListener('keypress', async (e) => {
      if (e.key === 'Enter') {
        chatPopupSend.click();
      }
    });
  }

  let recognition = null;
  let isListening = false;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    if (chatPopupMic) chatPopupMic.style.display = 'none';
  } else {
    recognition = new SpeechRecognition();
    recognition.lang = 'ru-RU';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      isListening = true;
      if (chatPopupMic) {
        chatPopupMic.innerHTML = '<i class="bi bi-mic-fill"></i>';
        chatPopupMic.style.color = '#fff';
        chatPopupMic.style.backgroundColor = '#dc3545';
        chatPopupMic.style.borderColor = '#dc3545';
      }
      chatPopupInput.placeholder = 'Слушаю...';
    };

    recognition.onend = () => {
      isListening = false;
      if (chatPopupMic) {
        chatPopupMic.innerHTML = '<i class="bi bi-mic"></i>';
        chatPopupMic.style.color = '#ff6b6b';
        chatPopupMic.style.backgroundColor = 'transparent';
        chatPopupMic.style.borderColor = '#ff6b6b';
      }
      chatPopupInput.placeholder = 'Спросить...';
    };

    recognition.onerror = (e) => {
      console.error('Speech recognition error:', e.error);
      addPopupMessage('bot', `Ошибка голосового ввода: ${e.error}. Убедитесь, что доступ к микрофону разрешен, и сайт открыт по HTTPS или localhost.`);
    };

    recognition.onresult = async (event) => {
      const text = event.results[0][0].transcript;
      if (text) {
        chatPopupInput.value = text;
        chatPopupSend.click();
      }
    };

    if (chatPopupMic) {
      chatPopupMic.addEventListener('click', (e) => {
        e.preventDefault();
        if ('speechSynthesis' in window) {
          const silentUtterance = new SpeechSynthesisUtterance(' ');
          silentUtterance.volume = 0;
          window.speechSynthesis.speak(silentUtterance);
        }
        if (isListening) {
          recognition.stop();
        } else {
          recognition.start();
        }
      });
    }
  }
  
  function addPopupMessage(sender, text) {
    const el = document.createElement('div');
    el.className = `chat-popup-msg ${sender}`;
    el.textContent = text;
    chatPopupMessages.appendChild(el);
    chatPopupMessages.scrollTop = chatPopupMessages.scrollHeight;
  }
}

// ── INITIALIZATION ───────────────────────────────────────────────────────────
async function initAll() {
  console.log('TV Player initializing...');
  
  // Initialize i18n
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

  // Load media files
  await loadMediaFiles();
  
  // Init auth modules
  await initAuth();
  
  // Init chat
  initChatPopup();
  
  // Setup Quick Access bookmark & homepage buttons
  setupQuickAccess();
  
  // Init websocket control sync
  await initControlWebSocket();
  
  // Set up hiding activity listeners
  ['mousemove', 'mousedown', 'keydown', 'touchstart'].forEach(event => {
    document.addEventListener(event, showControls);
  });
  
  const video = document.getElementById('video');
  if (video) {
    video.addEventListener('play', resetHideTimer);
    video.addEventListener('pause', showControls);
    video.addEventListener('ended', showControls);
    
    // Send updates to control WebSocket on player events
    ['timeupdate', 'play', 'pause', 'volumechange', 'loadedmetadata', 'ended'].forEach(evt => {
      video.addEventListener(evt, sendStatusUpdate);
    });
  }

  // Listen to modal events to refresh visibility timer
  ['hidden.bs.modal', 'shown.bs.modal'].forEach(evt => {
    document.addEventListener(evt, () => {
      showControls();
    });
  });
  
  console.log('TV Player ready');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAll);
} else {
  initAll();
}

// Global functions for playback buttons
window.tvPlayPrev = playPrev;
window.tvPlayNext = playNext;
window.tvTogglePlay = togglePlay;
