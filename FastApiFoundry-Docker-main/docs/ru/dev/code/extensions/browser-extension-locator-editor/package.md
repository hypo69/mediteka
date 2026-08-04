# Package

**Файл:** `extensions/browser-extension-locator-editor/package.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `name` | `str` | locator-editor |
| `private` | `bool` | True |
| `version` | `str` | 0.0.0 |
| `type` | `str` | module |
| `scripts` | `dict` | объект: `dev`, `build`, `preview` |
| `dependencies` | `dict` | объект: `react`, `react-dom` |
| `devDependencies` | `dict` | объект: `@types/node`, `@vitejs/plugin-react`, `typescript`, `vite` |

**Полная структура:**

```json
{
  "name": "locator-editor",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.2.0",
    "react-dom": "^19.2.0"
  },
  "devDependencies": {
    "@types/node": "^22.14.0",
    "@vitejs/plugin-react": "^5.0.0",
    "typescript": "~5.8.2",
    "vite": "^6.2.0"
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
