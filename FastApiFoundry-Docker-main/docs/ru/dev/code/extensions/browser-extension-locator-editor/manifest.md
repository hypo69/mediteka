# Manifest

**Файл:** `extensions/browser-extension-locator-editor/manifest.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `manifest_version` | `int` | 3 |
| `name` | `str` | __MSG_appName__ |
| `description` | `str` | __MSG_appDescription__ |
| `version` | `str` | 1.0.1 |
| `default_locale` | `str` | en |
| `permissions` | `list` | массив [2] |
| `background` | `dict` | объект: `service_worker` |
| `action` | `dict` | объект: `default_popup`, `default_icon` |
| `icons` | `dict` | объект: `16`, `32`, `48`, `128` |
| `web_accessible_resources` | `list` | массив [1] |

**Полная структура:**

```json
{
  "manifest_version": 3,
  "name": "__MSG_appName__",
  "description": "__MSG_appDescription__",
  "version": "1.0.1",
  "default_locale": "en",
  "permissions": [
    "storage",
    "contextMenus"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "32": "icons/icon32.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "icons": {
    "16": "icons/icon16.png",
    "32": "icons/icon32.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "web_accessible_resources": [
    {
      "resources": [
        "editor/editor.html",
        "vendor/*"
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
