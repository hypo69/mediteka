// ── CHAT.JS ───────────────────────────────────────────────────────────────────

let currentMediaPath = null;
let chatHistory = [];

function initChatTab() {
  const chatWindow = document.getElementById('chat-window');
  if (chatWindow) {
    // Приветственное сообщение
    const welcome = document.createElement('div');
    welcome.className = 'message bot-message';
    welcome.innerHTML = '<strong>Ai Ассистент</strong> (System): Добро пожаловать в чат! Можете спрашивать о фильмах и сериалах — я покажу путь к файлу и смогу открыть его в плеере.';
    chatWindow.appendChild(welcome);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Обработчик скачивания торрентов
    chatWindow.addEventListener('click', async (e) => {
      const btn = e.target.closest('.download-torrent-btn');
      if (!btn) return;
      
      const url = btn.getAttribute('data-url');
      const source = btn.getAttribute('data-source');
      const title = btn.getAttribute('data-title');
      
      btn.disabled = true;
      const originalHtml = btn.innerHTML;
      btn.textContent = '⏳ Добавление...';
      
      try {
        const response = await fetch('/api/torrents/download', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, source, title })
        });
        
        if (response.ok) {
          btn.textContent = '✅ Добавлено в qBittorrent';
          btn.classList.remove('btn-outline-success');
          btn.classList.add('btn-success');
        } else {
          const errData = await response.json();
          alert('Ошибка при добавлении торрента: ' + (errData.detail || response.statusText));
          btn.disabled = false;
          btn.innerHTML = originalHtml;
        }
      } catch (err) {
        alert('Ошибка соединения с сервером: ' + err.message);
        btn.disabled = false;
        btn.innerHTML = originalHtml;
      }
    });
  }


  // Event listeners for chat
  const sendBtn = document.getElementById('send-button');
  const msgInput = document.getElementById('message-input');

  if (sendBtn) sendBtn.addEventListener('click', sendMessage);
  if (msgInput) msgInput.addEventListener('keypress', e => { if (e.key==='Enter') sendMessage(); });

  // Media controls handlers
  document.getElementById('btn-toggle-player-body')?.addEventListener('click', togglePlayerBody);
  document.getElementById('btn-close-player')?.addEventListener('click', closeMediaControls);

  // Initialize CosmicPlayer
  initCosmicPlayer();
}

// Export init function for main.js
if (typeof window !== 'undefined') {
  window.initChatTab = initChatTab;
}

function togglePlayerBody() {
  const body = document.getElementById('media-player-body');
  const btn = document.getElementById('btn-toggle-player-body');
  if (body.classList.contains('d-none')) {
    body.classList.remove('d-none');
    btn.textContent = 'Свернуть плеер';
  } else {
    body.classList.add('d-none');
    btn.textContent = 'Развернуть плеер';
  }
}

let cosmicHls = null;
let cosmicHistory = [];

