# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Data Access Layer — Chat History SQLite DB
# =============================================================================
# Description:
#   Async SQLite access layer for chat session and message persistence.
#   Provides ChatDB class and module-level singleton via get_chat_db().
#
# File: src/db/chat_db.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import logging
import time
from pathlib import Path
from typing import Optional

import aiosqlite

from src.db.schemas import MessageRecord, SessionRecord

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SQL schema
# ---------------------------------------------------------------------------

_SQL_INIT = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id    TEXT    PRIMARY KEY,
    model         TEXT    NOT NULL DEFAULT '',
    title         TEXT    NOT NULL DEFAULT '',
    created_at    INTEGER NOT NULL,
    updated_at    INTEGER NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0,
    aborted       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT    NOT NULL,
    role       TEXT    NOT NULL,
    content    TEXT    NOT NULL,
    timestamp  INTEGER NOT NULL,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON chat_messages(session_id);
"""


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class DatabaseInitError(Exception):
    """Raised when the SQLite database cannot be initialised.

    This exception is thrown by :meth:`ChatDB.initialize` when the database
    file is inaccessible, corrupted, or the schema cannot be created.
    """


# ---------------------------------------------------------------------------
# ChatDB
# ---------------------------------------------------------------------------


class ChatDB:
    """Async SQLite data-access layer for chat sessions and messages.

    All public methods are coroutines and must be awaited.  The underlying
    connection is created lazily on the first call to :meth:`initialize`.

    Attributes:
        _db_path: Absolute path to the SQLite database file.
        _db: Active :class:`aiosqlite.Connection`, or ``None`` before
            :meth:`initialize` is called.
    """

    def __init__(self, db_path: str) -> None:
        """Store the database path and prepare the connection slot.

        Args:
            db_path: Path to the SQLite file.  ``~`` is expanded to the
                current user's home directory.  Use ``":memory:"`` for an
                in-memory database (useful in tests).
        """
        if db_path == ":memory:":
            self._db_path: str = db_path
        else:
            self._db_path = str(Path(db_path).expanduser())
        self._db: Optional[aiosqlite.Connection] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Open the database connection and create tables / indexes.

        Creates the ``chat_sessions`` and ``chat_messages`` tables together
        with the ``idx_messages_session_id`` index if they do not already
        exist.  WAL journal mode and foreign-key enforcement are enabled.

        Raises:
            DatabaseInitError: If the database file cannot be opened or the
                schema cannot be applied (e.g. path is not writable, file is
                corrupted).
        """
        try:
            self._db = await aiosqlite.connect(self._db_path)
            self._db.row_factory = aiosqlite.Row
            await self._db.executescript(_SQL_INIT)
            await self._db.commit()
            logger.debug("ChatDB initialised at %s", self._db_path)
        except Exception as exc:
            logger.error("ChatDB initialisation failed: %s", exc)
            raise DatabaseInitError(
                f"Cannot initialise database at '{self._db_path}': {exc}"
            ) from exc

    async def close(self) -> None:
        """Close the underlying database connection.

        Safe to call even if :meth:`initialize` was never called or the
        connection is already closed.
        """
        if self._db is not None:
            try:
                await self._db.close()
            except Exception as exc:  # pragma: no cover
                logger.warning("Error closing ChatDB: %s", exc)
            finally:
                self._db = None

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    async def create_session(
        self,
        session_id: str,
        model: str = "",
        title: str = "",
    ) -> SessionRecord:
        """Insert a new chat session record.

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
        """
        now = int(time.time())
        await self._db.execute(
            """
            INSERT INTO chat_sessions
                (session_id, model, title, created_at, updated_at, message_count, aborted)
            VALUES (?, ?, ?, ?, ?, 0, 0)
            """,
            (session_id, model, title, now, now),
        )
        await self._db.commit()
        return SessionRecord(
            session_id=session_id,
            model=model,
            title=title,
            created_at=now,
            updated_at=now,
            message_count=0,
            aborted=False,
        )

    async def session_exists(self, session_id: str) -> bool:
        """Check whether a session exists in the database.

        Args:
            session_id: The UUID v4 string identifying the session.

        Returns:
            ``True`` if the session exists, ``False`` otherwise.
        """
        async with self._db.execute(
            "SELECT 1 FROM chat_sessions WHERE session_id = ?",
            (session_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return row is not None

    async def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SessionRecord], int]:
        """Return a paginated list of sessions ordered by last update.

        Args:
            limit: Maximum number of sessions to return.
            offset: Number of sessions to skip (for pagination).

        Returns:
            A tuple ``(sessions, total)`` where *sessions* is a list of
            :class:`~src.db.schemas.SessionRecord` objects sorted by
            ``updated_at`` descending, and *total* is the total count of
            sessions in the database.
        """
        async with self._db.execute(
            "SELECT COUNT(*) FROM chat_sessions"
        ) as cursor:
            row = await cursor.fetchone()
            total: int = row[0]

        async with self._db.execute(
            """
            SELECT session_id, model, title, created_at, updated_at,
                   message_count, aborted
            FROM chat_sessions
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ) as cursor:
            rows = await cursor.fetchall()

        sessions = [
            SessionRecord(
                session_id=r["session_id"],
                model=r["model"],
                title=r["title"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                message_count=r["message_count"],
                aborted=bool(r["aborted"]),
            )
            for r in rows
        ]
        return sessions, total

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages (cascade).

        Args:
            session_id: The UUID v4 string identifying the session to delete.

        Returns:
            ``True`` if the session was found and deleted, ``False`` if no
            session with the given ``session_id`` existed.
        """
        cursor = await self._db.execute(
            "DELETE FROM chat_sessions WHERE session_id = ?",
            (session_id,),
        )
        await self._db.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        timestamp: Optional[int] = None,
    ) -> MessageRecord:
        """Persist a single message and atomically update session metadata.

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
        """
        if timestamp is None:
            timestamp = int(time.time())

        await self._db.execute(
            """
            INSERT INTO chat_messages (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, timestamp),
        )
        await self._db.execute(
            """
            UPDATE chat_sessions
            SET message_count = message_count + 1,
                updated_at    = ?
            WHERE session_id = ?
            """,
            (int(time.time()), session_id),
        )
        await self._db.commit()
        return MessageRecord(role=role, content=content, timestamp=timestamp)

    async def get_session_history(
        self,
        session_id: str,
    ) -> list[MessageRecord]:
        """Retrieve all messages for a session in chronological order.

        Args:
            session_id: The UUID v4 string identifying the session.

        Returns:
            A list of :class:`~src.db.schemas.MessageRecord` objects sorted
            by ``timestamp`` ascending.  Returns an empty list if the session
            has no messages or does not exist.
        """
        async with self._db.execute(
            """
            SELECT role, content, timestamp
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
            """,
            (session_id,),
        ) as cursor:
            rows = await cursor.fetchall()

        return [
            MessageRecord(
                role=r["role"],
                content=r["content"],
                timestamp=r["timestamp"],
            )
            for r in rows
        ]

    async def get_messages_since(
        self,
        since_timestamp: int,
        session_ids: Optional[list[str]] = None,
    ) -> list[dict]:
        """Return messages created after a given Unix timestamp.

        Args:
            since_timestamp: Only messages with ``timestamp`` strictly
                greater than this value are returned.
            session_ids: Optional list of session IDs to restrict the query.
                When ``None``, messages from all sessions are considered.

        Returns:
            A list of dicts with keys ``session_id``, ``role``, ``content``,
            and ``timestamp``, ordered by ``timestamp`` ascending.
        """
        if session_ids is not None:
            placeholders = ",".join("?" * len(session_ids))
            query = f"""
                SELECT session_id, role, content, timestamp
                FROM chat_messages
                WHERE timestamp > ?
                  AND session_id IN ({placeholders})
                ORDER BY timestamp ASC
            """
            params: tuple = (since_timestamp, *session_ids)
        else:
            query = """
                SELECT session_id, role, content, timestamp
                FROM chat_messages
                WHERE timestamp > ?
                ORDER BY timestamp ASC
            """
            params = (since_timestamp,)

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        return [
            {
                "session_id": r["session_id"],
                "role": r["role"],
                "content": r["content"],
                "timestamp": r["timestamp"],
            }
            for r in rows
        ]


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_chat_db_instance: Optional[ChatDB] = None


async def get_chat_db() -> ChatDB:
    """Return (or lazily create) the module-level :class:`ChatDB` singleton.

    On the first call the instance is created using the path from
    :attr:`src.core.config.config.chat_history_db_path` and
    :meth:`ChatDB.initialize` is called automatically.

    Returns:
        The initialised :class:`ChatDB` singleton.

    Raises:
        DatabaseInitError: If the database cannot be initialised on the
            first call.
    """
    global _chat_db_instance
    if _chat_db_instance is None:
        from src.core.config import config

        _chat_db_instance = ChatDB(config.chat_history_db_path)
        await _chat_db_instance.initialize()
    return _chat_db_instance
