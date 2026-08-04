# Indexer

**Файл:** `src/rag/indexer.py`  
**Тип:** `.py`

---

### `RAGIndexer` — Класс

```python
class RAGIndexer
```

Класс для индексации документов в системе RAG.

### `main` — Функция

```python
def main() -> None
```

Точка входа CLI для индексации документов.

### `__init__` — Функция

```python
def __init__(self, model_name: str='sentence-transformers/all-mpnet-base-v2') -> None
```

Инициализация индексатора.

Args:
    model_name (str): Имя модели sentence-transformer. По умолчанию 'sentence-transformers/all-mpnet-base-v2'.

### `load_model` — Функция

```python
def load_model(self) -> None
```

Загрузка модели эмбеддингов.

Raises:
    Exception: Если не удалось загрузить модель (неверное имя или отсутствие связи).

### `_read_file` — Функция

```python
def _read_file(self, file_path: Path) -> str
```

Чтение содержимого файла.

Args:
    file_path (Path): Путь к файлу.

Returns:
    str: Текстовое содержимое файла или пустая строка в случае ошибки.

### `_calculate_checksum` — Функция

```python
def _calculate_checksum(self, content: str) -> str
```

Расчет SHA256 контрольной суммы для содержимого.

Args:
    content (str): Строковое содержимое.

Returns:
    str: Хеш-сумма в виде строки.

### `chunk_text` — Функция

```python
def chunk_text(self, text: str, chunk_size: int=1000, overlap: int=50) -> List[str]
```

Разбиение текста на перекрывающиеся чанки.

Args:
    text (str): Исходный текст.
    chunk_size (int): Размер чанка.
    overlap (int): Размер перекрытия.

Returns:
    List[str]: Список текстовых фрагментов.

### `process_markdown` — Функция

```python
def process_markdown(self, content: str, metadata: Dict[str, Any], chunk_size: int, overlap: int) -> List[Dict[str, Any]]
```

Обработка Markdown с учетом структуры разделов.

Args:
    content (str): Содержимое файла.
    metadata (Dict[str, Any]): Метаданные файла.
    chunk_size (int): Размер чанка.
    overlap (int): Перекрытие.

Returns:
    List[Dict[str, Any]]: Список словарей с чанками и метаданными.

### `process_file` — Функция

```python
def process_file(self, file_path: Path, chunk_size: int=1000, overlap: int=50, content: Optional[str]=None) -> List[Dict[str, Any]]
```

Обработка одного файла и разбивка на чанки.

Args:
    file_path (Path): Путь к файлу.
    chunk_size (int): Размер фрагмента.
    overlap (int): Перекрытие.
    content (Optional[str]): Предзагруженное содержимое (если есть).

Returns:
    List[Dict[str, Any]]: Список обработанных фрагментов.

### `index_directory` — Функция

```python
def index_directory(self, docs_dir: Path, chunk_size: int=1000, overlap: int=50, existing_chunks: Optional[List[Dict[str, Any]]]=None) -> None
```

Рекурсивная индексация всех поддерживаемых файлов в директории.

Args:
    docs_dir (Path): Корневая папка с документами.
    chunk_size (int): Размер фрагмента.
    overlap (int): Перекрытие.
    existing_chunks (Optional[List[Dict[str, Any]]]): Ранее созданные чанки для инкрементальной проверки.

### `create_embeddings` — Функция

```python
def create_embeddings(self, existing_index: Optional[Any]=None) -> None
```

Создание векторов эмбеддингов для всех чанков.

Args:
    existing_index (Optional[Any]): Существующий индекс FAISS для повторного использования векторов.

Raises:
    ValueError: Если список чанков пуст.
    Exception: При ошибке кодирования (например, OOM).

### `save_index` — Функция

```python
def save_index(self, output_dir: Path) -> None
```

Сборка индекса FAISS и сохранение всех артефактов.

Args:
    output_dir (Path): Директория для сохранения.

Raises:
    Exception: Если не удалось создать индекс.
    OSError: Если не удалось записать файлы на диск.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
