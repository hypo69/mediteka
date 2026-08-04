# McpHuggingFaceServer.ps1

**Файл:** `mcp/src/servers/McpHuggingFaceServer.ps1`  
**Протокол:** HTTP SSE  
**Порт по умолчанию:** 8080  
**Требования:** PowerShell 7.0+, переменная окружения `HF_TOKEN`

## Назначение

Минимальный MCP сервер для отправки промптов в HuggingFace Inference API. Возвращает ответ модели как SSE-событие.

## Параметры запуска

| Параметр | По умолчанию | Описание |
|---|---|---|
| `-Model` | `meta-llama/Llama-3-8b-instruct` | Модель HuggingFace |
| `-Port` | `8080` | Порт HTTP сервера |

## Запуск

```powershell
$env:HF_TOKEN = "hf_ваш_токен"
pwsh -NoProfile -File mcp/src/servers/McpHuggingFaceServer.ps1 -Model "mistralai/Mistral-7B-Instruct-v0.2" -Port 8080
```

## Пример запроса

```
GET http://localhost:8080/mcp/?prompt=Hello
```

Ответ возвращается как SSE-событие `message` с JSON-телом от HuggingFace API.

!!! note
    Для Python-версии HuggingFace MCP сервера см. [`huggingface_mcp.py`](mcp-huggingface-py.md).
