# Архитектура расширения

## Разделение ответственности

```
popup.html / popup.js
  └── Показывает активный провайдер и модель
  └── Кнопки: Chat, Providers & Models, Server Debug

providers.html / providers-page.js
  └── Управление API-ключами и моделями
  └── Выбор языка суммаризации
  └── Экспорт / Импорт конфигурации

chat.html / chat.js
  └── Интерактивный чат с AI-моделью
  └── История сообщений в памяти (контекст)
  └── Открытие результатов factcheck и summary

debug.html / debug.js
  └── Тестирование endpoints FastAPI Foundry
  └── Произвольные HTTP-запросы к серверу

background.js  (Service Worker)
  └── Контекстное меню (Summarise, Check This Fact)
  └── Создание и обновление job-объектов в storage
  └── Оркестрация суммаризации: extractPageText → summarizePage → patchJob

summarizer.js
  └── Выбор промпта по языку (prompts/index.js)
  └── Обрезка текста до 80 000 символов
  └── Маршрутизация запроса в нужный коннектор

connectors/
  ├── gemini.js         — Gemini API (ключ в query, формат contents/parts)
  ├── openrouter.js     — OpenRouter (reasoning: {enabled: true})
  └── openai-compat.js  — Все остальные провайдеры (OpenAI-совместимые)
```

## Поток данных — суммаризация страницы

```
Пользователь: правый клик → Summarise → Only This Page
        │
        ▼
background.js: handleSummarizePage(tab)
  ├── createJob('single', 1)          → chrome.storage.local: job_<ts>
  ├── UIManager.openSummaryTab(jobId) → открывает summary.html?job=job_<ts>
  ├── extractPageText(tabId)          → chrome.scripting.executeScript
  ├── summarizePage(text, ...)        → summarizer.js → connector → API
  └── patchJob(jobId, {status:'done', finalSummary})
        │
        ▼
summary.js (polling каждые 800мс)
  └── chrome.runtime.sendMessage({action:'getJob'})
  └── рендерит прогресс и финальный результат
```

## Поток данных — суммаризация всех вкладок

```
background.js: handleSummarizeAllTabs()
  ├── chrome.tabs.query({})           → список всех http/https вкладок
  ├── createJob('multi', N)
  ├── UIManager.openSummaryTab(jobId)
  │
  └── Promise.allSettled(tabs.map(tab =>
        extractPageText(tab.id)
        → summarizePage(text, ...)    ← параллельно для каждой вкладки
        → patchJob(tabs[i].status)
      ))
        │
        ▼
  mergeSummaries(successful, ...)     → один финальный запрос к API
  patchJob({status:'done', finalSummary})
```

## Поток данных — чат

```
chat.js: init()
  ├── loadModelSelector()             → chrome.storage.sync → заполняет <select>
  ├── (если ?factcheck=jobId)         → polling storage → показывает результат
  │
  └── handleSend()
        ├── messages.push({role:'user', content})
        ├── sendToAPI(messages)       → connector напрямую (без summarizer.js)
        └── appendMessage('assistant', reply)
```

## Хранилище — схема

| Ключ | Хранилище | Тип | Описание |
|---|---|---|---|
| `activeProvider` | sync | string | ID активного провайдера |
| `activeModel` | sync | string | ID активной модели |
| `activeKeyIndex` | sync | `{[providerId]: number}` | Индекс активного ключа |
| `providerKeys` | sync | `{[providerId]: string[]}` | API-ключи по провайдерам |
| `customModels` | sync | `{[providerId]: {id,label}[]}` | Модели добавленные вручную |
| `summaryLang` | sync | string | Язык суммаризации (`auto`, `en`, `ru`…) |
| `summaryProvider` | sync | string | Оверрайд провайдера для суммаризации |
| `summaryModel` | sync | string | Оверрайд модели для суммаризации |
| `uiLang` | sync | string | Язык UI расширения (`en`, `ru`, `he`) |
| `debugBaseUrl` | sync | string | URL сервера в debug-вкладке |
| `debugApiKey` | sync | string | API-ключ в debug-вкладке |
| `providerModels` | local | `{[providerId]: {id,label}[]}` | Кэш моделей из API |
| `job_<timestamp>` | local | Job | Данные задачи суммаризации |

### Структура Job

```json
{
  "mode": "single | multi | factcheck",
  "status": "running | merging | done | error",
  "total": 3,
  "done": 2,
  "tabs": [
    { "title": "Page title", "url": "https://...", "status": "done", "summary": "..." }
  ],
  "finalSummary": "<p>...</p>",
  "selection": "выделенный текст (только для factcheck)",
  "error": null,
  "createdAt": 1700000000000
}
```

## Manifest V3 — ключевые решения

**Service Worker вместо background page** — MV3 требует service worker. Он может быть приостановлен браузером. Поэтому `summary.js` использует `chrome.runtime.sendMessage` для polling — сообщение будит service worker если он спит.

**ES Modules в service worker** — `"type": "module"` в `manifest.json` позволяет использовать `import/export` в `background.js`. Это единственный способ разделить код на модули без сборщика.

**Статические импорты в prompts** — динамический `import()` ненадёжен в MV3 service worker. Все промпты импортируются статически в `prompts/index.js`.

**`chrome.storage.sync` для ключей** — ключи переживают переустановку расширения и синхронизируются между устройствами через аккаунт Chrome. Лимит: 8 KB на ключ, 100 KB суммарно.

**`chrome.storage.local` для кэша и job** — модели и данные задач большие (до нескольких MB). Лимит local: 10 MB.
