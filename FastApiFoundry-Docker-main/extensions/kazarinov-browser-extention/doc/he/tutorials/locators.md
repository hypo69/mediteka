# לוקאטורים של אלמנטים בדף אינטרנט

לוקאטור הוא אובייקט JSON המתאר כיצד למצוא אלמנט בדף, איזו פעולה לבצע עליו ואיזה ערך לחלץ ממנו. התוסף משתמש בלוקאטורים לאיסוף אוטומטי של נתוני מוצרים מאתרי ספקים.

---

## מדוע נדרשים לוקאטורים

לכל אתר ספק יש מבנה HTML משלו. כדי שהתוסף יוכל למצוא שמות מוצרים, מחירים ומפרטים באתרים שונים — לכל אתר מוגדר קובץ JSON עם לוקאטורים ייעודיים.

קבצי הלוקאטורים נמצאים בתיקייה `locators/` ושמם תואם את ה-hostname של האתר:
- `locators/ksp.co.il.json`
- `locators/ivory.co.il.json`
- `locators/morlevi.co.il.json`
- `locators/grandadvance.co.il.json`

שם הלוקאטור תואם את שם השדה שיש למלא. לדוגמה, הלוקאטור `name` מחלץ את שם המוצר, `price` — את המחיר:

```js
const data = executeLocators(locators);
// data.name    → שם המוצר
// data.price   → מחיר המוצר
```

ניתן גם ליצור לוקאטורים עזר לפעולות בדף. לדוגמה, `close_banner` — לסגירת חלון קופץ לפני איסוף הנתונים.

---

## מבנה הלוקאטור

