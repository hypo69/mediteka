# AI Assistant — Summarizer

Chrome-расширение (Manifest V3) для суммаризации веб-страниц и чата с AI-моделями. Поддерживает 12 LLM-провайдеров, несколько API-ключей на провайдера, выбор языка вывода и экспорт/импорт конфигурации.

## Возможности

- **Only This Page** — суммаризация текущей вкладки
- **All Open Tabs** — параллельная суммаризация всех вкладок с иерархическим объединением результатов
- **Chat** — интерактивный чат с любой из настроенных моделей
- **12 провайдеров** — Gemini, OpenAI, OpenRouter, Anthropic, Mistral, Groq, Cohere, DeepSeek, xAI, NVIDIA NIM, Custom (OpenAI-compatible), **AI Assistant (FastAPI Foundry)**
- **Несколько API-ключей** на провайдера — ротация, разные проекты
- **Выбор языка** саммари — Auto, English, Русский, Deutsch, Français, Español, 中文, 日本語
- **Экспорт / Импорт** конфигурации в JSON (включая все ключи и модели)
- Отображение прогресса в реальном времени для каждой вкладки
- Копирование итогового саммари в буфер обмена
- Настройки переживают переустановку расширения (`chrome.storage.sync`)

## Структура проекта

```
browser-extention-summarizer/
├── manifest.json          — MV3: разрешения, service worker, popup
├── background.js          — Service worker: контекстное меню, оркестрация задач
├── summarizer.js          — Логика суммаризации: промпты, обрезка текста, маршрутизация
├── providers.js           — Реестр провайдеров: метаданные, fetchModels()
├── logger.js              — Логгер: запись в chrome.storage.local
├── ui-manager.js          — Открытие вкладок summary, индикаторы на странице
│
├── connectors/            — Транспортный слой: только HTTP к API
│   ├── gemini.js          — Google Gemini (формат contents/parts, ключ в query)
│   ├── openrouter.js      — OpenRouter (reasoning: {enabled: true})
│   └── openai-compat.js   — Универсальный OpenAI-совместимый клиент
│
├── prompts/               — Промпты суммаризации по языкам
│   ├── index.js           — Реестр языков (LANGUAGES) и getPrompts(lang)
│   ├── en.js              — English
│   ├── ru.js              — Русский
│   ├── de.js              — Deutsch
│   ├── fr.js              — Français
│   ├── es.js              — Español
│   ├── zh.js              — 中文
│   └── ja.js              — 日本語
│
├── popup.html / popup.js  — Popup: активный провайдер/модель, кнопки Chat и Providers
├── providers.html         — Страница настройки провайдеров (открывается в новой вкладке)
├── providers-page.js      — UI провайдеров: ключи, модели, язык, экспорт/импорт
├── summary.html           — Страница прогресса и результата суммаризации
├── summary.js             — Polling storage каждые 800 мс, рендер прогресса
├── chat.html / chat.js    — Чат с AI-моделью
│
├── css/
│   └── summary.css        — Стили страницы результата
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── _locales/
    ├── en/messages.json
    └── ru/messages.json
```

## Архитектура

### Разделение ответственности

```
popup.html/js
  └── показывает активный провайдер/модель
  └── открывает providers.html и chat.html

providers.html / providers-page.js
  └── управление ключами и моделями провайдеров
  └── выбор языка саммари
  └── экспорт / импорт конфигурации

background.js (service worker)
  └── читает настройки через getSettings()
  └── создаёт job в chrome.storage.local
  └── вызывает summarizer.js

summarizer.js
  └── выбирает промпт по языку из prompts/
  └── обрезает текст до 80 000 символов
  └── маршрутизирует запрос в нужный коннектор

connectors/
  ├── gemini.js        — Gemini API (нестандартный формат)
  ├── openrouter.js    — OpenRouter (reasoning)
  └── openai-compat.js — все остальные провайдеры

summary.js
  └── polling chrome.runtime.sendMessage каждые 800 мс
  └── рендерит прогресс и финальный результат

chat.js
  └── история сообщений в памяти
  └── вызывает коннекторы напрямую (без summarizer.js)
```

### Хранилище

| Ключ | Хранилище | Описание |
|---|---|---|
| `providerKeys` | `sync` | API-ключи всех провайдеров `{ gemini: ['key1', ...], ... }` |
| `customModels` | `sync` | Модели добавленные вручную |
| `activeProvider` | `sync` | ID активного провайдера |
| `activeModel` | `sync` | ID активной модели |
| `activeKeyIndex` | `sync` | Индекс активного ключа на провайдера |
| `summaryLang` | `sync` | Язык саммари (`auto`, `en`, `ru`, ...) |
| `providerModels` | `local` | Кэш загруженных через API моделей |
| `job_<timestamp>` | `local` | Данные задачи суммаризации |

`sync` — переживает переустановку расширения и синхронизируется между устройствами через аккаунт Chrome.  
`local` — только на текущем устройстве, большой объём (до 10 MB).

## Как работает суммаризация

### Only This Page

1. Открывается `summary.html?job=job_<timestamp>`
2. Из вкладки извлекается очищенный текст (удаляются `script`, `style`, `nav`, `header`, `footer`, реклама)
3. Текст обрезается до 80 000 символов если превышает лимит
4. Один запрос к активной модели → результат отображается на странице

### All Open Tabs — иерархическая суммаризация

