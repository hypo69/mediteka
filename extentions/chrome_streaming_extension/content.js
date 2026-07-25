// Content script для взаимодействия со страницей плеера

console.log('Content script loaded');

// Сообщает background.js что плеер готов
chrome.runtime.sendMessage({
  action: 'playerReady',
  timestamp: Date.now()
});

// Обработчики сообщений от background.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Content script received message:', message);
  
  if (message.action === 'startStream') {
    handleStartStream(message.videoUrl);
    sendResponse({ status: 'started' });
  }
  
  if (message.action === 'getVideoElement') {
    const video = document.querySelector('video');
    sendResponse({ 
      found: !!video,
      src: video ? video.src : null,
      paused: video ? video.paused : null
    });
  }
  
  return true; // Асинхронный ответ
});

// Функция обработки команды запуска стрима
function handleStartStream(videoUrl) {
  console.log('Starting stream:', videoUrl);
  
  const video = document.querySelector('video');
  
  if (video) {
    // Если источник тот же, просто воспроизводим
    if (video.src === videoUrl) {
      video.play()
        .then(() => console.log('Stream resumed'))
        .catch(err => console.error('Error resuming:', err));
      return;
    }
    
    // Устанавливаем новый источник
    video.src = videoUrl;
    
    // Пытаемся загрузить и воспроизвести
    video.load()
      .then(() => {
        console.log('Stream loaded');
        return video.play();
      })
      .then(() => {
        console.log('Stream playing');
        chrome.runtime.sendMessage({
          action: 'streamStarted',
          videoUrl: videoUrl
        });
      })
      .catch(err => {
        console.error('Error playing stream:', err);
        chrome.runtime.sendMessage({
          action: 'streamError',
          error: err.message,
          videoUrl: videoUrl
        });
      });
  } else {
    console.error('Video element not found on page');
    
    // Попытка создать видеоэлемент если его нет
    createVideoElement(videoUrl);
  }
}

// Создает видеоэлемент если его нет на странице
function createVideoElement(videoUrl) {
  console.log('Creating video element');
  
  const video = document.createElement('video');
  video.id = 'stream-player';
  video.controls = true;
  video.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 9999;
    background: black;
  `;
  
  document.body.innerHTML = ''; // Очищаем страницу
  document.body.appendChild(video);
  
  video.src = videoUrl;
  video.play()
    .then(() => console.log('New video element created and playing'))
    .catch(err => console.error('Error with new video element:', err));
}

// Мониторинг загрузки страницы
window.addEventListener('load', () => {
  console.log('Page loaded, player ready');
  
  // Уведомляем background.js
  chrome.runtime.sendMessage({
    action: 'pageLoaded',
    timestamp: Date.now()
  });
});

// Проверка готовности DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded');
  });
}