function initCosmicPlayer() {
  const streamForm = document.getElementById('cosmic-stream-form');
  const streamUrlInput = document.getElementById('cosmic-stream-url');
  const badges = document.querySelectorAll('#cosmic-provider-badges [data-prov]');
  
  if (streamForm) {
    streamForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const url = streamUrlInput.value.trim();
      if (url) loadCosmicVideo(url);
    });
  }

  badges.forEach(badge => {
    badge.addEventListener('click', () => {
      const prov = badge.getAttribute('data-prov');
      let demo = '';
      if (prov === 'youtube') demo = 'https://www.youtube.com/watch?v=aqz-KE-bpKQ';
      else if (prov === 'vk') demo = 'https://vk.com/video-22822305_456239018';
      else if (prov === 'rutube') demo = 'https://rutube.ru/video/e7cfcb8cb4310d54026fb4bd56e828d1/';
      else if (prov === 'direct') demo = 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8';
      
      if (demo) {
        streamUrlInput.value = demo;
        loadCosmicVideo(demo);
      }
    });
  });

  // Load history from localStorage
  try {
    cosmicHistory = JSON.parse(localStorage.getItem('cosmic_history_chat') || '[]');
  } catch(e) {}
  renderCosmicHistory();

  // Custom Controls Event Listeners
  const playBtn = document.getElementById('cosmic-play-btn');
  const stopBtn = document.getElementById('cosmic-stop-btn');
  const muteBtn = document.getElementById('cosmic-mute-btn');
  const volSlider = document.getElementById('cosmic-volume-slider');
  const speedSel = document.getElementById('cosmic-speed-select');
  const fullBtn = document.getElementById('cosmic-fullscreen-btn');
  const progContainer = document.getElementById('cosmic-progress-container');
  const videoEl = document.getElementById('cosmic-video-element');

  if (videoEl) {
    videoEl.addEventListener('timeupdate', () => {
      const cur = videoEl.currentTime;
      const dur = videoEl.duration || 0;
      if (dur > 0) {
        document.getElementById('cosmic-progress-bar').style.width = `${(cur / dur) * 100}%`;
      }
      document.getElementById('cosmic-time-current').textContent = formatTime(cur);
      document.getElementById('cosmic-time-duration').textContent = formatTime(dur);
    });

    videoEl.addEventListener('loadedmetadata', () => {
      document.getElementById('cosmic-time-duration').textContent = formatTime(videoEl.duration);
    });
  }

  playBtn?.addEventListener('click', () => {
    if (videoEl.paused) {
      videoEl.play();
      playBtn.textContent = '⏸';
    } else {
      videoEl.pause();
      playBtn.textContent = '▶';
    }
  });

  stopBtn?.addEventListener('click', () => {
    videoEl.pause();
    videoEl.currentTime = 0;
    playBtn.textContent = '▶';
  });

  volSlider?.addEventListener('input', (e) => {
    videoEl.volume = e.target.value;
    if (muteBtn) muteBtn.textContent = e.target.value === '0' ? '🔇' : '🔊';
  });

  muteBtn?.addEventListener('click', () => {
    if (videoEl.muted) {
      videoEl.muted = false;
      volSlider.value = videoEl.volume;
      muteBtn.textContent = '🔊';
    } else {
      videoEl.muted = true;
      volSlider.value = 0;
      muteBtn.textContent = '🔇';
    }
  });

  speedSel?.addEventListener('change', (e) => {
    videoEl.playbackRate = parseFloat(e.target.value);
  });

  progContainer?.addEventListener('click', (e) => {
    const rect = progContainer.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    videoEl.currentTime = pct * videoEl.duration;
  });

  fullBtn?.addEventListener('click', () => {
    const wrapper = document.getElementById('cosmic-video-wrapper');
    if (!document.fullscreenElement) {
      wrapper.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen();
    }
  });
}

