# Agent

**Файл:** `src/api/endpoints/agent.py`  
**Тип:** `.py`

---

### `_build_registry` — Функция

```python
def _build_registry()
```

### `get_registry` — Функция

```python
def get_registry()
```

### `select_agent_name` — Функция

```python
def select_agent_name(message: str, requested_agent: str, registry: dict) -> str
```

Select an agent for auto mode.

The first implementation routes OS administration tasks to ComputerAdminAgent.
It is intentionally small while the system has one autonomous diagnostic agent.

### `AgentRequest` — Класс

```python
class AgentRequest(BaseModel)
```

### `list_agents` — Функция

```python
@router.get('/agent/list')
```

Список зарегистрированных агентов

### `list_agent_tools` — Функция

```python
@router.get('/agent/{agent_name}/tools')
```

Список инструментов конкретного агента

### `run_agent` — Функция

```python
@router.post('/agent/run')
```

Запустить агента.

Агент сам решает какие инструменты вызвать для ответа на вопрос.
По умолчанию используется агент 'powershell'.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
