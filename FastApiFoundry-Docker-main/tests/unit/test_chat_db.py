# -*- coding: utf-8 -*-
# =============================================================================
# Tests for src/db/chat_db.py — ChatDB unit tests + property-based tests
# =============================================================================

import uuid

import pytest
import pytest_asyncio
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.db.chat_db import ChatDB, DatabaseInitError

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db():
    """In-memory ChatDB instance, initialised and torn down per test."""
    chat_db = ChatDB(":memory:")
    await chat_db.initialize()
    yield chat_db
    await chat_db.close()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _new_session_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Task 3.2 — Unit tests
# ---------------------------------------------------------------------------


class TestTablesCreated:
    """3.2 test_tables_created — both tables exist after initialize()."""

    async def test_tables_created(self, db: ChatDB) -> None:
        """After initialize(), chat_sessions and chat_messages tables exist."""
        async with db._db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ) as cursor:
            tables = {row[0] for row in await cursor.fetchall()}
        assert "chat_sessions" in tables
        assert "chat_messages" in tables


class TestCreateSession:
    """3.2 test_create_session — creates session, returns correct SessionRecord."""

    async def test_create_session_returns_session_record(self, db: ChatDB) -> None:
        """create_session() returns a SessionRecord with the correct fields."""
        sid = _new_session_id()
        record = await db.create_session(sid, model="gpt-4", title="Test session")

        assert record.session_id == sid
        assert record.model == "gpt-4"
        assert record.title == "Test session"
        assert record.message_count == 0
        assert record.aborted is False
        assert record.created_at > 0
        assert record.updated_at > 0

    async def test_session_exists_after_create(self, db: ChatDB) -> None:
        """session_exists() returns True after create_session()."""
        sid = _new_session_id()
        await db.create_session(sid)
        assert await db.session_exists(sid) is True

    async def test_session_not_exists_for_unknown_id(self, db: ChatDB) -> None:
        """session_exists() returns False for an unknown session_id."""
        assert await db.session_exists(_new_session_id()) is False


class TestSaveMessageIncrementsCount:
    """3.2 test_save_message_increments_count."""

    async def test_message_count_increments_by_one(self, db: ChatDB) -> None:
        """message_count increases by 1 after each save_message()."""
        sid = _new_session_id()
        await db.create_session(sid)

        for expected_count in range(1, 4):
            await db.save_message(sid, "user", f"message {expected_count}")
            sessions, _ = await db.list_sessions()
            session = next(s for s in sessions if s.session_id == sid)
            assert session.message_count == expected_count


class TestGetSessionHistoryChronological:
    """3.2 test_get_session_history_chronological."""

    async def test_messages_returned_in_timestamp_asc_order(self, db: ChatDB) -> None:
        """get_session_history() returns messages ordered by timestamp ASC."""
        sid = _new_session_id()
        await db.create_session(sid)

        timestamps = [1000, 3000, 2000]
        for i, ts in enumerate(timestamps):
            await db.save_message(sid, "user", f"msg {i}", timestamp=ts)

        history = await db.get_session_history(sid)
        assert len(history) == 3
        assert [m.timestamp for m in history] == sorted(timestamps)


class TestDeleteSessionCascades:
    """3.2 test_delete_session_cascades."""

    async def test_delete_removes_session_and_messages(self, db: ChatDB) -> None:
        """After delete_session(), session_exists() is False and history is []."""
        sid = _new_session_id()
        await db.create_session(sid)
        await db.save_message(sid, "user", "hello")
        await db.save_message(sid, "assistant", "hi there")

        deleted = await db.delete_session(sid)

        assert deleted is True
        assert await db.session_exists(sid) is False
        assert await db.get_session_history(sid) == []

    async def test_delete_nonexistent_returns_false(self, db: ChatDB) -> None:
        """delete_session() returns False when the session does not exist."""
        result = await db.delete_session(_new_session_id())
        assert result is False


class TestDatabaseInitError:
    """3.2 test_database_init_error — DatabaseInitError for invalid path."""

    async def test_invalid_path_raises_database_init_error(self) -> None:
        """DatabaseInitError is raised when the DB path is not writable."""
        bad_db = ChatDB("/nonexistent_dir/subdir/chat.db")
        with pytest.raises(DatabaseInitError):
            await bad_db.initialize()


