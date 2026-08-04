# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Training Dataset Store — QA Pair Collection
# =============================================================================
# Description:
#   Stores and manages question-answer pairs used for fine-tuning.
#   Each pair has a question, a correct answer, and optionally a wrong answer.
#   Status tracks whether the pair is pending review, approved, or rejected.
#   Data is persisted as JSONL in the configured training_data directory.
#
# File: dataset_store.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial scaffold: QAPair model, DatasetStore CRUD, JSONL persistence
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class QAPairStatus(str, Enum):
    """Lifecycle status of a QA training pair."""
    PENDING  = "pending"   # Awaiting human review
    APPROVED = "approved"  # Confirmed correct, ready for training
    REJECTED = "rejected"  # Marked as bad data, excluded from training


class QAPair:
    """A single question-answer training example.

    Attributes:
        id: Unique identifier (UUID4).
        question: The input question or user utterance.
        answer_correct: The ideal / ground-truth answer.
        answer_wrong: An example of a bad answer (used for preference training).
        status: Review status — pending / approved / rejected.
        source: Optional tag describing where this pair came from
                (e.g. "helpdesk", "manual", "synthetic").
        created_at: ISO-8601 creation timestamp.
        metadata: Arbitrary extra fields (model used, score, etc.).

    Example:
        >>> pair = QAPair(
        ...     question="Как сбросить пароль?",
        ...     answer_correct="Перейдите в Настройки → Безопасность → Сбросить пароль.",
        ...     answer_wrong="Не знаю.",
        ...     source="helpdesk",
        ... )
        >>> pair.status
        <QAPairStatus.PENDING: 'pending'>
    """

    def __init__(
        self,
        question: str,
        answer_correct: str,
        answer_wrong: str = "",
        source: str = "manual",
        status: QAPairStatus = QAPairStatus.PENDING,
        id: Optional[str] = None,
        created_at: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        self.id: str = id or str(uuid.uuid4())
        self.question: str = question
        self.answer_correct: str = answer_correct
        self.answer_wrong: str = answer_wrong
        self.source: str = source
        self.status: QAPairStatus = QAPairStatus(status) if isinstance(status, str) else status
        self.created_at: str = created_at or datetime.utcnow().isoformat()
        self.metadata: dict = metadata or {}

    def to_dict(self) -> dict:
        """Serialize to a plain dict (for JSONL storage)."""
        return {
            "id":             self.id,
            "question":       self.question,
            "answer_correct": self.answer_correct,
            "answer_wrong":   self.answer_wrong,
            "source":         self.source,
            "status":         self.status.value,
            "created_at":     self.created_at,
            "metadata":       self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QAPair":
        """Deserialize from a plain dict."""
        return cls(**data)


class DatasetStore:
    """Persistent store for QA training pairs.

    Pairs are stored as JSONL (one JSON object per line) in
    ``<data_dir>/qa_pairs.jsonl``.  The file is read once on first access
    and written on every mutation.

    Args:
        data_dir: Directory where ``qa_pairs.jsonl`` is stored.
                  Defaults to ``./training_data``.

    Example:
        >>> store = DatasetStore()
        >>> pair = store.add("Что такое RAG?", "RAG — поиск + генерация.", "Не знаю.")
        >>> store.approve(pair.id)
        >>> approved = store.list(status=QAPairStatus.APPROVED)
        >>> len(approved)
        1
    """

    _FILENAME = "qa_pairs.jsonl"

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self._dir: Path = Path(data_dir) if data_dir else Path("training_data")
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path: Path = self._dir / self._FILENAME
        self._pairs: List[QAPair] = []
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load pairs from JSONL file (lazy, called once)."""
        if self._loaded:
            return
        self._pairs = []
        if not self._path.exists():
            self._loaded = True
            return
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                self._pairs.append(QAPair.from_dict(json.loads(line)))
            except Exception as e:
                logger.warning(f"⚠️ Skipping malformed QA line: {e}")
        self._loaded = True
        logger.info(f"✅ Loaded {len(self._pairs)} QA pairs from {self._path}")

    def _save(self) -> None:
        """Persist all pairs to JSONL file."""
        lines = [json.dumps(p.to_dict(), ensure_ascii=False) for p in self._pairs]
        self._path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(
        self,
        question: str,
        answer_correct: str,
        answer_wrong: str = "",
        source: str = "manual",
        metadata: Optional[dict] = None,
    ) -> QAPair:
        """Add a new QA pair with PENDING status.

        Args:
            question: User question or prompt.
            answer_correct: Ground-truth / ideal answer.
            answer_wrong: Example of a bad answer (optional but recommended).
            source: Origin tag — "helpdesk", "manual", "synthetic", etc.
            metadata: Arbitrary extra fields.

        Returns:
            QAPair: The newly created pair.
        """
        self._load()
        pair = QAPair(
            question=question,
            answer_correct=answer_correct,
            answer_wrong=answer_wrong,
            source=source,
            metadata=metadata or {},
        )
        self._pairs.append(pair)
        self._save()
        logger.info(f"✅ QA pair added: {pair.id} (source={source})")
        return pair

    def get(self, pair_id: str) -> Optional[QAPair]:
        """Get a pair by ID.

        Args:
            pair_id: UUID of the pair.

        Returns:
            QAPair or None if not found.
        """
        self._load()
        for p in self._pairs:
            if p.id == pair_id:
                return p
        return None

    def list(
        self,
        status: Optional[QAPairStatus] = None,
        source: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[QAPair]:
        """List pairs with optional filtering.

        Args:
            status: Filter by status (pending / approved / rejected).
            source: Filter by source tag.
            limit: Maximum number of results.
            offset: Skip first N results.

        Returns:
            List[QAPair]: Matching pairs.
        """
        self._load()
        result = self._pairs
        if status:
            result = [p for p in result if p.status == status]
        if source:
            result = [p for p in result if p.source == source]
        return result[offset : offset + limit]

    def _set_status(self, pair_id: str, status: QAPairStatus) -> bool:
        """Internal: change status of a pair by ID."""
        self._load()
        for p in self._pairs:
            if p.id == pair_id:
                p.status = status
                self._save()
                return True
        return False

    def approve(self, pair_id: str) -> bool:
        """Mark a pair as approved (ready for training).

        Args:
            pair_id: UUID of the pair.

        Returns:
            bool: True if found and updated.
        """
        return self._set_status(pair_id, QAPairStatus.APPROVED)

    def reject(self, pair_id: str) -> bool:
        """Mark a pair as rejected (excluded from training).

        Args:
            pair_id: UUID of the pair.

        Returns:
            bool: True if found and updated.
        """
        return self._set_status(pair_id, QAPairStatus.REJECTED)

    def delete(self, pair_id: str) -> bool:
        """Permanently delete a pair.

        Args:
            pair_id: UUID of the pair.

        Returns:
            bool: True if found and deleted.
        """
        self._load()
        before = len(self._pairs)
        self._pairs = [p for p in self._pairs if p.id != pair_id]
        if len(self._pairs) < before:
            self._save()
            return True
        return False

    def stats(self) -> dict:
        """Return counts by status.

        Returns:
            dict: {"total": N, "pending": N, "approved": N, "rejected": N}
        """
        self._load()
        return {
            "total":    len(self._pairs),
            "pending":  sum(1 for p in self._pairs if p.status == QAPairStatus.PENDING),
            "approved": sum(1 for p in self._pairs if p.status == QAPairStatus.APPROVED),
            "rejected": sum(1 for p in self._pairs if p.status == QAPairStatus.REJECTED),
        }

    def export_approved(self) -> List[dict]:
        """Export all approved pairs as plain dicts (for training pipeline).

        Returns:
            List[dict]: Approved QA pairs serialized as dicts.
        """
        return [p.to_dict() for p in self.list(status=QAPairStatus.APPROVED)]


# Module-level singleton
dataset_store = DatasetStore()
