# Web-Element-Locatoren

Ein Locator ist ein JSON-Objekt, das beschreibt, wie ein Element auf einer Seite gefunden wird, welche Aktion darauf ausgeführt werden soll und welcher Wert extrahiert werden soll. Die Erweiterung verwendet Locatoren, um Produktdaten von Lieferanten-Websites automatisch zu sammeln.

---

## Warum Locatoren benötigt werden

Jede Lieferanten-Website hat ihre eigene HTML-Struktur. Damit die Erweiterung Produktnamen, Preise und Spezifikationen auf verschiedenen Websites finden kann — hat jede Website ihre eigene JSON-Datei mit Locatoren.

Die Locator-Dateien werden im Ordner `locators/` gespeichert und nach dem Hostname der Website benannt:
- `locators/mindfactory.de.json`
- `locators/alternate.de.json`
- `locators/computeruniverse.net.json`
- `locators/notebooksbilliger.de.json`

Der Name jedes Locators entspricht dem Feld, das befüllt werden soll. Zum Beispiel ruft der Locator `name` den Produktnamen ab, `price` — den Preis:

```js
const data = executeLocators(locators);
// data.name    → Produktname
// data.price   → Produktpreis
```

Es können auch Hilfs-Locatoren für Seitenaktionen erstellt werden. Zum Beispiel `close_banner` — zum Schließen eines Pop-up-Fensters vor der Datenerfassung.

---

## Struktur eines Locators

Jeder Locator ist ein JSON-Objekt mit folgenden Schlüsseln:

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
    "locator_description": "Schließt das Pop-up-Banner. Falls es nicht erschienen ist — kein Problem (mandatory: false)."
}
```

---

## Beschreibung der Schlüssel

### `attribute`

Das Attribut, das aus dem gefundenen Element extrahiert werden soll. Beispiele: `innerText`, `src`, `href`, `id`, `aria-label`.

Bei `null` oder `false` — wird das gesamte Web-Element (`WebElement`) zurückgegeben statt eines Attributwerts.

---

### `by`

Die Suchstrategie für das Element auf der Seite:

| Wert | Entspricht |
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

Der Ausdruck zum Finden des Elements. Beispiele:

```
(//li[@class = 'slide selected previous'])[1]//img
//a[@id = 'mainpic']//img
//span[@class = 'ltr sku-copy']
```

---

### `if_list`

Legt fest, was zu tun ist, wenn mehrere Elemente gefunden werden:

| Wert | Verhalten |
|---|---|
| `first` | Erstes Element nehmen |
| `last` | Letztes Element nehmen |
| `all` | Alle Elemente nehmen (gibt eine Liste zurück) |
| `even` | Gerade Elemente nehmen |
| `odd` | Ungerade Elemente nehmen |
| `1,2,...` oder `[1,3,5]` | Elemente an den angegebenen Positionen nehmen |

Der Index kann auch direkt im XPATH-Selektor angegeben werden:
```
(//div[contains(@class, 'description')])[2]//p
```

---

### `event`

Eine Aktion, die **vor** der Attributextraktion am Element ausgeführt wird. Die Reihenfolge ist immer: **Aktion → Attribut**.

Verfügbare Ereignisse:

- `click()` — auf das Element klicken
- `screenshot()` — Element als PNG aufnehmen. Nützlich wenn ein CDN-Server das Bild nicht per URL liefert
- `scroll()` — zum Element scrollen
- `send_message()` — Text an ein Eingabefeld senden

Beispiel — klicken und dann `href` abrufen:
```json
{
    "attribute": "href",
    "event": "click()",
    "timeout_for_event": "presence_of_element_located"
}
```

Für `send_message` wird empfohlen, die Variable `%EXTERNAL_MESSAGE%` mit einer Befehlskette zu verwenden:
```json
{
    "event": "click();backspace(10);%EXTERNAL_MESSAGE%"
}
```
Dies führt sequenziell aus: Feld fokussieren → 10 Zeichen löschen → Nachricht eingeben.

---

### `mandatory`

Ob der Locator obligatorisch ist:
- `true` — wirft einen Fehler, wenn das Element nicht gefunden wird oder die Aktion fehlschlägt
- `false` — überspringt das Element stillschweigend

---

### `timeout`

Wartezeit in Sekunden vor der Elementsuche. `0` — sofortige Suche.

---

### `timeout_for_event`

Wartebedingung vor der Ereignisausführung. Zum Beispiel `"presence_of_element_located"` — wartet auf das Erscheinen des Elements im DOM.

---

### `use_mouse`

`true` / `false` — ob die Maus für die Interaktion mit dem Element verwendet werden soll.

---

### `locator_description`

Textbeschreibung des Locators für Dokumentation und Debugging.

---

## Komplexe Locatoren

Locator-Schlüssel können **Listen** akzeptieren, um sequenzielle Aktionen auszuführen.

### Locator mit Listen

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
        "Klick auf den Tab zum Öffnen der Beschreibung.",
        "Daten aus dem Div lesen."
    ]
}
```

### Locator mit Dictionary

```json
"sample_locator": {
    "attribute": {"href": "name"},
    ...
}
```

---

## Mehrere Locator-Versionen für eine Website

Die Seitenstruktur kann sich ändern — z.B. haben Desktop- und Mobile-Versionen unterschiedliche HTML-Strukturen. Es wird empfohlen, separate Dateien zu pflegen:

```
locators/mindfactory.de.json
locators/mindfactory.de_mobile.json
```

---

## Einen Locator für eine neue Website schreiben

1. Produktseite beim Lieferanten öffnen
2. `F12` drücken um die DevTools zu öffnen
3. **Inspect** (`Ctrl+Shift+C`) verwenden um das Zielelement auszuwählen
4. XPATH- oder CSS-Selektor erstellen

Test in der Browser-Konsole:
```js
$x("//h1[contains(@class, 'product-title')]")
document.querySelectorAll(".product-title h1")
```

5. Datei `locators/{hostname}.json` erstellen
6. `"supplier_prefix"` gleich dem Hostname setzen

### Beispiel einer minimalen Locator-Datei

```json
{
  "supplier_prefix": "mindfactory.de",

  "name": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//h1[contains(@class,'product-name')]",
    "if_list": "first",
    "mandatory": true,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Produktname auf mindfactory.de"
  },

  "default_image_url": {
    "attribute": null,
    "by": "XPATH",
    "selector": "//div[contains(@class,'product-image')]//img",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": "screenshot()",
    "locator_description": "Hauptproduktbild per Screenshot"
  },

  "price": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//span[contains(@class,'price')]",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Produktpreis auf mindfactory.de"
  },

  "specification": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[contains(@class,'product-details')]//table",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Technische Spezifikationstabelle"
  }
}
```
