# Локаторы элементов на веб-странице

Локатор — это JSON-объект, описывающий как найти элемент на странице, что с ним сделать и что из него извлечь. Расширение использует локаторы для автоматического сбора данных о товарах у поставщиков.

---

## Зачем нужны локаторы

Каждый сайт поставщика имеет свою HTML-структуру. Чтобы расширение умело находить название товара, цену и характеристики на разных сайтах — для каждого сайта описывается свой набор локаторов в JSON-файле.

Файлы локаторов хранятся в папке `locators/` и называются по hostname сайта:
- `locators/dns-shop.ru.json`
- `locators/citilink.ru.json`
- `locators/mvideo.ru.json`
- `locators/regard.ru.json`

Имя каждого локатора соответствует имени поля, которое нужно заполнить. Например, локатор `name` используется для получения имени товара, `price` — для цены:

```js
const data = executeLocators(locators);
// data.name    → название товара
// data.price   → цена товара
```

Помимо полей товара, можно создавать вспомогательные локаторы для действий на странице. Например, `close_banner` — для закрытия всплывающего окна перед сбором данных.

---

## Структура локатора

Каждый локатор — это JSON-объект со следующими ключами:

```json
"close_banner": {
    "attribute": null,
    "by": "XPATH",
    "selector": "//button[@id = 'closeXButton']",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": "click()",
    "use_mouse": false,
    "text_to_be_present_in_element": "",
    "locator_description": "Закрываю pop-up окно. Если оно не появилось — не страшно (mandatory: false)."
}
```

---

## Описание всех ключей

### `attribute`

Атрибут, который нужно получить из найденного элемента. Примеры значений: `innerText`, `src`, `href`, `id`, `aria-label`.

Если установить `null` или `false` — вернётся весь веб-элемент целиком (`WebElement`), а не значение атрибута.

---

### `by`

Стратегия поиска элемента на странице:

| Значение | Соответствует |
|---|---|
| `XPATH` | `By.XPATH` |
| `ID` | `By.ID` |
| `NAME` | `By.NAME` |
| `CLASS_NAME` | `By.CLASS_NAME` |
| `TAG_NAME` | `By.TAG_NAME` |
| `LINK_TEXT` | `By.LINK_TEXT` |
| `PARTIAL_LINK_TEXT` | `By.PARTIAL_LINK_TEXT` |
| `CSS_SELECTOR` | `By.CSS_SELECTOR` |

---

### `selector`

Выражение для поиска элемента. Примеры:

```
(//li[@class = 'slide selected previous'])[1]//img
//a[@id = 'mainpic']//img
//span[@class = 'ltr sku-copy']
```

---

### `if_list`

Определяет, что делать если найдено несколько элементов:

| Значение | Поведение |
|---|---|
| `first` | Взять первый элемент |
| `last` | Взять последний элемент |
| `all` | Взять все элементы (вернёт список) |
| `even` | Взять чётные элементы |
| `odd` | Взять нечётные элементы |
| `1,2,...` или `[1,3,5]` | Взять элементы с указанными номерами |

Альтернативный способ — указать номер прямо в XPATH-селекторе:
```
(//div[contains(@class, 'description')])[2]//p
```

---

### `event`

Действие, которое нужно выполнить с элементом **до** получения атрибута. Порядок всегда: **действие → атрибут**.

Примеры событий:

- `click()` — кликнуть на элемент
- `screenshot()` — сделать скриншот элемента и вернуть его как PNG-байты. Используется когда CDN-сервер не отдаёт изображение по URL
- `scroll()` — прокрутить к элементу
- `send_message()` — отправить текст в поле ввода

Пример: сначала кликнуть, потом получить `href`:
```json
{
    "attribute": "href",
    "event": "click()",
    "timeout_for_event": "presence_of_element_located"
}
```

Для `send_message` рекомендуется использовать переменную `%EXTERNAL_MESSAGE%` и цепочку команд:
```json
{
    "event": "click();backspace(10);%EXTERNAL_MESSAGE%"
}
```
Это выполнит последовательно: фокус на поле → очистка 10 символов → ввод текста.

---

### `mandatory`

Обязательность локатора:
- `true` — если элемент не найден или действие не выполнено, будет выброшена ошибка
- `false` — элемент будет пропущен без ошибки

---

### `timeout`

Время ожидания в секундах перед поиском элемента. `0` — искать немедленно.

---

### `timeout_for_event`

Условие ожидания перед выполнением события. Например, `"presence_of_element_located"` — ждать появления элемента в DOM.

---

### `use_mouse`

`true` / `false` — использовать ли мышь для взаимодействия с элементом.

---

### `locator_description`

Текстовое описание локатора для документирования и отладки.

---

## Сложные локаторы

В ключи локатора можно передавать **списки** для выполнения последовательных действий.

