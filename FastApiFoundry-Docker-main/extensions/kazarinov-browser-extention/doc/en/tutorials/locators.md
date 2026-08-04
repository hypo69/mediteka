# Web Page Element Locators

A locator is a JSON object that describes how to find an element on a page, what action to perform on it, and what value to extract. The extension uses locators to automatically collect product data from supplier websites.

---

## Why Locators Are Needed

Every supplier website has its own HTML structure. To let the extension find product names, prices, and specifications across different sites, each site has its own set of locators described in a JSON file.

Locator files are stored in the `locators/` folder and named after the site's hostname:
- `locators/amazon.com.json`
- `locators/newegg.com.json`
- `locators/bestbuy.com.json`
- `locators/bhphotovideo.com.json`

Each locator name corresponds to the field it fills. For example, the `name` locator retrieves the product name, `price` retrieves the price:

```js
const data = executeLocators(locators);
// data.name    → product name
// data.price   → product price
```

You can also create helper locators for page actions. For example, `close_banner` closes a pop-up before data collection begins.

---

## Locator Structure

Each locator is a JSON object with the following keys:

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
    "locator_description": "Closes the pop-up banner. If it didn't appear — no problem (mandatory: false)."
}
```

---

## Key Reference

### `attribute`

The attribute to extract from the found element. Examples: `innerText`, `src`, `href`, `id`, `aria-label`.

If set to `null` or `false` — the entire web element (`WebElement`) is returned instead of an attribute value.

---

### `by`

The strategy used to locate the element on the page:

| Value | Corresponds to |
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

The expression used to find the element. Examples:

```
(//li[@class = 'slide selected previous'])[1]//img
//a[@id = 'mainpic']//img
//span[@class = 'ltr sku-copy']
```

---

### `if_list`

Defines what to do when multiple elements are found:

| Value | Behavior |
|---|---|
| `first` | Take the first element |
| `last` | Take the last element |
| `all` | Take all elements (returns a list) |
| `even` | Take even-indexed elements |
| `odd` | Take odd-indexed elements |
| `1,2,...` or `[1,3,5]` | Take elements at specified positions |

You can also specify the index directly in the XPATH selector:
```
(//div[contains(@class, 'description')])[2]//p
```

---

### `event`

An action to perform on the element **before** extracting the attribute. Order is always: **action → attribute**.

Available events:

- `click()` — click the element
- `screenshot()` — capture the element as a PNG screenshot. Useful when a CDN server doesn't serve the image via URL
- `scroll()` — scroll to the element
- `send_message()` — send text to an input field

Example — click first, then get `href`:
```json
{
    "attribute": "href",
    "event": "click()",
    "timeout_for_event": "presence_of_element_located"
}
```

For `send_message`, use the `%EXTERNAL_MESSAGE%` variable with a command chain:
```json
{
    "event": "click();backspace(10);%EXTERNAL_MESSAGE%"
}
```
This executes sequentially: focus the field → clear 10 characters → type the message.

---

### `mandatory`

Whether the locator is required:
- `true` — throws an error if the element is not found or the action fails
- `false` — silently skips the element

---

### `timeout`

Wait time in seconds before searching for the element. `0` means search immediately.

---

### `timeout_for_event`

The wait condition before executing the event. For example, `"presence_of_element_located"` waits for the element to appear in the DOM.

---

### `use_mouse`

`true` / `false` — whether to use the mouse for interaction.

---

### `locator_description`

A text description of the locator for documentation and debugging purposes.

---

## Complex Locators

Locator keys can accept **lists** to perform sequential actions.

### List-based locator

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
        "Click the tab to open the description panel.",
        "Read data from the div."
    ]
}
```

Steps executed:
1. Find `//a[contains(@href, '#tab-description')]`
2. Execute `click()` on it
3. Find `//div[@id = 'tab-description']//p`
4. Return its `href` attribute

### Dictionary-based locator

```json
"sample_locator": {
    "attribute": {"href": "name"},
    ...
}
```

A dictionary allows renaming attributes during extraction.

---

## How Data Extraction Works

The `getElementValue` function in `execute-locators.js` runs directly in the page context:

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
        if (mandatory) console.error(`Required locator not found: ${locator_description}`);
        return if_list === 'all' ? [] : null;
    }

    if (if_list === 'all') {
        return elements.map(el => el[attribute] ?? el.getAttribute(attribute));
    } else {
        return elements[0][attribute] ?? elements[0].getAttribute(attribute);
    }
}
```

It first tries direct DOM property access (`el[attribute]`), then falls back to `getAttribute()`. This handles both standard DOM properties (`innerText`, `src`) and arbitrary HTML attributes.

`executeLocators` applies all locators from the file and returns a result object:

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

## How the Extension Selects the Locator File

In `handlers.js`, when adding a component, the current tab's hostname is used as the filename:

```js
const url = new URL(tab.url);
const hostname = url.hostname.replace(/^www\./, '');  // strip www.
const locatorPath = `locators/${hostname}.json`;
const response = await fetch(chrome.runtime.getURL(locatorPath));
const locators = await response.json();
```

If no locator file exists for the current site, the extension will show an error.

---

## Multiple Locator Versions for One Site

Page markup can change — for example, desktop and mobile versions of a site have different HTML structures. It is recommended to keep separate locator files for each version:

```
locators/amazon.com.json
locators/amazon.com_mobile.json
```

---

## Writing a Locator for a New Site

1. Open a product page on the supplier's website
2. Press `F12` to open DevTools
3. Use **Inspect** (`Ctrl+Shift+C`) to select the target element
4. Build an XPATH or CSS selector

Test in the browser console:
```js
// Test XPATH
$x("//h1[contains(@class, 'product-title')]")

// Test CSS selector
document.querySelectorAll(".product-title h1")
```

5. Create `locators/{hostname}.json`
6. Set `"supplier_prefix"` equal to the hostname

### Minimal locator file example

```json
{
  "supplier_prefix": "amazon.com",

  "name": {
    "attribute": "innerText",
    "by": "ID",
    "selector": "productTitle",
    "if_list": "first",
    "mandatory": true,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Product title"
  },

  "default_image_url": {
    "attribute": null,
    "by": "XPATH",
    "selector": "//div[@id='imgTagWrapperId']//img",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": "screenshot()",
    "locator_description": "Main product image via screenshot"
  },

  "price": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//span[contains(@class, 'a-price-whole')]",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Product price"
  },

  "specification": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[@id='productDetails_techSpec_section_1']//table",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Technical specifications table"
  }
}
```
