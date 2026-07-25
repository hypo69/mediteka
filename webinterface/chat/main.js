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
  document.getElementById('btn-open-player')?.addEventListener('click', openMediaPlayer);
  document.getElementById('btn-close-player')?.addEventListener('click', closeMediaControls);
}

// Export init function for main.js
if (typeof window !== 'undefined') {
  window.initChatTab = initChatTab;
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
    }, chatHistory);

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


    if (typeof fullReply === 'string' && !card) {
      await parseFilmTags(fullReply);
    }
  } catch (err) {
    if (!started) {
      textDiv.textContent = '';
    }
    const errText = typeof err === 'object' && err !== null ? JSON.stringify(err) : String(err);
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
        const encoded = encodeURIComponent(data.path);
        window.open(`/html/player/index.html?file=${encoded}`, '_blank');
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
