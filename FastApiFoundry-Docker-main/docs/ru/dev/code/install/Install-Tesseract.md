# Install-Tesseract.ps1

Загружает и устанавливает Tesseract OCR 5.x для Windows x64.

**Файл:** `install\Install-Tesseract.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install\Install-Tesseract.ps1`

---

## Назначение

Tesseract OCR необходим для:
- Индексации изображений в RAG (PNG, JPG, TIFF)
- OCR встроенных изображений внутри PDF-файлов

Скрипт:
1. Проверяет, установлен ли Tesseract (через PATH или по пути по умолчанию)
2. Если установлен и передан `-SkipIfExists` — обновляет PATH и `config.json` без переустановки
3. Проверяет интернет-соединение
4. Скачивает установщик `tesseract-ocr-w64-setup-5.5.0.20241111.exe`
5. Запускает тихую установку в `C:\Program Files\Tesseract-OCR`
6. Добавляет директорию в системный PATH
7. Записывает `text_extractor.tesseract_cmd` в `config.json`

---

## Параметры

| Параметр | Тип | Описание |
|---|---|---|
| `-ConfigFile` | string | Путь к `config.json` (по умолчанию: `..\\config.json`) |
| `-Force` | switch | Переустановить даже если уже установлен |
| `-SkipIfExists` | switch | Пропустить скачивание если уже установлен |

---

## Примеры

```powershell
# Стандартная установка
powershell -ExecutionPolicy Bypass -File .\install\Install-Tesseract.ps1

# Пропустить если уже установлен
powershell -ExecutionPolicy Bypass -File .\install\Install-Tesseract.ps1 -SkipIfExists

# Указать другой config.json
powershell -ExecutionPolicy Bypass -File .\install\Install-Tesseract.ps1 -ConfigFile "D:\project\config.json"
```

---

## Функции

### Test-TesseractInstalled
Проверяет доступность `tesseract.exe` через PATH или по пути установки по умолчанию.

### Add-TesseractToPath
Добавляет `C:\Program Files\Tesseract-OCR` в системный PATH (уровень Machine).

### Write-TesseractToConfig
Записывает `text_extractor.tesseract_cmd` в `config.json`.

### Install-Tesseract
Скачивает установщик и запускает тихую установку (`/S /D=...`).

---

## Результат в config.json

```json
{
  "text_extractor": {
    "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
  }
}
```

!!! warning "Перезапуск PowerShell"
    После установки нужно перезапустить PowerShell чтобы изменения PATH вступили в силу.

