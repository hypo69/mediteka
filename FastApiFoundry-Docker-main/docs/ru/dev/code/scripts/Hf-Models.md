# Hf Models

**Файл:** `scripts/Hf-Models.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Название процесса: Управление HuggingFace моделями
=============================================================================
Описание:
Просмотр скачанных и загруженных HF моделей, загрузка/выгрузка в память.

Примеры:
.\hf-models.ps1                              # список всех моделей
.\hf-models.ps1 -Action load   -ModelId "google/gemma-2b"
.\hf-models.ps1 -Action unload -ModelId "google/gemma-2b"
.\hf-models.ps1 -Action status              # статус библиотек

File: scripts/hf-models.ps1
Project: Ai Assistant (Docker)
Version: 0.4.1
Author: hypo69
Copyright: © 2026 hypo69
Copyright: © 2026 hypo69
=============================================================================

### `Test-Server`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
