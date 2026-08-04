# Manifest

**Файл:** `extensions/browser-extension-summarizer/manifest.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `manifest_version` | `int` | 3 |
| `name` | `str` | AI Assistant — Summarizer |
| `description` | `str` | Summarise current page or all open tabs using Gemini AI |
| `version` | `str` | 1.0.0 |
| `default_locale` | `str` | en |
| `permissions` | `list` | массив [6] |
| `host_permissions` | `list` | массив [13] |
| `background` | `dict` | объект: `service_worker`, `type` |
| `action` | `dict` | объект: `default_popup`, `default_title` |
| `icons` | `dict` | объект: `16`, `48`, `128` |
| `web_accessible_resources` | `list` | массив [1] |

**Полная структура:**

```json
{
  "manifest_version": 3,
  "name": "AI Assistant — Summarizer",
  "description": "Summarise current page or all open tabs using Gemini AI",
  "version": "1.0.0",
  "default_locale": "en",
  "permissions": [
    "contextMenus",
    "activeTab",
    "tabs",
    "storage",
    "scripting",
    "notifications"
  ],
  "host_permissions": [
    "https://generativelanguage.googleapis.com/",
    "https://api.openai.com/",
    "https://openrouter.ai/",
    "https://api.anthropic.com/",
    "https://api.mistral.ai/",
    "https://api.groq.com/",
    "https://api.cohere.com/",
    "https://api.deepseek.com/",
    "https://api.x.ai/",
    "https://integrate.api.nvidia.com/",
    "http://localhost/*",
    "http://127.0.0.1/*",
    "<all_urls>"
  ],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "action": {
    "default_popup": "popup.html",
    "default_title": "AI Assistant"
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "web_accessible_resources": [
    {
      "resources": [
        "providers.html",
        "chat.html",
        "debug.html",
        "rag-storage.html",
        "locales/*.json"
      ],
      "matches": [
        "<all_urls>"
      ]
    }
  ]
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
