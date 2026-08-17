# Chrome Stream Controller

Расширение для Chrome браузера для удаленного управления видеостримингом.

## Возможности

- Проверка существования вкладки с плеером
- Открытие новой вкладки с плеером при необходимости
- Запуск видеострима в плеере по команде с сервера
- Управление через popup интерфейс

## Структура

```
chrome_streaming_extension/
├── manifest.json      # Конфигурация расширения
├── background.js      # Service worker для управления вкладками
├── content.js         # Content script для взаимодействия со страницей
├── content.css        # Стили для content script
├── player.html        # Страница плеера
├── popup.html         # Интерфейс popup
├── popup.js           # Скрипт popup
└── README.md          # Документация
```

## Установка

1. Откройте Chrome и перейдите в `chrome://extensions/`
2. Включите "Режим разработчика"
3. Нажмите "Загрузить распакованное расширение"
4. Выберите папку `chrome_streaming_extension`

## Использование

### Через Popup интерфейс

1. Нажмите на иконку расширения в панели инструментов
2. Введите URL видео стрима
3. Нажмите "Запустить стрим"

### Через Popup (для тестирования)

1. Нажмите на иконку расширения
2. Введите URL видео стрима (например, любой MP4 URL)
3. Нажмите "Запустить стрим"

### Интеграция с сервером

Расширение ожидает команды от сервера через WebSocket или HTTP polling. В `background.js` есть пример подключения к серверу:

```javascript
const SERVER_URL = 'ws://localhost:8080/stream-control';
```

Сервер должен отправлять команды в формате:
```json
{
  "type": "start_stream",
  "videoUrl": "https://example.com/stream.mp4"
}
```

## Основные функции

### Проверка вкладки

Функция `findExistingPlayerTab()` в `background.js` проверяет все открытые вкладки и ищет ту, которая содержит `player.html` в URL.

### Управление вкладками

- Если вкладка найдена → активируется она
- Если вкладка не найдена → создается новая

### Запуск стрима

Команда `startStream(videoUrl)`:
1. Обеспечивает наличие вкладки плеера
2. Инъецирует JavaScript код для управления видеоэлементом
3. Устанавливает URL стрима и запускает воспроизведение

## Настройка

### Изменение URL плеера

В `background.js` измените:
```javascript
const PLAYER_URL = 'https://your-player-url.com/player.html';
```

### Изменение URL сервера

В `background.js` измените:
```javascript
const SERVER_URL = 'ws://your-server-url:port/stream-control';
```

## Отладка

1. Откройте `chrome://extensions/`
2. Найдите расширение "Remote Stream Controller"
3. Нажмите "service worker" для просмотра логов
4. Откройте popup для тестирования

## Разработка

Для разработки можно использовать LiveReload или автоматическую перезагрузку при изменении файлов.

### Полезные команды

- Проверка вкладки: `chrome.runtime.sendMessage({action: 'checkPlayerTab'})`
- Запуск стрима: `chrome.runtime.sendMessage({action: 'startStream', videoUrl: 'URL'})`

## Примечания

- Расширение использует Manifest V3
- Требуются разрешения: `tabs`, `storage`, `activeTab`, `scripting`, `webRequest`
- Поддерживает все URLs (`<all_urls>`)
