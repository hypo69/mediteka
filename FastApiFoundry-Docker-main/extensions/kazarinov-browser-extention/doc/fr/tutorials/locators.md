# Localisateurs d'éléments sur une page web

Un localisateur est un objet JSON qui décrit comment trouver un élément sur une page, quelle action effectuer dessus et quelle valeur en extraire. L'extension utilise des localisateurs pour collecter automatiquement les données produits sur les sites des fournisseurs.

---

## Pourquoi les localisateurs sont nécessaires

Chaque site fournisseur possède sa propre structure HTML. Pour que l'extension puisse trouver les noms de produits, les prix et les spécifications sur différents sites — chaque site dispose de son propre fichier JSON de localisateurs.

Les fichiers de localisateurs sont stockés dans le dossier `locators/` et nommés d'après le hostname du site :
- `locators/ldlc.com.json`
- `locators/materiel.net.json`
- `locators/rueducommerce.fr.json`
- `locators/topachat.com.json`

Le nom de chaque localisateur correspond au champ à remplir. Par exemple, le localisateur `name` récupère le nom du produit, `price` — le prix :

```js
const data = executeLocators(locators);
// data.name    → nom du produit
// data.price   → prix du produit
```

Il est également possible de créer des localisateurs auxiliaires pour des actions sur la page. Par exemple, `close_banner` — pour fermer une fenêtre pop-up avant la collecte des données.

---

## Structure d'un localisateur

Chaque localisateur est un objet JSON avec les clés suivantes :

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
    "locator_description": "Ferme la fenêtre pop-up. Si elle n'est pas apparue — pas de problème (mandatory: false)."
}
```

---

## Description des clés

### `attribute`

L'attribut à extraire de l'élément trouvé. Exemples : `innerText`, `src`, `href`, `id`, `aria-label`.

Si défini à `null` ou `false` — l'élément web entier (`WebElement`) est retourné au lieu d'une valeur d'attribut.

---

### `by`

La stratégie de recherche de l'élément sur la page :

| Valeur | Correspond à |
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

L'expression pour trouver l'élément. Exemples :

```
(//li[@class = 'slide selected previous'])[1]//img
//a[@id = 'mainpic']//img
//span[@class = 'ltr sku-copy']
```

---

### `if_list`

Définit quoi faire lorsque plusieurs éléments sont trouvés :

| Valeur | Comportement |
|---|---|
| `first` | Prendre le premier élément |
| `last` | Prendre le dernier élément |
| `all` | Prendre tous les éléments (retourne une liste) |
| `even` | Prendre les éléments pairs |
| `odd` | Prendre les éléments impairs |
| `1,2,...` ou `[1,3,5]` | Prendre les éléments aux positions indiquées |

Il est aussi possible de spécifier l'index directement dans le sélecteur XPATH :
```
(//div[contains(@class, 'description')])[2]//p
```

---

### `event`

Une action à effectuer sur l'élément **avant** l'extraction de l'attribut. L'ordre est toujours : **action → attribut**.

Événements disponibles :

- `click()` — cliquer sur l'élément
- `screenshot()` — capturer l'élément en PNG. Utile quand un serveur CDN ne sert pas l'image via URL
- `scroll()` — faire défiler jusqu'à l'élément
- `send_message()` — envoyer du texte à un champ de saisie

Exemple — cliquer puis obtenir `href` :
```json
{
    "attribute": "href",
    "event": "click()",
    "timeout_for_event": "presence_of_element_located"
}
```

Pour `send_message`, il est recommandé d'utiliser la variable `%EXTERNAL_MESSAGE%` avec une chaîne de commandes :
```json
{
    "event": "click();backspace(10);%EXTERNAL_MESSAGE%"
}
```
Cela exécute séquentiellement : focus sur le champ → effacement de 10 caractères → saisie du message.

---

### `mandatory`

Caractère obligatoire du localisateur :
- `true` — lève une erreur si l'élément n'est pas trouvé ou si l'action échoue
- `false` — ignore silencieusement l'élément

---

### `timeout`

Temps d'attente en secondes avant la recherche de l'élément. `0` — recherche immédiate.

---

### `timeout_for_event`

Condition d'attente avant l'exécution de l'événement. Par exemple, `"presence_of_element_located"` — attend l'apparition de l'élément dans le DOM.

---

### `use_mouse`

`true` / `false` — utiliser ou non la souris pour interagir avec l'élément.

---

### `locator_description`

Description textuelle du localisateur à des fins de documentation et de débogage.

---

## Localisateurs complexes

Les clés du localisateur peuvent accepter des **listes** pour effectuer des actions séquentielles.

### Localisateur avec listes

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
        "Clic sur l'onglet pour ouvrir la description.",
        "Lecture des données depuis le div."
    ]
}
```

### Localisateur avec dictionnaire

```json
"sample_locator": {
    "attribute": {"href": "name"},
    ...
}
```

---

## Plusieurs versions de localisateurs pour un même site

La structure de la page peut changer — par exemple, les versions bureau et mobile ont des structures HTML différentes. Il est recommandé de conserver des fichiers séparés :

```
locators/ldlc.com.json
locators/ldlc.com_mobile.json
```

---

## Écrire un localisateur pour un nouveau site

1. Ouvrez une page produit sur le site du fournisseur
2. Appuyez sur `F12` pour ouvrir les DevTools
3. Utilisez **Inspect** (`Ctrl+Shift+C`) pour sélectionner l'élément cible
4. Construisez un sélecteur XPATH ou CSS

Test dans la console du navigateur :
```js
$x("//h1[contains(@class, 'product-title')]")
document.querySelectorAll(".product-title h1")
```

5. Créez le fichier `locators/{hostname}.json`
6. Définissez `"supplier_prefix"` égal au hostname

### Exemple de fichier localisateur minimal

```json
{
  "supplier_prefix": "ldlc.com",

  "name": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//h1[contains(@class, 'title-1')]",
    "if_list": "first",
    "mandatory": true,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Nom du produit sur ldlc.com"
  },

  "default_image_url": {
    "attribute": null,
    "by": "XPATH",
    "selector": "//div[contains(@class,'pic-product')]//img",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": "screenshot()",
    "locator_description": "Image principale du produit via capture d'écran"
  },

  "price": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[contains(@class,'price')]//span[contains(@class,'price')]",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Prix du produit sur ldlc.com"
  },

  "specification": {
    "attribute": "innerText",
    "by": "XPATH",
    "selector": "//div[@id='caracteristiques']//table",
    "if_list": "first",
    "mandatory": false,
    "timeout": 0,
    "timeout_for_event": "presence_of_element_located",
    "event": null,
    "locator_description": "Tableau des caractéristiques techniques"
  }
}
```
