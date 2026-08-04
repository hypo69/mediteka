# Суммаризация

## Режимы работы

Доступны через правый клик на странице → **Summarise**:

| Режим | Описание |
|---|---|
| **Only This Page** | Суммаризация текущей вкладки |
| **All Open Tabs** | Параллельная суммаризация всех вкладок + финальное объединение |
| **Check This Fact** | Проверка выделенного текста (через контекстное меню выделения) |

## Only This Page

```
1. Открывается summary.html?job=job_<timestamp>
2. Из вкладки извлекается очищенный текст:
   - удаляются: script, style, nav, header, footer, реклама, cookie-баннеры
   - текст обрезается до 80 000 символов если превышает лимит
3. Один запрос к активной модели
4. Результат отображается на странице
```

## All Open Tabs — иерархическая суммаризация

```
Вкладка 1 ──┐
Вкладка 2 ──┼──► мини-саммари × N ──► merge-запрос ──► финальный результат
Вкладка N ──┘
     (параллельно, Promise.allSettled)
```

Статусы каждой вкладки в реальном времени:

```
Pending → Extracting → Summarizing → Done
                                   → Skipped  (нет извлекаемого текста)
                                   → Error    (ошибка не прерывает остальные)
```

Если успешная вкладка одна — merge-запрос не делается, берётся её саммари напрямую.

## Check This Fact

1. Выделить текст на странице
2. Правый клик → **Check This Fact**
3. Открывается страница чата с результатом проверки
4. Пользователь может продолжить диалог по теме

## Языки суммаризации

Выбирается на вкладке **🤖 Summarizer** в настройках провайдеров:

| Значение | Поведение |
|---|---|
| `Auto` | Модель отвечает на языке исходного контента |
| `English`, `Русский`, `Deutsch`… | Саммари всегда на выбранном языке |

## Промпты — prompts/

Каждый язык — отдельный файл с двумя промптами:

```js
// prompts/ru.js
export const PAGE = `Ты — краткий суммаризатор. ...`;
export const MERGE = `Ты — краткий суммаризатор. Ниже — саммари нескольких вкладок. ...`;
```

`PAGE` — промпт для суммаризации одной страницы.  
`MERGE` — промпт для объединения нескольких мини-саммари.

### Добавление нового языка

1. Создать файл `prompts/xx.js` (где `xx` — код языка):

```js
export const PAGE = `You are a concise summarizer. Respond in [Language].
...
Page content:
`;

export const MERGE = `You are a concise summarizer. Respond in [Language].
...
Individual tab summaries:
`;
```

2. Добавить в `prompts/index.js`:

```js
import * as xx from './xx.js';

export const LANGUAGES = [
    ...
    { value: 'xx', label: 'Language Name' },  // добавить в список
];

const PROMPTS = { en, ru, de, fr, es, zh, ja, xx };  // добавить в карту
```

3. Добавить перевод в `locales/en.json`, `ru.json`, `he.json` если нужно отображать название языка в UI.

## Лимиты и обрезка текста

```js
const MAX_CHARS = 80_000;  // ~20K токенов — безопасный минимум для всех провайдеров
```

Если текст страницы превышает лимит — он обрезается и к промпту добавляется:
```
[Content was truncated due to length]
```

## summarizer.js — API

```js
// Суммаризация одной страницы
summarizePage(pageText, provider, apiKey, model, customUrl?, lang?)
  → Promise<string>  // HTML-строка с результатом

// Объединение нескольких мини-саммари
mergeSummaries(summaries, provider, apiKey, model, customUrl?, lang?)
  → Promise<string>  // HTML-строка с финальным результатом

// summaries: Array<{ title: string, summary: string }>
```

## Формат ответа

Все промпты требуют от модели возвращать **валидный HTML**:

```
Разрешены теги: <p>, <ul>, <li>, <strong>
Запрещены: markdown, code fences (```)
```

`chat.js` рендерит ответ через `innerHTML` — если модель вернула plain text (без тегов), он оборачивается в `<p>`.
