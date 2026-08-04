# Utils

**Файл:** `src/rag/text_extractors/text_extractor_4_rag/utils.py`  
**Тип:** `.py`

---

### `setup_logging` — Функция

```python
def setup_logging() -> None
```

Настройка структурированного логирования.

### `get_file_extension` — Функция

```python
def get_file_extension(filename: str) -> Optional[str]
```

Получение расширения файла.

### `is_supported_format` — Функция

```python
def is_supported_format(filename: str, supported_formats: dict) -> bool
```

Проверка поддерживается ли формат файла.

### `is_archive_format` — Функция

```python
def is_archive_format(filename: str, supported_formats: dict) -> bool
```

Проверка, является ли файл архивом.

### `safe_filename` — Функция

```python
def safe_filename(filename: str) -> str
```

Безопасное имя файла для логов.

### `sanitize_filename` — Функция

```python
def sanitize_filename(filename: str) -> str
```

Санитизация имени файла для безопасности с поддержкой кириллицы.

Удаляет опасные символы для path traversal атак, но сохраняет кириллические символы

### `validate_file_type` — Функция

```python
def validate_file_type(content: bytes, filename: str) -> tuple[bool, Optional[str]]
```

Проверка соответствия расширения файла его содержимому.

Returns:
    tuple: (is_valid, error_message)

### `cleanup_temp_files` — Функция

```python
def cleanup_temp_files() -> None
```

Очистка временных файлов при старте приложения.

Удаляет временные файлы, которые могли остаться после предыдущих запусков

### `cleanup_recent_temp_files` — Функция

```python
def cleanup_recent_temp_files() -> None
```

Немедленная очистка временных файлов текущего процесса.

Удаляет временные файлы, созданные в последние 10 минут

### `run_subprocess_with_limits` — Функция

```python
def run_subprocess_with_limits(command: list, timeout: int=30, memory_limit: Optional[int]=None, capture_output: bool=True, text: bool=True, **kwargs: object) -> subprocess.CompletedProcess
```

Запуск подпроцесса с ограничениями ресурсов.

Args:
    command: Команда для выполнения
    timeout: Таймаут в секундах
    memory_limit: Ограничение памяти в байтах (None для использования настроек по умолчанию)
    capture_output: Захватывать ли вывод
    text: Использовать ли текстовый режим
    **kwargs: Дополнительные параметры для subprocess.run

Returns:
    subprocess.CompletedProcess: Результат выполнения

Raises:
    subprocess.TimeoutExpired: При превышении таймаута
    subprocess.CalledProcessError: При ошибке выполнения
    MemoryError: При превышении лимита памяти

### `validate_image_for_ocr` — Функция

```python
def validate_image_for_ocr(image_content: bytes) -> tuple[bool, Optional[str]]
```

Валидация изображения перед OCR для предотвращения DoS атак.

Args:
    image_content: Содержимое изображения

Returns:
    tuple[bool, Optional[str]]: (is_valid, error_message)

### `get_memory_usage` — Функция

```python
def get_memory_usage() -> Dict[str, Any]
```

Получение информации об использовании памяти.

Returns:
    Dict[str, Any]: Информация о памяти

### `get_extension_from_mime` — Функция

```python
def get_extension_from_mime(content_type: str, supported_formats: dict) -> Optional[str]
```

Определение расширения файла по MIME-типу с учетом поддерживаемых форматов.

Args:
    content_type: MIME-тип из заголовка Content-Type
    supported_formats: Словарь поддерживаемых форматов из settings.SUPPORTED_FORMATS

Returns:
    Optional[str]: Расширение файла или None, если тип не поддерживается

### `decode_base64_image` — Функция

```python
def decode_base64_image(base64_data: str) -> Optional[bytes]
```

Декодирование base64 изображения из data URI.

Args:
    base64_data: Строка в формате data:image/jpeg;base64,/9j/4AAQ...

Returns:
    Optional[bytes]: Декодированные байты изображения или None при ошибке

### `extract_mime_from_base64_data_uri` — Функция

```python
def extract_mime_from_base64_data_uri(data_uri: str) -> Optional[str]
```

Извлечение MIME-типа из data URI.

Args:
    data_uri: Строка в формате data:image/jpeg;base64,/9j/4AAQ...

Returns:
    Optional[str]: MIME-тип (например, 'image/jpeg') или None при ошибке

### `preexec_fn` — Функция

```python
def preexec_fn()
```

Функция для установки ограничений ресурсов перед выполнением.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
