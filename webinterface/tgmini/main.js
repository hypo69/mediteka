// Telegram Mini App Main JS
// Инициализация Telegram Web App и модулей

import { initI18n, switchLang, applyTranslations } from '../js/i18n.js';

window.switchLang = switchLang;
window.applyTranslations = applyTranslations;

// ── TELEGRAM WEB APP INITIALIZATION ────────────────────────────────────────

function initTelegramWebApp() {
  const tg = window.Telegram.WebApp;
  
  // Expand to full height
  tg.ready();
  tg.expand();
  
  // Enable safe area for iOS
  if (tg.version >= 5) {
    tg.setHeaderColor('secondary_bg_color');
    tg.setBackgroundColor('secondary_bg_color');
  }
  
  // Update theme colors from Telegram
  function updateThemeColors() {
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#0d1117');
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#c9d1d9');
    document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#8b949e');
    document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color || '#58a6ff');
    document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#238636');
    document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff');
    document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#161b22');
  }
  
  // Initial theme update
  updateThemeColors();
  
  // Listen for theme changes
  tg.onEvent('themeChanged', updateThemeColors);
  
  return tg;
}

// ── TELEGRAM-SPECIFIC API CLIENT ───────────────────────────────────────────

window.api = {
  // Get base URL - use window.location.origin for local or CDN
  get baseUrl() {
    // For Telegram Mini App, we need to use relative URLs or absolute from window.location
    return window.location.origin;
  },
  
  async fetch(url, options = {}) {
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        let msg = response.statusText;
        try {
          const data = await response.json();
          msg = data.detail || msg;
        } catch {
          // Try text response
          const text = await response.text();
          if (text) msg = text;
        }
        throw new Error(`${response.status} ${msg}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API fetch error:', error);
      throw error;
    }
  },
  
  // Telegram Mini App specific methods
  tg: {
    // Get user data from Telegram
    async getUser() {
      const tg = window.Telegram.WebApp;
      return tg.initDataUnsafe?.user || null;
    },
    
    // Get theme parameters
    getThemeParams() {
      const tg = window.Telegram.WebApp;
      return tg.themeParams;
    },
    
    // Haptic feedback
    hapticFeedback(options = { type: 'impact', impactStyle: 'medium' }) {
      const tg = window.Telegram.WebApp;
      if (tg.HapticFeedback) {
        tg.HapticFeedback.impactOccurred(options.impactStyle || 'medium');
      }
    },
    
    // Vibrate (fallback if HapticFeedback not available)
    vibrate(duration = 50) {
      const tg = window.Telegram.WebApp;
      if (tg.HapticFeedback) {
        tg.HapticFeedback.notificationOccurred('success');
      } else if (navigator.vibrate) {
        navigator.vibrate(duration);
      }
    },
    
    // Open link in external browser
    openLink(url, options = {}) {
      const tg = window.Telegram.WebApp;
      tg.openLink(url, options);
    },
    
    // Show confirm dialog
    async confirm(message) {
      const tg = window.Telegram.WebApp;
      return new Promise((resolve) => {
        tg.showConfirm(message, (confirmed) => resolve(confirmed));
      });
    },
    
    // Show alert
    showAlert(message) {
      const tg = window.Telegram.WebApp;
      tg.showAlert(message);
    },
    
    // Main button
    setMainButton(text, options = {}) {
      const tg = window.Telegram.WebApp;
      tg.MainButton.setText(text);
      tg.MainButton.setParams(options);
      tg.MainButton.show();
    },
    
    hideMainButton() {
      const tg = window.Telegram.WebApp;
      tg.MainButton.hide();
    },
    
    // Close Mini App
    close() {
      const tg = window.Telegram.WebApp;
      tg.close();
    }
  }
};

// ── I18N INITIALIZATION ────────────────────────────────────────────────────

async function initI18nAndLanguage() {
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
  
  applyTranslations();
}

// ── PLAYER MODULE ──────────────────────────────────────────────────────────

let mediaFiles = [];
let currentIndex = -1;

function initPlayer() {
  const fileList = document.getElementById('file-list');
  const video = document.getElementById('video');
  const prevBtn = document.getElementById('btn-prev');
  const nextBtn = document.getElementById('btn-next');
  
  loadMediaFiles();
  
  prevBtn?.addEventListener('click', () => {
    window.api.tg.vibrate(50);
    playPrev();
  });
  
  nextBtn?.addEventListener('click', () => {
    window.api.tg.vibrate(50);
    playNext();
  });
  
  // Handle video ended
  video?.addEventListener('ended', () => {
    window.api.tg.vibrate(50);
    playNext();
  });
}

async function loadMediaFiles() {
  try {
    const files = await window.api.fetch('/api/media/files');
    mediaFiles = files || [];
    renderFileList();
  } catch (e) {
    console.error('Failed to load media files:', e);
    document.getElementById('file-list').innerHTML = 
      '<div class="text-danger p-3" data-i18n="player.loadError">Ошибка загрузки файлов</div>';
  }
}

function renderFileList() {
  const list = document.getElementById('file-list');
  if (!mediaFiles.length) {
    list.innerHTML = '<div class="text-muted text-center p-3" data-i18n="player.noFiles">Нет файлов</div>';
    return;
  }
  
  list.innerHTML = mediaFiles.map((file, i) => `
    <div class="file-item ${i === currentIndex ? 'active' : ''}" data-index="${i}">
      <i class="bi bi-film"></i> ${escapeHtml(file.name || file.path)}
    </div>
  `).join('');
  
  // Add click handlers
  list.querySelectorAll('.file-item').forEach(item => {
    item.addEventListener('click', () => {
      const idx = parseInt(item.dataset.index);
      window.api.tg.vibrate(50);
      playFile(idx);
    });
  });
}

function playFile(index) {
  if (index < 0 || index >= mediaFiles.length) return;
  
  currentIndex = index;
  const file = mediaFiles[index];
  const video = document.getElementById('video');
  
  // Build streaming URL
  const filePath = encodeURIComponent(file.path || file);
  video.src = `/api/media/stream?path=${filePath}`;
  
  document.getElementById('current-file').textContent = file.name || file.path;
  renderFileList();
  
  video.play().catch(e => console.error('Play error:', e));
}

function playNext() {
  if (currentIndex < mediaFiles.length - 1) {
    playFile(currentIndex + 1);
  }
}

function playPrev() {
  if (currentIndex > 0) {
    playFile(currentIndex - 1);
  }
}

// ── CHAT MODULE ────────────────────────────────────────────────────────────

function initChat() {
  const sendBtn = document.getElementById('send-button');
  const input = document.getElementById('message-input');
  
  sendBtn?.addEventListener('click', () => {
    window.api.tg.vibrate(50);
    sendMessage();
  });
  
  input?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      window.api.tg.vibrate(50);
      sendMessage();
    }
  });
}

async function sendMessage() {
  const input = document.getElementById('message-input');
  const chatWindow = document.getElementById('chat-window');
  const message = input.value.trim();
  
  if (!message) return;
  
  // Clear input
  input.value = '';
  
  // Hide empty message
  document.getElementById('chat-empty')?.remove();
  
  // Add user message
  addMessage(message, 'user');
  
  // Show typing indicator
  const typingId = addTypingIndicator();
  
  try {
    const reply = await window.chatService.sendChatMessage(message);
    removeTypingIndicator(typingId);
    addMessage(reply, 'assistant');
  } catch (e) {
    removeTypingIndicator(typingId);
    addMessage(e, 'assistant', true);
  }
}

function parseContentToHtml(text) {
  if (!text) return '';
  
  // Clean markdown code blocks if the content is wrapped in them
  let cleaned = text.trim();
  const codeBlockRegex = /^```(?:html|xml)?\s*([\s\S]*?)\s*```$/i;
  const match = cleaned.match(codeBlockRegex);
  if (match) {
    cleaned = match[1];
  }

  let html = cleaned;
  if (window.marked && typeof window.marked.parse === 'function') {
    html = window.marked.parse(cleaned);
  } else {
    // Basic fallback for formatting if marked is not loaded
    html = cleaned
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }
  return html;
}

function addMessage(text, sender, isError = false) {
  const chatWindow = document.getElementById('chat-window');
  const div = document.createElement('div');
  div.className = `chat-message ${sender}${isError ? ' error' : ''}`;
  
  if (typeof text === 'object' && text !== null) {
    div.innerHTML = window.chatService.formatMessage(text);
  } else {
    div.innerHTML = parseContentToHtml(text);
  }
  
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addTypingIndicator() {
  const chatWindow = document.getElementById('chat-window');
  const id = 'typing-' + Date.now();
  const div = document.createElement('div');
  div.id = id;
  div.className = 'chat-message assistant';
  div.innerHTML = '<i class="bi bi-three-dots"></i> Печатает...';
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  document.getElementById(id)?.remove();
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ── REMOTE CONTROL MODULE ──────────────────────────────────────────────────
let remoteWs = null;
let cachedUserEmail = 'default';
let remoteState = {
  duration: 0,
  currentTime: 0,
  isPlaying: false,
  volume: 1
};
let isSeeking = false;

function initRemoteControl() {
  const statusBadge = document.getElementById('remote-ws-status');
  const trackTitle = document.getElementById('remote-track-title');
  const timeDisplay = document.getElementById('remote-time-display');
  const seekSlider = document.getElementById('remote-seek-slider');
  const volumeSlider = document.getElementById('remote-volume-slider');
  const playIcon = document.getElementById('remote-play-icon');
  const playlistContainer = document.getElementById('remote-playlist-items');

  function triggerHaptic() {
    window.api.tg.hapticFeedback({ impactStyle: 'light' });
  }

  function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '00:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  async function connect() {
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
      console.error('Failed to check auth for remote websocket room, using cached email:', e);
    }

    const wsUrl = `${protocol}//${window.location.host}/api/control/ws?role=remote&room=${encodeURIComponent(email)}`;

    remoteWs = new WebSocket(wsUrl);

    remoteWs.onopen = () => {
      console.log('Remote Control WebSocket connected');
      if (statusBadge) {
        statusBadge.className = 'badge bg-success';
        statusBadge.innerHTML = '<i class="bi bi-wifi"></i> Подключено к серверу';
      }
      const roomInfo = document.getElementById('remote-room-info');
      if (roomInfo) {
        const displayRoom = email.includes('@') ? 'kino.davidka.net.tv' : email;
        roomInfo.textContent = `Комната: ${displayRoom}`;
      }
    };

    remoteWs.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.event === 'status_update') {
          updateUI(msg);
        } else if (msg.event === 'playlist_update') {
          updatePlaylist(msg.files || []);
        }
      } catch (e) {
        console.error('Error parsing remote WS message:', e);
      }
    };

    remoteWs.onclose = () => {
      if (statusBadge) {
        statusBadge.className = 'badge bg-warning text-dark';
        statusBadge.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Переподключение...';
      }
      setTimeout(connect, 3000);
    };

    remoteWs.onerror = (err) => {
      console.error('Remote WS error:', err);
    };
  }

  function sendRemoteCommand(action, payload = {}) {
    triggerHaptic();
    if (remoteWs && remoteWs.readyState === WebSocket.OPEN) {
      remoteWs.send(JSON.stringify({ action, ...payload }));
    }
  }

  function updateUI(data) {
    remoteState = { ...remoteState, ...data };

    if (trackTitle) trackTitle.textContent = data.fileName || 'Файл не выбран';
    if (timeDisplay) {
      timeDisplay.textContent = `${formatTime(data.currentTime)} / ${formatTime(data.duration)}`;
    }

    if (seekSlider && !isSeeking && data.duration > 0) {
      seekSlider.max = Math.floor(data.duration);
      seekSlider.value = Math.floor(data.currentTime);
    }

    if (volumeSlider && typeof data.volume === 'number') {
      volumeSlider.value = data.volume;
    }

    if (playIcon) {
      if (data.isPlaying) {
        playIcon.className = 'bi bi-pause-fill fs-2';
      } else {
        playIcon.className = 'bi bi-play-fill fs-2';
      }
    }
  }

  function updatePlaylist(files) {
    if (!playlistContainer) return;
    if (!files.length) {
      playlistContainer.innerHTML = '<div class="text-muted small p-2 text-center">Плейлист пуст</div>';
      return;
    }

    playlistContainer.innerHTML = files.map((f, i) => `
      <button class="list-group-item list-group-item-action bg-transparent text-white border-secondary py-2 px-3 small d-flex justify-content-between align-items-center" onclick="window.playRemoteFile(${i})">
        <span class="text-truncate">${i + 1}. ${escapeHtml(f.name)}</span>
        <span class="badge bg-secondary ms-2">${f.type === 'series' ? 'Сериал' : 'Фильм'}</span>
      </button>
    `).join('');
  }

  window.playRemoteFile = (index) => {
    sendRemoteCommand('play_file', { index });
  };

  // Bind Control Buttons
  document.getElementById('remote-btn-playtoggle')?.addEventListener('click', () => {
    sendRemoteCommand('toggle_play');
  });

  document.getElementById('remote-btn-prev')?.addEventListener('click', () => {
    sendRemoteCommand('prev');
  });

  document.getElementById('remote-btn-next')?.addEventListener('click', () => {
    sendRemoteCommand('next');
  });

  // Seek Slider
  if (seekSlider) {
    seekSlider.addEventListener('mousedown', () => { isSeeking = true; });
    seekSlider.addEventListener('touchstart', () => { isSeeking = true; });
    seekSlider.addEventListener('change', (e) => {
      isSeeking = false;
      sendRemoteCommand('seek', { seconds: parseFloat(e.target.value) });
    });
  }

  // Volume Slider
  if (volumeSlider) {
    volumeSlider.addEventListener('change', (e) => {
      sendRemoteCommand('set_volume', { level: parseFloat(e.target.value) });
    });
  }

  // ── VOICE CONTROL MODULE ────────────────────────────────────────────────
  let recognition = null;
  let isListening = false;

  function initVoiceControl() {
    const btnMic = document.getElementById('remote-btn-mic');
    const micIcon = document.getElementById('remote-mic-icon');
    const voiceStatus = document.getElementById('remote-voice-status');
    const voiceLog = document.getElementById('remote-voice-log');

    if (!btnMic) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      voiceStatus.textContent = 'Голос не поддерживается браузером';
      btnMic.disabled = true;
      return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = 'ru-RU';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      isListening = true;
      btnMic.className = 'btn btn-danger btn-circle-lg mx-auto';
      micIcon.className = 'bi bi-mic-fill fs-4 animate-pulse';
      voiceStatus.textContent = 'Слушаю... Говорите';
    };

    recognition.onend = () => {
      isListening = false;
      btnMic.className = 'btn btn-outline-danger btn-circle-lg mx-auto';
      micIcon.className = 'bi bi-mic-fill fs-4';
    };

    recognition.onerror = (e) => {
      voiceStatus.textContent = `Ошибка: ${e.error}`;
    };

    recognition.onresult = async (event) => {
      const text = event.results[0][0].transcript.trim().toLowerCase();
      logVoice(`Вы: ${text}`);
      
      if (handleLocalVoiceCommand(text)) {
        voiceStatus.textContent = `Выполнено: "${text}"`;
        speakText(`Команда выполнена`);
      } else {
        voiceStatus.textContent = 'Обработка запроса AI...';
        try {
          const reply = await sendToAiModel(text);
          logVoice(`AI: ${reply}`);
          voiceStatus.textContent = 'AI ответил';
          speakText(reply);
        } catch (err) {
          voiceStatus.textContent = `Ошибка AI: ${err.message}`;
          logVoice(`Ошибка AI: ${err.message}`);
        }
      }
    };

    btnMic.addEventListener('click', () => {
      triggerHaptic();
      if (isListening) {
        recognition.stop();
      } else {
        recognition.start();
      }
    });
  }

  function logVoice(msg) {
    const voiceLog = document.getElementById('remote-voice-log');
    if (!voiceLog) return;
    voiceLog.style.display = 'block';
    const div = document.createElement('div');
    div.textContent = msg;
    voiceLog.appendChild(div);
    voiceLog.scrollTop = voiceLog.scrollHeight;
  }

  function speakText(text) {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ru-RU';
      window.speechSynthesis.speak(utterance);
    }
  }

  function handleLocalVoiceCommand(text) {
    if (text.includes('пауз') || text.includes('стоп')) {
      sendRemoteCommand('pause');
      return true;
    }
    if (text.includes('продолж') || text.includes('плей') || text.includes('играй') || text.includes('старт')) {
      sendRemoteCommand('play');
      return true;
    }
    if (text.includes('громче') || text.includes('прибавь звук')) {
      const targetVol = Math.min(1, remoteState.volume + 0.2);
      sendRemoteCommand('set_volume', { level: targetVol });
      return true;
    }
    if (text.includes('тише') || text.includes('убавь звук')) {
      const targetVol = Math.max(0, remoteState.volume - 0.2);
      sendRemoteCommand('set_volume', { level: targetVol });
      return true;
    }
    if (text.includes('следующ') || text.includes('вперед')) {
      sendRemoteCommand('next');
      return true;
    }
    if (text.includes('предыдущ') || text.includes('назад')) {
      sendRemoteCommand('prev');
      return true;
    }
    return false;
  }

  async function sendToAiModel(message) {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    if (!response.ok) {
      throw new Error('Ошибка чата');
    }
    const data = await response.json();
    return data.response || data.message || 'Модель не ответила';
  }

  connect();
  initVoiceControl();
}


// ── MAIN INITIALIZATION ────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
  console.log('Telegram Mini App initializing...');
  
  // Initialize Telegram Web App
  const tg = initTelegramWebApp();
  console.log('Telegram Web App ready:', tg.version);
  
  // Initialize i18n
  await initI18nAndLanguage();

  
  // Initialize player
  initPlayer();
  
  // Initialize chat
  initChat();
  
  // Initialize remote control
  initRemoteControl();

  // Check for auto-play from query parameter
  const params = new URLSearchParams(window.location.search);
  const fileParam = params.get('file');
  if (fileParam) {
    console.log('Auto-play file requested:', fileParam);
    const video = document.getElementById('video');
    if (video) {
      video.src = `/api/media/stream?path=${encodeURIComponent(fileParam)}`;
      const currentFileEl = document.getElementById('current-file');
      if (currentFileEl) {
        currentFileEl.textContent = fileParam.split(/[/\\]/).pop();
      }
      
      // Switch tab to #tab-player
      const playerTabBtn = document.querySelector('button[data-bs-target="#tab-player"]');
      if (playerTabBtn) {
        playerTabBtn.click();
      }
      
      video.play().catch(e => console.error('Auto-play error:', e));
    }
  }

  console.log('Telegram Mini App ready');
});