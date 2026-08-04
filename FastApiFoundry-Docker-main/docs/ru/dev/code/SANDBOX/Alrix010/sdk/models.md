# Models

**Файл:** `SANDBOX/Alrix010/sdk/models.py`  
**Тип:** `.py`

---

### `GenerationRequest` — Класс

```python
@dataclass
```

Запрос на генерацию текста

### `GenerationResponse` — Класс

```python
@dataclass
```

Ответ генерации текста

### `ModelInfo` — Класс

```python
@dataclass
```

Информация о модели

### `HealthStatus` — Класс

```python
@dataclass
```

Статус здоровья системы

### `dict` — Функция

```python
def dict(self, exclude_none: bool=False) -> Dict[str, Any]
```

Преобразовать в словарь

### `__init__` — Функция

```python
def __init__(self, **kwargs)
```

### `__init__` — Функция

```python
def __init__(self, **kwargs)
```

### `__init__` — Функция

```python
def __init__(self, **kwargs)
```

### `is_healthy` — Функция

```python
@property
```

Проверить, здорова ли система

### `is_foundry_connected` — Функция

```python
@property
```

Проверить, подключен ли Foundry


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
