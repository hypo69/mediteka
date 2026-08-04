# Localizzatori di elementi nelle pagine web

Un localizzatore è un oggetto JSON che descrive come trovare un elemento in una pagina, quale azione eseguire su di esso e quale valore estrarre. L'estensione utilizza i localizzatori per raccogliere automaticamente i dati dei prodotti dai siti dei fornitori.

---

## Perché sono necessari i localizzatori

Ogni sito fornitore ha la propria struttura HTML. Per consentire all'estensione di trovare nomi di prodotti, prezzi e specifiche su siti diversi — ogni sito ha il proprio file JSON di localizzatori.

I file dei localizzatori sono memorizzati nella cartella `locators/` e denominati in base all'hostname del sito:
- `locators/amazon.it.json`
- `locators/unieuro.it.json`
- `locators/mediaworld.it.json`
- `locators/euronics.it.json`

Il nome di ogni localizzatore corrisponde al campo da compilare. Ad esempio, il localizzatore `name` recupera il nome del prodotto, `price` — il prezzo:

```js
const data = executeLocators(locators);
// data.name    → nome del prodotto
// data.price   → prezzo del prodotto
```

È anche possibile creare localizzatori ausiliari per azioni sulla pagina. Ad esempio, `close_banner` — per chiudere una finestra pop-up prima della raccolta dei dati.

---

## Struttura di un localizzatore

Ogni localizzatore è un oggetto JSON con le seguenti chiavi:

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
    "locator_description": "Chiude il banner pop-up. Se non è apparso — nessun problema (mandatory: false)."
}
```

---

## Descrizione delle chiavi

### `attribute`

L'attributo da estrarre dall'elemento trovato. Esempi: `innerText`, `src`, `href`, `id`, `aria-label`.

Se impostato su `null` o `false` — viene restituito l'intero elemento web (`WebElement`) invece del valore dell'attributo.

---

### `by`

La strategia di ricerca dell'elemento nella pagina:

| Valore | Corrisponde a |
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

L'espressione per trovare l'elemento. Esempi:

```
(//li[@class = 'slide selected previous'])[1]//img
//a[@id = 'mainpic']//img
//span[@class = 'ltr sku-copy']
```

---

### `if_list`

Definisce cosa fare quando vengono trovati più elementi:

| Valore | Comportamento |
|---|---|
| `first` | Prendere il primo elemento |
| `last` | Prendere l'ultimo elemento |
| `all` | Prendere tutti gli elementi (restituisce una lista) |
| `even` | Prendere gli elementi pari |
| `odd` | Prendere gli elementi dispari |
| `1,2,...` o `[1,3,5]` | Prendere gli elementi nelle posizioni indicate |

È anche possibile specificare l'indice direttamente nel selettore XPATH:
```
(//div[contains(@class, 'description')])[2]//p
```

---

### `event`

Un'azione da eseguire sull'elemento **prima** di estrarre l'attributo. L'ordine è sempre: **azione → attributo**.

Eventi disponibili:

- `click()` — fare clic sull'elemento
- `screenshot()` — catturare l'elemento come PNG. Utile quando un server CDN non serve l'immagine tramite URL
- `scroll()` — scorrere fino all'elemento
- `send_message()` — inviare testo a un campo di input

Esempio — fare clic e poi ottenere `href`:
```json
{
    "attribute": "href",
    "event": "click()",
    "timeout_for_event": "presence_of_element_located"
}
```

Per `send_message`, si raccomanda di usare la variabile `%EXTERNAL_MESSAGE%` con una catena di comandi:
```json
{
    "event": "click();backspace(10);%EXTERNAL_MESSAGE%"
}
```
Questo esegue in sequenza: focus sul campo → cancellazione di 10 caratteri → digitazione del messaggio.

---

### `mandatory`

Se il localizzatore è obbligatorio:
- `true` — genera un errore se l'elemento non viene trovato o l'azione fallisce
- `false` — ignora silenziosamente l'elemento

---

### `timeout`

Tempo di attesa in secondi prima di cercare l'elemento. `0` — ricerca immediata.

---

### `timeout_for_event`

Condizione di attesa prima di eseguire l'evento. Ad esempio, `"presence_of_element_located"` — attende che l'elemento appaia nel DOM.

---

### `use_mouse`

`true` / `false` — se utilizzare il mouse per interagire con l'elemento.

---

### `locator_description`

Descrizione testuale del localizzatore per documentazione e debug.

---

## Localizzatori complessi

Le chiavi del localizzatore possono accettare **liste** per eseguire azioni sequenziali.

### Localizzatore con liste

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
        "Clic sulla scheda per aprire la descrizione.",
        "Lettura dei dati dal div."
    ]
}
```

### Localizzatore con dizionario

```json
"sample_locator": {
    "attribute": {"href": "name"},
    ...
}
```

---

## Più versioni di localizzatori per lo stesso sito

La struttura della pagina può cambiare — ad esempio, le versioni desktop e mobile hanno strutture HTML diverse. Si raccomanda di mantenere file separati:

```
locators/unieuro.it.json
locators/unieuro.it_mobile.json
```

---

## Scrivere un localizzatore per un nuovo sito

1. Aprire una pagina prodotto sul sito del fornitore
2. Premere `F12` per aprire i DevTools
3. Usare **Inspect** (`Ctrl+Shift+C`) per selezionare l'elemento target
4. Costruire un selettore XPATH o CSS

Test nella console del browser:
```js
$x("//h1[contains(@class, 'product-title')]")
document.querySelectorAll(".product-title h1")
```

5. Creare il file `locators/{hostname}.json`
6. Impostare `"supplier_prefix"` uguale all'hostname

### Esempio di file localizzatore minimale

```json
{
  "supplier_prefix": "unieuro.it",

  "name": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//h1[contains(@class,'product-name')]",
    "if_list": "first",
    "mandatory": true,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Nome del prodotto su unieuro.it"
  },

  "default_image_url": {
    "attribute": null,
    "by": "XPATH",
    "selector": "//div[contains(@class,'product-gallery')]//img",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": "screenshot()",
    "locator_description": "Immagine principale del prodotto tramite screenshot"
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
    "locator_description": "Prezzo del prodotto su unieuro.it"
  },

  "specification": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[contains(@class,'product-specs')]",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Specifiche tecniche del prodotto"
  }
}
```
