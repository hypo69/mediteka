# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: RAG Document Store — SQLite metadata layer
# =============================================================================
# Description:
#   Persistent storage for RAG documents and their chunks.
#   Tracks file hashes for incremental indexing.
#   Schema:
#     documents(id, title, content, source_path, content_hash, created_at, updated_at)
#     chunks(id, document_id, vector_id, chunk_no, text, active)
#
# File: src/rag/document_store.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from src.logger import logger


class DocumentStore:
    """SQLite-backed store for RAG documents and chunk metadata.

    Provides CRUD for documents and tracks which FAISS vector IDs
    belong to which document so incremental updates are possible.

    Args:
        db_path (str | Path): Path to the SQLite database file.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            from src.core.config import config
            db_path = Path(config.rag_index_dir) / "documents.db"
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ── Internal helpers ──────────────────────────────────────────────────────

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager that yields an open SQLite connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Create tables if they do not exist yet."""
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    title        TEXT    NOT NULL,
                    content      TEXT    NOT NULL DEFAULT '',
                    source_path  TEXT    NOT NULL DEFAULT '',
                    content_hash TEXT    NOT NULL DEFAULT '',
                    created_at   TEXT    NOT NULL,
                    updated_at   TEXT    NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    vector_id   INTEGER NOT NULL DEFAULT -1,
                    chunk_no    INTEGER NOT NULL DEFAULT 0,
                    text        TEXT    NOT NULL,
                    active      INTEGER NOT NULL DEFAULT 1
                );
                CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id);
                CREATE INDEX IF NOT EXISTS idx_chunks_active ON chunks(active);
                CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(content_hash);
            """)

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    # ── Documents CRUD ────────────────────────────────────────────────────────

    def add_document(self, title: str, content: str, source_path: str = "") -> int:
        """Insert a new document and return its id.

        Args:
            title (str): Human-readable title.
            content (str): Full text content.
            source_path (str): Optional file path this content came from.

        Returns:
            int: New document id.
        """
        now = datetime.now().isoformat()
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO documents(title, content, source_path, content_hash, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (title, content, source_path, self._hash(content), now, now),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single document by id.

        Args:
            doc_id (int): Document primary key.

        Returns:
            dict | None: Document row as dict, or None if not found.
        """
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None

    def list_documents(self) -> List[Dict[str, Any]]:
        """Return all documents ordered by updated_at desc.

        Returns:
            List[dict]: List of document rows.
        """
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT d.id, d.title, d.source_path, d.content_hash, d.created_at, d.updated_at, "
                "COUNT(c.id) AS chunk_count "
                "FROM documents d LEFT JOIN chunks c ON c.document_id = d.id AND c.active = 1 "
                "GROUP BY d.id ORDER BY d.updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def update_document(self, doc_id: int, title: str, content: str) -> bool:
        """Update title and content of an existing document.

        Args:
            doc_id (int): Document id.
            title (str): New title.
            content (str): New content.

        Returns:
            bool: True if a row was updated.
        """
        now = datetime.now().isoformat()
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE documents SET title=?, content=?, content_hash=?, updated_at=? WHERE id=?",
                (title, content, self._hash(content), now, doc_id),
            )
        return cur.rowcount > 0

    def delete_document(self, doc_id: int) -> bool:
        """Delete a document and cascade-delete its chunks.

        Args:
            doc_id (int): Document id.

        Returns:
            bool: True if a row was deleted.
        """
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        return cur.rowcount > 0

    def content_changed(self, doc_id: int, new_content: str) -> bool:
        """Check whether content hash differs from stored value.

        Args:
            doc_id (int): Document id.
            new_content (str): Candidate new content.

        Returns:
            bool: True if content has changed.
        """
        doc = self.get_document(doc_id)
        if not doc:
            return True
        return doc["content_hash"] != self._hash(new_content)

    # ── Chunks ────────────────────────────────────────────────────────────────

    def save_chunks(self, doc_id: int, chunks: List[Dict[str, Any]]) -> None:
        """Deactivate old chunks and insert new ones for a document.

        Args:
            doc_id (int): Document id.
            chunks (List[dict]): Each dict must have 'text', 'vector_id', 'chunk_no'.
        """
        with self._conn() as conn:
            conn.execute("UPDATE chunks SET active = 0 WHERE document_id = ?", (doc_id,))
            conn.executemany(
                "INSERT INTO chunks(document_id, vector_id, chunk_no, text, active) VALUES (?,?,?,?,1)",
                [(doc_id, c["vector_id"], c["chunk_no"], c["text"]) for c in chunks],
            )

    def get_active_chunks(self, doc_id: int) -> List[Dict[str, Any]]:
        """Return active chunks for a document.

        Args:
            doc_id (int): Document id.

        Returns:
            List[dict]: Active chunk rows.
        """
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM chunks WHERE document_id = ? AND active = 1 ORDER BY chunk_no",
                (doc_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all_active_chunks(self) -> List[Dict[str, Any]]:
        """Return all active chunks across all documents.

        Returns:
            List[dict]: All active chunk rows with document title.
        """
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT c.*, d.title AS doc_title FROM chunks c "
                "JOIN documents d ON d.id = c.document_id WHERE c.active = 1 ORDER BY c.id"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_active_chunks_by_ids(self, chunk_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """Return active chunks keyed by chunk id.

        Args:
            chunk_ids (List[int]): SQLite chunk primary keys, usually returned by FAISS IndexIDMap.

        Returns:
            Dict[int, dict]: Active chunk rows enriched with document metadata.
        """
        if not chunk_ids:
            return {}

        placeholders = ",".join("?" for _ in chunk_ids)
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT c.*, d.title AS doc_title, d.source_path AS source_path "
                f"FROM chunks c JOIN documents d ON d.id = c.document_id "
                f"WHERE c.active = 1 AND c.id IN ({placeholders})",
                tuple(chunk_ids),
            ).fetchall()
        return {int(r["id"]): dict(r) for r in rows}

    def stats(self) -> Dict[str, int]:
        """Return basic statistics.

        Returns:
            dict: documents, active_chunks, inactive_chunks counts.
        """
        with self._conn() as conn:
            docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            active = conn.execute("SELECT COUNT(*) FROM chunks WHERE active=1").fetchone()[0]
            inactive = conn.execute("SELECT COUNT(*) FROM chunks WHERE active=0").fetchone()[0]
        return {"documents": docs, "active_chunks": active, "inactive_chunks": inactive}


# Module-level singleton — index_dir resolved at runtime
_store: Optional[DocumentStore] = None


def get_store(index_dir: str = "rag_index") -> DocumentStore:
    """Return (or create) the module-level DocumentStore singleton.

    Args:
        index_dir (str): Directory that contains the FAISS index.

    Returns:
        DocumentStore: Singleton instance.
    """
    global _store
    if _store is None:
        _store = DocumentStore(db_path=Path(index_dir) / "documents.db")
    return _store
