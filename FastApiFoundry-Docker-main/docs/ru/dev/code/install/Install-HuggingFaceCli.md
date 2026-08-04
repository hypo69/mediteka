# Install-HuggingFaceCli.ps1

Устанавливает HuggingFace-пакеты и авторизует CLI через токен из `.env`.

**Файл:** `install\Install-HuggingFaceCli.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install\Install-HuggingFaceCli.ps1`

---

## Назначение

1. Находит Python/venv в проекте
2. Устанавливает `huggingface_hub>=0.23.0`, `transformers>=4.40.0`, `accelerate>=0.30.0`
3. Читает `HF_TOKEN` из `.env` или запрашивает интерактивно
4. Авторизуется через `huggingface_hub.login()`
5. Сохраняет токен в `.env`
6. Проверяет установку и выводит версии пакетов
7. Показывает инструкции по работе с публичными и закрытыми моделями

---

## Параметры

| Параметр | Тип | Описание |
|---|---|---|
| `-Token` | string | HuggingFace токен (иначе читается из `.env`) |
| `-SkipAuth` | switch | Пропустить авторизацию |
| `-SkipInstall` | switch | Пропустить установку пакетов |

---

## Примеры

```powershell
# Полная установка + авторизация
powershell -ExecutionPolicy Bypass -File .\install\Install-HuggingFaceCli.ps1

# Только установка пакетов
powershell -ExecutionPolicy Bypass -File .\install\Install-HuggingFaceCli.ps1 -SkipAuth

# С явным токеном
powershell -ExecutionPolicy Bypass -File .\install\Install-HuggingFaceCli.ps1 -Token "hf_ваш_токен"
```

---

## Публичные модели (без токена)

```
microsoft/phi-2
microsoft/Phi-3-mini-4k-instruct
TinyLlama/TinyLlama-1.1B-Chat-v1.0
Qwen/Qwen2.5-0.5B-Instruct
deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B
```

## Закрытые модели (требуют токен + согласие)

```
google/gemma-2-2b-it
meta-llama/Llama-3.2-1B-Instruct
mistralai/Mistral-7B-Instruct-v0.3
```

!!! warning "Закрытые модели"
    Перед скачиванием нужно принять лицензию на странице модели на huggingface.co.

