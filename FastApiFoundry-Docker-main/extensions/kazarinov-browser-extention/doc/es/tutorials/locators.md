# Localizadores de elementos en páginas web

Un localizador es un objeto JSON que describe cómo encontrar un elemento en una página, qué acción realizar sobre él y qué valor extraer. La extensión utiliza localizadores para recopilar automáticamente datos de productos en los sitios de proveedores.

---

## Por qué se necesitan los localizadores

Cada sitio proveedor tiene su propia estructura HTML. Para que la extensión pueda encontrar nombres de productos, precios y especificaciones en diferentes sitios — cada sitio tiene su propio archivo JSON de localizadores.

Los archivos de localizadores se almacenan en la carpeta `locators/` y se nombran según el hostname del sitio:
- `locators/pccomponentes.com.json`
- `locators/mediamarkt.es.json`
- `locators/fnac.es.json`
- `locators/elcorteingles.es.json`

El nombre de cada localizador corresponde al campo que debe rellenarse. Por ejemplo, el localizador `name` obtiene el nombre del producto, `price` — el precio:

```js
const data = executeLocators(locators);
// data.name    → nombre del producto
// data.price   → precio del producto
```

También se pueden crear localizadores auxiliares para acciones en la página. Por ejemplo, `close_banner` — para cerrar una ventana emergente antes de recopilar datos.

---

## Estructura de un localizador

Cada localizador es un objeto JSON con las siguientes claves:

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
    "locator_description": "Cierra la ventana emergente. Si no apareció — no hay problema (mandatory: false)."
}
```

---

## Descripción de las claves

### `attribute`

El atributo a extraer del elemento encontrado. Ejemplos: `innerText`, `src`, `href`, `id`, `aria-label`.

Si se establece en `null` o `false` — se devuelve el elemento web completo (`WebElement`) en lugar del valor del atributo.

---

### `by`

La estrategia de búsqueda del elemento en la página:

| Valor | Corresponde a |
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

La expresión para encontrar el elemento. Ejemplos:

```
(//li[@class = 'slide selected previous'])[1]//img
//a[@id = 'mainpic']//img
//span[@class = 'ltr sku-copy']
```

---

### `if_list`

Define qué hacer cuando se encuentran varios elementos:

| Valor | Comportamiento |
|---|---|
| `first` | Tomar el primer elemento |
| `last` | Tomar el último elemento |
| `all` | Tomar todos los elementos (devuelve una lista) |
| `even` | Tomar los elementos pares |
| `odd` | Tomar los elementos impares |
| `1,2,...` o `[1,3,5]` | Tomar los elementos en las posiciones indicadas |

También se puede especificar el índice directamente en el selector XPATH:
```
(//div[contains(@class, 'description')])[2]//p
```

---

### `event`

Una acción a realizar sobre el elemento **antes** de extraer el atributo. El orden siempre es: **acción → atributo**.

Eventos disponibles:

- `click()` — hacer clic en el elemento
- `screenshot()` — capturar el elemento como PNG. Útil cuando un servidor CDN no sirve la imagen por URL
- `scroll()` — desplazarse hasta el elemento
- `send_message()` — enviar texto a un campo de entrada

Ejemplo — hacer clic y luego obtener `href`:
```json
{
    "attribute": "href",
    "event": "click()",
    "timeout_for_event": "presence_of_element_located"
}
```

Para `send_message`, se recomienda usar la variable `%EXTERNAL_MESSAGE%` con una cadena de comandos:
```json
{
    "event": "click();backspace(10);%EXTERNAL_MESSAGE%"
}
```
Esto ejecuta secuencialmente: enfocar el campo → borrar 10 caracteres → escribir el mensaje.

---

### `mandatory`

Si el localizador es obligatorio:
- `true` — lanza un error si el elemento no se encuentra o la acción falla
- `false` — omite silenciosamente el elemento

---

### `timeout`

Tiempo de espera en segundos antes de buscar el elemento. `0` — búsqueda inmediata.

---

### `timeout_for_event`

Condición de espera antes de ejecutar el evento. Por ejemplo, `"presence_of_element_located"` — espera a que el elemento aparezca en el DOM.

---

### `use_mouse`

`true` / `false` — si se debe usar el ratón para interactuar con el elemento.

---

### `locator_description`

Descripción textual del localizador para documentación y depuración.

---

## Localizadores complejos

Las claves del localizador pueden aceptar **listas** para realizar acciones secuenciales.

### Localizador con listas

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
        "Clic en la pestaña para abrir la descripción.",
        "Lectura de datos desde el div."
    ]
}
```

### Localizador con diccionario

```json
"sample_locator": {
    "attribute": {"href": "name"},
    ...
}
```

---

## Varias versiones de localizadores para un mismo sitio

La estructura de la página puede cambiar — por ejemplo, las versiones de escritorio y móvil tienen estructuras HTML diferentes. Se recomienda mantener archivos separados:

```
locators/pccomponentes.com.json
locators/pccomponentes.com_mobile.json
```

---

## Escribir un localizador para un nuevo sitio

1. Abra una página de producto en el sitio del proveedor
2. Pulse `F12` para abrir las DevTools
3. Use **Inspect** (`Ctrl+Shift+C`) para seleccionar el elemento objetivo
4. Construya un selector XPATH o CSS

Prueba en la consola del navegador:
```js
$x("//h1[contains(@class, 'product-title')]")
document.querySelectorAll(".product-title h1")
```

5. Cree el archivo `locators/{hostname}.json`
6. Establezca `"supplier_prefix"` igual al hostname

### Ejemplo de archivo de localizadores mínimo

```json
{
  "supplier_prefix": "pccomponentes.com",

  "name": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//h1[contains(@class,'product-title')]",
    "if_list": "first",
    "mandatory": true,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Nombre del producto en pccomponentes.com"
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
    "locator_description": "Imagen principal del producto mediante captura de pantalla"
  },

  "price": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//span[contains(@class,'price-container')]",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Precio del producto en pccomponentes.com"
  },

  "specification": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[contains(@class,'product-specs')]//table",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Tabla de especificaciones técnicas"
  }
}
```
