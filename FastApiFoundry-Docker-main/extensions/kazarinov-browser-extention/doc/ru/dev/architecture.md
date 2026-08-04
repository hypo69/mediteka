# Документация для разработчика

## Архитектура расширения

Расширение построено на Manifest V3 и состоит из нескольких независимых модулей.

```
background.js       — Service Worker, оркестрация всей логики
menu.js             — Управление контекстным меню (MenuManager)
handlers.js         — Обработчики действий меню
gemini.js           — Интеграция с Gemini API (GeminiAPI)
execute-locators.js — Извлечение данных со страниц по локаторам
content.js          — Content Script, инжектируется на все страницы
ui-manager.js       — Управление UI (индикаторы, уведомления, вкладки)
logger.js           — Логирование
popup.js            — Настройки расширения (API ключ, модель)
preview-offer.js    — Страница предпросмотра предложения
```

---

## Файлы конфигурации

### manifest.json

Определяет разрешения, точки входа и доступные ресурсы.

Ключевые разрешения:
- `contextMenus` — создание контекстного меню
- `storage` — хранение компонентов и настроек
- `scripting` — инжекция скриптов на страницы
- `activeTab` — доступ к активной вкладке

`host_permissions` ограничены доменом `generativelanguage.googleapis.com` для запросов к Gemini.

### locators/*.json

Каждый файл описывает локаторы для одного поставщика. Имя файла соответствует hostname сайта.

Структура локатора:
```json
{
  "field_name": {
    "by": "XPATH | ID | CLASS | CSS_SELECTOR",
    "selector": "<выражение>",
    "attribute": "<атрибут элемента для извлечения>",
    "if_list": "first | all",
    "mandatory": true | false,
    "locator_description": "<описание>"
  }
}
```

### _locales/{lang}/price_offer_prompt.txt

Промпт для Gemini. Определяет формат ответа (JSON), язык, правила обработки компонентов и сборок.

### _locales/{lang}/messages.json

Строки интерфейса для локализации через стандартный механизм Chrome i18n.

---

## Модули

### MenuManager (`menu.js`)

Класс управления контекстным меню.

**Статические свойства:**
- `CONFIG` — идентификаторы пунктов меню
- `STORAGE_KEY` — ключ хранения компонентов (`'addedComponents'`)

**Методы:**
- `initialize()` — пересоздаёт всё меню с нуля
- `refreshMenu()` — алиас для `initialize()`, используется после изменений
- `_createSavedComponentsMenu()` — строит подменю из компонентов в storage
- `addSavedOfferItem(offerId, offerName)` — добавляет сохранённое предложение в меню

Меню динамически строится при каждом вызове `initialize()`. Список языков загружается из `locales-manifest.json`.

---

### GeminiAPI (`gemini.js`)

Объект-неймспейс для работы с Gemini API.

**Методы:**
- `getFullPriceOffer(pageText, apiKey, model)` — отправляет запрос, возвращает текст ответа
- `getModelResponseJSON(pageText, apiKey, model)` — то же, но парсит ответ как JSON

**Вспомогательные функции:**
- `loadPriceOfferPrompt()` — загружает промпт из `_locales/{lang}/price_offer_prompt.txt`. Язык определяется из URL-параметра `?lang=`, fallback — `ru`
- `_sendRequestToGemini(fullPrompt, apiKey, model)` — низкоуровневый HTTP-запрос к API

Промпт обрезается до `MAX_PROMPT_LENGTH = 10000` символов перед отправкой.

---

### Обработчики (`handlers.js`)

Функции, вызываемые из `background.js` при кликах по меню.

| Функция | Описание |
|---|---|
| `handleAddComponent(tab)` | Загружает локаторы для текущего сайта, инжектирует `execute-locators.js`, сохраняет компонент |
| `handleDeleteComponent(menuItemId)` | Удаляет компонент по ID из storage |
| `handleCopyComponent(menuItemId, tab)` | Копирует JSON компонента в буфер обмена |
| `handleLoadOffer(menuItemId, tab)` | Загружает сохранённое предложение |
| `handleGenerateOffer(tab, language)` | Запускает генерацию: собирает компоненты, открывает `preview-offer.html` |
| `handleClearAllComponents(tab)` | Очищает все компоненты из storage |

`handleGenerateOffer` использует `Mutex` (`previewTabMutex`) для предотвращения параллельных запросов.

---

### Извлечение данных (`execute-locators.js`)

Инжектируется в страницу поставщика через `chrome.scripting.executeScript`.

- `getElementValue(locator)` — находит элемент по локатору и возвращает значение атрибута
- `executeLocators(locators)` — применяет все локаторы из объекта, возвращает `{field: value}`

Поддерживаемые стратегии поиска: `XPATH`, `ID`, `CLASS`, `CSS_SELECTOR`.

---

### Background Service Worker (`background.js`)

Точка входа. Импортирует все модули через `importScripts`.

**Обработчики событий:**
- `chrome.runtime.onInstalled` — инициализирует меню при установке
- `chrome.contextMenus.onClicked` — маршрутизирует клики по меню к нужному handler
- `chrome.runtime.onMessage` — обрабатывает запросы на повтор генерации (`repeatLastAction`, `repeatFullGeneration`)

Защита от двойных кликов реализована через `MenuClickState` с debounce 500 мс.

---

## Хранилище данных

| Ключ | Тип | Хранилище | Описание |
|---|---|---|---|
| `addedComponents` | `Array` | `local` | Список добавленных компонентов |
| `savedOffers` | `Object` | `local` | Сохранённые предложения |
| `componentsForOffer` | `Array` | `local` | Компоненты для текущей генерации |
| `previewOfferTabId` | `number` | `local` | ID вкладки предпросмотра |
| `geminiApiKey` | `string` | `sync` | API ключ Gemini |
| `geminiModel` | `string` | `sync` | Название модели |

---

## Добавление нового поставщика

1. Создайте файл `locators/{hostname}.json` по образцу существующих
2. Определите локаторы для полей: `name`, `default_image_url`, `description_short`, `specification`, `brand`
3. Поле `supplier_prefix` должно совпадать с hostname
4. Расширение автоматически подберёт файл локаторов по `url.hostname` текущей вкладки

---

## Отладка

В консоли Service Worker (`chrome://extensions/` → **Inspect views: service worker**) доступны команды:

```js
checkPreviewTabs()      // список открытых вкладок предпросмотра
checkState()            // состояние MenuClickState и Mutex
fullDiagnostic()        // полная диагностика storage и вкладок
resetAllFlags()         // сброс всех флагов блокировки
closeAllPreviewTabs()   // закрытие дублирующих вкладок
```

Для просмотра логов откройте popup расширения и нажмите кнопку **Открыть логи**.
