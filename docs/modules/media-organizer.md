# Модуль медиатеки

## База данных

### MediaDatabase

```python
from plugins.media_organizer.core.database import MediaDatabase

db = MediaDatabase("media.db")

# Основные методы
records = db.export_all()
movies = db.export_movies()
series = db.export_series()
duplicates = db.find_duplicates()
```

### Таблицы

| Таблица | Описание |
|---------|----------|
| `media` | Записи медиафайлов |
| `categories` | Категории жанров |
| `metadata` | Метаданные (TMDB) |
| `plugins` | Плагины |

## Сканирование

### MediaScanner

```python
from plugins.media_organizer.core.media_organizer import MediaScanner

scanner = MediaScanner()
scanner.scan_paths([Path("E:"), Path("L:")])

movies = scanner.movies
series = scanner.series
```

### Методы сканирования

| Метод | Описание |
|-------|----------|
| `scan_paths()` | Сканирование путей |
| `scan_directory()` | Сканирование директории |
| `find_media_files()` | Поиск медиа файлов |

## Классификация

### PersistentGenreClassifier

```python
from plugins.media_organizer.core.media_organizer import PersistentGenreClassifier

classifier = PersistentGenreClassifier(tmdb, ai, db, disk_name)
await classifier.classify_media(movies, series)
```

### Методы классификации

| Метод | Описание |
|-------|----------|
| `classify_media()` | Классификация медиа |
| `get_tmdb_data()` | Получение данных TMDB |
| `update_categories()` | Обновление категорий |

## Аудит

### MediaAuditor

```python
from plugins.media_organizer.core.media_organizer import MediaAuditor

auditor = MediaAuditor(db, gemini=model, qbt=qbt)
issues = await auditor.audit()
```

### Типы проблем

| Тип | Описание |
|-----|----------|
| `missing_season` | Отсутствует сезон |
| `episodes` | Неправильное количество серий |
| `incomplete_files` | Неполные файлы |
| `incomplete_metadata` | Отсутствуют метаданные |

## RAG

### build_media_rag()

```python
from plugins.media_organizer.media_rag import build_media_rag

rag = build_media_rag(api_key="key_name")
```

### rag_search_tool()

```python
from plugins.media_organizer.media_rag import rag_search_tool

results = rag_search_tool("фильм про войну", top_k=5)
```

---

[← Меню](../index.md) | [Troubleshooting →](../troubleshooting.md)