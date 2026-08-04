# Rag Agent

**Файл:** `src/agents/rag_agent.py`  
**Тип:** `.py`

---

### `RagAgent` — Класс

```python
class RagAgent(BaseAgent)
```

Агент для ответов на вопросы с использованием RAG-контекста.

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
    name (str): Имя инструмента ('rag_search' или 'generate_answer').
    arguments (Dict[str, Any]): Аргументы вызова.

Returns:
    str: Результат выполнения инструмента.

### `_rag_search` — Функция

```python
async def _rag_search(self, args: Dict[str, Any]) -> str
```

Поиск в RAG-индексе.

Args:
    args (Dict[str, Any]): query (str), top_k (int, optional).

Returns:
    str: Найденные фрагменты или сообщение об отсутствии результатов.

### `_format_answer` — Функция

```python
def _format_answer(self, args: Dict[str, Any]) -> str
```

Форматирует промпт для финального ответа.

Модель получит этот текст как результат tool_call и сформирует ответ.

Args:
    args (Dict[str, Any]): question (str), context (str).

Returns:
    str: Инструкция для модели с вопросом и контекстом.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
