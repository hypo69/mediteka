# Hf Downloadmodel

**Файл:** `scripts/Hf-DownloadModel.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Название процесса: Скачивание HuggingFace модели
=============================================================================
Описание:
Скачивает модель с HuggingFace Hub через FastAPI Foundry API.
Для закрытых моделей (Gemma, Llama) нужен HF токен.

Примеры:
.\hf-download-model.ps1 -ModelId "google/gemma-2b"
.\hf-download-model.ps1 -ModelId "google/gemma-2b" -Token "hf_..."
.\hf-download-model.ps1 -ModelId "microsoft/phi-2"

File: scripts/hf-download-model.ps1
Project: Ai Assistant (Docker)
Version: 0.4.1
Author: hypo69
Copyright: © 2026 hypo69
Copyright: © 2026 hypo69
=============================================================================


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