function formatTime(sec) {
  if (isNaN(sec)) return '0:00';
  const mins = Math.floor(sec / 60);
  const secs = Math.floor(sec % 60);
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

function loadCosmicVideo(url, title = null) {
  // Clear existing HLS or frames
  const embed = document.getElementById('cosmic-embed-player');
  const videoWrapper = document.getElementById('cosmic-video-wrapper');
  const placeholder = document.getElementById('cosmic-player-placeholder');
  const videoEl = document.getElementById('cosmic-video-element');
  const glow = document.getElementById('cosmic-ambient-glow');

  embed.classList.add('hidden');
  embed.src = '';
  videoWrapper.classList.add('hidden');
  videoEl.pause();
  videoEl.src = '';
  placeholder.classList.add('hidden');

  if (cosmicHls) {
    cosmicHls.destroy();
    cosmicHls = null;
  }

  // Parse URL
  const parsed = parseVideoUrl(url);
  const resolvedTitle = title || parsed.defaultTitle;
  
  document.getElementById('now-playing-title').textContent = resolvedTitle;

  const colors = {
    youtube: 'radial-gradient(circle, rgba(255, 0, 0, 0.15) 0%, transparent 60%)',
    vk: 'radial-gradient(circle, rgba(74, 118, 168, 0.15) 0%, transparent 60%)',
    rutube: 'radial-gradient(circle, rgba(235, 95, 30, 0.15) 0%, transparent 60%)',
    direct: 'radial-gradient(circle, rgba(121, 40, 202, 0.15) 0%, transparent 60%)'
  };
  glow.style.background = colors[parsed.provider] || colors.direct;

  if (parsed.type === 'embed') {
    embed.src = parsed.embedUrl;
    embed.classList.remove('hidden');
  } else if (parsed.type === 'html5') {
    videoWrapper.classList.remove('hidden');
    if (url.includes('.m3u8')) {
      if (typeof Hls !== 'undefined' && Hls.isSupported()) {
        cosmicHls = new Hls();
        cosmicHls.loadSource(url);
        cosmicHls.attachMedia(videoEl);
        cosmicHls.on(Hls.Events.MANIFEST_PARSED, () => videoEl.play());
      } else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
        videoEl.src = url;
        videoEl.play();
      }
    } else {
      videoEl.src = url;
      videoEl.play();
    }
  } else {
    // Iframe fallback
    embed.src = url;
    embed.classList.remove('hidden');
  }

  // Save to history list
  addToCosmicHistory(url, resolvedTitle, parsed.provider);
}

function parseVideoUrl(url) {
  const ytReg = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
  const ytMatch = url.match(ytReg);
  if (ytMatch) {
    return {
      provider: 'youtube',
      type: 'embed',
      embedUrl: `https://www.youtube.com/embed/${ytMatch[1]}?autoplay=1&rel=0`,
      defaultTitle: `YouTube (${ytMatch[1]})`
    };
  }

  const vkReg = /vk\.com\/video(-?\d+)_(\d+)/;
  const vkMatch = url.match(vkReg);
  if (vkMatch) {
    return {
      provider: 'vk',
      type: 'embed',
      embedUrl: `https://vk.com/video_ext.php?oid=${vkMatch[1]}&id=${vkMatch[2]}&autoplay=1`,
      defaultTitle: `VK Video (${vkMatch[1]}_${vkMatch[2]})`
    };
  }

  const rutubeReg = /rutube\.ru\/(?:video|play\/embed)\/([a-f0-9]{32})/;
  const rutubeMatch = url.match(rutubeReg);
  if (rutubeMatch) {
    return {
      provider: 'rutube',
      type: 'embed',
      embedUrl: `https://rutube.ru/play/embed/${rutubeMatch[1]}?autoplay=1`,
      defaultTitle: `RuTube Video`
    };
  }

  if (url.includes('.m3u8') || url.includes('.mp4')) {
    return {
      provider: 'direct',
      type: 'html5',
      defaultTitle: url.includes('.m3u8') ? 'Поток HLS' : 'Прямой файл MP4'
    };
  }

  return {
    provider: 'direct',
    type: 'iframe_fallback',
    defaultTitle: 'Веб-фрейм'
  };
}

function addToCosmicHistory(url, title, provider) {
  cosmicHistory = cosmicHistory.filter(h => h.url !== url);
  cosmicHistory.unshift({ url, title, provider });
  if (cosmicHistory.length > 5) cosmicHistory.pop();
  localStorage.setItem('cosmic_history_chat', JSON.stringify(cosmicHistory));
  renderCosmicHistory();
}

