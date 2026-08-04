# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Incremental RAG Indexer
# =============================================================================
# Description:
#   Manages incremental updates to the FAISS index.
#   Workflow:
#     add_document    → chunk → embed → add vectors to FAISS → save chunks to DB
#     update_document → deactivate old chunks → re-embed → add new vectors
#     delete_document → deactivate chunks in DB (FAISS vectors stay, filtered at search)
#     compact         → rebuild FAISS from active chunks only (run when inactive > 20%)
#
#   Uses IndexIDMap so each vector has a stable integer ID matching chunks.id.
#
# File: src/rag/incremental_indexer.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial implementation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import faiss
import numpy as np

from src.logger import logger
from src.core.config import config
from .document_store import DocumentStore, get_store


class IncrementalIndexer:
    """Manages incremental FAISS updates backed by DocumentStore.

    Args:
        index_dir (str | Path): Directory for faiss.index and documents.db.
    """

    def __init__(self, index_dir: str | Path | None = None) -> None:
        self.index_dir: Path = Path(index_dir or config.rag_index_dir).expanduser()
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path: Path = self.index_dir / "faiss.index"
        self.store: DocumentStore = get_store(str(self.index_dir))
        self._model: Any = None
        self._index: Optional[faiss.Index] = None
        self._lock = threading.RLock()

    # ── Model ─────────────────────────────────────────────────────────────────

    def _get_model(self) -> Any:
        """Lazy-load the sentence-transformer model.

        Returns:
            SentenceTransformer: Loaded embedding model.
        """
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(config.rag_model)
        return self._model

    # ── FAISS index ───────────────────────────────────────────────────────────

    def _load_or_create_index(self) -> faiss.Index:
        """Load existing IndexIDMap or create a new one.

        Returns:
            faiss.Index: IndexIDMap wrapping IndexFlatIP.
        """
        if self._index is not None:
            return self._index

        if self.index_path.exists():
            try:
                self._index = faiss.read_index(str(self.index_path))
                if "IDMap" not in type(self._index).__name__:
                    logger.warning("⚠️ Existing FAISS index is not IndexIDMap; rebuilding incremental index from SQLite chunks")
                    self._index = self._build_index_from_store()
                    self._save_index(self._index)
                logger.info(f"✅ Loaded FAISS index: {self._index.ntotal} vectors")
                return self._index
            except Exception as e:
                logger.warning(f"⚠️ Could not load index, creating new: {e}")

        dim = self._get_model().get_sentence_embedding_dimension()
        self._index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
        logger.info(f"✅ Created new FAISS IndexIDMap (dim={dim})")
        return self._index

    def _build_index_from_store(self) -> faiss.Index:
        """Build a fresh IndexIDMap from active SQLite chunks."""
        active = self.store.get_all_active_chunks()
        if not active:
            dim = self._get_model().get_sentence_embedding_dimension()
            return faiss.IndexIDMap(faiss.IndexFlatIP(dim))

        texts = [c["text"] for c in active]
        ids = np.array([c["id"] for c in active], dtype="int64")
        vecs = self._embed(texts)
        idx = faiss.IndexIDMap(faiss.IndexFlatIP(vecs.shape[1]))
        idx.add_with_ids(vecs, ids)
        return idx

    def _save_index(self, idx: faiss.Index) -> None:
        """Persist FAISS index to disk.

        Args:
            idx (faiss.Index): Index to save.
        """
        tmp_path = self.index_path.with_suffix(".index.tmp")
        faiss.write_index(idx, str(tmp_path))
        tmp_path.replace(self.index_path)
        logger.debug(f"💾 FAISS index saved: {idx.ntotal} vectors → {self.index_path}")

    def _maybe_compact(self) -> None:
        """Compact automatically when inactive chunks exceed the recommended threshold."""
        stats = self.store.stats()
        total = stats["active_chunks"] + stats["inactive_chunks"]
        if total > 0 and (stats["inactive_chunks"] / total) > 0.2:
            self.compact()

    # ── Chunking ──────────────────────────────────────────────────────────────

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks using config values.

        Args:
            text (str): Source text.

        Returns:
            List[str]: List of text chunks.
        """
        chunk_size: int = config.rag_chunk_size
        overlap: int = max(0, chunk_size // 8)

        if len(text) <= chunk_size:
            return [text]

        chunks: List[str] = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end].strip())
            start = end - overlap
        return [c for c in chunks if c]

    # ── Embedding ─────────────────────────────────────────────────────────────

    def _embed(self, texts: List[str], progress_cb=None) -> np.ndarray:
        """Compute L2-normalised embeddings for a list of texts.

        Args:
            texts (List[str]): Texts to embed.
            progress_cb (callable | None): Optional callback(done, total) called per batch.

        Returns:
            np.ndarray: Float32 array of shape (len(texts), dim).
        """
        model = self._get_model()
        if progress_cb:
            # Encode in small batches so we can report progress
            batch = 16
            parts = []
            for i in range(0, len(texts), batch):
                parts.append(model.encode(texts[i:i + batch], show_progress_bar=False).astype("float32"))
                progress_cb(min(i + batch, len(texts)), len(texts))
            vecs = np.vstack(parts) if parts else model.encode([], show_progress_bar=False).astype("float32")
        else:
            vecs = model.encode(texts, show_progress_bar=False).astype("float32")
        faiss.normalize_L2(vecs)
        return vecs

    # ── Public API ────────────────────────────────────────────────────────────

    def add_document(self, title: str, content: str, source_path: str = "") -> Dict[str, Any]:
        """Add a new document: chunk → embed → insert into FAISS + DB.

        Args:
            title (str): Document title.
            content (str): Full text.
            source_path (str): Optional origin path.

        Returns:
            dict: success, doc_id, chunks_added.
        """
        with self._lock:
            if not content.strip():
                return {"success": False, "error": "Content is empty"}

            doc_id = self.store.add_document(title, content, source_path)
            chunks_added = self._index_document(doc_id, content)
            self._maybe_compact()
            return {"success": True, "doc_id": doc_id, "chunks_added": chunks_added}

    def update_document(self, doc_id: int, title: str, content: str) -> Dict[str, Any]:
        """Update document: deactivate old chunks, re-embed new content.

        Args:
            doc_id (int): Existing document id.
            title (str): New title.
            content (str): New content.

        Returns:
            dict: success, chunks_added, changed.
        """
        with self._lock:
            if not self.store.get_document(doc_id):
                return {"success": False, "error": f"Document {doc_id} not found"}

            changed = self.store.content_changed(doc_id, content)
            self.store.update_document(doc_id, title, content)

            if not changed:
                return {"success": True, "chunks_added": 0, "changed": False}

            chunks_added = self._index_document(doc_id, content)
            self._maybe_compact()
            return {"success": True, "chunks_added": chunks_added, "changed": True}

    def delete_document(self, doc_id: int) -> Dict[str, Any]:
        """Mark document chunks as inactive and remove document record.

        Args:
            doc_id (int): Document id.

        Returns:
            dict: success.
        """
        with self._lock:
            if not self.store.get_document(doc_id):
                return {"success": False, "error": f"Document {doc_id} not found"}

            # Deactivate chunks before deleting; stale FAISS vectors are filtered by SQLite lookup.
            self.store.save_chunks(doc_id, [])
            self.store.delete_document(doc_id)
            self._maybe_compact()
            return {"success": True}

    def compact(self) -> Dict[str, Any]:
        """Rebuild FAISS index from active chunks only.

        Should be called when inactive_chunks / total_chunks > 0.2.

        Returns:
            dict: success, vectors_before, vectors_after.
        """
        with self._lock:
            active = self.store.get_all_active_chunks()
            if not active:
                old_total = self._index.ntotal if self._index else 0
                dim = self._get_model().get_sentence_embedding_dimension()
                new_idx = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
                self._save_index(new_idx)
                self._index = new_idx
                return {"success": True, "vectors_before": old_total, "vectors_after": 0}

            texts = [c["text"] for c in active]
            ids = np.array([c["id"] for c in active], dtype="int64")
            vecs = self._embed(texts)

            dim = vecs.shape[1]
            new_idx = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
            new_idx.add_with_ids(vecs, ids)

            old_total = self._index.ntotal if self._index else 0
            self._save_index(new_idx)
            self._index = new_idx

            logger.info(f"✅ Compact: {old_total} → {new_idx.ntotal} vectors")
            return {"success": True, "vectors_before": old_total, "vectors_after": new_idx.ntotal}

    def get_stats(self) -> Dict[str, Any]:
        """Return index and store statistics.

        Returns:
            dict: documents, active_chunks, inactive_chunks, faiss_vectors, compact_recommended.
        """
        with self._lock:
            db_stats = self.store.stats()
            total = db_stats["active_chunks"] + db_stats["inactive_chunks"]
            compact_recommended = total > 0 and (db_stats["inactive_chunks"] / total) > 0.2
            idx = self._load_or_create_index()
        return {
            **db_stats,
            "faiss_vectors": idx.ntotal,
            "compact_recommended": compact_recommended,
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _index_document(self, doc_id: int, content: str, progress_cb=None) -> int:
        """Chunk, embed and add vectors for one document.

        Args:
            doc_id (int): Document id in the store.
            content (str): Text to index.
            progress_cb (callable | None): Optional callback(done, total) for embed progress.

        Returns:
            int: Number of chunks added.
        """
        idx = self._load_or_create_index()
        texts = self._chunk_text(content)
        if not texts:
            return 0

        vecs = self._embed(texts, progress_cb=progress_cb)

        # Assign sequential IDs starting after current max
        # Use negative doc_id-based range to avoid collisions with chunk DB ids
        # Actually we use chunk DB ids: insert first, get ids, then add to FAISS
        chunk_rows: List[Dict[str, Any]] = []
        for i, text in enumerate(texts):
            chunk_rows.append({"vector_id": -1, "chunk_no": i, "text": text})

        # Save with placeholder vector_id=-1 to get real DB ids
        self.store.save_chunks(doc_id, chunk_rows)
        db_chunks = self.store.get_active_chunks(doc_id)

        # Now we have real chunk ids — add to FAISS with those ids
        ids = np.array([c["id"] for c in db_chunks], dtype="int64")
        idx.add_with_ids(vecs, ids)
        self._save_index(idx)
        self._index = idx

        logger.info(f"✅ Indexed doc_id={doc_id}: {len(texts)} chunks, {idx.ntotal} total vectors")
        return len(texts)


# Module-level singleton
_indexer: Optional[IncrementalIndexer] = None


def get_indexer(index_dir: str | None = None) -> IncrementalIndexer:
    """Return (or create) the module-level IncrementalIndexer singleton.

    Args:
        index_dir (str | None): Override index directory.

    Returns:
        IncrementalIndexer: Singleton instance.
    """
    global _indexer
    if _indexer is None:
        _indexer = IncrementalIndexer(index_dir)
    return _indexer
