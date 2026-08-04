# Qa Agent

**Файл:** `src/agents/qa_agent.py`  
**Тип:** `.py`

---

### `QAAgent` — Класс

```python
class QAAgent(BaseAgent)
```

Agent that runs pytest and reports results.

Workflow:
    user prompt
      └─ run_tests(path) → subprocess pytest → parse stdout
      └─ get_coverage()  → pytest --cov → parse report
      └─ answer with summary

### `tools` — Функция

```python
@property
```

### `_execute_tool` — Функция

```python
async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str
```

### `_run_tests` — Функция

```python
async def _run_tests(self, path: str, filter_expr: str | None, coverage: bool) -> str
```

Run pytest and return formatted output.

Args:
    path: Test path relative to project root.
    filter_expr: Optional -k expression.
    coverage: Whether to add --cov flag.

Returns:
    str: Formatted test result summary.

### `_list_test_files` — Функция

```python
def _list_test_files(self) -> str
```

List all test files in tests/ directory.

Returns:
    str: Newline-separated list of test file paths.

### `_get_coverage` — Функция

```python
async def _get_coverage(self, source: str) -> str
```

Run pytest with coverage report.

Args:
    source: Source directory to measure coverage for.

Returns:
    str: Coverage report output.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
