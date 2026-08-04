# Скрипты установки (scripts/Install/)

**Проект:** AI Assistant
**Автор:** hypo69
**Copyright:** © 2024 - 2026 hypo69
**Лицензия:** MIT

Вспомогательные скрипты для автоматизации первичной настройки и развёртывания.
Вызываются основным установщиком `install.ps1`, но могут запускаться отдельно.

## Файлы

| Скрипт | Описание |
|---|---|
| `Common.ps1` | Общие функции логирования, путей, режима и конфигурации |
| `Step-PythonEnvironment.ps1` | Python, venv, pip и requirements |
| `Step-UserInterface.ps1` | Chromium for Testing и GUI-инсталлятор |
| `Step-ConfigAndData.ps1` | Tesseract, `.env`, `config.json`, logs и базы данных |
| `install_rag_deps.py` | Интеллектуальная установка RAG-зависимостей (torch, sentence-transformers, faiss) |
| `Step-Backends.ps1` | llama.cpp, Foundry Local, LM Studio, Ollama и OpenCode |
| `Step-Finalize.ps1` | Модели по умолчанию, иконка, аудит и итоговая сводка |
| `Install-Chromium.ps1` | Установка Chromium for Testing |
| `Install-Foundry.ps1` | Установка Microsoft Foundry Local CLI через `winget` |
| `Install-Llama.ps1` | Настройка llama.cpp и каталога моделей |
| `Install-LMStudio.ps1` | Проверка и установка LM Studio |
| `Install-Ollama.ps1` | Установка Ollama через официальный PowerShell installer |
| `Install-OpenCode.ps1` | Установка OpenCode через `npm install -g opencode-ai` |
| `Install-Winget.ps1` | Проверка и установка Windows Package Manager |
| `Install-Models.ps1` | Загрузка базовых моделей для Foundry и RAG |
| `Install-HuggingFaceCli.ps1` | Установка `huggingface-hub` и авторизация `hf auth login` |
| `Install-Tesseract.ps1` | Загрузка и тихая установка Tesseract OCR 5.x |
| `Install-Shortcuts.ps1` | Создание ярлыков на рабочем столе для быстрого запуска |
| `Install-Autostart.ps1` | Настройка автозапуска сервера при входе в систему |
| `Setup-Env.ps1` | Интерактивная настройка файла `.env` |
| `Make-Ico.ps1` | Конвертация PNG-иконок в `icon.ico` |
| `ReinstallFoundry.ps1` | Полная переустановка Foundry Local (CI/QA) |

## Использование

```powershell
# Установить Foundry Local
.\scripts\Install\Install-Foundry.ps1

# Скачать модели по умолчанию
.\scripts\Install\Install-Models.ps1

# Установить HuggingFace CLI и авторизоваться
.\scripts\Install\Install-HuggingFaceCli.ps1

# Установить Tesseract OCR
.\scripts\Install\Install-Tesseract.ps1

# Настроить .env интерактивно
.\scripts\Install\Setup-Env.ps1

# Создать ярлыки на рабочем столе
.\scripts\Install\Install-Shortcuts.ps1

# Зарегистрировать автозапуск
.\scripts\Install\Install-Autostart.ps1
```

## Примечание

Все скрипты вызываются автоматически из `install.ps1` при первичной установке.
Запускайте их отдельно только для обновления отдельных компонентов.
