# Messages

**Файл:** `extensions/browser-extension-locator-editor/_locales/en-GB/messages.json`  
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
    "description": "Extension name"
  },
  "extensionDescription": {
    "message": "Create creative content from the information on the page",
    "description": "Extension description"
  },
  "contextMenuTitle": {
    "message": "Generate a price proposal",
    "description": "Context menu item title"
  },
  "apiKeyLabel": {
    "message": "Google Gemini API key",
    "description": "Label for API key input field"
  },
  "modelLabel": {
    "message": "Model",
    "description": "Label for model selection"
  },
  "saveButton": {
    "message": "Save",
    "description": "Save button text"
  },
  "statusNoApiKey": {
    "message": "Please enter your API key",
    "description": "Message when API key is not entered"
  },
  "indicatorAnalyzing": {
    "message": "Your price offer is being generated…",
    "description": "Message during analysis"
  },
  "errorFetchContent": {
    "message": "Failed to get page content",
    "description": "Error when getting page content"
  },
  "errorPageTooShort": {
    "message": "The page contains too little content",
    "description": "Error when page is too short"
  },
  "errorApi": {
    "message": "API error: $error$",
    "description": "General API error message",
    "placeholders": {
      "error": {
        "content": "$1",
        "example": "Invalid API key"
      }
    }
  },
  "price": {
    "message": "Price",
    "description": "Build price"
  },
  "totalPriceLabel": {
    "message": "Total price:",
    "description": "Label for total price in the offer"
  },
  "saveOfferButton": {
    "message": "Save offer",
    "description": "Text for 'Save offer' button"
  },
  "changeImageButton": {
    "message": "Change image",
    "description": "Text for 'Change image' button in the footer"
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
