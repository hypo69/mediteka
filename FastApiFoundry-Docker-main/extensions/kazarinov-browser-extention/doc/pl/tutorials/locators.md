# Lokatory elementów na stronach internetowych

Lokator to obiekt JSON opisujący jak znaleźć element na stronie, jaką akcję na nim wykonać i jaką wartość wyodrębnić. Rozszerzenie używa lokatorów do automatycznego zbierania danych o produktach ze stron dostawców.

---

## Dlaczego lokatory są potrzebne

Każda strona dostawcy ma własną strukturę HTML. Aby rozszerzenie mogło znajdować nazwy produktów, ceny i specyfikacje na różnych stronach — każda strona ma własny plik JSON z lokatorami.

Pliki lokatorów są przechowywane w folderze `locators/` i nazwane według hostname strony:
- `locators/morele.net.json`
- `locators/x-kom.pl.json`
- `locators/mediaexpert.pl.json`
- `locators/komputronik.pl.json`

Nazwa każdego lokatora odpowiada polu, które ma zostać wypełnione. Na przykład lokator `name` pobiera nazwę produktu, `price` — cenę:

```js
const data = executeLocators(locators);
// data.name    → nazwa produktu
// data.price   → cena produktu
```

Można też tworzyć pomocnicze lokatory do akcji na stronie. Na przykład `close_banner` — do zamknięcia okna pop-up przed zbieraniem danych.

---

## Struktura lokatora

Każdy lokator to obiekt JSON z następującymi kluczami:

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
    "locator_description": "Zamyka baner pop-up. Jeśli nie pojawił się — nie ma problemu (mandatory: false)."
}
```

---

## Opis kluczy

### `attribute`

Atrybut do wyodrębnienia ze znalezionego elementu. Przykłady: `innerText`, `src`, `href`, `id`, `aria-label`.

Jeśli ustawiono `null` lub `false` — zwracany jest cały element webowy (`WebElement`) zamiast wartości atrybutu.

---

### `by`

Strategia wyszukiwania elementu na stronie:

| Wartość | Odpowiada |
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

Wyrażenie do znalezienia elementu. Przykłady:

```
(//li[@class = 'slide selected previous'])[1]//img
//a[@id = 'mainpic']//img
//span[@class = 'ltr sku-copy']
```

---

### `if_list`

Określa co zrobić gdy znaleziono wiele elementów:

| Wartość | Zachowanie |
|---|---|
| `first` | Wziąć pierwszy element |
| `last` | Wziąć ostatni element |
| `all` | Wziąć wszystkie elementy (zwraca listę) |
| `even` | Wziąć elementy parzyste |
| `odd` | Wziąć elementy nieparzyste |
| `1,2,...` lub `[1,3,5]` | Wziąć elementy na wskazanych pozycjach |

Można też podać indeks bezpośrednio w selektorze XPATH:
```
(//div[contains(@class, 'description')])[2]//p
```

---

### `event`

Akcja do wykonania na elemencie **przed** wyodrębnieniem atrybutu. Kolejność zawsze: **akcja → atrybut**.

Dostępne zdarzenia:

- `click()` — kliknięcie elementu
- `screenshot()` — przechwycenie elementu jako PNG. Przydatne gdy serwer CDN nie serwuje obrazu przez URL
- `scroll()` — przewinięcie do elementu
- `send_message()` — wysłanie tekstu do pola wejściowego

Przykład — kliknij, a następnie pobierz `href`:
```json
{
    "attribute": "href",
    "event": "click()",
    "timeout_for_event": "presence_of_element_located"
}
```

Dla `send_message` zaleca się użycie zmiennej `%EXTERNAL_MESSAGE%` z łańcuchem poleceń:
```json
{
    "event": "click();backspace(10);%EXTERNAL_MESSAGE%"
}
```
Wykonuje sekwencyjnie: fokus na polu → usunięcie 10 znaków → wpisanie wiadomości.

---

### `mandatory`

Czy lokator jest obowiązkowy:
- `true` — zgłasza błąd jeśli element nie zostanie znaleziony lub akcja się nie powiedzie
- `false` — cicho pomija element

---

### `timeout`

Czas oczekiwania w sekundach przed wyszukaniem elementu. `0` — natychmiastowe wyszukiwanie.

---

### `timeout_for_event`

Warunek oczekiwania przed wykonaniem zdarzenia. Na przykład `"presence_of_element_located"` — czeka na pojawienie się elementu w DOM.

---

### `use_mouse`

`true` / `false` — czy używać myszy do interakcji z elementem.

---

### `locator_description`

Tekstowy opis lokatora do celów dokumentacji i debugowania.

---

## Złożone lokatory

Klucze lokatora mogą przyjmować **listy** do wykonywania sekwencyjnych akcji.

### Lokator z listami

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
        "Kliknięcie zakładki w celu otwarcia opisu.",
        "Odczyt danych z diva."
    ]
}
```

### Lokator ze słownikiem

```json
"sample_locator": {
    "attribute": {"href": "name"},
    ...
}
```

---

## Wiele wersji lokatorów dla jednej strony

Struktura strony może się zmieniać — np. wersje desktopowe i mobilne mają różne struktury HTML. Zaleca się utrzymywanie osobnych plików:

```
locators/x-kom.pl.json
locators/x-kom.pl_mobile.json
```

---

## Pisanie lokatora dla nowej strony

1. Otwórz stronę produktu u dostawcy
2. Naciśnij `F12` aby otworzyć DevTools
3. Użyj **Inspect** (`Ctrl+Shift+C`) aby wybrać docelowy element
4. Zbuduj selektor XPATH lub CSS

Test w konsoli przeglądarki:
```js
$x("//h1[contains(@class, 'product-title')]")
document.querySelectorAll(".product-title h1")
```

5. Utwórz plik `locators/{hostname}.json`
6. Ustaw `"supplier_prefix"` równy hostname

### Przykład minimalnego pliku lokatorów

```json
{
  "supplier_prefix": "x-kom.pl",

  "name": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//h1[contains(@class,'product-name')]",
    "if_list": "first",
    "mandatory": true,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Nazwa produktu na x-kom.pl"
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
    "locator_description": "Główne zdjęcie produktu przez zrzut ekranu"
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
    "locator_description": "Cena produktu na x-kom.pl"
  },

  "specification": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[contains(@class,'specification')]//table",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Tabela specyfikacji technicznych"
  }
}
```
