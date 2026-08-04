# 🛠️ FastAPI Foundry SDK Documentation

**Version:** 0.2.1  
**Project:** FastApiFoundry (Docker)  
**Date:** 9 декабря 2025  

---

## 📋 Содержание

- [Быстрый старт](#-быстрый-старт)
- [API Reference](#-api-reference)
- [Примеры использования](#-примеры-использования)
- [Обработка ошибок](#-обработка-ошибок)
- [Модели данных](#-модели-данных)

---

## 🚀 Быстрый старт

### Установка

```bash
# Скопировать SDK в проект
cp -r sdk /path/to/your/project/

# Или добавить в PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/FastApiFoundry-Docker/SANDBOX"
```

### Базовое использование

```python
from sdk import FoundryClient

# Создание клиента
with FoundryClient("http://localhost:9696") as client:
    # Проверка здоровья
    health = client.health()
    print(f"Status: {health.status}")
    
    # Генерация текста
    response = client.generate("Hello world")
    if response.success:
        print(response.content)
```

---

## 📚 API Reference

### FoundryClient

Основной класс для работы с API.

#### Инициализация

```python
client = FoundryClient(
    base_url="http://localhost:9696",  # URL API сервера
    api_key=None,                      # API ключ (опционально)
    timeout=30                         # Таймаут запросов
)
```

#### Основные методы

| Метод | Описание | Возвращает |
|-------|----------|------------|
| `health()` | Проверка здоровья системы | `HealthStatus` |
| `generate(prompt, **kwargs)` | Генерация текста | `GenerationResponse` |
| `chat(message, **kwargs)` | Отправка сообщения в чат | `GenerationResponse` |
| `list_models()` | Список доступных моделей | `List[ModelInfo]` |
| `rag_search(query, top_k=5)` | Поиск в RAG индексе | `List[Dict]` |

---

## 💡 Примеры использования

### Генерация текста

```python
# Простая генерация
response = client.generate("Расскажи о FastAPI")

# С параметрами
response = client.generate(
    prompt="Как установить Docker?",
    model="deepseek-r1-distill-qwen-7b-generic-cpu:3",
    temperature=0.7,
    max_tokens=500,
    use_rag=True
)
```

### Пакетная генерация

```python
prompts = ["Что такое AI?", "Как работает ML?"]
responses = client.batch_generate(prompts, max_tokens=100)

for response in responses:
    print(response.content)
```

### RAG поиск

```python
results = client.rag_search("Docker configuration", top_k=3)
for result in results:
    print(f"Source: {result['source']}")
    print(f"Text: {result['text'][:100]}...")
```

### Управление моделями

```python
# Список моделей
models = client.list_models()
for model in models:
    print(f"{model.id} - {model.status}")

# Загрузка модели
success = client.load_model("model-id")
```

---

## ⚠️ Обработка ошибок

```python
from sdk import FoundryClient, FoundryError, FoundryConnectionError

try:
    with FoundryClient() as client:
        response = client.generate("Test")
        
except FoundryConnectionError:
    print("Не удалось подключиться к API")
except FoundryError as e:
    print(f"SDK Error: {e}")
```

---

## 📊 Модели данных

### GenerationResponse

```python
@dataclass
class GenerationResponse:
    success: bool                    # Успешность генерации
    content: Optional[str]           # Сгенерированный текст
    error: Optional[str]             # Ошибка (если есть)
    model_used: Optional[str]        # Использованная модель
    tokens_used: Optional[int]       # Количество токенов
    rag_sources: Optional[List[str]] # Источники RAG
    generation_time: Optional[float] # Время генерации
```

### ModelInfo

```python
@dataclass
class ModelInfo:
    id: str                    # ID модели
    name: Optional[str]        # Название
    provider: Optional[str]    # Провайдер
    status: Optional[str]      # Статус
    max_tokens: Optional[int]  # Максимум токенов
```

### HealthStatus

```python
@dataclass
class HealthStatus:
    status: str                      # Статус API
    foundry_status: Optional[str]    # Статус Foundry
    foundry_url: Optional[str]       # URL Foundry
    rag_loaded: bool                 # RAG загружен
    rag_chunks: int                  # Количество RAG чанков
    models_count: int                # Количество моделей
```

---

**FastAPI Foundry SDK v0.2.1** - часть экосистемы Ai Assistant  
© 2025 Ai Assistant Team