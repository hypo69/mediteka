# Messages

**Файл:** `extensions/kazarinov-browser-extention/_locales/uk/messages.json`  
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
    "message": "Пропозиція ціни Казарінов",
    "description": "Назва розширення"
  },
  "extensionDescription": {
    "message": "Створює чіткі та структуровані описи комп’ютерних компонентів",
    "description": "Опис розширення"
  },
  "contextMenuTitle": {
    "message": "Створити пропозицію ціни",
    "description": "Назва пункту контекстного меню"
  },
  "apiKeyLabel": {
    "message": "API-ключ Google Gemini",
    "description": "Мітка поля для введення ключа API"
  },
  "modelLabel": {
    "message": "Модель",
    "description": "Мітка для вибору моделі"
  },
  "saveButton": {
    "message": "Зберегти",
    "description": "Текст кнопки збереження"
  },
  "statusNoApiKey": {
    "message": "Будь ласка, введіть ваш API-ключ",
    "description": "Повідомлення про стан, коли API-ключ не введено"
  },
  "indicatorAnalyzing": {
    "message": "Створюється ваша пропозиція ціни…",
    "description": "Повідомлення під час аналізу"
  },
  "errorFetchContent": {
    "message": "Не вдалося отримати вміст сторінки",
    "description": "Помилка при отриманні вмісту сторінки"
  },
  "errorPageTooShort": {
    "message": "Сторінка містить недостатньо контенту",
    "description": "Помилка, коли сторінка занадто коротка"
  },
  "errorApi": {
    "message": "Помилка API: $error$",
    "description": "Загальна помилка API",
    "placeholders": {
      "error": {
        "content": "$1",
        "example": "Невірний API-ключ"
      }
    }
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
