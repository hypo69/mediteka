# 🧪 SANDBOX

**Экспериментальная зона и SDK для FastAPI Foundry**

---

## 📋 Описание

SANDBOX - это экспериментальная директория для разработки и тестирования новых функций FastAPI Foundry. Содержит SDK, прототипы и экспериментальные модули.

## 📁 Структура

```
SANDBOX/
└── sdk/                      # Python SDK для FastAPI Foundry
    ├── __init__.py          # Инициализация пакета
    ├── client.py            # Основной клиент API
    ├── models.py            # Модели данных (Pydantic)
    ├── exceptions.py        # Кастомные исключения
    ├── example.py           # Примеры использования SDK
    └── README.md            # Документация SDK
```

## 🚀 SDK для FastAPI Foundry

### 🎯 Основные возможности
- **Простой API клиент** для всех endpoints
- **Type-safe модели** с Pydantic
- **Обработка ошибок** с кастомными исключениями
- **Синхронный интерфейс** для легкого использования
- **Автоматическая аутентификация** с API ключами

### 📦 Установка SDK
```python
# Добавить в PYTHONPATH
import sys
sys.path.append('./SANDBOX')

# Импорт SDK
from sdk import FoundryClient
from sdk.models import GenerationRequest, ModelInfo
from sdk.exceptions import FoundryError
```

### 🔧 Использование SDK
```python
# Инициализация клиента
with FoundryClient(base_url="http://localhost:9696") as client:
    # Проверка здоровья
    health = client.health()
    print(f"Status: {health.status}")
    
    # Генерация текста
    response = client.generate(
        prompt="Привет, как дела?",
        model="deepseek-r1-distill-qwen-7b",
        temperature=0.7,
        max_tokens=2048
    )
    print(f"Response: {response.content}")
    
    # Список моделей
    models = client.list_models()
    for model in models:
        print(f"Model: {model.id} - {model.status}")
```

## 🧩 Компоненты SDK

### 🔌 Client (client.py)
```python
class FoundryClient:
    """Основной клиент для FastAPI Foundry API"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None)
    def health() -> HealthStatus
    def generate(...) -> GenerationResponse
    def list_models() -> List[ModelInfo]
    def rag_search(...) -> List[Dict]
    def batch_generate(...) -> List[GenerationResponse]
```

### 📊 Models (models.py)
```python
# Pydantic модели для type safety
class GenerationRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    use_rag: bool = True

class GenerationResponse(BaseModel):
    content: str
    model: str
    tokens_used: int
    processing_time: float

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    status: str
    size_mb: Optional[int] = None
```

### ⚠️ Exceptions (exceptions.py)
```python
# Кастомные исключения
class FoundryError(Exception):
    """Базовое исключение SDK"""

class FoundryConnectionError(FoundryError):
    """Ошибка подключения к API"""

class FoundryAPIError(FoundryError):
    """HTTP ошибка API"""
```

## 🧪 Экспериментальные функции

### 🔬 Прототипы
- **Асинхронный клиент** для высокой производительности
- **Streaming генерация** для длинных ответов
- **Batch операции** для массовой обработки
- **Кэширование ответов** для оптимизации

### 🚀 Будущие возможности
- **GraphQL интерфейс** для гибких запросов
- **WebSocket клиент** для реального времени
- **Plugin система** для расширений
- **Метрики и аналитика** встроенные в SDK

## 📝 Примеры использования

### 🎯 Базовое использование
```python
from sdk import FoundryClient

# Простой пример
client = FoundryClient("http://localhost:9696")

# Генерация с RAG
response = client.generate(
    prompt="Что такое FastAPI Foundry?",
    use_rag=True
)
print(response.content)

client.close()
```

### 🔄 Пакетная обработка
```python
# Обработка множественных запросов
prompts = [
    "Объясни машинное обучение",
    "Что такое нейронные сети?",
    "Как работает RAG система?"
]

responses = client.batch_generate(
    prompts=prompts,
    model="deepseek-r1-distill-qwen-7b",
    temperature=0.6
)

for i, response in enumerate(responses):
    print(f"Ответ {i+1}: {response.content[:100]}...")
```

### 🔍 RAG поиск
```python
# Поиск в документации
results = client.rag_search(
    query="настройка конфигурации",
    top_k=5
)

for result in results:
    print(f"Источник: {result['source']}")
    print(f"Контент: {result['content'][:200]}...")
    print(f"Релевантность: {result['score']:.3f}")
    print("-" * 50)
```

## 🔧 Разработка и тестирование

### 🧪 Тестирование SDK
```python
# Запуск примера
python SANDBOX/sdk/example.py

# Тестирование всех функций
python -m pytest SANDBOX/sdk/tests/ -v
```

### 🔨 Разработка новых функций
```python
# Добавление нового метода в клиент
class FoundryClient:
    def experimental_feature(self, data):
        """Экспериментальная функция"""
        return self._make_request("POST", "/api/v1/experimental", json=data)
```

## 📊 Мониторинг и отладка

### 🐛 Отладка SDK
```python
import logging

# Включение отладочных логов
logging.basicConfig(level=logging.DEBUG)

# Использование с отладкой
client = FoundryClient("http://localhost:9696")
try:
    response = client.generate("test prompt")
except FoundryError as e:
    print(f"SDK Error: {e}")
```

### 📈 Метрики
```python
# Измерение производительности
import time

start_time = time.time()
response = client.generate("test prompt")
end_time = time.time()

print(f"Время генерации: {end_time - start_time:.2f}s")
print(f"Токенов использовано: {response.tokens_used}")
print(f"Скорость: {response.tokens_used / (end_time - start_time):.1f} tokens/s")
```

## 🔗 Интеграция

### 🌐 С веб-приложениями
```python
# Flask интеграция
from flask import Flask, request, jsonify
from sdk import FoundryClient

app = Flask(__name__)
client = FoundryClient("http://localhost:9696")

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    response = client.generate(data['prompt'])
    return jsonify({'content': response.content})
```

### 🤖 С другими AI системами
```python
# Интеграция с LangChain
from langchain.llms.base import LLM
from sdk import FoundryClient

class FoundryLLM(LLM):
    def __init__(self):
        self.client = FoundryClient("http://localhost:9696")
    
    def _call(self, prompt: str, stop=None) -> str:
        response = self.client.generate(prompt)
        return response.content
```

## 📖 Документация

- **[SDK Documentation](sdk/README.md)** - Подробная документация SDK
- **[API Reference](../docs/api.md)** - Справочник по API
- **[Examples Guide](../docs/examples.md)** - Примеры использования

---

**📖 Документация:** [Главное README](../README.md) | [SDK Docs](sdk/README.md) | [API Reference](../docs/api.md)