# ---------------------------------------------------------------------------
# Task 3.3 — Property 5: Round-trip storage
# Validates: Requirements 3.3, 9.6
# ---------------------------------------------------------------------------

_ROLES = ["user", "assistant", "system"]

_message_list_st = st.lists(
    st.fixed_dictionaries(
        {
            "role": st.sampled_from(_ROLES),
            "content": st.text(min_size=1, max_size=500),
            "timestamp": st.integers(min_value=1, max_value=2_000_000_000),
        }
    ),
    min_size=1,
    max_size=10,
)


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(messages=_message_list_st)
def test_round_trip_storage(messages: list[dict]) -> None:
    """**Validates: Requirements 3.3, 9.6**

    Property 5: Round-trip хранения сообщений в Chat_DB.

    After saving messages to ChatDB and reading via get_session_history(),
    messages are returned in timestamp ASC order with the same field values.
    """
    import asyncio

    async def _run() -> None:
        chat_db = ChatDB(":memory:")
        await chat_db.initialize()
        try:
            sid = str(uuid.uuid4())
            await chat_db.create_session(sid)

            for msg in messages:
                await chat_db.save_message(
                    sid, msg["role"], msg["content"], timestamp=msg["timestamp"]
                )

            history = await chat_db.get_session_history(sid)

            # Sort input by timestamp to match expected order
            sorted_messages = sorted(messages, key=lambda m: m["timestamp"])

            assert len(history) == len(sorted_messages)
            for stored, original in zip(history, sorted_messages):
                assert stored.role == original["role"]
                assert stored.content == original["content"]
                assert stored.timestamp == original["timestamp"]
        finally:
            await chat_db.close()

    asyncio.get_event_loop().run_until_complete(_run())


# ---------------------------------------------------------------------------
# Task 3.4 — Property 6: Monotonic message_count
# Validates: Requirements 3.2
# ---------------------------------------------------------------------------

_save_count_st = st.integers(min_value=1, max_value=20)


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(n=_save_count_st)
def test_monotonic_message_count(n: int) -> None:
    """**Validates: Requirements 3.2**

    Property 6: Монотонный рост message_count.

    After each save_message() call, message_count increases by exactly 1.
    """
    import asyncio

    async def _run() -> None:
        chat_db = ChatDB(":memory:")
        await chat_db.initialize()
        try:
            sid = str(uuid.uuid4())
            await chat_db.create_session(sid)

            for i in range(1, n + 1):
                await chat_db.save_message(sid, "user", f"message {i}")
                sessions, _ = await chat_db.list_sessions()
                session = next(s for s in sessions if s.session_id == sid)
                assert session.message_count == i
        finally:
            await chat_db.close()

    asyncio.get_event_loop().run_until_complete(_run())


# ---------------------------------------------------------------------------
# Task 3.5 — Property 7: Cascade delete
# Validates: Requirements 3.5
# ---------------------------------------------------------------------------

_cascade_messages_st = st.lists(
    st.fixed_dictionaries(
        {
            "role": st.sampled_from(_ROLES),
            "content": st.text(min_size=1, max_size=200),
        }
    ),
    min_size=0,
    max_size=10,
)


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(messages=_cascade_messages_st)
def test_cascade_delete(messages: list[dict]) -> None:
    """**Validates: Requirements 3.5**

    Property 7: Каскадное удаление сессии.

    After delete_session(), neither the session nor its messages are returned
    by session_exists() or get_session_history().
    """
    import asyncio

    async def _run() -> None:
        chat_db = ChatDB(":memory:")
        await chat_db.initialize()
        try:
            sid = str(uuid.uuid4())
            await chat_db.create_session(sid)

            for msg in messages:
                await chat_db.save_message(sid, msg["role"], msg["content"])

            deleted = await chat_db.delete_session(sid)
            assert deleted is True
            assert await chat_db.session_exists(sid) is False
            assert await chat_db.get_session_history(sid) == []
        finally:
            await chat_db.close()

    asyncio.get_event_loop().run_until_complete(_run())
