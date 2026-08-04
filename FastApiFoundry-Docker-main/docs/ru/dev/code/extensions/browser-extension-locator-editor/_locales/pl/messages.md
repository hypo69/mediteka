# Messages

**Файл:** `extensions/browser-extension-locator-editor/_locales/pl/messages.json`  
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
    "description": "Nazwa rozszerzenia"
  },
  "extensionDescription": {
    "message": "Tworzyć kreatywną treść z informacji na stronie",
    "description": "Opis rozszerzenia"
  },
  "contextMenuTitle": {
    "message": "Stwórz ofertę cenową",
    "description": "Tytuł elementu menu kontekstowego"
  },
  "apiKeyLabel": {
    "message": "Klucz API Google Gemini",
    "description": "Etykieta dla pola wprowadzania klucza API"
  },
  "modelLabel": {
    "message": "Model",
    "description": "Etykieta wyboru modelu"
  },
  "saveButton": {
    "message": "Zapisać",
    "description": "Tekst przycisku Zapisz"
  },
  "statusNoApiKey": {
    "message": "Proszę wprowadzić swój klucz API",
    "description": "Komunikat, gdy klucz API nie został wprowadzony"
  },
  "indicatorAnalyzing": {
    "message": "Twoja oferta cenowa jest w trakcie tworzenia…",
    "description": "Komunikat podczas analizy"
  },
  "errorFetchContent": {
    "message": "Nie udało się pobrać zawartości strony",
    "description": "Błąd podczas pobierania zawartości strony"
  },
  "errorPageTooShort": {
    "message": "Strona zawiera zbyt mało treści",
    "description": "Błąd, gdy strona jest za krótka"
  },
  "errorApi": {
    "message": "Błąd API: $error$",
    "description": "Ogólny komunikat o błędzie API",
    "placeholders": {
      "error": {
        "content": "$1",
        "example": "Nieprawidłowy klucz API"
      }
    }
  },
  "price": {
    "message": "Cena",
    "description": "Cena kompilacji"
  },
  "totalPriceLabel": {
    "message": "Całkowita cena:",
    "description": "Etykieta dla ceny całkowitej w ofercie"
  },
  "saveOfferButton": {
    "message": "Zapisz ofertę",
    "description": "Tekst przycisku 'Zapisz ofertę'"
  },
  "changeImageButton": {
    "message": "Zmień obraz",
    "description": "Tekst przycisku 'Zmień obraz' w stopce"
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
