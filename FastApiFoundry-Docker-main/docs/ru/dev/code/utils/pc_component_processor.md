# Pc Component Processor

**Файл:** `utils/pc_component_processor.py`  
**Тип:** `.py`

---

### `PCComponentProcessor` — Класс

```python
class PCComponentProcessor
```

Класс для обработки и нормализации данных о компонентах ПК

Attributes:
    banned_brands (List[str]): Список брендов, подлежащих удалению.

### `__init__` — Функция

```python
def __init__(self) -> None
```

Инициализация экземпляра класса.

### `execute` — Функция

```python
def execute(self, data_path: str) -> Optional[Dict]
```

Запуск процесса обработки данных

Args:
    data_path (str): Путь к файлу с входными данными.

Returns:
    Optional[Dict]: Обработанный JSON ответ или None.

### `_process_items` — Функция

```python
def _process_items(self, data: Dict) -> Dict
```

Внутренняя обработка элементов данных

Args:
    data (Dict): Словарь данных.

Returns:
    Dict: Результат нормализации.

### `_filter_brands` — Функция

```python
def _filter_brands(self, text: str) -> str
```

Фильтрация текста от упоминания компаний

Args:
    text (str): Исходный текст.

Returns:
    str: Очищенный текст.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
