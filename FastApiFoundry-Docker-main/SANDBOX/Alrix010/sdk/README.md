# 🛠️ FastAPI Foundry SDK (Simple)

Простой Python SDK для работы с FastAPI Foundry API.

## 🚀 Использование

```python
from sdk import FoundryClient

# Создание клиента
with FoundryClient("http://localhost:9696") as client:
    
    # Проверка здоровья
    health = client.health()
    print(health.get("status"))
    
    # Генерация текста
    response = client.generate("Hello world")
    if response.get("success"):
        print(response.get("content"))
    
    # Чат
    chat_response = client.chat("Hi there!")
    
    # Список моделей
    models = client.list_models()
    
    # RAG поиск
    results = client.rag_search("FastAPI")
```

## 📋 Методы

- `health()` - проверка здоровья системы
- `generate(prompt, model=None, max_tokens=None, use_rag=True)` - генерация текста
- `chat(message, conversation_id=None, use_rag=True)` - чат
- `list_models()` - список моделей
- `rag_search(query, top_k=5)` - RAG поиск

## 📦 Зависимости

Только `requests` - никаких дополнительных библиотек.

---

**FastAPI Foundry SDK v0.2.1**  
© 2025 Ai Assistant Team