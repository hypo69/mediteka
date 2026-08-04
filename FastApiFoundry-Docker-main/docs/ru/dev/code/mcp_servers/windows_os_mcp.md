# Windows Os Mcp

**Файл:** `servers/windows_os_mcp.py`  
**Тип:** `.py`

---

### `_run_ps` — Функция

```python
def _run_ps(script: str) -> str
```

Run a PowerShell snippet and return stdout.

### `_safe_name` — Функция

```python
def _safe_name(value: str, label: str='name') -> str
```

Allow only simple Windows identifiers used in service and task names.

### `_clamp_int` — Функция

```python
def _clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int
```

### `_truncate` — Функция

```python
def _truncate(value: str, limit: int=8000) -> str
```

### `_clean_text` — Функция

```python
def _clean_text(value: Any) -> str
```

Normalize text so JSON-RPC output never contains invalid surrogate chars.

### `_ensure_script_dir` — Функция

```python
def _ensure_script_dir() -> Path
```

### `_reject_unsafe_script` — Функция

```python
def _reject_unsafe_script(script: str, language: str) -> None
```

Block obvious mutating operations in model-generated diagnostic scripts.

### `get_processes` — Функция

```python
def get_processes(sort_by: str='cpu', top: int=20) -> str
```

Return top processes sorted by CPU or memory.

### `get_services` — Функция

```python
def get_services(filter_status: str='all') -> str
```

Return Windows services, optionally filtered by status.

### `get_disk_info` — Функция

```python
def get_disk_info() -> str
```

Return disk usage for all drives.

### `get_network_stats` — Функция

```python
def get_network_stats() -> str
```

Return active TCP connections and network adapter stats.

### `get_system_info` — Функция

```python
def get_system_info() -> str
```

Return OS version, uptime, CPU and RAM summary.

### `kill_process` — Функция

```python
def kill_process(pid: int) -> str
```

Stop a process by PID.

### `get_startup_items` — Функция

```python
def get_startup_items() -> str
```

Return programs configured to run at startup.

### `get_event_logs` — Функция

```python
def get_event_logs(log_name: str='System', level: str='Error', newest: int=20) -> str
```

Return recent Windows event log records.

### `get_installed_apps` — Функция

```python
def get_installed_apps() -> str
```

Return installed applications from common uninstall registry keys.

### `get_local_users` — Функция

```python
def get_local_users() -> str
```

Return local Windows users and basic account state.

### `get_scheduled_tasks` — Функция

```python
def get_scheduled_tasks(task_state: str='all') -> str
```

Return scheduled tasks, optionally filtered by state.

### `get_defender_status` — Функция

```python
def get_defender_status() -> str
```

Return Microsoft Defender computer status.

### `get_windows_update_status` — Функция

```python
def get_windows_update_status() -> str
```

Return Windows Update service state and latest installed hotfixes.

### `control_service` — Функция

```python
def control_service(name: str, action: str) -> str
```

Start, stop or restart a Windows service.

### `cleanup_temp_files` — Функция

```python
def cleanup_temp_files(path: str='', dry_run: bool=True, older_than_days: int=7) -> str
```

Estimate or remove old files from a temp directory.

### `invoke_os_diagnostic` — Функция

```python
def invoke_os_diagnostic(output_dir: str='', window_hours: int=24, skip_events: bool=False, no_store: bool=False) -> str
```

Run the production PowerShell diagnostic toolkit and return its JSON report.

### `run_powershell_check` — Функция

```python
def run_powershell_check(script: str, timeout_seconds: int=30, reason: str='') -> str
```

Run a model-generated PowerShell diagnostic script from a temporary file.

### `run_python_check` — Функция

```python
def run_python_check(script: str, timeout_seconds: int=30, reason: str='') -> str
```

Run a model-generated Python diagnostic script from a temporary file.

### `_respond` — Функция

```python
def _respond(id_: Any, result: Any=None, error: Any=None) -> None
```

### `_handle` — Функция

```python
def _handle(req: Dict[str, Any]) -> None
```

### `main` — Функция

```python
def main() -> None
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