function renderCosmicHistory() {
  const container = document.getElementById('cosmic-history-list');
  if (!container) return;
  
  if (cosmicHistory.length === 0) {
    container.innerHTML = '<div class="text-muted small text-center py-2">История пуста</div>';
    return;
  }

  container.innerHTML = cosmicHistory.map(h => `
    <div class="p-1 border rounded bg-dark small cursor-pointer text-truncate cosmic-hist-item" style="cursor:pointer; font-size:0.75rem;" data-url="${h.url}" data-title="${h.title.replace(/"/g, '&quot;')}">
      📁 [${h.provider.toUpperCase()}] ${h.title}
    </div>
  `).join('');

  container.querySelectorAll('.cosmic-hist-item').forEach(item => {
    item.addEventListener('click', () => {
      const url = item.getAttribute('data-url');
      const title = item.getAttribute('data-title');
      document.getElementById('cosmic-stream-url').value = url;
      loadCosmicVideo(url, title);
    });
  });
}

async function sendMessage() {
  const input = document.getElementById('message-input');
  const btn   = document.getElementById('send-button');
  const msg   = input.value.trim();
  if (!msg) return;
  addMessage('user', msg);
  
  input.value = '';
  btn.disabled = true; btn.textContent = 'Отправка…';


  const win = document.getElementById('chat-window');
  const botMessageEl = document.createElement('div');
  botMessageEl.className = 'message bot-message';
  botMessageEl.innerHTML = `<strong>Ai Ассистент</strong> (${new Date().toLocaleTimeString()}): <div class="bot-text">⏳ Ожидание ответа...</div>`;
  win.appendChild(botMessageEl);
  win.scrollTop = win.scrollHeight;
  const textDiv = botMessageEl.querySelector('.bot-text');

  let fullReply = '';
  let started = false;

  const modeSelector = document.getElementById('chat-mode-selector');
  const chatMode = modeSelector ? modeSelector.value : 'story';

  try {
    const replyObj = await window.chatService.sendChatMessage(msg, (chunk, status, voice) => {
      if (status) {
        textDiv.innerHTML = `<span style="color: #8b949e; font-style: italic;">⚙️ ${status}</span>`;
      }
      if (chunk) {
        if (!started) {
          textDiv.textContent = '';
          started = true;
        }
        fullReply += chunk;
        textDiv.innerHTML = parseContentToHtml(fullReply);
      }
      win.scrollTop = win.scrollHeight;
    }, chatHistory, { chat_mode: chatMode });

    const reply = replyObj.text;
    const voiceReply = replyObj.voice || reply;

    const card = tryParseMovieCard(reply);
    if (card) {
      textDiv.innerHTML = renderMovieCardHtml(card);
      window.chatService.speak(card);
    } else {
      textDiv.innerHTML = parseContentToHtml(reply);
      window.chatService.speak(voiceReply);
    }

    // Save both turns to history after successful response
    chatHistory.push({ role: 'user', parts: [msg] });
    chatHistory.push({ role: 'model', parts: [reply] });

    // Добавляем кнопку "Сохранить в RAG"
    const ragBtnContainer = document.createElement('div');
    ragBtnContainer.className = 'mt-2 text-end';
    
    const ragBtn = document.createElement('button');
    ragBtn.className = 'btn btn-sm btn-outline-secondary';
    ragBtn.innerHTML = '💾 Сохранить в RAG';
    ragBtn.onclick = async () => {
      ragBtn.disabled = true;
      ragBtn.innerHTML = '⏳ Сохранение...';
      try {
        const r = await fetch('/api/chat/save-rag', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ query: msg, chat_text: reply, voice_text: voiceReply })
        });
        if (r.ok) {
          ragBtn.innerHTML = '✅ Сохранено';
          ragBtn.classList.remove('btn-outline-secondary');
          ragBtn.classList.add('btn-success');
        } else {
          const errData = await r.json().catch(() => ({}));
          alert('Ошибка при сохранении в RAG: ' + (errData.detail || r.statusText));
          ragBtn.innerHTML = '❌ Ошибка';
          ragBtn.disabled = false;
        }
      } catch (err) {
        alert('Ошибка сети: ' + err.message);
        ragBtn.innerHTML = '❌ Ошибка сети';
        ragBtn.disabled = false;
      }
    };
    ragBtnContainer.appendChild(ragBtn);
    botMessageEl.appendChild(ragBtnContainer);

    if (typeof fullReply === 'string' && !card) {
      await parseFilmTags(fullReply);
    }
  } catch (err) {
    if (!started) {
      textDiv.textContent = '';
    }
    let errText;
    if (err instanceof Error) {
      errText = err.message;
    } else if (typeof err === 'object' && err !== null) {
      errText = JSON.stringify(err);
    } else {
      errText = String(err);
    }
    textDiv.innerHTML = `<span style="color: #ff7070;">Ошибка: ${errText}</span>`;
  }
  finally { btn.disabled = false; btn.textContent = 'Отправить'; }
}

