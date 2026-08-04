# Log Analyzer

**Файл:** `src/utils/log_analyzer.py`  
**Тип:** `.py`

---

### `LogAnalyzer` — Класс

```python
class LogAnalyzer
```

Анализатор логов с метриками и статистикой

### `__init__` — Функция

```python
def __init__(self, logs_dir: str='logs')
```

### `get_system_health` — Функция

```python
async def get_system_health(self) -> Dict[str, Any]
```

Получить общее состояние системы на основе логов

### `get_error_summary` — Функция

```python
async def get_error_summary(self, hours: int=24) -> Dict[str, Any]
```

Получить сводку ошибок за период

### `get_performance_metrics` — Функция

```python
async def get_performance_metrics(self, hours: int=24) -> Dict[str, Any]
```

Получить метрики производительности

### `_count_errors` — Функция

```python
async def _count_errors(self, start_time: datetime, end_time: datetime) -> int
```

Подсчет ошибок за период

### `_count_warnings` — Функция

```python
async def _count_warnings(self, start_time: datetime, end_time: datetime) -> int
```

Подсчет предупреждений за период

### `_collect_errors` — Функция

```python
async def _collect_errors(self, start_time: datetime, end_time: datetime) -> List[Dict]
```

Сбор ошибок из логов

### `_collect_warnings` — Функция

```python
async def _collect_warnings(self, start_time: datetime, end_time: datetime) -> List[Dict]
```

Сбор предупреждений из логов

### `_analyze_api_performance` — Функция

```python
async def _analyze_api_performance(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]
```

Анализ производительности API

### `_analyze_model_performance` — Функция

```python
async def _analyze_model_performance(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]
```

Анализ производительности моделей

### `_analyze_system_performance` — Функция

```python
async def _analyze_system_performance(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]
```

Анализ системной производительности

### `_classify_error` — Функция

```python
def _classify_error(self, message: str) -> str
```

Классификация ошибок по типам


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
