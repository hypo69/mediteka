# Работа с языковой моделью Gemini

В расширении используется Google Gemini API для обработки данных о компонентах и генерации ценового предложения. Вся логика взаимодействия с моделью сосредоточена в файле `gemini.js`.

---

## Что такое языковая модель и зачем она здесь

Языковая модель (LLM) принимает текст на входе и возвращает текст на выходе. В нашем случае:

- **Вход:** сырые данные о компонентах (название, характеристики, цена), собранные со страниц поставщиков
- **Выход:** структурированный JSON с названием сборки, описаниями компонентов на нужном языке

Модель не просто переводит — она дополняет характеристики из своих знаний, формулирует продающие описания и классифицирует тип сборки.

---

## Как устроен запрос к Gemini

Запрос состоит из двух частей, склеенных вместе:

```
[промпт с инструкциями]

[данные о компонентах]
```

```js
const fullPrompt = `${instructions}\n\n${truncatedText}`;
```

Данные обрезаются до `10 000` символов, чтобы не превысить лимиты модели:

```js
const MAX_PROMPT_LENGTH = 10000;
const truncatedText = pageText.substring(0, MAX_PROMPT_LENGTH);
```

---

## Промпт и его загрузка

Промпт — это инструкция для модели, описывающая что делать и в каком формате вернуть результат. Он хранится в файле `_locales/{lang}/price_offer_prompt.txt`.

Загрузка промпта с учётом языка:

```js
async function loadPriceOfferPrompt() {
    // Приоритет 1: язык из URL-параметра ?lang=ru
    const urlParams = new URLSearchParams(window.location.search);
    const langFromUrl = urlParams.get('lang');
    if (langFromUrl) {
        const text = await tryLoad(langFromUrl);
        if (text) return text;
    }

    // Приоритет 2: язык по умолчанию — русский
    return await tryLoad('ru');
}
```

Функция `tryLoad` загружает файл через `fetch` по URL вида:
```
chrome-extension://{id}/_locales/ru/price_offer_prompt.txt
```

`chrome.runtime.getURL()` преобразует относительный путь в полный URL расширения.

---

## HTTP-запрос к API

Gemini API принимает POST-запрос с JSON-телом:

```js
async function _sendRequestToGemini(fullPrompt, apiKey, model) {
    const url = `https://generativelanguage.googleapis.com/v1/models/${model}:generateContent?key=${apiKey}`;

    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            contents: [{
                parts: [{ text: fullPrompt }]
            }]
        })
    });

    const data = await response.json();
    return data.candidates[0].content.parts[0].text;
}
```

Структура ответа от Gemini:
```json
{
  "candidates": [{
    "content": {
      "parts": [{ "text": "...ответ модели..." }]
    }
  }]
}
```

---

## Получение JSON из ответа модели

Промпт требует от модели вернуть строго JSON. После получения ответа он парсится:

```js
GeminiAPI.getModelResponseJSON = async (pageText, apiKey, model) => {
    const modelResponse = await GeminiAPI.getFullPriceOffer(pageText, apiKey, model);
    return JSON.parse(modelResponse);
};
```

Если модель вернула текст не в формате JSON (например, добавила вводную фразу), `JSON.parse` выбросит ошибку. Именно поэтому промпт явно запрещает модели добавлять что-либо кроме JSON.

---

## Формат ответа модели

Модель возвращает JSON следующей структуры:

```json
{
    "title": "Игровая сборка среднего класса",
    "description": "Сбалансированный компьютер для современных игр...",
    "components": [
        {
            "component_name": "Процессор Intel Core i5-13600K",
            "component_description": "Производительный процессор для игр и работы...",
            "component_specification": [
                "Ядра: 14 (6P + 8E)",
                "Частота: до 5.1 ГГц",
                "TDP: 125 Вт"
            ],
            "component_image": "https://..."
        }
    ]
}
```

---

## Настройка модели

API ключ и название модели хранятся в `chrome.storage.sync` (синхронизируются между устройствами):

```js
// Сохранение (popup.js)
await chrome.storage.sync.set({ geminiApiKey: apiKey, geminiModel: model });

// Чтение (background.js)
const { geminiApiKey } = await chrome.storage.sync.get('geminiApiKey');
const { geminiModel = 'gemini-2.5-flash' } = await chrome.storage.sync.get('geminiModel');
```

Модель по умолчанию — `gemini-2.5-flash`. Можно выбрать другую в настройках расширения.

---

## Обработка ошибок

API может вернуть ошибку или заблокировать запрос:

```js
if (data.error) {
    throw new Error(data.error.message);
}

if (!data.candidates || data.candidates.length === 0) {
    const blockReason = data.promptFeedback?.blockReason || 'Неизвестная причина';
    throw new Error(`Ответ заблокирован. Причина: ${blockReason}`);
}
```

При ошибке пользователю показывается уведомление с кнопкой **Повторить** — это позволяет не начинать процесс заново.

---

## Добавление нового языка

1. Создайте папку `_locales/{код_языка}/`
2. Добавьте файл `price_offer_prompt.txt` с инструкцией на нужном языке
3. Добавьте код языка в `locales-manifest.json`
4. Добавьте отображаемое название в `MenuManager.languageNames` в `menu.js`

После этого новый язык автоматически появится в подменю генерации.
