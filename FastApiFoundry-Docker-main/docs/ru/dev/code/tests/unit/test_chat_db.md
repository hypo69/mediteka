# Test Chat Db

**Файл:** `tests/unit/test_chat_db.py`  
**Тип:** `.py`

---

### `db` — Функция

```python
@pytest_asyncio.fixture
```

In-memory ChatDB instance, initialised and torn down per test.

### `_new_session_id` — Функция

```python
def _new_session_id() -> str
```

### `TestTablesCreated` — Класс

```python
class TestTablesCreated
```

3.2 test_tables_created — both tables exist after initialize().

### `TestCreateSession` — Класс

```python
class TestCreateSession
```

3.2 test_create_session — creates session, returns correct SessionRecord.

### `TestSaveMessageIncrementsCount` — Класс

```python
class TestSaveMessageIncrementsCount
```

3.2 test_save_message_increments_count.

### `TestGetSessionHistoryChronological` — Класс

```python
class TestGetSessionHistoryChronological
```

3.2 test_get_session_history_chronological.

### `TestDeleteSessionCascades` — Класс

```python
class TestDeleteSessionCascades
```

3.2 test_delete_session_cascades.

### `TestDatabaseInitError` — Класс

```python
class TestDatabaseInitError
```

3.2 test_database_init_error — DatabaseInitError for invalid path.

### `test_round_trip_storage` — Функция

```python
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
```

**Validates: Requirements 3.3, 9.6**

Property 5: Round-trip хранения сообщений в Chat_DB.

After saving messages to ChatDB and reading via get_session_history(),
messages are returned in timestamp ASC order with the same field values.

### `test_monotonic_message_count` — Функция

```python
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
```

**Validates: Requirements 3.2**

Property 6: Монотонный рост message_count.

After each save_message() call, message_count increases by exactly 1.

### `test_cascade_delete` — Функция

```python
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
```

**Validates: Requirements 3.5**

Property 7: Каскадное удаление сессии.

After delete_session(), neither the session nor its messages are returned
by session_exists() or get_session_history().

### `test_tables_created` — Функция

```python
async def test_tables_created(self, db: ChatDB) -> None
```

After initialize(), chat_sessions and chat_messages tables exist.

### `test_create_session_returns_session_record` — Функция

```python
async def test_create_session_returns_session_record(self, db: ChatDB) -> None
```

create_session() returns a SessionRecord with the correct fields.

### `test_session_exists_after_create` — Функция

```python
async def test_session_exists_after_create(self, db: ChatDB) -> None
```

session_exists() returns True after create_session().

### `test_session_not_exists_for_unknown_id` — Функция

```python
async def test_session_not_exists_for_unknown_id(self, db: ChatDB) -> None
```

session_exists() returns False for an unknown session_id.

### `test_message_count_increments_by_one` — Функция

```python
async def test_message_count_increments_by_one(self, db: ChatDB) -> None
```

message_count increases by 1 after each save_message().

### `test_messages_returned_in_timestamp_asc_order` — Функция

```python
async def test_messages_returned_in_timestamp_asc_order(self, db: ChatDB) -> None
```

get_session_history() returns messages ordered by timestamp ASC.

### `test_delete_removes_session_and_messages` — Функция

```python
async def test_delete_removes_session_and_messages(self, db: ChatDB) -> None
```

After delete_session(), session_exists() is False and history is [].

### `test_delete_nonexistent_returns_false` — Функция

```python
async def test_delete_nonexistent_returns_false(self, db: ChatDB) -> None
```

delete_session() returns False when the session does not exist.

### `test_invalid_path_raises_database_init_error` — Функция

```python
async def test_invalid_path_raises_database_init_error(self) -> None
```

DatabaseInitError is raised when the DB path is not writable.

### `_run` — Функция

```python
async def _run() -> None
```

### `_run` — Функция

```python
async def _run() -> None
```

### `_run` — Функция

```python
async def _run() -> None
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
