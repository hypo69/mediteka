# Windows Os Agent

**Файл:** `src/agents/windows_os_agent.py`  
**Тип:** `.py`

---

### `_call_mcp` — Функция

```python
def _call_mcp(tool_name: str, arguments: Dict[str, Any]) -> str
```

Call windows_os_mcp.py via STDIO JSON-RPC.

### `WindowsOsAgent` — Класс

```python
class WindowsOsAgent(BaseAgent)
```

Агент-специалист по Windows OS.

Сценарий: prompt → RAG (контекст) → model → MCP tools (реальные данные) → ответ.

### `_send` — Функция

```python
def _send(method: str, params: Dict) -> Dict
```

### `tools` — Функция

```python
@property
```

### `_execute_tool` — Функция

```python
async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str
```

Execute tool by name.

Args:
    name: Tool name.
    arguments: Tool arguments.

Returns:
    str: Tool result.

### `_rag_search` — Функция

```python
async def _rag_search(self, args: Dict[str, Any]) -> str
```

Search RAG index for Windows OS knowledge.

Args:
    args: query (str), top_k (int, optional).

Returns:
    str: Found context or message about empty results.

### `run` — Функция

```python
async def run(self, user_message: str, model: str, **kwargs: object) -> Any
```

Inject system prompt before running the agent loop.

Args:
    user_message: User's question.
    model: Model ID.
    **kwargs: Passed to BaseAgent.run.

Returns:
    AgentResult


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
