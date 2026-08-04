# Messages

**Файл:** `extensions/kazarinov-browser-extention/_locales/pl/messages.json`  
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

**Полная структура:**

```json
{
  "extensionName": {
    "message": "Oferta Cenowa Kazarinov",
    "description": "Nazwa rozszerzenia"
  },
  "extensionDescription": {
    "message": "Tworzy przejrzyste i uporządkowane opisy komponentów komputerowych",
    "description": "Opis rozszerzenia"
  },
  "contextMenuTitle": {
    "message": "Utwórz ofertę cenową",
    "description": "Tytuł elementu w menu kontekstowym"
  },
  "apiKeyLabel": {
    "message": "Klucz API Google Gemini",
    "description": "Etykieta pola dla klucza API"
  },
  "modelLabel": {
    "message": "Model",
    "description": "Etykieta wyboru modelu"
  },
  "saveButton": {
    "message": "Zapisz",
    "description": "Tekst przycisku zapisu"
  },
  "statusNoApiKey": {
    "message": "Proszę wprowadzić klucz API",
    "description": "Komunikat, gdy klucz API nie został wprowadzony"
  },
  "indicatorAnalyzing": {
    "message": "Tworzenie Twojej oferty cenowej…",
    "description": "Komunikat wyświetlany podczas analizy"
  },
  "errorFetchContent": {
    "message": "Nie udało się pobrać zawartości strony",
    "description": "Błąd podczas pobierania zawartości strony"
  },
  "errorPageTooShort": {
    "message": "Strona zawiera zbyt mało treści",
    "description": "Błąd, gdy strona jest zbyt krótka"
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
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
