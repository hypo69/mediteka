# Computer Admin Agent

**Файл:** `src/agents/computer_admin_agent.py`  
**Тип:** `.py`

---

### `ComputerAdminAgent` — Класс

```python
class ComputerAdminAgent(BaseAgent)
```

ИИ-агент для администрирования локального Windows-компьютера.

### `tools` — Функция

```python
@property
```

### `_execute_tool` — Функция

```python
async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str
```

Execute a typed Windows administration tool.

### `run` — Функция

```python
async def run(self, user_message: str, model: str, **kwargs) -> Any
```

Inject administrator behavior rules before running the agent loop.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
