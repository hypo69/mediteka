# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Database Initializer
# =============================================================================
# Description:
#   Creates SQLite databases for chat history and RAG document store.
#   Called by install.ps1 during installation.
#   Also called automatically when a new RAG index directory is created.
#
# File: scripts/Install/Init-Databases.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sqlite3
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))


def init_chat_db(db_path: Path) -> None:
    """Create chat history database with sessions and messages tables.

    Args:
        db_path (Path): Absolute path to the SQLite file.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
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
    """)
    conn.commit()
    conn.close()
    print(f"  ✅ Chat DB: {db_path}")


def init_rag_db(db_path: Path) -> None:
    """Create RAG document store database with documents and chunks tables.

    Args:
        db_path (Path): Absolute path to the SQLite file.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
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
    """)
    conn.commit()
    conn.close()
    print(f"  ✅ RAG DB:  {db_path}")


def main() -> None:
    """Read paths from config and initialise both databases."""
    try:
        from config_manager import config
        chat_db = Path(config.chat_history_db_path)
        rag_db  = Path(config.rag_index_dir) / "documents.db"
    except Exception as e:
        # Fallback to defaults when config is unavailable
        print(f"  ⚠️  Config unavailable ({e}), using defaults")
        home = Path.home()
        chat_db = home / ".aiassistant" / "chat" / "history" / "chat_history.db"
        rag_db  = home / ".aiassistant" / "rag" / "default_index" / "documents.db"

    print("\nInitialising databases...")
    init_chat_db(chat_db)
    init_rag_db(rag_db)
    print("Done.\n")


if __name__ == "__main__":
    main()
