# Check Port

**Файл:** `check_engine/Check-Port.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Foundry Port Discovery
=============================================================================
Description:
Finds the TCP port on which the Foundry inference service is listening
by scanning the Inference.Service.Agent process ports via netstat and
probing each with a GET /v1/models request.
Sets FOUNDRY_BASE_URL environment variable when a live port is found.

Examples:
powershell -ExecutionPolicy Bypass -File .\check_port.ps1

File: check_engine/check_port.ps1
Project: Ai Assistant (Docker)
Version: 0.4.1
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

### `Get-FoundryPort`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
