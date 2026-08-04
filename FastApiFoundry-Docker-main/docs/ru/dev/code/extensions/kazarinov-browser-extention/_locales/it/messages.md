# Messages

**Файл:** `extensions/kazarinov-browser-extention/_locales/it/messages.json`  
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
    "message": "Offerta di Prezzo Kazarinov",
    "description": "Nome dell'estensione"
  },
  "extensionDescription": {
    "message": "Crea descrizioni chiare e strutturate dei componenti del computer",
    "description": "Descrizione dell'estensione"
  },
  "contextMenuTitle": {
    "message": "Genera Offerta di Prezzo",
    "description": "Titolo della voce del menu contestuale"
  },
  "apiKeyLabel": {
    "message": "Chiave API di Google Gemini",
    "description": "Etichetta del campo per la chiave API"
  },
  "modelLabel": {
    "message": "Modello",
    "description": "Etichetta del selettore del modello"
  },
  "saveButton": {
    "message": "Salva",
    "description": "Testo del pulsante Salva"
  },
  "statusNoApiKey": {
    "message": "Per favore, inserisci la tua chiave API",
    "description": "Messaggio mostrato quando la chiave API non è presente"
  },
  "indicatorAnalyzing": {
    "message": "Generazione della tua offerta di prezzo…",
    "description": "Messaggio mostrato durante l'analisi"
  },
  "errorFetchContent": {
    "message": "Impossibile recuperare il contenuto della pagina",
    "description": "Errore durante il recupero del contenuto della pagina"
  },
  "errorPageTooShort": {
    "message": "La pagina contiene troppo poco contenuto",
    "description": "Errore quando la pagina è troppo corta"
  },
  "errorApi": {
    "message": "Errore API: $error$",
    "description": "Messaggio di errore generico dell'API",
    "placeholders": {
      "error": {
        "content": "$1",
        "example": "Chiave API non valida"
      }
    }
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
