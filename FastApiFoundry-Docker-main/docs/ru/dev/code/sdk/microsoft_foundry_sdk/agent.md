# Agent

**Файл:** `sdk/microsoft_foundry_sdk/agent.py`  
**Тип:** `.py`

---

### `FoundryAgent` — Класс

```python
class FoundryAgent
```

AI Agent powered by Foundry Local + Microsoft Agent Framework.

Connects a local Foundry model with MCP tools. The agent automatically
decides which tools to call based on user input.

Example:
    >>> agent = FoundryAgent(
    ...     base_url="http://localhost:50477/v1",
    ...     model_id="phi-4",
    ...     instructions="You are a helpful assistant.",
    ... )
    >>> async with agent:
    ...     response = await agent.run("List files in current directory")
    ...     print(response)

### `__init__` — Функция

```python
def __init__(self, base_url: str, model_id: str, api_key: str='local', instructions: str='You are a helpful AI assistant.', tools: Optional[List[Any]]=None) -> None
```

### `__aenter__` — Функция

```python
async def __aenter__(self) -> 'FoundryAgent'
```

### `__aexit__` — Функция

```python
async def __aexit__(self, *args: Any) -> None
```

### `run` — Функция

```python
async def run(self, message: str) -> str
```

Run agent with a single message, return full response.

Args:
    message: User input text.

Returns:
    str: Full agent response text.

### `stream` — Функция

```python
async def stream(self, message: str) -> AsyncGenerator[str, None]
```

Stream agent response token by token.

Args:
    message: User input text.

Yields:
    str: Text chunks as they arrive.

### `new_thread` — Функция

```python
def new_thread(self) -> None
```

Start a new conversation thread (clears history).

### `add_tool` — Функция

```python
def add_tool(self, tool: Any) -> None
```

Add a tool (MCP or custom) to the agent.

Args:
    tool: Tool object compatible with agent-framework.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
