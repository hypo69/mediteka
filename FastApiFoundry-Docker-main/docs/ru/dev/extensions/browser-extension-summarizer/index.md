# Browser Extension Summarizer

Chrome-расширение (Manifest V3) для суммаризации веб-страниц, проверки фактов и чата с AI-моделями.
Поддерживает 11 LLM-провайдеров и подключение к локальному серверу FastAPI Foundry.

## Разделы документации

| Раздел | Описание |
|---|---|
| [Архитектура](architecture.md) | Структура файлов, разделение ответственности, поток данных |
| [Установка и первый запуск](installation.md) | Загрузка расширения в Chrome, первичная настройка |
| [Провайдеры и модели](providers.md) | Настройка API-ключей, загрузка моделей, Custom провайдер |
| [Суммаризация](summarization.md) | Режимы работы, промпты, иерархическое объединение |
| [Чат](chat.md) | Интерфейс чата, история, проверка фактов |
| [Отладка сервера](debug.md) | Вкладка Server Debug, тестирование endpoints |
| [Многоязычность (i18n)](i18n.md) | Механизм переводов, добавление нового языка |
| [Стили и UI](styles.md) | Bootstrap 5, кастомные компоненты, создание новых страниц |
| [Хранилище](storage.md) | chrome.storage.sync / local, схема данных |
| [API Reference](api_reference.md) | Все JS модули, экспортируемые функции |

## Быстрый старт

```
1. chrome://extensions/ → Режим разработчика → Загрузить распакованное
2. Выбрать папку extensions/browser-extension-summarizer/
3. Popup → ⚙️ Providers & Models → добавить API-ключ
4. Правый клик на странице → Summarise → Only This Page
```

## Структура файлов

```
browser-extension-summarizer/
├── manifest.json              — MV3: разрешения, service worker, popup
├── background.js              — Service worker: меню, оркестрация задач
├── summarizer.js              — Логика суммаризации и merge
├── providers.js               — Реестр провайдеров
├── logger.js                  — Логгер в chrome.storage.local
├── ui-manager.js              — Открытие вкладок, индикаторы
│
├── connectors/
│   ├── gemini.js              — Google Gemini API
│   ├── openrouter.js          — OpenRouter API
│   └── openai-compat.js       — Универсальный OpenAI-совместимый клиент
│
├── prompts/
│   ├── index.js               — Реестр языков (LANGUAGES) и getPrompts()
│   ├── en.js / ru.js / de.js … — Промпты по языкам
│   └── factcheck.js           — Промпт проверки фактов
│
├── js/
│   └── i18n.js                — Модуль многоязычности UI
│
├── locales/
│   ├── en.json / ru.json / he.json — Строки UI по языкам
│
├── css/
│   └── theme.css              — Bootstrap 5 + кастомные компоненты
│
├── popup.html / popup.js      — Popup расширения
├── chat.html / chat.js        — Страница чата
├── providers.html             — Страница настройки провайдеров
├── providers-page.js          — Логика страницы провайдеров
├── debug.html / debug.js      — Страница отладки сервера
│
├── _locales/en/ ru/           — Chrome i18n (название расширения)
└── icons/                     — Иконки 16/48/128px
```
