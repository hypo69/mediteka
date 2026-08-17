// Background service worker for Remote Stream Controller

const PLAYER_URL = 'https://example.com/player.html'; // Замените на ваш URL плеера
const PLAYER_TAB_NAME = 'StreamPlayer';

let serverConnection = null;
let playerTabId = null;

// Проверяет, открыта ли уже вкладка с плеером
async function findExistingPlayerTab() {
  const tabs = await chrome.tabs.query({});
  
  for (const tab of tabs) {
    if (tab.url && tab.url.includes('player.html')) {
      console.log('Found existing player tab:', tab.id, tab.url);
      return tab.id;
    }
  }
  
  return null;
}

// Открывает новую вкладку с плеером или возвращает существующую
async function ensurePlayerTab() {
  playerTabId = await findExistingPlayerTab();
  
  if (playerTabId) {
    // Вкладка найдена, активируем её
    await chrome.tabs.update(playerTabId, { active: true });
    return playerTabId;
  }
  
  // Создаем новую вкладку
  const createProperties = {
    url: PLAYER_URL,
    active: true
  };
  
  const tab = await chrome.tabs.create(createProperties);
  playerTabId = tab.id;
  
  console.log('Created new player tab:', playerTabId);
  
  return playerTabId;
}

// Отправляет команду плееру на запуск стрима
async function startStream(videoUrl) {
  try {
    playerTabId = await ensurePlayerTab();
    
    // Ждем, пока страница загрузится
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Инъецируем код для запуска стрима
    await chrome.scripting.executeScript({
      target: { tabId: playerTabId },
      func: (videoUrl) => {
        // Пытаемся найти видеоэлемент на странице
        const video = document.querySelector('video');
        
        if (video) {
          video.src = videoUrl;
          video.play().then(() => {
            console.log('Stream started successfully');
          }).catch(err => {
            console.error('Error playing stream:', err);
          });
        } else {
          console.error('Video element not found');
        }
      },
      args: [videoUrl]
    });
    
    console.log('Stream command sent to tab:', playerTabId);
    return { success: true, tabId: playerTabId };
  } catch (error) {
    console.error('Error starting stream:', error);
    return { success: false, error: error.message };
  }
}

// Обработка сообщений от popup или других частей расширения
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Received message:', message);
  
  if (message.action === 'startStream') {
    startStream(message.videoUrl).then(result => {
      sendResponse(result);
    });
    return true; // Ответ будет асинхронным
  }
  
  if (message.action === 'getPlayerTabId') {
    sendResponse({ tabId: playerTabId });
  }
  
  if (message.action === 'checkPlayerTab') {
    findExistingPlayerTab().then(tabId => {
      sendResponse({ found: tabId !== null, tabId: tabId });
    });
    return true;
  }
});

// Обработка когда вкладка закрывается
chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
  if (tabId === playerTabId) {
    console.log('Player tab closed, resetting playerTabId');
    playerTabId = null;
  }
});

// Подключение к серверу для получения команд (пример с WebSocket)
async function connectToServer() {
  const SERVER_URL = 'ws://localhost:8080/stream-control';
  
  try {
    // Для демонстрации - можно заменить на реальный WebSocket или HTTP polling
    console.log('Server connection initialized');
    
    // Пример эмуляции получения команды от сервера
    // В реальном приложении здесь будет WebSocket соединение
    /*
    serverConnection = new WebSocket(SERVER_URL);
    
    serverConnection.onmessage = (event) => {
      const command = JSON.parse(event.data);
      
      if (command.type === 'start_stream') {
        startStream(command.videoUrl);
      }
    };
    
    serverConnection.onopen = () => {
      console.log('Connected to server');
    };
    
    serverConnection.onerror = (error) => {
      console.error('Server connection error:', error);
    };
    */
    
  } catch (error) {
    console.error('Server connection failed:', error);
  }
}

// Инициализация при запуске
chrome.runtime.onInstalled.addListener(() => {
  console.log('Remote Stream Controller installed');
  connectToServer();
});

console.log('Background script loaded');
