# Как работает контекстное меню расширения

Контекстное меню — это меню, которое появляется при клике правой кнопкой мыши на странице. В расширении оно является основным интерфейсом для работы с компонентами.

---

## Как Chrome создаёт контекстное меню

Chrome предоставляет API `chrome.contextMenus` для управления пунктами меню. Каждый пункт создаётся вызовом `chrome.contextMenus.create()` с уникальным `id`.

Пример создания простого пункта:

```js
chrome.contextMenus.create({
    id: 'my-action',
    title: 'Моё действие',
    contexts: ['page']  // показывать при клике на странице
});
```

Параметр `contexts` определяет, где показывается пункт: `page`, `selection`, `image`, `link` и др.

---

## Структура меню расширения

Меню строится динамически классом `MenuManager` при каждом вызове `initialize()`. Структура:

```
Добавить компонент
└── (всегда видно)

Сохраненные компоненты          ← появляется только если есть компоненты
├── Сформировать предложение цены
│   ├── на Русском
│   ├── in English
│   ├── בעברית
│   └── ...
├── ─────────────────
├── Компонент 1
│   └── ❌ Удалить
├── Компонент 2
│   └── ❌ Удалить
├── ─────────────────
└── 💣 Очистить все компоненты
```

Пункт **Сохраненные компоненты** и всё его содержимое создаётся только если в `chrome.storage.local` есть хотя бы один сохранённый компонент.

---

## Иерархия пунктов меню

Пункты меню могут быть вложенными. Для этого используется параметр `parentId`:

```js
// Родительский пункт
chrome.contextMenus.create({
    id: 'saved-components-parent',
    title: 'Сохраненные компоненты',
    contexts: ['page']
});

// Дочерний пункт
chrome.contextMenus.create({
    id: 'generate-offer-parent',
    parentId: 'saved-components-parent',  // ← вложен в родителя
    title: 'Сформировать предложение цены',
    contexts: ['page']
});
```

---

## Динамические пункты: список языков

Список языков для генерации предложения загружается из файла `locales-manifest.json` и создаётся динамически:

```js
const manifestUrl = chrome.runtime.getURL('locales-manifest.json');
const response = await fetch(manifestUrl);
const locales = await response.json();  // ['ru', 'en', 'he', ...]

locales.forEach(locale => {
    chrome.contextMenus.create({
        id: `generate-offer-lang-${locale}`,
        parentId: 'generate-offer-parent',
        title: this.languageNames[locale] || locale,
        contexts: ['page']
    });
});
```

Чтобы добавить новый язык — достаточно добавить его код в `locales-manifest.json` и создать папку `_locales/{lang}/` с нужными файлами.

---

## Обработка кликов

Клики по всем пунктам меню обрабатываются одним слушателем в `background.js`:

```js
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    const menuItemId = info.menuItemId;

    if (menuItemId === 'add-component-action') {
        await handleAddComponent(tab);
    } else if (menuItemId.startsWith('generate-offer-lang-')) {
        const lang = menuItemId.replace('generate-offer-lang-', '');
        await handleGenerateOffer(tab, lang);
    } else if (menuItemId.startsWith('delete-')) {
        const componentId = menuItemId.replace('delete-', '');
        await handleDeleteComponent(componentId);
    }
    // ...
});
```

Маршрутизация построена на проверке `id` пункта меню: по префиксу определяется нужное действие.

---

## Обновление меню

Меню нельзя изменить частично — при любом изменении данных оно пересоздаётся полностью:

```js
async refreshMenu() {
    await this.initialize();  // удаляет все пункты и создаёт заново
}
```

`chrome.contextMenus.removeAll()` удаляет все существующие пункты, после чего `initialize()` строит меню заново на основе актуальных данных из storage.

---

## Разделители

Для визуального разделения групп пунктов используются разделители:

```js
chrome.contextMenus.create({
    id: 'my-separator',
    parentId: 'saved-components-parent',
    type: 'separator',  // ← тип разделитель
    contexts: ['page']
});
```

---

## Защита от двойных кликов

Быстрые повторные клики могут запустить одно действие несколько раз. Для защиты используется флаг `processing` и debounce:

```js
const MenuClickState = {
    processing: false,
    lastClickTime: 0,
    lastMenuItemId: null
};

// В обработчике клика:
if (MenuClickState.processing) return;  // блокируем повторный клик
MenuClickState.processing = true;

try {
    await handleAction();
} finally {
    setTimeout(() => { MenuClickState.processing = false; }, 100);
}
```