```
Вкладка 1 ──┐
Вкладка 2 ──┼──► мини-саммари × N ──► финальный merge-запрос ──► результат
Вкладка N ──┘
     (параллельно, Promise.allSettled)
```

1. Открывается `summary.html` — пользователь видит прогресс в реальном времени
2. Все вкладки суммаризируются **параллельно** — ошибка одной не прерывает остальные
3. Финальный запрос объединяет мини-саммари в один связный текст
4. Если успешная вкладка одна — merge-запрос не делается

Статусы вкладки: `Pending → Extracting → Summarizing → Done / Skipped / Error`

## Провайдеры

| Провайдер | Base URL | API Key | Особенности |
|---|---|---|---|
| Google Gemini | `generativelanguage.googleapis.com` | ✅ | Ключ в query-параметре `?key=`, формат `contents/parts` |
| OpenAI | `api.openai.com/v1` | ✅ | Стандарт OpenAI |
| OpenRouter | `openrouter.ai/api/v1` | ✅ | Агрегатор, поддержка `reasoning: {enabled: true}` |
| Anthropic | `api.anthropic.com/v1` | ✅ | Заголовок `x-api-key`, обязательный `anthropic-version` |
| Mistral AI | `api.mistral.ai/v1` | ✅ | OpenAI-совместимый |
| Groq | `api.groq.com/openai/v1` | ✅ | OpenAI-совместимый, быстрый inference |
| Cohere | `api.cohere.com/v2` | ✅ | Отличается форматом ошибок |
| DeepSeek | `api.deepseek.com` | ✅ | OpenAI-совместимый |
| xAI Grok | `api.x.ai/v1` | ✅ | OpenAI-совместимый |
| NVIDIA NIM | `integrate.api.nvidia.com/v1` | ✅ | Требует `stream: false` |
| Custom | задаётся вручную | ❌ | Любой OpenAI-совместимый endpoint (Ollama, vLLM и др.) |
| **AI Assistant** | `localhost:9696/v1` | **❌** | **FastAPI Foundry — локальный оркестратор AI (Foundry, HuggingFace, llama.cpp, Ollama, LM Studio)** |

## Настройка провайдеров

1. Открыть popup расширения → нажать **⚙️ Providers & Models**
2. Найти нужного провайдера → ввести API-ключ → нажать **+ Add key**
3. Нажать **Load models** — список моделей загрузится через API провайдера
4. Кликнуть на нужную модель — она появится в строке ключа
5. Нажать **Set Active** — пара ключ→модель становится активной

Можно добавить несколько ключей на одного провайдера (ротация, разные проекты).  
Модели можно добавить вручную через поле **Add model ID manually**.

## Язык саммари

На странице Providers & Models выбирается язык вывода саммари:

| Значение | Поведение |
|---|---|
| `Auto` | Модель отвечает на языке исходного контента страницы |
| `English`, `Русский`, ... | Саммари всегда на выбранном языке |

Промпты для каждого языка хранятся в `prompts/*.js`. Добавить новый язык — создать файл `prompts/xx.js` и добавить одну строку в `prompts/index.js`.

## Экспорт / Импорт конфигурации

На странице Providers & Models доступны кнопки **Export** и **Import**.

**Экспорт** сохраняет в JSON:
- все API-ключи всех провайдеров (в открытом виде — будет предупреждение)
- кастомные модели
- активный провайдер, модель, индекс ключа
- язык саммари
- кэш загруженных моделей

**Импорт** полностью заменяет текущую конфигурацию данными из файла.

> ⚠️ Файл экспорта содержит API-ключи в открытом виде. Не публикуйте его и не передавайте по незащищённым каналам.

## Чат

Кнопка **💬 Chat** в popup открывает страницу чата в новой вкладке.

- Выбор модели из всех настроенных провайдеров (сгруппировано по провайдеру)
- История сообщений передаётся в каждом запросе — модель помнит контекст
- `Enter` — отправить, `Shift+Enter` — новая строка
- **Clear chat** — очистить историю

## Первый запуск

1. Открыть `chrome://extensions/`
2. Включить **Режим разработчика**
3. Нажать **Загрузить распакованное расширение** → выбрать папку `browser-extention-summarizer`
4. Нажать иконку расширения → **⚙️ Providers & Models**
5. Добавить API-ключ нужного провайдера, загрузить модели, выбрать активную пару
6. Кликнуть правой кнопкой на любой странице → **Summarise** → выбрать режим

## Разрешения

| Разрешение | Назначение |
|---|---|
| `contextMenus` | Пункт меню «Summarise» |
| `activeTab` | Доступ к текущей вкладке |
| `tabs` | Список всех вкладок для режима All Tabs |
| `scripting` | Извлечение текста со страниц |
| `storage` | Хранение настроек и данных задач |
| `notifications` | Уведомления об ошибках |
| `host_permissions: <all_urls>` | Извлечение текста с любых сайтов |
| `host_permissions: *.googleapis.com` и др. | Запросы к API провайдеров |

## Технологии

- **Chrome Extension Manifest V3** — service worker, ES modules
- **Vanilla JavaScript** — без сборщиков и npm-зависимостей
- **ES Modules** (`type: module` в manifest) — нативные импорты в service worker
- **chrome.storage.sync** — настройки и ключи (переживают переустановку)
- **chrome.storage.local** — кэш моделей и данные задач (большой объём)
- **chrome.runtime.sendMessage** — polling из summary.js будит service worker если он приостановлен
