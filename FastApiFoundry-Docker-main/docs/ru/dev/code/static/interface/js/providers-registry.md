# Providers Registry

**Файл:** `static/interface/js/providers-registry.js`  
**Тип:** `.js`

---

### `validateConfigFile`

=============================================================================
 * Process Name: Unified LLM Providers Registry
 * =============================================================================
 * Description:
 *   Single source of truth for provider metadata and model-fetching logic.
 *   Used by BOTH the FastAPI Foundry web app (static/js/) and the browser
 *   extension (extensions/browser-extension-summarizer/).
 *
 *   Each provider entry:
 *     label          — human-readable name for UI
 *     placeholder    — API key input hint
 *     hint           — URL where the key can be obtained (without https://)
 *     fetchModels    — async (apiKey, opts?) => [{id, label}]
 *                      opts.customUrl — used only by 'custom' provider
 *
 * Storage contract (NOT handled here):
 *   Web app  → keys stored in .env via /api/v1/config/provider-keys
 *   Extension → keys stored in chrome.storage.sync as arrays
 *   Both sides use the shared export/import file format (see EXPORT_FORMAT below).
 *
 * Export/Import file format (version 2):
 *   {
 *     schema:         "ai-assistant-config",   // identifies the file type
 *     version:        2,
 *     exportedAt:     ISO8601 string,
 *     exportedFrom:   "app" | "extension",
 *     providerKeys:   { [providerId]: string | string[] },
 *     customModels:   { [providerId]: [{id, label}] },   // optional
 *     activeProvider: string | null,
 *     activeModel:    string | null,
 *     // Extension-only fields (ignored by app on import):
 *     activeKeyIndex: { [providerId]: number },
 *     providerModels: { [providerId]: [{id, label}] },
 *     summaryLang:    string,
 *     summaryProvider: string,
 *     summaryModel:   string,
 *   }
 *
 * File: providers-registry.js
 * Project: FastApiFoundry (Docker)
 * Version: 0.6.0
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================

| Параметр | Тип | Описание |
|---|---|---|
| `obj` | `object` | * @returns {string|null} |

### `normalizeProviderKeys`

Normalizes providerKeys to always be { [id]: string } (first key wins for arrays).
 * The app stores single strings; the extension stores arrays.
 *
 *

| Параметр | Тип | Описание |
|---|---|---|
| `providerKeys` | `object` | raw providerKeys from the file |

### `wrapProviderKeysAsArrays`

Wraps providerKeys values as arrays (extension format).
 *
 *

| Параметр | Тип | Описание |
|---|---|---|
| `providerKeys` | `object` | { [id]: string } |


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
