# Keystroke Agent

**Файл:** `src/agents/keystroke_agent.py`  
**Тип:** `.py`

---

### `KeystrokeAgent` — Класс

```python
class KeystrokeAgent(BaseAgent)
```

Агент идентификации пользователя по клавиатурному почерку.

Хранит обученную ML-модель в памяти между вызовами инструментов.
Использует RandomForestClassifier из scikit-learn.

### `__init__` — Функция

```python
def __init__(self, foundry_client)
```

### `tools` — Функция

```python
@property
```

### `_execute_tool` — Функция

```python
async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str
```

Выполнить инструмент агента.

Args:
    name (str): Имя инструмента.
    arguments (Dict[str, Any]): Аргументы вызова.

Returns:
    str: Результат выполнения.

### `_extract_features` — Функция

```python
def _extract_features(self, session: List[float]) -> List[float]
```

Извлечь признаки из одной сессии нажатий клавиш.

Признаки: среднее, стандартное отклонение, медиана, мин, макс,
межквартильный размах (IQR).

Args:
    session (List[float]): Длительности нажатий в мс.

Returns:
    List[float]: Вектор из 6 признаков.

### `_train_model` — Функция

```python
def _train_model(self, args: Dict[str, Any]) -> str
```

Обучить RandomForestClassifier на данных пользователей.

Args:
    args: users_data — {username: [[сессия], ...]}.

Returns:
    str: Результат обучения с метриками.

### `_predict_user` — Функция

```python
def _predict_user(self, args: Dict[str, Any]) -> str
```

Идентифицировать пользователя по сессии нажатий.

Args:
    args: session — список длительностей нажатий в мс.

Returns:
    str: Предсказанный пользователь и вероятности.

### `_get_model_info` — Функция

```python
def _get_model_info(self) -> str
```

Вернуть статус и метрики модели.

Returns:
    str: JSON со статусом модели.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
