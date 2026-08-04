# browser-extension-simple-chat

Минимальное браузерное расширение — чат с локальным AI через `http://localhost:9696`.

## Установка

1. Открыть `chrome://extensions/`
2. Включить **Developer mode**
3. **Load unpacked** → выбрать папку `browser-extension-simple-chat`

## Использование

- Нажать иконку расширения → откроется чат
- Выбрать модель из списка (загружается с `/api/v1/models`)
- Писать сообщения, Enter — отправить, Shift+Enter — новая строка

## Требования

Запущенный FastAPI AI Assistant на `http://localhost:9696`.

## API

Использует только `POST /api/v1/ai/chat` с телом:
```json
{
  "messages": [{"role": "user", "content": "..."}],
  "model": "foundry::model-id"
}
```
