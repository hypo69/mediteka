# Model Badge

**Файл:** `js/model-badge.js`  
**Тип:** `.js`

---

### `_fetchActiveModel`

model-badge.js — Global active model banner with resource monitor
 *
 * Renders the selected model from the chat dropdown.
 * Updates #active-model-banner above the tab bar.
 *
 * File: js/model-badge.js
 * Project: FastApiFoundry (Docker)
 * Version: 0.6.0
 * Author: hypo69
 * Copyright: © 2026 hypo69

### `_sysStats`

Fetch system stats from /api/v1/system/stats.

### `_lookupSize`

Look up model size from the Foundry available list (window._foundryModels cache).

### `_renderBanner`

Render the banner content.

### `_poll`

Poll and update the banner.

### `initModelBanner`

Initialize banner once without polling model providers.

### `refreshModelBanner`

Force immediate refresh.
 * If modelInfo is provided, renders it directly without polling.
 *


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
