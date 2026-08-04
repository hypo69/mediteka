# Ftp Mcp

**Файл:** `servers/ftp_mcp.py`  
**Тип:** `.py`

---

### `_get_ftp_connection` — Функция

```python
def _get_ftp_connection() -> ftplib.FTP
```

Create and return an authenticated FTP connection.

Reads FTP_HOST, FTP_USER, FTP_PASSWORD, FTP_PORT from environment.

Returns:
    ftplib.FTP: Connected and authenticated FTP instance.

Raises:
    ValueError: If required env vars are missing.
    ftplib.all_errors: On connection or auth failure.

### `FtpMCPServer` — Класс

```python
class FtpMCPServer
```

MCP server for FTP file operations.

Reads connection parameters from environment variables:
    FTP_HOST     — FTP server hostname or IP
    FTP_USER     — FTP username
    FTP_PASSWORD — FTP password
    FTP_PORT     — FTP port (default: 21)

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

Return the list of available FTP tools.

Returns:
    list[types.Tool]: Tool definitions for all FTP operations.

### `call_tool` — Функция

```python
async def call_tool(self, name: str, arguments: dict[str, Any]) -> list[types.TextContent]
```

Dispatch a tool call to the appropriate FTP operation.

Args:
    name: Tool name.
    arguments: Tool arguments dict.

Returns:
    list[types.TextContent]: Result as text content.

### `_ftp_list` — Функция

```python
def _ftp_list(self, path: str) -> list[types.TextContent]
```

List files in a remote directory.

Args:
    path: Remote directory path.

Returns:
    list[types.TextContent]: Directory listing as text.

### `_ftp_upload` — Функция

```python
def _ftp_upload(self, local_path: str, remote_path: str) -> list[types.TextContent]
```

Upload a local file to FTP.

Args:
    local_path: Local file path.
    remote_path: Destination path on FTP.

Returns:
    list[types.TextContent]: Success or error message.

### `_ftp_download` — Функция

```python
def _ftp_download(self, remote_path: str, local_path: str) -> list[types.TextContent]
```

Download a file from FTP.

Args:
    remote_path: File path on FTP.
    local_path: Local destination path.

Returns:
    list[types.TextContent]: Success or error message.

### `_ftp_delete` — Функция

```python
def _ftp_delete(self, remote_path: str) -> list[types.TextContent]
```

Delete a file on FTP.

Args:
    remote_path: File path on FTP to delete.

Returns:
    list[types.TextContent]: Success or error message.

### `_ftp_rename` — Функция

```python
def _ftp_rename(self, from_path: str, to_path: str) -> list[types.TextContent]
```

Rename or move a file on FTP.

Args:
    from_path: Current file path on FTP.
    to_path: New file path on FTP.

Returns:
    list[types.TextContent]: Success or error message.

### `run` — Функция

```python
async def run(self) -> None
```

Start the MCP server STDIO loop.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
