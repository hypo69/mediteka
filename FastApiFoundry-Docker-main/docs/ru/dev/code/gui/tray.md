# Tray

**Файл:** `gui/tray.py`  
**Тип:** `.py`

---

### `_is_server_running` — Функция

```python
def _is_server_running() -> bool
```

Check FastAPI server availability via health endpoint.

### `_load_image` — Функция

```python
def _load_image() -> Image.Image
```

Load tray icon image.

### `_run_ps1` — Функция

```python
def _run_ps1(script: str) -> None
```

Run a PowerShell script in a new minimized window.

### `_focus_or_open_browser` — Функция

```python
def _focus_or_open_browser() -> None
```

Focus existing browser window or open new one (best-effort on Windows).

### `on_admin` — Функция

```python
def on_admin(_icon: pystray.Icon, _item: pystray.MenuItem) -> None
```

Open admin interface in browser.

### `on_user` — Функция

```python
def on_user(_icon: pystray.Icon, _item: pystray.MenuItem) -> None
```

Open user (pywebview) interface; start it if not running.

### `on_start` — Функция

```python
def on_start(_icon: pystray.Icon, _item: pystray.MenuItem) -> None
```

Start FastAPI server via start.ps1.

### `on_shutdown` — Функция

```python
def on_shutdown(_icon: pystray.Icon, _item: pystray.MenuItem) -> None
```

Stop FastAPI server by PID file.

### `on_quit` — Функция

```python
def on_quit(_icon: pystray.Icon, _item: pystray.MenuItem) -> None
```

Remove tray icon and exit.

### `_stop_server` — Функция

```python
def _stop_server() -> None
```

Kill FastAPI process by PID file.

### `_build_menu` — Функция

```python
def _build_menu() -> pystray.Menu
```

### `_poll_state` — Функция

```python
def _poll_state(icon: pystray.Icon) -> None
```

### `main` — Функция

```python
def main() -> None
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
