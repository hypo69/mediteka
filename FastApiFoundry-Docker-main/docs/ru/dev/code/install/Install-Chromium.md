# Install-Chromium.ps1

Устанавливает Chrome for Testing через `@puppeteer/browsers` в `bin/chromium/`.

**Файл:** `install\Install-Chromium.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install\Install-Chromium.ps1`

---

## Назначение

Chromium for Testing используется GUI-установщиком для открытия веб-интерфейса в изолированном браузере.

1. Проверяет наличие `npx` (требуется Node.js)
2. Создаёт директорию `bin\chromium\`
3. Скачивает `chrome@<Channel>` через `npx @puppeteer/browsers install`
4. Находит `chrome.exe` в скачанных файлах
5. Записывает путь в `config.json`: `browser.chromium_path` и `browser.channel`

---

## Параметры

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `-Channel` | string | `stable` | Канал Chrome: `stable`, `beta`, `canary` |

---

## Примеры

```powershell
# Стабильная версия
powershell -ExecutionPolicy Bypass -File .\install\Install-Chromium.ps1

# Canary-версия
powershell -ExecutionPolicy Bypass -File .\install\Install-Chromium.ps1 -Channel canary
```

---

## Результат в config.json

```json
{
  "browser": {
    "chromium_path": "D:\\project\\bin\\chromium\\chrome\\win64-...\\chrome-win64\\chrome.exe",
    "channel": "stable"
  }
}
```

!!! warning "Требуется Node.js"
    Установите Node.js с [nodejs.org](https://nodejs.org) перед запуском скрипта.
