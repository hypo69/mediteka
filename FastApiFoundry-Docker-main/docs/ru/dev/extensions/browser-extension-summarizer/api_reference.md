# API Reference — browser-extension-summarizer

Все JS модули и экспортируемые функции расширения.

## `background.js` — Service Worker

| Функция | Описание |
|---|---|
| `handleSummarize(tab, mode)` | Запуск суммаризации для вкладки |
| `handleFactCheck(tab)` | Запуск проверки фактов |

## `summarizer.js`

| Функция | Описание |
|---|---|
| `summarizePage(text, provider, lang)` | Суммаризация текста страницы |
| `mergeChunks(chunks, provider, lang)` | Иерархическое объединение чанков |

## `providers.js`

| Функция | Описание |
|---|---|
| `getProvider(name)` | Получить провайдер по имени |
| `listProviders()` | Список всех зарегистрированных провайдеров |

## `ui-manager.js`

| Функция | Описание |
|---|---|
| `openChat()` | Открыть страницу чата |
| `openProviders()` | Открыть страницу настройки провайдеров |
| `showProgress(msg)` | Показать индикатор прогресса |

## `logger.js`

| Функция | Описание |
|---|---|
| `log(level, message, data)` | Записать в `chrome.storage.local` |
| `getLogs()` | Получить все логи |
| `clearLogs()` | Очистить логи |

## `js/i18n.js`

| Функция | Описание |
|---|---|
| `i18n(key)` | Получить строку по ключу |
| `applyI18n()` | Применить переводы к DOM |
