# huggingface_mcp.py

**Файл:** `mcp/src/servers/huggingface_mcp.py`  
**Протокол:** MCP STDIO  
**Версия:** 0.6.1

## Назначение

MCP сервер для генерации текста через HuggingFace Inference API. Использует `huggingface_hub.InferenceClient`.

## Инструменты

| Инструмент | Описание |
|---|---|
| `text_generation` | Генерация текста через HuggingFace Inference API |

### text_generation

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `prompt` | string | — | Промпт для генерации |
| `model` | string | `mistralai/Mistral-7B-Instruct-v0.2` | Модель HuggingFace |
| `max_tokens` | number | 100 | Максимум токенов |

## Переменные окружения

| Переменная | Описание |
|---|---|
| `HF_TOKEN` | HuggingFace API токен (обязательно) |

## Запуск

```powershell
$env:HF_TOKEN = "hf_ваш_токен"
venv\Scripts\python.exe mcp/src/servers/huggingface_mcp.py
```

!!! note
    Для PowerShell-версии см. [`McpHuggingFaceServer.ps1`](mcp-huggingface-ps.md).