function tryParseMovieCard(text) {
  const trimmed = text.trim();
  if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
    try {
      const data = JSON.parse(trimmed);
      if (data.title || data.title_ru) return data;
    } catch (e) {}
  }
  const match = text.match(/\{[\s\S]*?\}/);
  if (match) {
    try {
      const data = JSON.parse(match[0]);
      if (data.title || data.title_ru) return data;
    } catch (e) {}
  }
  return null;
}

function renderMovieCardHtml(card) {
  const title = card.title_ru || card.title;
  const subtitle = card.title_orig || '';
  const year = card.year || '';
  const category = card.main_category || '';
  const genres = card.genres ? card.genres.join(', ') : '';
  const directors = card.directors ? card.directors.join(', ') : '';
  const cast = card.cast ? card.cast.slice(0, 5).join(', ') : '';
  const plot = card.plot || '';
  const whyWatch = card.why_watch || '';
  
  let ratingHtml = '';
  if (card.rating) {
    if (card.rating.imdb) ratingHtml += `<span class="badge bg-warning text-dark me-1">IMDb: ${card.rating.imdb}</span>`;
    if (card.rating.кинопоиск) ratingHtml += `<span class="badge bg-danger text-white me-1">КП: ${card.rating.кинопоиск}</span>`;
    if (card.rating.tmdb) ratingHtml += `<span class="badge bg-primary text-white">TMDB: ${card.rating.tmdb}</span>`;
  }

  return `
    <div class="p-3 text-white card-media-custom" style="border-radius: 10px; background: rgba(88, 166, 255, 0.08); border: 1px solid rgba(88, 166, 255, 0.2); max-width: 480px; margin-top: 10px;">
      <h5 class="mb-1 text-info">${title}</h5>
      <div class="small text-muted mb-2">${subtitle} ${year ? `(${year})` : ''}</div>
      <div class="mb-2">${ratingHtml}</div>
      ${category ? `<div class="small text-muted mb-1" style="font-size: 0.8rem;"><strong>Категория:</strong> ${category}</div>` : ''}
      ${genres ? `<div class="small text-muted mb-1" style="font-size: 0.8rem;"><strong>Жанры:</strong> ${genres}</div>` : ''}
      ${directors ? `<div class="small text-muted mb-1" style="font-size: 0.8rem;"><strong>Режиссер:</strong> ${directors}</div>` : ''}
      ${cast ? `<div class="small text-muted mb-2" style="font-size: 0.8rem;"><strong>В ролях:</strong> ${cast}...</div>` : ''}
      ${plot ? `<p class="small text-secondary mb-2" style="font-size: 0.85rem; line-height: 1.4;">${plot}</p>` : ''}
      ${whyWatch ? `<div class="small text-info mb-2" style="font-size: 0.8rem;"><strong>Рекомендация:</strong> ${whyWatch}</div>` : ''}
      <div class="d-flex justify-content-end mt-2">
        <button class="btn btn-sm btn-primary rounded-pill px-3" onclick="playMovieDirect('${title.replace(/'/g, "\\'")}')">
          <i class="bi bi-play-fill"></i> Запустить фильм
        </button>
      </div>
    </div>
  `;
}

