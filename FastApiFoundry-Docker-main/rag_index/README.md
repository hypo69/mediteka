# 🔍 RAG Index

**Индекс системы поиска и извлечения контекста (Retrieval-Augmented Generation)**

---

## 📋 Описание

Эта директория содержит индекс RAG системы FastAPI Foundry - векторную базу данных для поиска релевантного контекста в документации проекта.

**Путь к директории**: ~/.rag

Внутри директории можно хранить несколь индексов.

Например:
```
~/.rag/index_helpdesk
~/.rag/index_docs
```
Внутренний механизм программы умеет с ними работать.


---


## 📁 Структура файлов

| Файл | Описание | Размер | Назначение |
|------|----------|--------|------------|
| **`faiss.index`** | FAISS векторный индекс | ~MB | Векторный поиск по эмбеддингам |
| **`chunks.json`** | Текстовые чанки документов | ~KB | Исходные тексты для контекста |
| **`index_info.json`** | Метаданные индекса | ~KB | Информация о модели и параметрах |

## 🤖 Текущая конфигурация

### 📊 Статистика индекса
```json
{
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "chunks_count": 532,
  "dimension": 384,
  "version": "1.0.0"
}
```

### 🔧 Параметры
- **Модель эмбеддингов**: `sentence-transformers/all-MiniLM-L6-v2`
- **Размерность векторов**: 384
- **Количество чанков**: 532
- **Источники**: Документация FastAPI Foundry (Markdown файлы)

## 🚀 Как работает RAG система

### 1. 📝 Индексация документов
```python
# Процесс создания индекса    
1. Парсинг Markdown файлов из docs/
2. Разбиение на чанки (chunks) по разделам
3. Генерация эмбеддингов через sentence-transformers
4. Создание FAISS индекса для быстрого поиска
5. Сохранение метаданных и текстов
```

### 2. 🔍 Поиск контекста

#### Процесс поиска

1. Пользователь задает вопрос
2. Генерируется эмбеддинг вопроса
3. FAISS ищет похожие векторы в индексе
4. Возвращаются наиболее релевантные чанки
5. Контекст передается в AI модель


### 3. 🤖 Генерация ответа

##### Процесс генерации

1. AI модель получает вопрос + найденный контекст
2. Генерируется ответ на основе документации
3. Ответ содержит актуальную информацию из проекта

## 📚 Источники данных

### 📖 Индексированные документы
- `configuration.md` - Настройка и конфигурация
- `deployment.md` - Развертывание и production
- `development.md` - Разработка и архитектура
- `examples.md` - Примеры использования API
- `howto.md` - Практические рецепты
- `installation.md` - Установка системы
- `launchers.md` - Способы запуска
- `mcp_integration.md` - MCP интеграция
- `project_info.md` - Информация о проекте
- `README.md` - Основная документация
- `running.md` - Запуск сервера
- `tunnel_guide.md` - Туннели и публичный доступ
- `usage.md` - Использование API

### 🔍 Примеры чанков
```json
{
  "source": "configuration.md",
  "section": "⚙️ Настройка",
  "text": "Создание конфигурации: cp .env.example .env"
},
{
  "source": "examples.md", 
  "section": "Генерация текста",
  "text": "curl -X POST http://localhost:9696/api/v1/generate..."
}
```

## ⚙️ Использование RAG

### 🔍 Поиск через API
```bash
# Поиск в документации
curl -X POST http://localhost:9696/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "как настроить конфигурацию",
    "top_k": 5
  }'
```

### 🤖 Генерация с RAG контекстом
```bash
# Генерация с использованием найденного контекста
curl -X POST http://localhost:9696/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Как настроить FastAPI Foundry?",
    "use_rag": true,
    "temperature": 0.6
  }'
```

### 📊 Результат поиска
```json
{
  "success": true,
  "results": [
    {
      "source": "configuration.md",
      "section": "Создание конфигурации", 
      "content": "cp .env.example .env",
      "score": 0.892
    }
  ],
  "total_found": 5,
  "search_time": 0.045
}
```

## 🔄 Обновление индекса

### 📝 Переиндексация
```bash
# Полная переиндексация документации
python rag_indexer.py --docs-dir docs/ --output-dir rag_index/

# Через API
curl -X POST http://localhost:9696/api/v1/rag/reload \
  -H "Authorization: Bearer your-api-key"
```

### ➕ Добавление новых документов
```python
from src.rag.rag_system import rag_system

# Добавить документ в индекс
await rag_system.add_document(
    text="Новое содержимое документа",
    source="new_doc.md",
    section="Новый раздел"
)
```

## 🎯 Оптимизация поиска

### 📊 Параметры поиска
- **`top_k`**: Количество результатов (по умолчанию: 5)
- **`threshold`**: Минимальный порог релевантности (0.0-1.0)
- **`max_length`**: Максимальная длина контекста

### 🔧 Настройка в config.json
```json
{
  "rag_system": {
    "enabled": true,
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "index_dir": "./rag_index",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "top_k": 5
  }
}
```

## 📈 Производительность

### ⚡ Скорость поиска
- **Поиск в индексе**: ~10-50ms
- **Генерация эмбеддинга**: ~100-200ms
- **Общее время RAG поиска**: ~150-300ms

### 💾 Использование памяти
- **FAISS индекс**: ~2-5MB в RAM
- **Модель эмбеддингов**: ~90MB в RAM
- **Чанки текста**: ~1-2MB в RAM

## 🔧 Техническая информация

### 🤖 Модель эмбеддингов
- **Название**: `sentence-transformers/all-MiniLM-L6-v2`
- **Размер**: ~90MB
- **Языки**: Английский, частично русский
- **Качество**: Хорошее для технической документации

### 📊 FAISS индекс
- **Тип**: IndexFlatIP (Inner Product)
- **Метрика**: Косинусное сходство
- **Размерность**: 384
- **Точность**: Высокая для небольших коллекций

## 🛠️ Обслуживание

### 🔍 Диагностика
```bash
# Проверка состояния RAG системы
curl http://localhost:9696/api/v1/rag/status

# Статистика индекса
ls -la rag_index/
```

### 🧹 Очистка
```bash
# Удаление старого индекса
rm -rf rag_index/*

# Создание нового индекса
python rag_indexer.py --docs-dir docs/ --output-dir rag_index/
```

### 📦 Бэкап
```bash
# Создание резервной копии
tar -czf rag_index_backup.tar.gz rag_index/

# Восстановление
tar -xzf rag_index_backup.tar.gz
```

## 🔗 Интеграция

### 🌐 С веб-интерфейсом
- RAG поиск доступен в веб-консоли
- Автоматическое использование в чате
- Настройка через Settings

### 🤖 С AI моделями
- Автоматическая передача контекста в промпт
- Поддержка всех Foundry моделей
- Настраиваемые параметры генерации

### 🔌 С MCP сервером
- RAG поиск доступен через MCP протокол
- Интеграция с Claude Desktop
- Использование в других MCP клиентах

## 📖 Документация

- **[RAG System](../src/rag/rag_system.py)** - Исходный код RAG системы
- **[API Reference](../docs/api.md)** - Документация RAG API
- **[Configuration](../docs/configuration.md)** - Настройка RAG системы

---

**📖 Документация:** [Главное README](../README.md) | [API Reference](../docs/api.md) | [Configuration](../docs/configuration.md)