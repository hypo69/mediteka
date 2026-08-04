# 🤖 Agents

Директория для AI агентов проекта FastAPI Foundry.

Агент — это компонент, который получает сообщение от пользователя, решает какие инструменты вызвать, выполняет их через MCP серверы и возвращает финальный ответ.

---

## Архитектура

```
Пользователь
    ↓ сообщение
BaseAgent.run()
    ↓ messages + tools → Foundry (OpenAI API)
Модель возвращает tool_calls
    ↓
_execute_tool(name, arguments)
    ↓
MCP сервер (STDIO / HTTP)
    ↓ результат
Модель формирует финальный ответ
    ↓
Пользователь
```

---

## Файлы

| Файл | Назначение |
|------|-----------|
| `base.py` | Базовый класс `BaseAgent` с агентным циклом |
| `powershell_agent.py` | Агент для работы с локальной системой через PowerShell |

---

## Базовый класс `BaseAgent`

Определён в `base.py`. Реализует агентный цикл — подклассы только определяют инструменты и их выполнение.

```python
class MyAgent(BaseAgent):
    name = "my_agent"
    description = "Описание агента"

    @property
    def tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="my_tool",
                description="Что делает инструмент",
                parameters={
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "Входные данные"}
                    },
                    "required": ["input"]
                }
            )
        ]

    async def _execute_tool(self, name: str, arguments: dict) -> str:
        if name == "my_tool":
            return f"Результат: {arguments['input']}"
        return f"❌ Неизвестный инструмент: {name}"
```

### Вспомогательные классы

- `ToolDefinition(name, description, parameters)` — описание инструмента в формате OpenAI function calling
- `ToolCallResult(tool, arguments, result)` — результат вызова инструмента
- `AgentResult(success, answer, tool_calls, iterations, error, note)` — результат работы агента

---

## Существующие агенты

### `PowerShellAgent`

Файл: `powershell_agent.py`  
Имя: `powershell`

Инструменты:

| Инструмент | MCP сервер | Описание |
|-----------|-----------|---------|
| `run_powershell` | `McpSTDIOServer.ps1` | Выполнить PowerShell команду |
| `run_wp_cli` | `McpWPCLIServer.ps1` | Выполнить WP-CLI команду |
| `http_get` | — (прямой запрос) | HTTP GET запрос |

Примеры запросов:
- `"покажи содержимое текущей директории"` → `run_powershell("Get-ChildItem")`
- `"сколько файлов .py в проекте"` → `run_powershell("(Get-ChildItem -Recurse -Filter *.py).Count")`
- `"список плагинов WordPress"` → `run_wp_cli("plugin list")`

---

## Как добавить нового агента

**1. Создай файл** `src/agents/my_agent.py`:

```python
from .base import BaseAgent, ToolDefinition
from typing import List, Dict, Any

class MyAgent(BaseAgent):
    name = "my_agent"
    description = "Краткое описание"

    @property
    def tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="my_tool",
                description="...",
                parameters={
                    "type": "object",
                    "properties": {
                        "param": {"type": "string", "description": "..."}
                    },
                    "required": ["param"]
                }
            )
        ]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if name == "my_tool":
            # логика выполнения
            return "результат"
        return f"❌ Неизвестный инструмент: {name}"
```

**2. Зарегистрируй** в `src/api/endpoints/agent.py`:

```python
from ...agents.my_agent import MyAgent

def _build_registry():
    return {
        "powershell": PowerShellAgent(foundry_client),
        "my_agent":   MyAgent(foundry_client),   # ← добавить
    }
```

**3. Готово** — агент появится в UI на вкладке Agent и в API:
- `GET /v1/agent/list`
- `GET /v1/agent/my_agent/tools`
- `POST /v1/agent/run` с `{"agent": "my_agent", "message": "..."}`

---

## API

| Метод | Путь | Описание |
|-------|------|---------|
| `GET` | `/v1/agent/list` | Список всех агентов |
| `GET` | `/v1/agent/{name}/tools` | Инструменты агента |
| `POST` | `/v1/agent/run` | Запустить агента |

Тело запроса `POST /v1/agent/run`:

```json
{
  "message": "покажи содержимое текущей директории",
  "agent": "powershell",
  "model": "qwen3-0.6b-generic-cpu:4:4",
  "temperature": 0.3,
  "max_tokens": 2048,
  "max_iterations": 5
}
```

---

## Требования

- PowerShell 7+ (для `PowerShellAgent`)
- Foundry Local запущен и доступен
- Модель с поддержкой function calling (Qwen, DeepSeek, Mistral)
