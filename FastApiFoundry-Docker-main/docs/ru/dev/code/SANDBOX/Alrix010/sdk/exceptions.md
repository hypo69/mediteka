# Exceptions

**Файл:** `SANDBOX/Alrix010/sdk/exceptions.py`  
**Тип:** `.py`

---

### `FoundryError` — Класс

```python
class FoundryError(Exception)
```

Базовое исключение SDK

### `FoundryConnectionError` — Класс

```python
class FoundryConnectionError(FoundryError)
```

Ошибка подключения к API

### `FoundryAPIError` — Класс

```python
class FoundryAPIError(FoundryError)
```

Ошибка API (HTTP статус коды)

### `FoundryConfigError` — Класс

```python
class FoundryConfigError(FoundryError)
```

Ошибка конфигурации

### `FoundryModelError` — Класс

```python
class FoundryModelError(FoundryError)
```

Ошибка работы с моделями


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
