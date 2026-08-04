# Хранилище

Схема данных `chrome.storage` в расширении browser-extension-summarizer.

## Типы хранилища

| Тип | Назначение |
|---|---|
| `chrome.storage.sync` | Настройки провайдеров, API-ключи (синхронизируются между устройствами) |
| `chrome.storage.local` | Логи, история чата (только локально) |

## Схема `storage.sync`

```json
{
  "providers": {
    "gemini": { "apiKey": "AIza...", "model": "gemini-2.0-flash" },
    "openai": { "apiKey": "sk-...", "model": "gpt-4o-mini" },
    "fastapi": { "baseUrl": "http://localhost:9696", "model": "" }
  },
  "activeProvider": "gemini",
  "language": "ru",
  "summaryMode": "page"
}
```

## Схема `storage.local`

```json
{
  "logs": [...],
  "chatHistory": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```