### Локатор со списками

```json
"sample_locator": {
    "attribute": [null, "href"],
    "by": ["XPATH", "XPATH"],
    "selector": [
        "//a[contains(@href, '#tab-description')]",
        "//div[@id = 'tab-description']//p"
    ],
    "event": ["click()", null],
    "use_mouse": [false, false],
    "mandatory": [true, true],
    "if_list": "first",
    "locator_description": [
        "Нажимаю на вкладку для открытия поля description.",
        "Читаю данные из div."
    ]
}
```

В этом примере:
1. Находится элемент `//a[contains(@href, '#tab-description')]`
2. Выполняется `click()` на нём
3. Находится элемент `//div[@id = 'tab-description']//p`
4. Возвращается его атрибут `href`

### Локатор со словарём

```json
"sample_locator": {
    "attribute": {"href": "name"},
    ...
}
```

Словарь позволяет переименовывать атрибуты при извлечении.

---

## Как работает извлечение данных

Функция `getElementValue` в `execute-locators.js` выполняется в контексте страницы:

```js
function getElementValue(locator) {
    const { by, selector, attribute, if_list, mandatory } = locator;
    let elements = [];

    if (by === 'XPATH') {
        const iterator = document.evaluate(
            selector, document, null,
            XPathResult.ORDERED_NODE_ITERATOR_TYPE, null
        );
        let node = iterator.iterateNext();
        while (node) { elements.push(node); node = iterator.iterateNext(); }
    } else if (by === 'CSS_SELECTOR') {
        elements = Array.from(document.querySelectorAll(selector));
    } else if (by === 'ID') {
        const el = document.getElementById(selector);
        if (el) elements.push(el);
    } else if (by === 'CLASS') {
        elements = Array.from(document.getElementsByClassName(selector));
    }

    if (!elements.length) {
        if (mandatory) console.error(`Обязательный локатор не найден: ${locator_description}`);
        return if_list === 'all' ? [] : null;
    }

    if (if_list === 'all') {
        return elements.map(el => el[attribute] ?? el.getAttribute(attribute));
    } else {
        return elements[0][attribute] ?? elements[0].getAttribute(attribute);
    }
}
```

Сначала пробуется прямое обращение к свойству DOM (`el[attribute]`), затем — через `getAttribute()`. Это позволяет работать как со стандартными свойствами (`innerText`, `src`), так и с произвольными HTML-атрибутами.

`executeLocators` применяет все локаторы из файла и возвращает объект с результатами:

```js
function executeLocators(locators) {
    const result = {};
    for (const key in locators) {
        result[key] = getElementValue(locators[key]);
    }
    return result;
}
```

---

## Как расширение выбирает файл локаторов

В `handlers.js` при добавлении компонента hostname текущей вкладки используется как имя файла:

```js
const url = new URL(tab.url);
const hostname = url.hostname.replace(/^www\./, '');  // убираем www.
const locatorPath = `locators/${hostname}.json`;
const response = await fetch(chrome.runtime.getURL(locatorPath));
const locators = await response.json();
```

Если файл для текущего сайта не найден — расширение покажет ошибку.

---

## Несколько версий локаторов для одного сайта

Разметка страницы может меняться — например, десктопная и мобильная версии сайта имеют разную структуру HTML. В таком случае рекомендуется держать отдельные файлы локаторов для каждой версии:

```
locators/dns-shop.ru.json
locators/dns-shop.ru_mobile.json
```

---

## Как написать локатор для нового сайта

1. Откройте страницу товара у поставщика
2. Нажмите `F12` для открытия DevTools
3. Используйте **Inspect** (`Ctrl+Shift+C`) для выбора нужного элемента
4. Составьте XPATH или CSS-селектор

Проверка в консоли браузера:
```js
// Проверить XPATH
$x("//h1[contains(@class, 'title')]")

// Проверить CSS-селектор
document.querySelectorAll(".product-title h1")
```

5. Создайте файл `locators/{hostname}.json`
6. Укажите `"supplier_prefix"` равный hostname

### Пример минимального файла локаторов

```json
{
  "supplier_prefix": "dns-shop.ru",

  "name": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//h1[contains(@class, 'product-card-top__title')]",
    "if_list": "first",
    "mandatory": true,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Название товара на dns-shop.ru"
  },

  "default_image_url": {
    "attribute": null,
    "by": "XPATH",
    "selector": "//div[contains(@class,'product-images-slider__main')]//img",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": "screenshot()",
    "locator_description": "Главное изображение товара через скриншот"
  },

  "price": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[contains(@class,'product-buy__price')]",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Цена товара на dns-shop.ru"
  },

  "specification": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[contains(@class,'product-characteristics')]",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Технические характеристики на dns-shop.ru"
  }
}
```
