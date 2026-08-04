# Install Tesseract

**Файл:** `scripts/Install/Install-Tesseract.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Установщик Tesseract OCR
=============================================================================
Description:
Загружает и устанавливает Tesseract OCR 5.x для Windows x64.
Добавляет Tesseract в системный PATH.
Записывает tesseract_cmd в config.json (секция text_extractor).
Необходим для OCR-индексации изображений в RAG и OCR внутри PDF.

Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Tesseract.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Tesseract.ps1 -SkipIfExists
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Tesseract.ps1 -ConfigFile "D:\project\config.json"

File: scripts\Install\Install-Tesseract.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Обновлён заголовок и проект
- Удалён дублирующий блок param()
- Комментарии переведены на русский
Author: hypo69
Copyright: © 2024 - 2026 hypo69
License: MIT
=============================================================================

### `Test-TesseractInstalled`

### `Add-TesseractToPath`

### `Write-TesseractToConfig`

### `Install-Tesseract`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
