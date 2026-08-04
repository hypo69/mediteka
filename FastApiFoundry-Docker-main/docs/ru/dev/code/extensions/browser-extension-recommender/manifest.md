# Manifest

**Файл:** `extensions/browser-extension-recommender/manifest.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `manifest_version` | `int` | 3 |
| `name` | `str` | AI Recommender |
| `description` | `str` | Tracks browsing time and provides AI-powered recommendations via AI Assistant |
| `version` | `str` | 0.7.1 |
| `default_locale` | `str` | en |
| `permissions` | `list` | массив [3] |
| `host_permissions` | `list` | массив [1] |
| `background` | `dict` | объект: `service_worker`, `type` |
| `content_scripts` | `list` | массив [1] |
| `action` | `dict` | объект: `default_popup`, `default_title`, `default_icon` |
| `web_accessible_resources` | `list` | массив [1] |

**Полная структура:**

```json
{
  "manifest_version": 3,
  "name": "AI Recommender",
  "description": "Tracks browsing time and provides AI-powered recommendations via AI Assistant",
  "version": "0.7.1",
  "default_locale": "en",
  "permissions": [
    "tabs",
    "storage",
    "activeTab"
  ],
  "host_permissions": [
    "<all_urls>"
  ],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": [
        "<all_urls>"
      ],
      "js": [
        "content.js"
      ],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_title": "AI Recommender",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "web_accessible_resources": [
    {
      "resources": [
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
