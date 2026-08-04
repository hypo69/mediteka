# Messages

**Файл:** `extensions/kazarinov-browser-extention/_locales/ru/messages.json`  
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
    "message": "Предложение цены Казаринов",
    "description": "Название расширения"
  },
  "extensionDescription": {
    "message": "Создаёт чёткие и структурированные описания компонентов компьютера",
    "description": "Описание расширения"
  },
  "contextMenuTitle": {
    "message": "Сформировать предложение цены",
    "description": "Название пункта контекстного меню"
  },
  "apiKeyLabel": {
    "message": "API-ключ Google Gemini",
    "description": "Подпись для поля ввода API-ключа"
  },
  "modelLabel": {
    "message": "Модель",
    "description": "Подпись для выбора модели"
  },
  "saveButton": {
    "message": "Сохранить",
    "description": "Текст кнопки сохранения"
  },
  "statusNoApiKey": {
    "message": "Пожалуйста, введите ваш API-ключ",
    "description": "Сообщение, когда API-ключ не введён"
  },
  "indicatorAnalyzing": {
    "message": "Формируется ваше предложение цены…",
    "description": "Сообщение во время анализа"
  },
  "errorFetchContent": {
    "message": "Не удалось получить содержимое страницы",
    "description": "Ошибка при получении содержимого страницы"
  },
  "errorPageTooShort": {
    "message": "Страница содержит слишком мало контента",
    "description": "Ошибка, когда страница слишком короткая"
  },
  "errorApi": {
    "message": "Ошибка API: $error$",
    "description": "Общее сообщение об ошибке API",
    "placeholders": {
      "error": {
        "content": "$1",
        "example": "Неверный API-ключ"
      }
    }
  },
  "price": {
    "message": "Цена",
    "description": "Цена сборки"
  },
  "totalPriceLabel": {
    "message": "Итоговая цена:",
    "description": "Подпись для итоговой цены в предложении"
  },
  "saveOfferButton": {
    "message": "Сохранить предложение",
    "description": "Текст кнопки 'Сохранить предложение'"
  },
  "changeImageButton": {
    "message": "Изменить картинку",
    "description": "Текст кнопки 'Изменить картинку' в футере"
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
