# Docs Deploy Mcp

**Файл:** `mcp/src/servers/docs_deploy_mcp.py`  
**Тип:** `.py`

---

### `_ftp_connect` — Функция

```python
def _ftp_connect() -> ftplib.FTP
```

Create authenticated FTP connection from environment variables.

Returns:
    ftplib.FTP: Connected and logged-in FTP instance.

Raises:
    ValueError: If required env vars are missing.

### `_ftp_mkdir_p` — Функция

```python
def _ftp_mkdir_p(ftp: ftplib.FTP, remote_path: str) -> None
```

Recursively create remote directories (like mkdir -p).

Args:
    ftp: Active FTP connection.
    remote_path: Remote directory path to create.

### `_upload_dir` — Функция

```python
def _upload_dir(ftp: ftplib.FTP, local_dir: Path, remote_dir: str) -> tuple[int, int]
```

Recursively upload a local directory to FTP.

Args:
    ftp: Active FTP connection.
    local_dir: Local directory to upload.
    remote_dir: Remote destination path.

Returns:
    tuple[int, int]: (files_uploaded, bytes_uploaded)

### `_deploy_lang` — Функция

```python
def _deploy_lang(lang: str) -> dict
```

Deploy built docs for one language to FTP.

Args:
    lang: Language code — 'ru' or 'en'.

Returns:
    dict: success, files, size_mb, remote_path, error.

### `DocsDeployMCPServer` — Класс

```python
class DocsDeployMCPServer
```

MCP server for deploying MkDocs documentation to FTP.

Environment variables (from .env):
    FTP_HOST        — FTP server hostname or IP
    FTP_USER        — FTP username
    FTP_PASSWORD    — FTP password
    FTP_PORT        — FTP port (default: 21)
    FTP_DOCS_RU     — remote path for Russian docs
    FTP_DOCS_EN     — remote path for English docs

### `main` — Функция

```python
async def main() -> None
```

Entry point.

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `list_tools` — Функция

```python
async def list_tools(self) -> list[types.Tool]
```

Return available deployment tools.

### `call_tool` — Функция

```python
async def call_tool(self, name: str, arguments: dict[str, Any]) -> list[types.TextContent]
```

Dispatch tool calls.

Args:
    name: Tool name.
    arguments: Tool arguments.

Returns:
    list[types.TextContent]: Result as text.

### `_build_docs` — Функция

```python
async def _build_docs(self) -> dict
```

Run mkdocs build subprocess.

Returns:
    dict: success, output, error.

### `_check_status` — Функция

```python
def _check_status(self) -> str
```

List file counts in remote docs directories.

Returns:
    str: Status text with file counts per language.

### `_fmt` — Функция

```python
@staticmethod
```

Format deploy result as human-readable string.

Args:
    result: Result dict from _deploy_lang.

Returns:
    str: Formatted status line.

### `run` — Функция

```python
async def run(self) -> None
```

Start the MCP STDIO server.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