window.playMovieDirect = async (title) => {
  try {
    const r = await fetch('/api/media/by-title', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({title})
    });
    if (r.ok) {
      const data = await r.json();
      if (data.path) {
        // Expand player bar
        const body = document.getElementById('media-player-body');
        const btn = document.getElementById('btn-toggle-player-body');
        body.classList.remove('d-none');
        btn.textContent = 'Свернуть плеер';
        
        // Load direct stream or file path
        const streamUrl = `/api/media/stream?path=${encodeURIComponent(data.path)}`;
        loadCosmicVideo(streamUrl, data.title || title);
      } else {
        alert(`Файл для фильма "${title}" не найден.`);
      }
    }
  } catch (e) {
    console.error(e);
  }
};

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
  return replaceFilmTagsWithLinks(html);
}

function addMessage(sender, text) {
  const win = document.getElementById('chat-window');
  const el  = document.createElement('div');
  el.className = 'message ' + (sender === 'user' ? 'user-message' : 'bot-message');
  
  let displayText;
  if (typeof text === 'object' && text !== null) {
    displayText = window.chatService.formatMessage(text);
  } else {
    displayText = parseContentToHtml(text);
  }
  
  el.innerHTML = `<strong>${sender === 'user' ? 'Вы' : 'Бот'}</strong> (${new Date().toLocaleTimeString()}): ${displayText}`;
  win.appendChild(el); win.scrollTop = win.scrollHeight;
}

// ── Film Tag Parsing & Media Player ───────────────────────────────────────────

const FILM_TAG_REGEX = /<film>(.*?)<\/film>/gi;

function replaceFilmTagsWithLinks(text) {
  if (!text) return '';
  return text.replace(FILM_TAG_REGEX, (match, title) => {
    const cleanTitle = title.replace(/'/g, "\\'");
    return `<span class="badge bg-primary film-inline-badge cursor-pointer" onclick="playMovieDirect('${cleanTitle}')" style="cursor: pointer; font-size: 0.95em; padding: 0.35em 0.65em; margin: 0 2px; border: 1px solid rgba(255,255,255,0.15); transition: background-color 0.2s;"><i class="bi bi-play-fill"></i> ${title}</span>`;
  });
}

async function parseFilmTags(text) {
  const matches = [...text.matchAll(FILM_TAG_REGEX)];
  if (matches.length === 0) return;

  // Показываем только первый найденный фильм
  const filmTitle = matches[0][1].trim();
  await findAndShowMedia(filmTitle);
}

async function findAndShowMedia(title) {
  try {
    const r = await fetch('/api/media/by-title', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({title})
    });
    if (!r.ok) return;
    const data = await r.json();
    if (!data.path) return;

    currentMediaPath = data.path;
    const controls = document.getElementById('media-controls');
    document.getElementById('now-playing-title').textContent = data.title || title;
    controls.classList.remove('d-none');
    
    // Automatically trigger toggle for previewing
    const body = document.getElementById('media-player-body');
    const btn = document.getElementById('btn-toggle-player-body');
    body.classList.remove('d-none');
    btn.textContent = 'Свернуть плеер';
    
    const streamUrl = `/api/media/stream?path=${encodeURIComponent(data.path)}`;
    loadCosmicVideo(streamUrl, data.title || title);
  } catch (e) {
    console.error('findAndShowMedia:', e);
  }
}

function openMediaPlayer() {
  if (!currentMediaPath) return;
  // Открываем в новой вкладке с локальным плеером
  const encoded = encodeURIComponent(currentMediaPath);
  window.open(`/html/player/index.html?file=${encoded}`, '_blank');
}

function closeMediaControls() {
  const controls = document.getElementById('media-controls');
  controls.classList.add('d-none');
  currentMediaPath = null;
}
