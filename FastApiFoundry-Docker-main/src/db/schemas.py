# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Pydantic v2 Schemas for Chat History DB
# =============================================================================
# Description:
#   Pydantic v2 models for chat history database API request/response validation.
#   Used by chat_db_endpoints.py and rag_ingest_endpoints.py.
#
# File: src/db/schemas.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import uuid
from typing import Literal

from pydantic import BaseModel, field_validator


class MessageRecord(BaseModel):
    """Represents a single chat message stored in the database.

    Attributes:
        role: The role of the message author. One of "user", "assistant", "system".
        content: The text content of the message.
        timestamp: Unix timestamp (integer) when the message was created.
    """

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: int


class SessionRecord(BaseModel):
    """Represents a chat session record stored in the database.

    Attributes:
        session_id: Unique identifier for the session (UUID v4 string).
        model: The AI model used in this session.
        title: Human-readable title for the session.
        created_at: Unix timestamp when the session was created.
        updated_at: Unix timestamp when the session was last updated.
        message_count: Total number of messages in the session.
        aborted: Whether the session was aborted before completion.
    """

    session_id: str
    model: str
    title: str
    created_at: int
    updated_at: int
    message_count: int
    aborted: bool


class StartSessionRequest(BaseModel):
    """Request body for starting a new chat session.

    Attributes:
        model: The AI model to use for this session. Defaults to "default".
        title: Human-readable title for the session. Defaults to empty string.
    """

    model: str = "default"
    title: str = ""


class SaveMessageRequest(BaseModel):
    """Request body for saving a message to an existing chat session.

    Attributes:
        session_id: UUID v4 string identifying the target session.
        role: The role of the message author. One of "user", "assistant", "system".
        content: The text content of the message. Must be non-empty and non-whitespace.

    Raises:
        ValidationError: If content is empty or whitespace-only.
        ValidationError: If session_id is not a valid UUID v4.
    """

    session_id: str
    role: Literal["user", "assistant", "system"]
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Validate that content is not empty or whitespace-only.

        Args:
            v: The content string to validate.

        Returns:
            The original content string if valid.

        Raises:
            ValueError: If content is empty or contains only whitespace characters.
        """
        if not v or not v.strip():
            raise ValueError("content must not be empty or whitespace-only")
        return v

    @field_validator("session_id")
    @classmethod
    def session_id_is_uuid4(cls, v: str) -> str:
        """Validate that session_id is a valid UUID v4.

        Args:
            v: The session_id string to validate.

        Returns:
            The original session_id string if valid.

        Raises:
            ValueError: If session_id is not a valid UUID v4 format.
        """
        try:
            parsed = uuid.UUID(v)
        except (ValueError, AttributeError) as exc:
            raise ValueError("session_id must be a valid UUID v4") from exc
        if parsed.version != 4:
            raise ValueError("session_id must be a valid UUID v4")
        return v


class SessionListResponse(BaseModel):
    """Response body for listing chat sessions.

    Attributes:
        success: Whether the request was successful.
        sessions: List of session records.
        total: Total number of sessions available (for pagination).
    """

    success: bool
    sessions: list[SessionRecord]
    total: int


class SessionHistoryResponse(BaseModel):
    """Response body for retrieving the message history of a session.

    Attributes:
        success: Whether the request was successful.
        session_id: The UUID v4 string of the requested session.
        messages: List of messages in chronological order.
    """

    success: bool
    session_id: str
    messages: list[MessageRecord]


class IngestRequest(BaseModel):
    """Request body for triggering RAG ingestion from chat history.

    Attributes:
        session_ids: Optional list of session IDs to ingest. If None, all sessions are ingested.
        since_timestamp: Optional Unix timestamp. Only messages created after this
            timestamp will be ingested. If None, all messages are ingested.
    """

    session_ids: list[str] | None = None
    since_timestamp: int | None = None


class IngestStatusResponse(BaseModel):
    """Response body for querying the status of a RAG ingestion task.

    Attributes:
        task_id: Unique identifier for the ingestion task.
        status: Current status of the task. One of "running", "completed", "failed".
        chunks_added: Number of chunks successfully added to the FAISS index.
        duration_seconds: Total duration of the ingestion task in seconds. None if still running.
        error: Error message if the task failed. None otherwise.
    """

    task_id: str
    status: Literal["running", "completed", "failed"]
    chunks_added: int = 0
    duration_seconds: float | None = None
    error: str | None = None
