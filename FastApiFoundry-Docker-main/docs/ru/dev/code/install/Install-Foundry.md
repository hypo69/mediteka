# Install-Foundry.ps1

Устанавливает Microsoft Foundry Local CLI через winget, запускает сервис и предлагает скачать модель.

**Файл:** `install\Install-Foundry.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install\Install-Foundry.ps1`

---

## Назначение

1. Проверяет наличие `winget` — завершает работу с инструкцией если не найден
2. Если Foundry уже установлен — выводит версию и завершает
3. Устанавливает `Microsoft.FoundryLocal` через winget
4. Обновляет PATH в текущей сессии
5. Запускает `foundry service start`
6. Скачивает модель по умолчанию (`-Model`)
7. Проверяет доступность API на порту 50477

---

## Параметры

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `-Model` | string | `qwen3-0.6b-generic-cpu:4` | Идентификатор модели для скачивания |

---

## Примеры

```powershell
# Установка с моделью по умолчанию
powershell -ExecutionPolicy Bypass -File .\install\Install-Foundry.ps1

# Установка с другой моделью
powershell -ExecutionPolicy Bypass -File .\install\Install-Foundry.ps1 -Model "phi-3-mini-4k-instruct-generic-cpu:4"
```

---

## Что происходит после установки

```
winget install Microsoft.FoundryLocal
    ↓
foundry service start
    ↓
foundry model download <Model>
    ↓
GET http://localhost:50477/v1/models  ← проверка API
```

!!! tip "Автоопределение порта"
    Если Foundry запустился на другом порту — `start.ps1` найдёт его автоматически через `foundry service status`.

