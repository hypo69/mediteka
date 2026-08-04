# -*- coding: utf-8 -*-
# =============================================================================
# Tests for src/db/schemas.py — Pydantic v2 schema validation
# =============================================================================

import uuid

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from src.db.schemas import (
    MessageRecord,
    SaveMessageRequest,
    SessionRecord,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

_ROLES = ["user", "assistant", "system"]

_valid_message_record_st = st.fixed_dictionaries(
    {
        "role": st.sampled_from(_ROLES),
        "content": st.text(min_size=1),
        "timestamp": st.integers(min_value=0),
    }
)

_valid_session_record_st = st.fixed_dictionaries(
    {
        "session_id": st.uuids(version=4).map(str),
        "model": st.text(min_size=0),
        "title": st.text(min_size=0),
        "created_at": st.integers(min_value=0),
        "updated_at": st.integers(min_value=0),
        "message_count": st.integers(min_value=0),
        "aborted": st.booleans(),
    }
)


def _is_valid_uuid4(s: str) -> bool:
    """Return True if *s* is a valid UUID v4 string."""
    try:
        parsed = uuid.UUID(s)
        return parsed.version == 4
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# Property 1: Round-trip serialisation of MessageRecord
# Validates: Requirements 2.1, 9.5
# ---------------------------------------------------------------------------


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(data=_valid_message_record_st)
def test_message_record_round_trip(data: dict) -> None:
    """**Validates: Requirements 2.1, 9.5**

    Property 1: Round-trip сериализации Pydantic-схем.

    For any valid MessageRecord, serialising via model_dump() and then
    deserialising via model_validate() must produce an equivalent object.
    """
    original = MessageRecord(**data)
    restored = MessageRecord.model_validate(original.model_dump())
    assert original == restored


# ---------------------------------------------------------------------------
# Property 2: Round-trip serialisation of SessionRecord
# Validates: Requirements 2.2
# ---------------------------------------------------------------------------


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(data=_valid_session_record_st)
def test_session_record_round_trip(data: dict) -> None:
    """**Validates: Requirements 2.2**

    Property 2: Round-trip сериализации SessionRecord.

    For any valid SessionRecord, serialising via model_dump() and then
    deserialising via model_validate() must produce an equivalent object.
    """
    original = SessionRecord(**data)
    restored = SessionRecord.model_validate(original.model_dump())
    assert original == restored


# ---------------------------------------------------------------------------
# Property 3: Whitespace-only content raises ValidationError
# Validates: Requirements 2.7
# ---------------------------------------------------------------------------


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(content=st.text(alphabet=" \t\n\r", min_size=0))
def test_whitespace_content_raises_validation_error(content: str) -> None:
    """**Validates: Requirements 2.7**

    Property 3: Валидация пустого content.

    For any string consisting solely of whitespace characters (including the
    empty string), creating a SaveMessageRequest with that content must raise
    a Pydantic ValidationError.
    """
    valid_session_id = str(uuid.uuid4())
    with pytest.raises(ValidationError):
        SaveMessageRequest(
            session_id=valid_session_id,
            role="user",
            content=content,
        )


# ---------------------------------------------------------------------------
# Property 4: Non-UUID session_id raises ValidationError
# Validates: Requirements 2.8
# ---------------------------------------------------------------------------


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(session_id=st.text(min_size=1).filter(lambda s: not _is_valid_uuid4(s)))
def test_non_uuid_session_id_raises_validation_error(session_id: str) -> None:
    """**Validates: Requirements 2.8**

    Property 4: Валидация session_id не-UUID.

    For any string that is not a valid UUID v4, creating a SaveMessageRequest
    with that session_id must raise a Pydantic ValidationError.
    """
    with pytest.raises(ValidationError):
        SaveMessageRequest(
            session_id=session_id,
            role="user",
            content="some valid content",
        )


# ---------------------------------------------------------------------------
# Task 2.7: Unit tests for edge cases
# Validates: Requirements 9.8
# ---------------------------------------------------------------------------


class TestSaveMessageRequestEdgeCases:
    """Unit tests for SaveMessageRequest boundary values."""

    def test_empty_content_raises_validation_error(self) -> None:
        """Empty string content must raise ValidationError."""
        with pytest.raises(ValidationError):
            SaveMessageRequest(
                session_id=str(uuid.uuid4()),
                role="user",
                content="",
            )

    def test_whitespace_only_content_raises_validation_error(self) -> None:
        """Content consisting only of spaces must raise ValidationError."""
        with pytest.raises(ValidationError):
            SaveMessageRequest(
                session_id=str(uuid.uuid4()),
                role="user",
                content="   ",
            )

    def test_tab_newline_content_raises_validation_error(self) -> None:
        """Content consisting only of tabs and newlines must raise ValidationError."""
        with pytest.raises(ValidationError):
            SaveMessageRequest(
                session_id=str(uuid.uuid4()),
                role="user",
                content="\t\n\r",
            )

    def test_invalid_role_raises_validation_error(self) -> None:
        """An unrecognised role value must raise ValidationError."""
        with pytest.raises(ValidationError):
            SaveMessageRequest(
                session_id=str(uuid.uuid4()),
                role="admin",  # type: ignore[arg-type]
                content="hello",
            )

    def test_invalid_session_id_format_raises_validation_error(self) -> None:
        """A non-UUID session_id must raise ValidationError."""
        with pytest.raises(ValidationError):
            SaveMessageRequest(
                session_id="not-a-uuid",
                role="user",
                content="hello",
            )

    def test_uuid_v1_session_id_raises_validation_error(self) -> None:
        """A UUID v1 (not v4) session_id must raise ValidationError."""
        uuid_v1 = str(uuid.uuid1())
        with pytest.raises(ValidationError):
            SaveMessageRequest(
                session_id=uuid_v1,
                role="user",
                content="hello",
            )

    def test_content_10000_chars_succeeds(self) -> None:
        """Content of exactly 10,000 characters must be accepted."""
        long_content = "a" * 10_000
        req = SaveMessageRequest(
            session_id=str(uuid.uuid4()),
            role="assistant",
            content=long_content,
        )
        assert len(req.content) == 10_000

    def test_valid_request_succeeds(self) -> None:
        """A fully valid SaveMessageRequest must be created without errors."""
        valid_id = str(uuid.uuid4())
        req = SaveMessageRequest(
            session_id=valid_id,
            role="system",
            content="System prompt.",
        )
        assert req.session_id == valid_id
        assert req.role == "system"
        assert req.content == "System prompt."
