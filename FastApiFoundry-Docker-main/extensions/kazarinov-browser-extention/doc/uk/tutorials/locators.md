# Локатори елементів на веб-сторінці

Локатор — це JSON-об'єкт, що описує як знайти елемент на сторінці, яку дію виконати над ним і яке значення витягти. Розширення використовує локатори для автоматичного збору даних про товари у постачальників.

---

## Навіщо потрібні локатори

Кожен сайт постачальника має власну HTML-структуру. Щоб розширення вміло знаходити назву товару, ціну та характеристики на різних сайтах — для кожного сайту описується власний набір локаторів у JSON-файлі.

Файли локаторів зберігаються у папці `locators/` і називаються за hostname сайту:
- `locators/rozetka.com.ua.json`
- `locators/comfy.ua.json`
- `locators/foxtrot.com.ua.json`
- `locators/eldorado.ua.json`

Ім'я кожного локатора відповідає імені поля, яке потрібно заповнити. Наприклад, локатор `name` використовується для отримання назви товару, `price` — для ціни:

```js
const data = executeLocators(locators);
// data.name    → назва товару
// data.price   → ціна товару
```

Крім полів товару, можна створювати допоміжні локатори для дій на сторінці. Наприклад, `close_banner` — для закриття спливаючого вікна перед збором даних.

---

## Структура локатора

Кожен локатор — це JSON-об'єкт з такими ключами:

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
    "locator_description": "Закриваю pop-up вікно. Якщо воно не з'явилось — не страшно (mandatory: false)."
}
```

---

## Опис усіх ключів

### `attribute`

Атрибут, який потрібно отримати зі знайденого елемента. Приклади значень: `innerText`, `src`, `href`, `id`, `aria-label`.

Якщо встановити `null` або `false` — повернеться весь веб-елемент (`WebElement`), а не значення атрибута.

---

### `by`

Стратегія пошуку елемента на сторінці:

| Значення | Відповідає |
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

Вираз для пошуку елемента. Приклади:

```
(//li[@class = 'slide selected previous'])[1]//img
//a[@id = 'mainpic']//img
//span[@class = 'ltr sku-copy']
```

---

### `if_list`

Визначає, що робити якщо знайдено кілька елементів:

| Значення | Поведінка |
|---|---|
| `first` | Взяти перший елемент |
| `last` | Взяти останній елемент |
| `all` | Взяти всі елементи (поверне список) |
| `even` | Взяти парні елементи |
| `odd` | Взяти непарні елементи |
| `1,2,...` або `[1,3,5]` | Взяти елементи із зазначеними номерами |

Альтернативний спосіб — вказати номер прямо в XPATH-селекторі:
```
(//div[contains(@class, 'description')])[2]//p
```

---

### `event`

Дія, яку потрібно виконати з елементом **до** отримання атрибута. Порядок завжди: **дія → атрибут**.

Приклади подій:

- `click()` — клікнути на елемент
- `screenshot()` — зробити скриншот елемента і повернути його як PNG-байти. Використовується коли CDN-сервер не віддає зображення по URL
- `scroll()` — прокрутити до елемента
- `send_message()` — відправити текст у поле вводу

Приклад: спочатку клікнути, потім отримати `href`:
```json
{
    "attribute": "href",
    "event": "click()",
    "timeout_for_event": "presence_of_element_located"
}
```

Для `send_message` рекомендується використовувати змінну `%EXTERNAL_MESSAGE%` і ланцюжок команд:
```json
{
    "event": "click();backspace(10);%EXTERNAL_MESSAGE%"
}
```
Це виконає послідовно: фокус на полі → очищення 10 символів → введення тексту.

---

### `mandatory`

Обов'язковість локатора:
- `true` — якщо елемент не знайдено або дія не виконана, буде викинуто помилку
- `false` — елемент буде пропущено без помилки

---

### `timeout`

Час очікування в секундах перед пошуком елемента. `0` — шукати негайно.

---

### `timeout_for_event`

Умова очікування перед виконанням події. Наприклад, `"presence_of_element_located"` — чекати появи елемента в DOM.

---

### `use_mouse`

`true` / `false` — використовувати чи ні мишу для взаємодії з елементом.

---

### `locator_description`

Текстовий опис локатора для документування та відлагодження.

---

## Складні локатори

У ключі локатора можна передавати **списки** для виконання послідовних дій.

### Локатор зі списками

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
        "Натискаю на вкладку для відкриття поля description.",
        "Читаю дані з div."
    ]
}
```

В цьому прикладі:
1. Знаходиться елемент `//a[contains(@href, '#tab-description')]`
2. Виконується `click()` на ньому
3. Знаходиться елемент `//div[@id = 'tab-description']//p`
4. Повертається його атрибут `href`

### Локатор зі словником

```json
"sample_locator": {
    "attribute": {"href": "name"},
    ...
}
```

Словник дозволяє перейменовувати атрибути при витяганні.

---

## Як розширення вибирає файл локаторів

У `handlers.js` при додаванні компонента hostname поточної вкладки використовується як ім'я файлу:

```js
const url = new URL(tab.url);
const hostname = url.hostname.replace(/^www\./, '');
const locatorPath = `locators/${hostname}.json`;
const response = await fetch(chrome.runtime.getURL(locatorPath));
const locators = await response.json();
```

---

## Кілька версій локаторів для одного сайту

Розмітка сторінки може змінюватись — наприклад, десктопна та мобільна версії сайту мають різну HTML-структуру. Рекомендується тримати окремі файли локаторів для кожної версії:

```
locators/rozetka.com.ua.json
locators/rozetka.com.ua_mobile.json
```

---

## Як написати локатор для нового сайту

1. Відкрийте сторінку товару у постачальника
2. Натисніть `F12` для відкриття DevTools
3. Використайте **Inspect** (`Ctrl+Shift+C`) для вибору потрібного елемента
4. Складіть XPATH або CSS-селектор

Перевірка в консолі браузера:
```js
$x("//h1[contains(@class, 'title')]")
document.querySelectorAll(".product-title h1")
```

5. Створіть файл `locators/{hostname}.json`
6. Вкажіть `"supplier_prefix"` рівний hostname

### Приклад мінімального файлу локаторів

```json
{
  "supplier_prefix": "rozetka.com.ua",

  "name": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//h1[contains(@class,'product__title')]",
    "if_list": "first",
    "mandatory": true,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Назва товару на rozetka.com.ua"
  },

  "default_image_url": {
    "attribute": null,
    "by": "XPATH",
    "selector": "//div[contains(@class,'product-photo')]//img",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": "screenshot()",
    "locator_description": "Головне зображення товару через скриншот"
  },

  "price": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//p[contains(@class,'product-price__big')]",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Ціна товару на rozetka.com.ua"
  },

  "specification": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[contains(@class,'characteristics-full')]",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Технічні характеристики на rozetka.com.ua"
  }
}
```
