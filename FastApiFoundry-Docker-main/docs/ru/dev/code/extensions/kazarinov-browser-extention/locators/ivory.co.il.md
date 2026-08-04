# Ivory.Co.Il

**Файл:** `extensions/kazarinov-browser-extention/locators/ivory.co.il.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `supplier_prefix` | `str` | ivory.co.il |
| `default_image_url` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |
| `name` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |
| `description_short` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |
| `specification` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |
| `summary` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |
| `description` | `dict` | объект: `attribute`, `by`, `selector`, `strategy_for_multiple_selectors`, `if_list` |

**Полная структура:**

```json
{
  "supplier_prefix": "ivory.co.il",
  "default_image_url": {
    "attribute": "src",
    "by": "XPATH",
    "selector": "//img[@id = 'img_zoom_inout']",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "text_to_be_present_in_element": "",
    "event": null,
    "timeout_for_event": "presence_of_element_located",
    "timeout": 0,
    "locator_description": "URL главного изображения товара ivory.co.il"
  },
  "name": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//h1[@id = 'titleProd']",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "text_to_be_present_in_element": "",
    "event": null,
    "timeout_for_event": "presence_of_element_located",
    "timeout": 0,
    "locator_description": "prestaShop: название товара ivory.co.il"
  },
  "description_short": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//h2[ contains( @class, 'col-12 h2fake')]",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "text_to_be_present_in_element": "",
    "event": null,
    "timeout_for_event": "presence_of_element_located",
    "timeout": 0,
    "locator_description": "prestaShop: краткое описание товара ivory.co.il"
  },
  "specification": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[ contains( @class, 'contentproducttable') or contains( @class, 'product-params')]//ul",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "text_to_be_present_in_element": "",
    "event": null,
    "timeout_for_event": "presence_of_element_located",
    "timeout": 0,
    "locator_description": "prestaShop: характеристики товара ivory.co.il"
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
    "locator_description": "сводка/краткие характеристики ivory.co.il"
  },
  "description": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[@id='productDescription']",
    "strategy_for_multiple_selectors": "find_first_match",
    "if_list": "first",
    "mandatory": false,
    "event": null,
    "timeout_for_event": "presence_of_element_located",
    "timeout": 0,
    "locator_description": "полное описание товара (дополнительно) ivory.co.il"
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
