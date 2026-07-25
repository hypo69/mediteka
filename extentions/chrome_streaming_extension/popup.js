// Popup script для управления стримом

const videoUrlInput = document.getElementById('videoUrl');
const startStreamBtn = document.getElementById('startStreamBtn');
const checkPlayerBtn = document.getElementById('checkPlayerBtn');
const refreshPlayerBtn = document.getElementById('refreshPlayerBtn');
const statusDiv = document.getElementById('status');
const playerStatusDiv = document.getElementById('playerStatus');
const connectionStatusDiv = document.getElementById('connectionStatus');

// Проверка вкладки плеера при загрузке
document.addEventListener('DOMContentLoaded', () => {
  checkPlayerTab();
  checkServerConnection();
});

// Проверка существующей вкладки плеера
function checkPlayerTab() {
  chrome.runtime.sendMessage({ action: 'checkPlayerTab' }, (response) => {
    if (response && response.found) {
      playerStatusDiv.innerHTML = `Вкладка плеера: <span>открыта (ID: ${response.tabId})</span>`;
      statusDiv.textContent = 'Вкладка плеера найдена';
      statusDiv.className = 'success';
    } else {
      playerStatusDiv.innerHTML = 'Вкладка плеера: <span>не открыта</span>';
      statusDiv.textContent = 'Вкладка плеера не найдена. Нажмите "Запустить стрим" для открытия.';
      statusDiv.className = 'info';
    }
  });
}

// Проверка подключения к серверу
function checkServerConnection() {
  // Здесь можно добавить реальную проверку подключения к серверу
  connectionStatusDiv.textContent = 'Сервер: готов (демо режим)';
}

// Запуск стрима
startStreamBtn.addEventListener('click', () => {
  const videoUrl = videoUrlInput.value.trim();
  
  if (!videoUrl) {
    statusDiv.textContent = 'Введите URL видео стрима';
    statusDiv.className = 'error';
    return;
  }
  
  statusDiv.textContent = 'Отправка команды...';
  statusDiv.className = 'info';
  startStreamBtn.disabled = true;
  
  chrome.runtime.sendMessage({ 
    action: 'startStream', 
    videoUrl: videoUrl 
  }, (response) => {
    startStreamBtn.disabled = false;
    
    if (response && response.success) {
      statusDiv.textContent = `Стрим запущен! Вкладка: ${response.tabId}`;
      statusDiv.className = 'success';
      checkPlayerTab();
    } else {
      statusDiv.textContent = `Ошибка: ${response.error || 'Неизвестная ошибка'}`;
      statusDiv.className = 'error';
    }
  });
});

// Проверка плеера
checkPlayerBtn.addEventListener('click', () => {
  statusDiv.textContent = 'Проверка вкладки плеера...';
  statusDiv.className = 'info';
  
  setTimeout(checkPlayerTab, 500);
});

// Обновление плеера
refreshPlayerBtn.addEventListener('click', () => {
  chrome.runtime.sendMessage({ action: 'refreshPlayer' }, (response) => {
    if (response && response.success) {
      statusDiv.textContent = 'Плеер обновлен';
      statusDiv.className = 'success';
    } else {
      statusDiv.textContent = 'Ошибка обновления плеера';
      statusDiv.className = 'error';
    }
  });
});

// Валидация URL при вводе
videoUrlInput.addEventListener('input', () => {
  const url = videoUrlInput.value.trim();
  
  if (url) {
    try {
      new URL(url);
      videoUrlInput.style.borderColor = '#28a745';
    } catch (e) {
      videoUrlInput.style.borderColor = '#dc3545';
    }
  } else {
    videoUrlInput.style.borderColor = '#ddd';
  }
});
