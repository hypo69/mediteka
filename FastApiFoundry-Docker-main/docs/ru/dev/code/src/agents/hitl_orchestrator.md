# Hitl Orchestrator

**Файл:** `src/agents/hitl_orchestrator.py`  
**Тип:** `.py`

---

### `HITLOrchestrator` — Класс

```python
class HITLOrchestrator
```

Класс для управления подтверждением действий пользователя (Human-in-the-loop)

Attributes:
    dangerous_patterns (list): Список маркеров опасности в описаниях инструментов.
    protected_tools (list): Список имен инструментов, требующих подтверждения.

### `__init__` — Функция

```python
def __init__(self) -> None
```

Инициализация оркестратора и загрузка конфигурации.

### `is_confirmation_required` — Функция

```python
def is_confirmation_required(self, tool_name: str, tool_description: str) -> bool
```

Проверка необходимости подтверждения перед выполнением.

Args:
    tool_name (str): Имя инструмента.
    tool_description (str): Текстовое описание функционала инструмента.

Returns:
    bool: True при необходимости ручного подтверждения.

Examples:
    >>> orchestrator = HITLOrchestrator()
    >>> orchestrator.is_confirmation_required("delete_file", "Удаляет файл")
    True

### `request_user_permission` — Функция

```python
async def request_user_permission(self, tool_name: str, arguments: dict) -> bool
```

Запрос разрешения у пользователя на выполнение действия.

Args:
    tool_name (str): Имя инструмента.
    arguments (dict): Параметры вызова.

Returns:
    bool: Результат выбора пользователя.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
