# Google Agent

**Файл:** `src/agents/google_agent.py`  
**Тип:** `.py`

---

### `_get_google_creds` — Функция

```python
def _get_google_creds() -> Optional['Credentials']
```

Load or refresh OAuth2 credentials.

Returns:
    Credentials: Valid Google OAuth2 credentials, or None on failure.

### `GoogleAgent` — Класс

```python
class GoogleAgent(BaseAgent)
```

Agent for Google Workspace: Gmail, Calendar, Sheets, Docs.

### `_extract_gmail_body` — Функция

```python
def _extract_gmail_body(payload: Dict) -> str
```

Recursively extract plain text body from Gmail message payload.

Args:
    payload: Gmail message payload dict.

Returns:
    str: Decoded plain text body.

### `tools` — Функция

```python
@property
```

### `_execute_tool` — Функция

```python
async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str
```

Dispatch tool call to the appropriate handler.

Args:
    name: Tool name.
    arguments: Parsed arguments from model tool_call.

Returns:
    str: Result string passed back to the model.

### `_gmail_list` — Функция

```python
async def _gmail_list(self, args: Dict) -> str
```

### `_gmail_read` — Функция

```python
async def _gmail_read(self, args: Dict) -> str
```

### `_gmail_send` — Функция

```python
async def _gmail_send(self, args: Dict) -> str
```

### `_calendar_list` — Функция

```python
async def _calendar_list(self, args: Dict) -> str
```

### `_calendar_create` — Функция

```python
async def _calendar_create(self, args: Dict) -> str
```

### `_sheets_read` — Функция

```python
async def _sheets_read(self, args: Dict) -> str
```

### `_sheets_write` — Функция

```python
async def _sheets_write(self, args: Dict) -> str
```

### `_docs_read` — Функция

```python
async def _docs_read(self, args: Dict) -> str
```

### `_docs_append` — Функция

```python
async def _docs_append(self, args: Dict) -> str
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
