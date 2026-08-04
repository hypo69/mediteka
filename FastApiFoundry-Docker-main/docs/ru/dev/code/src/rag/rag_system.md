# Rag System

**Файл:** `src/rag/rag_system.py`  
**Тип:** `.py`

---

### `RAGSystem` — Класс

```python
class RAGSystem
```

Класс для управления жизненным циклом RAG индекса и выполнения поиска.

### `__init__` — Функция

```python
def __init__(self) -> None
```

Инициализация экземпляра RAG системы.

### `_profile_index_dir` — Функция

```python
def _profile_index_dir(self, safe_name: str) -> Path
```

Получение пути к директории профиля.

### `_get_model` — Функция

```python
def _get_model(self) -> Any
```

Инициализация и получение модели эмбеддингов.

ПОЧЕМУ ВЫБРАНА ЛЕНИВАЯ ЗАГРУЗКА:
  - Модели SentenceTransformers (например, mpnet или MiniLM) занимают значительный объем RAM.
  - Загрузка при первом обращении предотвращает задержки при старте сервера, если RAG не используется.

Returns:
    Any: Экземпляр SentenceTransformer.

### `search` — Функция

```python
async def search(self, query: str, top_k: int=5) -> List[Dict[str, Any]]
```

Поиск релевантных фрагментов текста в векторном индексе.

ПОЧЕМУ ИСПОЛЬЗУЕТСЯ ЭТА РЕАЛИЗАЦИЯ:
  - FAISS обеспечивает сверхбыстрый поиск в векторном пространстве.
  - SentenceTransformers гарантирует высокое качество семантического сопоставления.
  - Проверка наличия индекса предотвращает ошибки при пустой базе знаний.

Args:
    query (str): Текст поискового запроса.
    top_k (int): Количество возвращаемых результатов.

Returns:
    List[Dict[str, Any]]: Список найденных сегментов с контентом и оценкой схожести.

### `_check_index_integrity` — Функция

```python
def _check_index_integrity(self, index_file: Path) -> bool
```

Проверка целостности и доступности файла индекса FAISS.

Обоснование:
  - Предотвращение загрузки поврежденных или пустых файлов.
  - Базовая проверка прав доступа и размера заголовка.

Args:
    index_file (Path): Путь к файлу faiss.index.

Returns:
    bool: True если файл прошел проверку.

### `_remove_duplicate_chunks` — Функция

```python
def _remove_duplicate_chunks(self) -> None
```

Удаление дубликатов фрагментов текста из текущего набора чанков.

Обоснование:
  - Предотвращает избыточность контекста при поиске.
  - Уменьшает потребление памяти.
  - Использует уникальность текста как критерий идентичности.

### `index_directories` — Функция

```python
async def index_directories(self, source_dirs: List[str]=None) -> bool
```

Индексация нескольких директорий и обновление векторной базы.

ПОЧЕМУ ЭТО ВАЖНО:
  - Позволяет объединять знания из разных локальных источников.
  - Использует TextExtractor для обработки файлов (PDF, DOCX и др.).
  
Args:
    source_dirs (List[str], optional): Список путей. Если None, берутся из конфига.

### `initialize` — Функция

```python
async def initialize(self) -> bool
```

Инициализация RAG системы при старте приложения.

Загружает индекс из директории, заданной в конфигурации.
Если индекс не найден — возвращает False без ошибки.

Returns:
    bool: True если индекс успешно загружен.

### `reload_index` — Функция

```python
async def reload_index(self, index_dir: str) -> bool
```

Динамическая перезагрузка индекса RAG для смены профилей.

ПОЧЕМУ ВЫБРАНО ЭТО РЕШЕНИЕ:
  - Позволяет переключать контекст знаний "на лету" без перезапуска API.
  - Использует стандартные файлы .index и .json для совместимости с индоксером.
  - Обеспечивает атомарность: состояние обновляется только после успешной загрузки файлов.

Args:
    index_dir (str): Путь к директории с файлами faiss.index и chunks.json.

Returns:
    bool: True если индекс и чанки успешно загружены.

### `format_context` — Функция

```python
def format_context(self, results: List[Dict[str, Any]]) -> str
```

Форматирование результатов поиска в единый блок текста.

### `filter_by_source` — Функция

```python
def filter_by_source(self, results: List[Dict[str, Any]], sources: List[str]) -> List[Dict[str, Any]]
```

Фильтрация результатов поиска по списку источников.

Обоснование:
  - Ограничение области поиска конкретными документами.
  - Поддержка пользовательских фильтров в интерфейсе.

Args:
    results (List[Dict[str, Any]]): Список результатов поиска.
    sources (List[str]): Список названий источников для фильтрации.

Returns:
    List[Dict[str, Any]]: Отфильтрованные результаты.

### `filter_by_score` — Функция

```python
def filter_by_score(self, results: List[Dict[str, Any]], min_score: float) -> List[Dict[str, Any]]
```

Фильтрация результатов поиска по минимальному порогу схожести.

Обоснование:
  - Отсечение нерелевантных фрагментов с низким весом совпадения.
  - Повышение качества контекста для LLM.

Args:
    results (List[Dict[str, Any]]): Список результатов поиска.
    min_score (float): Минимальный порог схожести.

Returns:
    List[Dict[str, Any]]: Отфильтрованные результаты.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
