# Manifest

**Файл:** `extensions/kazarinov-browser-extention/manifest.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `manifest_version` | `int` | 3 |
| `name` | `str` | __MSG_extensionName__ |
| `description` | `str` | __MSG_extensionDescription__ |
| `version` | `str` | 1.0.1 |
| `default_locale` | `str` | ru |
| `permissions` | `list` | массив [5] |
| `host_permissions` | `list` | массив [1] |
| `background` | `dict` | объект: `service_worker` |
| `action` | `dict` | объект: `default_popup` |
| `icons` | `dict` | объект: `16`, `32`, `48`, `128` |
| `content_scripts` | `list` | массив [1] |
| `web_accessible_resources` | `list` | массив [1] |

**Полная структура:**

```json
{
  "manifest_version": 3,
  "name": "__MSG_extensionName__",
  "description": "__MSG_extensionDescription__",
  "version": "1.0.1",
  "default_locale": "ru",
  "permissions": [
    "contextMenus",
    "activeTab",
    "storage",
    "scripting",
    "notifications"
  ],
  "host_permissions": [
    "https://generativelanguage.googleapis.com/"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_popup": "popup.html"
  },
  "icons": {
    "16": "icons/icon16.png",
    "32": "icons/icon32.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
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
  "web_accessible_resources": [
    {
      "resources": [
        "_locales//*",
        "image-manifest.json",
        "locales-manifest.json",
        "locators//*",
        "preview-offer.html",
        "assets/images//*"
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
