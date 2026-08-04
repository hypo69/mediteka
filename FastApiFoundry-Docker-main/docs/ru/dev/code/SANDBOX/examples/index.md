<!--
===============================================================================
Название процесса: Примеры использования FastAPI Foundry
===============================================================================
Описание:
    Практические примеры работы с FastAPI Foundry API и интеграций.
    Включает клиенты для API, RAG системы, MCP интеграции и управления моделями.

Примеры:
    Запуск примеров:
    python examples/example_client.py
    python examples/example_rag_client.py
    python examples/example_mcp_client.py

File: examples/README.md
Project: FastApiFoundry (Docker)
Version: 0.2.1
Author: hypo69
Copyright: © 2026 hypo69
Copyright: © 2026 hypo69
Date: 9 декабря 2025
===============================================================================
-->

# 📚 Examples

**Примеры использования FastAPI Foundry API и интеграций**

---

## 📋 Описание

Эта директория содержит практические примеры работы с FastAPI Foundry API, демонстрирующие различные сценарии использования и интеграции.

## 📁 Файлы примеров

| Файл | Описание | Использование |
|------|----------|---------------|
| **`example_client.py`** | Полный клиент API с демонстрацией всех endpoints | Основной пример для изучения API |
| **`example_rag_client.py`** | Работа с RAG системой поиска | Поиск в документации проекта |
| **`example_mcp_client.py`** | Model Context Protocol клиент | Интеграция с Claude Desktop |
| **`example_model_client.py`** | Управление AI моделями | Подключение и работа с моделями |
| **`example_microsoft_agent-framework.py`** | Интеграция с Microsoft Agent Framework | Корпоративные AI агенты |

## 🚀 Быстрый старт

### 1. Базовый API клиент
```bash
# Демонстрация всех возможностей API
python examples/example_client.py
```

### 2. RAG поиск
```bash
# Поиск в документации
python examples/example_rag_client.py
```

### 3. MCP интеграция
```bash
# Model Context Protocol
python examples/example_mcp_client.py
```

## 🎯 Основные сценарии

### 🤖 Генерация текста
- Простая генерация с промптом
- Генерация с системным промптом
- Пакетная обработка запросов
- Настройка параметров (temperature, max_tokens)

### 🔍 RAG система
- Поиск релевантного контекста
- Генерация с использованием найденного контекста
- Индексация новых документов

### 📊 Управление моделями
- Получение списка доступных моделей
- Подключение новых моделей
- Проверка состояния моделей
- Переключение между провайдерами

### 🔌 MCP интеграция
- Подключение к Claude Desktop
- Использование инструментов через MCP
- Обмен ресурсами и данными

## ⚙️ Конфигурация

### Переменные окружения
```bash
# .env файл
FASTAPI_BASE_URL=http://localhost:9696
API_KEY=your_api_key_here
FOUNDRY_URL=http://localhost:50477/v1/
```

### Настройка клиентов
```python
# Инициализация клиента
client = FastAPIFoundryClient(
    base_url="http://localhost:9696",
    api_key=os.getenv("API_KEY")
)
```

## 🧪 Тестирование

### Запуск всех примеров
```bash
# Через веб-интерфейс
# http://localhost:9696 -> Examples tab

# Или напрямую
python examples/example_client.py
python examples/example_rag_client.py
python examples/example_mcp_client.py
python examples/example_model_client.py
```

### Проверка работоспособности
```bash
# Проверка API
curl http://localhost:9696/api/v1/health

# Проверка моделей
curl http://localhost:9696/api/v1/models
```

## 📖 Документация

- **API Reference** - Полная документация API
- **Usage Guide** - Руководство по использованию
- **Examples Guide** - Подробные примеры
- **MCP Integration** - Интеграция с Claude

## 🔗 Связанные компоненты

- **API Endpoints** (`src/api/endpoints/`) - Реализация API
- **Foundry Client** (`src/models/foundry_client.py`) - Клиент для AI моделей
- **RAG System** (`src/rag/rag_system.py`) - Система поиска
- **MCP Server** (`mcp-servers/Ai Assistant-foundry/`) - MCP сервер

---

**📖 Документация:** Главное README | API Reference | Usage Guide