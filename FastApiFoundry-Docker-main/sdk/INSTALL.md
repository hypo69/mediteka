# Установка зависимостей SDK

## 1. Microsoft Foundry Local SDK

```bash
pip install foundry-local-sdk
```

Или с дополнительными зависимостями для агентов:

```bash
pip install foundry-local-sdk agent-framework --pre
```

## 2. FastAPI Foundry SDK (этот проект)

```bash
pip install -e sdk/
```

Или напрямую из корня проекта:

```bash
pip install aiohttp requests python-dotenv
```

## 3. MCP зависимости

```bash
pip install mcp
```

## 4. Полная установка всего SDK

```bash
pip install foundry-local-sdk agent-framework mcp aiohttp requests python-dotenv --pre
```

## Проверка установки

```python
# Microsoft Foundry Local SDK
from foundry_local_sdk import FoundryLocalManager
print("✅ foundry-local-sdk OK")

# FastAPI Foundry SDK
from sdk.fastapi_foundry_sdk import FastAPIFoundryClient
print("✅ fastapi-foundry-sdk OK")
```

## Требования

- Python 3.11+
- Windows 10/11 (для Foundry Local)
- Microsoft Foundry Local CLI: `winget install Microsoft.FoundryLocal`
