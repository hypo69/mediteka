# Messages

**Файл:** `extensions/browser-extension-locator-editor/_locales/pt-BR/messages.json`  
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
    "description": "Nome da extensão"
  },
  "extensionDescription": {
    "message": "Criar conteúdo criativo a partir das informações da página",
    "description": "Descrição da extensão"
  },
  "contextMenuTitle": {
    "message": "Gerar proposta de preço",
    "description": "Título do item do menu de contexto"
  },
  "apiKeyLabel": {
    "message": "Chave de API do Google Gemini",
    "description": "Rótulo para o campo de entrada da chave API"
  },
  "modelLabel": {
    "message": "Modelo",
    "description": "Rótulo para seleção do modelo"
  },
  "saveButton": {
    "message": "Salvar",
    "description": "Texto do botão Salvar"
  },
  "statusNoApiKey": {
    "message": "Por favor, insira sua chave de API",
    "description": "Mensagem quando a chave API não é inserida"
  },
  "indicatorAnalyzing": {
    "message": "Seu orçamento está sendo gerado…",
    "description": "Mensagem durante a análise"
  },
  "errorFetchContent": {
    "message": "Não foi possível recuperar o conteúdo da página",
    "description": "Erro ao obter o conteúdo da página"
  },
  "errorPageTooShort": {
    "message": "A página contém muito pouco conteúdo",
    "description": "Erro quando a página é muito curta"
  },
  "errorApi": {
    "message": "Erro da API: $error$",
    "description": "Mensagem de erro geral da API",
    "placeholders": {
      "error": {
        "content": "$1",
        "example": "Chave de API inválida"
      }
    }
  },
  "price": {
    "message": "Preço",
    "description": "Preço da construção"
  },
  "totalPriceLabel": {
    "message": "Preço total:",
    "description": "Rótulo para o preço total na oferta"
  },
  "saveOfferButton": {
    "message": "Salvar oferta",
    "description": "Texto do botão 'Salvar oferta'"
  },
  "changeImageButton": {
    "message": "Mudar imagem",
    "description": "Texto do botão 'Mudar imagem' no rodapé"
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
