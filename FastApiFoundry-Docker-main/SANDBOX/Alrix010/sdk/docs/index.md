# 📚 FastAPI Foundry SDK Documentation

**Version:** 0.2.1  
**Date:** 9 декабря 2025  

---

## 📋 Документация

| Файл | Описание |
|------|----------|
| [README.md](README.md) | Основная документация и быстрый старт |
| [api_methods.md](api_methods.md) | Полный справочник по методам API |
| [examples.md](examples.md) | Практические примеры использования |

---

## 🚀 Быстрый старт

```python
from sdk import FoundryClient

with FoundryClient("http://localhost:9696") as client:
    response = client.generate("Hello world")
    print(response.content)
```

---

## 📖 Основные разделы

### 🏥 [Health & Status](api_methods.md#-health--status)
- `health()` - проверка здоровья системы
- `is_alive()` - быстрая проверка доступности
- `wait_for_ready()` - ожидание готовности API

### 🤖 [Models Management](api_methods.md#-models-management)
- `list_models()` - список всех моделей
- `load_model()` - загрузка модели
- `get_model_status()` - статус модели

### ✍️ [Text Generation](api_methods.md#-text-generation)
- `generate()` - основная генерация текста
- `chat()` - чат с сессиями
- `batch_generate()` - пакетная обработка

### 🔍 [RAG System](api_methods.md#-rag-system)
- `rag_search()` - поиск в индексе
- `rag_clear()` - очистка индекса
- `rag_reload()` - перезагрузка

### ⚙️ [Configuration](api_methods.md#-configuration)
- `get_config()` - получение конфигурации
- `update_config()` - обновление настроек
- `set_default_model()` - модель по умолчанию

---

## 💡 Примеры использования

### Простая генерация
```python
response = client.generate("Расскажи о FastAPI")
```

### С параметрами
```python
response = client.generate(
    prompt="Как установить Docker?",
    temperature=0.7,
    max_tokens=500,
    use_rag=True
)
```

### RAG поиск
```python
results = client.rag_search("Docker configuration", top_k=3)
```

### Пакетная обработка
```python
responses = client.batch_generate([
    "Что такое AI?",
    "Как работает ML?"
])
```

---

## ⚠️ Обработка ошибок

```python
from sdk import FoundryError, FoundryConnectionError

try:
    response = client.generate("Test")
except FoundryConnectionError:
    print("Нет подключения к API")
except FoundryError as e:
    print(f"SDK Error: {e}")
```

---

## 🔧 Утилиты

- `test_connection()` - тест подключения
- `auto_setup()` - автоматическая настройка
- `quick_test()` - быстрый тест всех функций
- `get_metrics()` - метрики производительности

---

**FastAPI Foundry SDK v0.2.1** - часть экосистемы Ai Assistant  
© 2025 Ai Assistant Team