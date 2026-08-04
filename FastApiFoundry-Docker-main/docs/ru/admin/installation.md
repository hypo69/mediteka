# Установка

Подробное описание процесса установки AI Assistant.

Для большинства случаев достаточно [Быстрого старта](getting_started.md).

---

## Системные требования

- Windows 10/11
- Python 3.11+
- Windows PowerShell 5.1+ или PowerShell 7+
- Интернет-соединение (для первой установки)

!!! warning "Права администратора"
    Для полноценной установки запускайте PowerShell от имени администратора.
    Без прав администратора не установятся: Foundry Local, Tesseract OCR, автозапуск.

---

## Способы установки

| Способ | Когда использовать |
|---|---|
| `install.bat` | Первая установка через системный PowerShell |
| `install7.bat` | Fallback, если нужно установить или найти PowerShell 7 |
| `install.ps1` | Повторная установка, CI/CD |
| Ручная установка | Docker, автоматизация |

Подробнее: [install.ps1 — подробно](../user/installation.md)

---

## Параметры install.ps1

```powershell
# Стандартная установка
powershell -ExecutionPolicy Bypass -File .\install.ps1

# Пересоздать venv
.\install.ps1 -Force

# Без RAG-зависимостей (экономит ~3-5 GB)
.\install.ps1 -SkipRag

# Без Tesseract OCR
.\install.ps1 -SkipTesseract

# Без LM Studio
.\install.ps1 -SkipLMStudio
```

---

## Docker

```powershell
docker-compose up
```

Сервис будет доступен на порту 8000 (маппинг на 9696 внутри контейнера).

---

## После установки

1. Отредактируйте `.env` — добавьте токены и ключи
2. Запустите `.\start.ps1`
3. Откройте http://localhost:9696
