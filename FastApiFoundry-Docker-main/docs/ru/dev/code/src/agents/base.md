# Base

**Файл:** `src/agents/base.py`  
**Тип:** `.py`

---

### `ToolDefinition` — Класс

```python
@dataclass
```

### `ToolCallResult` — Класс

```python
@dataclass
```

### `AgentResult` — Класс

```python
@dataclass
```

### `BaseAgent` — Класс

```python
class BaseAgent(ABC)
```

Базовый класс агента.

Подклассы должны определить:
  - tools: List[ToolDefinition]
  - _execute_tool(name, arguments) -> str

### `to_openai` — Функция

```python
def to_openai(self) -> Dict
```

### `__init__` — Функция

```python
def __init__(self, foundry_client)
```

### `tools` — Функция

```python
@property
```

Список инструментов агента

### `_execute_tool` — Функция

```python
@abstractmethod
```

Выполнить инструмент и вернуть результат как строку.

Args:
    name: Tool name as defined in TOOLS.
    arguments: Parsed JSON arguments from the model's tool_call.

Returns:
    str: Tool execution result as a string passed back to the model.

### `tools_openai` — Функция

```python
def tools_openai(self) -> List[Dict]
```

Convert tool definitions to OpenAI function-calling format.

Returns:
    List[Dict]: List of tool dicts in OpenAI {type, function} schema.

### `run` — Функция

```python
async def run(self, user_message: str, model: str, temperature: float=0.7, max_tokens: int=2048, max_iterations: int=5) -> AgentResult
```

Запустить агентный цикл.

Args:
    user_message: User's input message.
    model: Foundry model ID to use.
    temperature: Sampling temperature.
    max_tokens: Maximum tokens per model response.
    max_iterations: Maximum tool-call iterations before stopping.

Returns:
    AgentResult: success, answer, tool_calls log, iterations count, error.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
