# Ksp.Co.Il

**Файл:** `extensions/kazarinov-browser-extention/locators/ksp.co.il.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `supplier_prefix` | `str` | ksp.co.il |
| `default_image_url` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |
| `name` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |
| `description_short` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |
| `specification` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |
| `brand` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |
| `summary` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |
| `description` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |

**Полная структура:**

```json
{
  "supplier_prefix": "ksp.co.il",
  "default_image_url": {
    "attribute": "src",
    "by": "XPATH",
    "selector": "//li[contains(@class,'slide selected')]//img",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "text_to_be_present_in_element": "",
    "event": "screenshot()",
    "timeout_for_event": "presence_of_element_located",
    "timeout": 0,
    "locator_description": "URL главного изображения товара ksp.co.il"
  },
  "name": {
    "attribute": "aria-label",
    "by": "XPATH",
    "selector": "//div[@id = 'product-page-root']//h1[contains(@class, 'title')]",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "text_to_be_present_in_element": "",
    "event": null,
    "timeout_for_event": "presence_of_element_located",
    "timeout": 1,
    "locator_description": "PrestaShop: Название товара ksp.co.il"
  },
  "description_short": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//h2[contains(text(), 'תיאור קצר')]/following-sibling::p",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "text_to_be_present_in_element": "",
    "event": null,
    "timeout_for_event": "presence_of_element_located",
    "timeout": 1,
    "locator_description": "PrestaShop: Краткое описание товара ksp.co.il"
  },
  "specification": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[@id = 'review-section']",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "text_to_be_present_in_element": "",
    "event": null,
    "timeout_for_event": "presence_of_element_located",
    "timeout": 0,
    "locator_description": "PrestaShop: Характеристики товара ksp.co.il"
  },
  "brand": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//span[contains(text(), 'Brand')]/parent::td/following-sibling::td/span[contains(@class, 'po-break-word')]",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "event": null,
    "timeout_for_event": "presence_of_element_located",
    "timeout": 0,
    "locator_description": "PrestaShop: Производитель (бренд) товара ksp.co.il"
  },
  "summary": {
    "attribute": "innerHTML",
    "by": "XPATH",
    "selector": "//div[contains(@data-a-expander-name , 'product_overview')]//table",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "event": null,
    "timeout_for_event": "presence_of_element_located",
    "timeout": 0,
    "locator_description": "Сводка/краткие характеристики ksp.co.il"
  },
  "description": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[@id='productDescription']",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "event": nu
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
