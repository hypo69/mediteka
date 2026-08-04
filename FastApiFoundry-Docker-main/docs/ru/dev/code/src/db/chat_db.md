# Chat Db

**Файл:** `src/db/chat_db.py`  
**Тип:** `.py`

---

### `DatabaseInitError` — Класс

```python
class DatabaseInitError(Exception)
```

Raised when the SQLite database cannot be initialised.

This exception is thrown by :meth:`ChatDB.initialize` when the database
file is inaccessible, corrupted, or the schema cannot be created.

### `ChatDB` — Класс

```python
class ChatDB
```

Async SQLite data-access layer for chat sessions and messages.

All public methods are coroutines and must be awaited.  The underlying
connection is created lazily on the first call to :meth:`initialize`.

Attributes:
    _db_path: Absolute path to the SQLite database file.
    _db: Active :class:`aiosqlite.Connection`, or ``None`` before
        :meth:`initialize` is called.

### `get_chat_db` — Функция

```python
async def get_chat_db() -> ChatDB
```

Return (or lazily create) the module-level :class:`ChatDB` singleton.

On the first call the instance is created using the path from
:attr:`src.core.config.config.chat_history_db_path` and
:meth:`ChatDB.initialize` is called automatically.

Returns:
    The initialised :class:`ChatDB` singleton.

Raises:
    DatabaseInitError: If the database cannot be initialised on the
        first call.

### `__init__` — Функция

```python
def __init__(self, db_path: str) -> None
```

Store the database path and prepare the connection slot.

Args:
    db_path: Path to the SQLite file.  ``~`` is expanded to the
        current user's home directory.  Use ``":memory:"`` for an
        in-memory database (useful in tests).

### `initialize` — Функция

```python
async def initialize(self) -> None
```

Open the database connection and create tables / indexes.

Creates the ``chat_sessions`` and ``chat_messages`` tables together
with the ``idx_messages_session_id`` index if they do not already
exist.  WAL journal mode and foreign-key enforcement are enabled.

Raises:
    DatabaseInitError: If the database file cannot be opened or the
        schema cannot be applied (e.g. path is not writable, file is
        corrupted).

### `close` — Функция

```python
async def close(self) -> None
```

Close the underlying database connection.

Safe to call even if :meth:`initialize` was never called or the
connection is already closed.

### `create_session` — Функция

```python
async def create_session(self, session_id: str, model: str='', title: str='') -> SessionRecord
```

Insert a new chat session record.

Args:
    session_id: Unique identifier for the session (UUID v4 string).
    model: Name of the AI model used in this session.
    title: Human-readable title for the session.

Returns:
    A :class:`~src.db.schemas.SessionRecord` representing the newly
    created session.

Raises:
    aiosqlite.IntegrityError: If a session with the same
        ``session_id`` already exists.

### `session_exists` — Функция

```python
async def session_exists(self, session_id: str) -> bool
```

Check whether a session exists in the database.

Args:
    session_id: The UUID v4 string identifying the session.

Returns:
    ``True`` if the session exists, ``False`` otherwise.

### `list_sessions` — Функция

```python
async def list_sessions(self, limit: int=50, offset: int=0) -> tuple[list[SessionRecord], int]
```

Return a paginated list of sessions ordered by last update.

Args:
    limit: Maximum number of sessions to return.
    offset: Number of sessions to skip (for pagination).

Returns:
    A tuple ``(sessions, total)`` where *sessions* is a list of
    :class:`~src.db.schemas.SessionRecord` objects sorted by
    ``updated_at`` descending, and *total* is the total count of
    sessions in the database.

### `delete_session` — Функция

```python
async def delete_session(self, session_id: str) -> bool
```

Delete a session and all its messages (cascade).

Args:
    session_id: The UUID v4 string identifying the session to delete.

Returns:
    ``True`` if the session was found and deleted, ``False`` if no
    session with the given ``session_id`` existed.

### `save_message` — Функция

```python
async def save_message(self, session_id: str, role: str, content: str, timestamp: Optional[int]=None) -> MessageRecord
```

Persist a single message and atomically update session metadata.

Inserts the message into ``chat_messages`` and, in the same
transaction, increments ``message_count`` and refreshes
``updated_at`` in the parent ``chat_sessions`` row.

Args:
    session_id: The UUID v4 string identifying the target session.
    role: Message author role — one of ``"user"``, ``"assistant"``,
        ``"system"``.
    content: Text content of the message.
    timestamp: Unix timestamp for the message.  Defaults to
        ``int(time.time())`` when ``None``.

Returns:
    A :class:`~src.db.schemas.MessageRecord` representing the saved
    message.

Raises:
    aiosqlite.Error: On any SQLite-level failure.

### `get_session_history` — Функция

```python
async def get_session_history(self, session_id: str) -> list[MessageRecord]
```

Retrieve all messages for a session in chronological order.

Args:
    session_id: The UUID v4 string identifying the session.

Returns:
    A list of :class:`~src.db.schemas.MessageRecord` objects sorted
    by ``timestamp`` ascending.  Returns an empty list if the session
    has no messages or does not exist.

### `get_messages_since` — Функция

```python
async def get_messages_since(self, since_timestamp: int, session_ids: Optional[list[str]]=None) -> list[dict]
```

Return messages created after a given Unix timestamp.

Args:
    since_timestamp: Only messages with ``timestamp`` strictly
        greater than this value are returned.
    session_ids: Optional list of session IDs to restrict the query.
        When ``None``, messages from all sessions are considered.

Returns:
    A list of dicts with keys ``session_id``, ``role``, ``content``,
    and ``timestamp``, ordered by ``timestamp`` ascending.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
