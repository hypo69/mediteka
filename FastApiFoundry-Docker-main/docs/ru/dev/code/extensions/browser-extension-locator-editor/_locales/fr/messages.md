# Messages

**Файл:** `extensions/browser-extension-locator-editor/_locales/fr/messages.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `extensionName` | `dict` | объект: `message`, `description` |
| `extensionDescription` | `dict` | объект: `message`, `description` |
| `contextMenuTitle` | `dict` | объект: `message`, `description` |
| `apiKeyLabel` | `dict` | объект: `message`, `description` |
| `modelLabel` | `dict` | объект: `message`, `description` |
| `saveButton` | `dict` | объект: `message`, `description` |
| `statusNoApiKey` | `dict` | объект: `message`, `description` |
| `indicatorAnalyzing` | `dict` | объект: `message`, `description` |
| `errorFetchContent` | `dict` | объект: `message`, `description` |
| `errorPageTooShort` | `dict` | объект: `message`, `description` |
| `errorApi` | `dict` | объект: `message`, `description`, `placeholders` |
| `price` | `dict` | объект: `message`, `description` |
| `totalPriceLabel` | `dict` | объект: `message`, `description` |
| `saveOfferButton` | `dict` | объект: `message`, `description` |
| `changeImageButton` | `dict` | объект: `message`, `description` |

**Полная структура:**

```json
{
  "extensionName": {
    "message": "SEOai",
    "description": "Nom de l'extension"
  },
  "extensionDescription": {
    "message": "Créer du contenu créatif à partir des informations de la page",
    "description": "Description de l'extension"
  },
  "contextMenuTitle": {
    "message": "Formuler une offre de prix",
    "description": "Titre de l'élément du menu contextuel"
  },
  "apiKeyLabel": {
    "message": "Clé API Google Gemini",
    "description": "Étiquette pour le champ de saisie de la clé API"
  },
  "modelLabel": {
    "message": "Modèle",
    "description": "Étiquette pour la sélection du modèle"
  },
  "saveButton": {
    "message": "Enregistrer",
    "description": "Texte du bouton Enregistrer"
  },
  "statusNoApiKey": {
    "message": "Veuillez saisir votre clé API",
    "description": "Message lorsque la clé API n'est pas saisie"
  },
  "indicatorAnalyzing": {
    "message": "Votre offre de prix est en cours de formation…",
    "description": "Message pendant l'analyse"
  },
  "errorFetchContent": {
    "message": "Impossible de récupérer le contenu de la page",
    "description": "Erreur lors de la récupération du contenu de la page"
  },
  "errorPageTooShort": {
    "message": "La page contient trop peu de contenu",
    "description": "Erreur lorsque la page est trop courte"
  },
  "errorApi": {
    "message": "Erreur API: $error$",
    "description": "Message d'erreur général de l'API",
    "placeholders": {
      "error": {
        "content": "$1",
        "example": "Clé API invalide"
      }
    }
  },
  "price": {
    "message": "Prix",
    "description": "Prix de la construction"
  },
  "totalPriceLabel": {
    "message": "Prix total:",
    "description": "Étiquette pour le prix total dans l'offre"
  },
  "saveOfferButton": {
    "message": "Sauvegarder l'offre",
    "description": "Texte du bouton 'Sauvegarder l'offre'"
  },
  "changeImageButton": {
    "message": "Changer l'image",
    "description": "Texte du bouton 'Changer l'image' dans le pied de page"
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