כל לוקאטור הוא אובייקט JSON עם המפתחות הבאים:

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
    "locator_description": "סוגר חלון קופץ. אם הוא לא הופיע — לא נורא (mandatory: false)."
}
```

---

## תיאור המפתחות

### `attribute`

המאפיין לחילוץ מהאלמנט שנמצא. דוגמאות: `innerText`, `src`, `href`, `id`, `aria-label`.

אם מוגדר `null` או `false` — יוחזר אובייקט האלמנט המלא (`WebElement`) במקום ערך מאפיין.

---

### `by`

אסטרטגיית החיפוש של האלמנט בדף:

| ערך | מתאים ל |
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

הביטוי לאיתור האלמנט. דוגמאות:

```
(//li[@class = 'slide selected previous'])[1]//img
//a[@id = 'mainpic']//img
//span[@class = 'ltr sku-copy']
```

---

### `if_list`

מגדיר מה לעשות כאשר נמצאים מספר אלמנטים:

| ערך | התנהגות |
|---|---|
| `first` | לקחת את האלמנט הראשון |
| `last` | לקחת את האלמנט האחרון |
| `all` | לקחת את כל האלמנטים (מחזיר רשימה) |
| `even` | לקחת אלמנטים זוגיים |
| `odd` | לקחת אלמנטים אי-זוגיים |
| `1,2,...` או `[1,3,5]` | לקחת אלמנטים במיקומים המצוינים |

ניתן גם לציין את האינדקס ישירות בסלקטור XPATH:
```
(//div[contains(@class, 'description')])[2]//p
```

---

### `event`

פעולה לביצוע על האלמנט **לפני** חילוץ המאפיין. הסדר תמיד: **פעולה → מאפיין**.

פעולות זמינות:

- `click()` — לחיצה על האלמנט
- `screenshot()` — צילום האלמנט כ-PNG. שימושי כאשר שרת CDN לא מחזיר תמונה דרך URL
- `scroll()` — גלילה לאלמנט
- `send_message()` — שליחת טקסט לשדה קלט

דוגמה — לחיצה ואז קבלת `href`:
```json
{
    "attribute": "href",
    "event": "click()",
    "timeout_for_event": "presence_of_element_located"
}
```

עבור `send_message` מומלץ להשתמש במשתנה `%EXTERNAL_MESSAGE%` עם שרשרת פקודות:
```json
{
    "event": "click();backspace(10);%EXTERNAL_MESSAGE%"
}
```
זה מבצע ברצף: מיקוד בשדה → מחיקת 10 תווים → הקלדת ההודעה.

---

### `mandatory`

האם הלוקאטור הוא חובה:
- `true` — יזרוק שגיאה אם האלמנט לא נמצא או הפעולה נכשלה
- `false` — ידלג על האלמנט בשקט

---

### `timeout`

זמן המתנה בשניות לפני חיפוש האלמנט. `0` — חיפוש מיידי.

---

### `timeout_for_event`

תנאי ההמתנה לפני ביצוע האירוע. לדוגמה, `"presence_of_element_located"` — ממתין להופעת האלמנט ב-DOM.

---

### `use_mouse`

`true` / `false` — האם להשתמש בעכבר לאינטראקציה עם האלמנט.

---

### `locator_description`

תיאור טקסטואלי של הלוקאטור לצורכי תיעוד ודיבאג.

---

## לוקאטורים מורכבים

ניתן להעביר **רשימות** כערכים למפתחות הלוקאטור לביצוע פעולות רצופות.

### לוקאטור עם רשימות

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
        "לוחץ על הלשונית לפתיחת תיאור המוצר.",
        "קורא נתונים מה-div."
    ]
}
```

שלבי הביצוע:
1. מציאת `//a[contains(@href, '#tab-description')]`
2. ביצוע `click()` עליו
3. מציאת `//div[@id = 'tab-description']//p`
4. החזרת מאפיין `href` שלו

### לוקאטור עם מילון

```json
"sample_locator": {
    "attribute": {"href": "name"},
    ...
}
```

מילון מאפשר שינוי שם המאפיין בעת החילוץ.

---

## כיצד פועל חילוץ הנתונים

הפונקציה `getElementValue` ב-`execute-locators.js` רצה ישירות בהקשר הדף:

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
        if (mandatory) console.error(`לוקאטור חובה לא נמצא: ${locator_description}`);
        return if_list === 'all' ? [] : null;
    }

    if (if_list === 'all') {
        return elements.map(el => el[attribute] ?? el.getAttribute(attribute));
    } else {
        return elements[0][attribute] ?? elements[0].getAttribute(attribute);
    }
}
```

---

## כיצד התוסף בוחר את קובץ הלוקאטורים

ב-`handlers.js`, בעת הוספת רכיב, ה-hostname של הלשונית הנוכחית משמש כשם הקובץ:

```js
const url = new URL(tab.url);
const hostname = url.hostname.replace(/^www\./, '');
const locatorPath = `locators/${hostname}.json`;
const response = await fetch(chrome.runtime.getURL(locatorPath));
const locators = await response.json();
```

---

## מספר גרסאות לוקאטורים לאותו אתר

מבנה הדף עשוי להשתנות — לדוגמה, גרסאות דסקטופ ומובייל. מומלץ לשמור קבצי לוקאטורים נפרדים לכל גרסה:

```
locators/ksp.co.il.json
locators/ksp.co.il_mobile.json
```

---

## כתיבת לוקאטור לאתר חדש

1. פתח דף מוצר באתר הספק
2. לחץ `F12` לפתיחת DevTools
3. השתמש ב-**Inspect** (`Ctrl+Shift+C`) לבחירת האלמנט הרצוי
4. בנה סלקטור XPATH או CSS

בדיקה בקונסולת הדפדפן:
```js
$x("//h1[contains(@class, 'title')]")
document.querySelectorAll(".product-title h1")
```

5. צור קובץ `locators/{hostname}.json`
6. הגדר `"supplier_prefix"` שווה ל-hostname

### דוגמה לקובץ לוקאטורים מינימלי

```json
{
  "supplier_prefix": "ksp.co.il",

  "name": {
    "attribute": "aria-label",
    "by": "XPATH",
    "selector": "//div[@id='product-page-root']//h1[contains(@class, 'title')]",
    "if_list": "first",
    "mandatory": true,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "שם המוצר ב-ksp.co.il"
  },

  "default_image_url": {
    "attribute": "src",
    "by": "XPATH",
    "selector": "//li[contains(@class,'slide selected')]//img",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "תמונה ראשית של המוצר ב-ksp.co.il"
  },

  "specification": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[@id='review-section']",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "מפרט טכני ב-ksp.co.il"
  }
}
```
