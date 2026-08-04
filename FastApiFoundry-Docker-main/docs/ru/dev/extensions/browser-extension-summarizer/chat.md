# Чат

## Интерфейс

Страница `chat.html` открывается в новой вкладке браузера.

```
┌─────────────────────────────────────────────────────┐
│ 💬 Chat  [badge: Provider · model]  [Model ▼] [Clear] [EN▼] │
├─────────────────────────────────────────────────────┤
│                                                     │
│   🤖  Ответ ассистента                              │
│                                                     │
│                          Сообщение пользователя  You│
│                                                     │
├─────────────────────────────────────────────────────┤
│  [textarea                              ] [Send]    │
│  Enter — отправить · Shift+Enter — новая строка     │
└─────────────────────────────────────────────────────┘
```

## Выбор модели

Селект **Model** в шапке показывает все настроенные провайдеры у которых есть хотя бы один ключ и хотя бы одна модель. Модели сгруппированы по провайдеру через `<optgroup>`.

Значение опции: `providerId|modelId` — позволяет определить провайдер и ключ при смене модели.

Если задан оверрайд `summaryProvider`/`summaryModel` в настройках суммаризатора — он используется как предвыбранная модель при открытии чата.

## История сообщений (контекст)

История хранится в памяти (массив `messages`) и передаётся целиком в каждый запрос:

```js
const messages = [];  // [{role: 'user'|'assistant', content: string}]

// При отправке:
messages.push({ role: 'user', content: text });
const reply = await sendToAPI(messages);  // передаём всю историю
messages.push({ role: 'assistant', content: reply });
```

Модель видит весь предыдущий диалог — это и есть контекст.

**Clear chat** очищает массив `messages` и DOM — история сбрасывается.

## Открытие из суммаризации

Когда чат открывается с параметром `?summary=job_<ts>` или `?factcheck=job_<ts>`:

1. Показывается индикатор печати
2. Polling `chrome.storage.local` каждые 400мс пока job не завершён
3. После завершения — результат добавляется в историю как сообщение ассистента
4. Пользователь может продолжить диалог по теме

```js
// Для суммаризации — добавляется контекстное сообщение пользователя:
messages.push({ role: 'user', content: 'Summarize this page' });
appendMessage('user', 'Summarize this page');

// Затем результат как ответ ассистента:
messages.push({ role: 'assistant', content: job.finalSummary });
appendMessage('assistant', job.finalSummary);
```

## Рендер ответов

Ответ ассистента рендерится через `innerHTML`:

```js
const isHtml = /<[a-z][\s\S]*>/i.test(content);
bubble.innerHTML = isHtml
    ? content
    : `<p>${content.replace(/\n/g, '<br>')}</p>`;
```

Если модель вернула HTML (теги `<p>`, `<ul>`, `<li>`, `<strong>`) — рендерится напрямую.  
Если plain text — оборачивается в `<p>` с заменой переносов строк на `<br>`.

## Маршрутизация запросов

```js
async function sendToAPI(history) {
    if (currentProvider === 'gemini')
        return geminiRequest(history, currentApiKey, currentModel);
    if (currentProvider === 'openrouter')
        return openrouterRequest(history, currentApiKey, currentModel);
    // Все остальные (OpenAI, Mistral, Groq, Custom, Foundry…)
    return openaiRequest(currentProvider, currentApiKey, currentModel, history, currentCustomUrl);
}
```

## Клавиатурные сокращения

| Клавиша | Действие |
|---|---|
| `Enter` | Отправить сообщение |
| `Shift+Enter` | Новая строка в textarea |

Textarea автоматически растягивается по высоте контента (до 120px).

## Обработка ошибок

При ошибке запроса:
- Показывается красный баннер с текстом ошибки на 6 секунд
- Последнее сообщение пользователя удаляется из `messages` — повторная отправка не дублирует его
- Кнопка Send разблокируется, фокус возвращается в textarea
