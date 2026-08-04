# Messages

**Файл:** `extensions/browser-extension-locator-editor/_locales/es/messages.json`  
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
    "description": "Nombre de la extensión"
  },
  "extensionDescription": {
    "message": "Crear contenido creativo a partir de la información de la página",
    "description": "Descripción de la extensión"
  },
  "contextMenuTitle": {
    "message": "Formar una propuesta de precio",
    "description": "Título del elemento del menú contextual"
  },
  "apiKeyLabel": {
    "message": "Clave de API de Google Gemini",
    "description": "Etiqueta para el campo de entrada de la clave API"
  },
  "modelLabel": {
    "message": "Modelo",
    "description": "Etiqueta para la selección del modelo"
  },
  "saveButton": {
    "message": "Guardar",
    "description": "Texto del botón Guardar"
  },
  "statusNoApiKey": {
    "message": "Por favor, introduzca su clave API",
    "description": "Mensaje cuando no se introduce la clave API"
  },
  "indicatorAnalyzing": {
    "message": "Se está generando su oferta de precio…",
    "description": "Mensaje durante el análisis"
  },
  "errorFetchContent": {
    "message": "No se pudo obtener el contenido de la página",
    "description": "Error al obtener el contenido de la página"
  },
  "errorPageTooShort": {
    "message": "La página contiene muy poco contenido",
    "description": "Error cuando la página es demasiado corta"
  },
  "errorApi": {
    "message": "Error de API: $error$",
    "description": "Mensaje de error general de la API",
    "placeholders": {
      "error": {
        "content": "$1",
        "example": "Clave de API no válida"
      }
    }
  },
  "price": {
    "message": "Precio",
    "description": "Precio de la construcción"
  },
  "totalPriceLabel": {
    "message": "Precio total:",
    "description": "Etiqueta para el precio total en la oferta"
  },
  "saveOfferButton": {
    "message": "Guardar oferta",
    "description": "Texto del botón 'Guardar oferta'"
  },
  "changeImageButton": {
    "message": "Cambiar imagen",
    "description": "Texto del botón 'Cambiar imagen' en el pie de página"
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
