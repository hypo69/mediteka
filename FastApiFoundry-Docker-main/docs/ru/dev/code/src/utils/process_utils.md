# Process Utils

**Файл:** `src/utils/process_utils.py`  
**Тип:** `.py`

---

### `run_command` — Функция

```python
def run_command(args: List[str], timeout: int=30, shell: bool=False, capture_output: bool=True) -> subprocess.CompletedProcess
```

Run a command via subprocess.run with project-standard defaults.

Args:
    args: List of command arguments.
    timeout: Execution timeout in seconds.
    shell: Whether to use the shell.
    capture_output: Whether to capture stdout and stderr.

Returns:
    subprocess.CompletedProcess: The result of the command execution.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
