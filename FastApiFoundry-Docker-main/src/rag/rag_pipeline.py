# -*- coding: utf-8 -*-
"""High-level RAG indexing pipeline.

This module keeps the write path in one place:
ingest/extract -> chunk/embed/store -> FAISS IndexIDMap.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional

import faiss

from fastapi import UploadFile

from src.core.config import config
from src.logger import logger
from src.utils.text_extractor import TextExtractor

from .document_ingestor import DocumentIngestor
from .document_store import DocumentStore
from .incremental_indexer import IncrementalIndexer, get_indexer
from .rag_system import rag_system


class RAGPipeline:
    """Coordinates ingestion and incremental indexing."""

    def __init__(self, index_dir: str | Path | None = None) -> None:
        self.index_dir = Path(index_dir or config.rag_index_dir).expanduser()
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.ingestor = DocumentIngestor(settings=config.get_section("text_extractor"))
        self.text_extractor = TextExtractor(settings=config.get_section("text_extractor"))

    def _indexer(self) -> IncrementalIndexer:
        return get_indexer(str(self.index_dir))

    async def add_text(self, title: str, content: str, source_path: str = "") -> Dict[str, Any]:
        """Index already extracted text."""
        if not content.strip():
            return {"success": False, "error": "Content is empty"}

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._indexer().add_document(title, content, source_path),
        )
        if result.get("success"):
            await rag_system.reload_index(str(self.index_dir))
        return result

    async def ingest_upload(self, file: UploadFile) -> Dict[str, Any]:
        """Extract and index a FastAPI upload."""
        content, source_name, method, metadata = await self.ingestor.process_upload(file)
        result = await self.add_text(source_name, content, source_name)
        return {
            **result,
            "source": source_name,
            "method": method,
            "length": len(content),
            "metadata": {"source": source_name, **metadata},
        }

    async def ingest_upload_stream(self, file: UploadFile) -> AsyncIterator[Dict[str, Any]]:
        """Extract and index a FastAPI upload, yielding SSE-style progress events.

        Stages emitted via 'stage' field:
          extract   — text extraction from file/archive
          chunk     — text split into chunks
          embed     — embedding progress (done/total chunks)
          index     — FAISS write + DB save
          done      — final summary
          error     — on failure

        Args:
            file (UploadFile): Uploaded file.

        Returns:
            AsyncIterator[dict]: Progress event dicts.
        """
        source_name = file.filename or "upload"
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        async def _put(event: dict) -> None:
            await queue.put(event)

        async def _run() -> None:
            try:
                # Stage 1: extract
                await _put({"stage": "extract", "message": f"Extracting text from {source_name}..."})
                content, src, method, metadata = await self.ingestor.process_upload(file)
                chars = len(content)
                await _put({"stage": "extract", "done": True, "chars": chars, "method": method,
                             "message": f"Extracted {chars:,} chars via {method}"})

                if not content.strip():
                    await _put({"stage": "error", "message": "No text extracted from file"})
                    return

                # Stage 2: chunk (happens inside indexer — report count after)
                await _put({"stage": "chunk", "message": "Splitting into chunks..."})

                # Stage 3+4: embed + index with progress callback
                embed_progress: Dict[str, int] = {"done": 0, "total": 0}

                def _progress_cb(done: int, total: int) -> None:
                    embed_progress["done"] = done
                    embed_progress["total"] = total
                    # Thread-safe: schedule coroutine on the event loop
                    asyncio.run_coroutine_threadsafe(
                        _put({"stage": "embed", "done": done, "total": total,
                              "message": f"Embedding chunks {done}/{total}"}),
                        loop,
                    )

                def _index_with_progress() -> Dict[str, Any]:
                    indexer = self._indexer()
                    if not content.strip():
                        return {"success": False, "error": "Content is empty"}
                    doc_id = indexer.store.add_document(src, content, src)
                    chunks_added = indexer._index_document(doc_id, content, progress_cb=_progress_cb)
                    indexer._maybe_compact()
                    return {"success": True, "doc_id": doc_id, "chunks_added": chunks_added}

                result = await loop.run_in_executor(None, _index_with_progress)

                if not result.get("success"):
                    await _put({"stage": "error", "message": result.get("error", "Indexing failed")})
                    return

                await rag_system.reload_index(str(self.index_dir))

                await _put({"stage": "index", "done": True,
                             "message": f"Saved to FAISS index ({result['chunks_added']} chunks)"})
                await _put({"stage": "done", "success": True,
                             "source": src, "method": method,
                             "chars": chars, "chunks": result["chunks_added"],
                             "message": f"Done: {result['chunks_added']} chunks indexed"})
            except Exception as e:
                logger.error(f"ingest_upload_stream error: {e}", exc_info=True)
                await _put({"stage": "error", "message": str(e)})
            finally:
                await queue.put(None)  # sentinel

        task = asyncio.create_task(_run())
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event
        await task

    async def ingest_url(self, url: str) -> Dict[str, Any]:
        """Extract and index a URL."""
        content = await self.text_extractor.extract_from_url(url)
        result = await self.add_text(url, content, url)
        return {
            **result,
            "source": url,
            "method": "URLExtractor",
            "length": len(content),
            "metadata": {"source": url, "type": "url"},
        }

    def migrate_to_index_id_map(self) -> Dict[str, Any]:
        """Migrate the active index directory to SQLite + FAISS IndexIDMap.

        If documents.db already exists, compaction rebuilds FAISS from active SQLite
        chunks. If only legacy chunks.json exists, this imports those chunks into
        SQLite first and then rebuilds FAISS with chunk IDs as vector IDs.
        """
        index_path = self.index_dir / "faiss.index"
        chunks_path = self.index_dir / "chunks.json"
        db_path = self.index_dir / "documents.db"

        before_type = None
        before_total = 0
        if index_path.exists():
            try:
                old_index = faiss.read_index(str(index_path))
                before_type = type(old_index).__name__
                before_total = int(old_index.ntotal)
            except Exception as exc:
                logger.warning("Could not inspect FAISS index before migration: %s", exc)

        store = DocumentStore(db_path)
        if not store.get_all_active_chunks() and chunks_path.exists():
            chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
            grouped: Dict[str, list[dict[str, Any]]] = {}
            for chunk in chunks:
                source = chunk.get("source") or chunk.get("path") or "legacy"
                grouped.setdefault(str(source), []).append(chunk)

            for source, source_chunks in grouped.items():
                content = "\n\n".join(c.get("text") or c.get("content") or "" for c in source_chunks).strip()
                if not content:
                    continue
                doc_id = store.add_document(source, content, source_chunks[0].get("path", source))
                store.save_chunks(
                    doc_id,
                    [
                        {
                            "vector_id": -1,
                            "chunk_no": i,
                            "text": c.get("text") or c.get("content") or "",
                        }
                        for i, c in enumerate(source_chunks)
                        if (c.get("text") or c.get("content") or "").strip()
                    ],
                )

        indexer = IncrementalIndexer(self.index_dir)
        result = indexer.compact()
        try:
            new_index = faiss.read_index(str(index_path))
            after_type = type(new_index).__name__
            after_total = int(new_index.ntotal)
        except Exception:
            after_type = None
            after_total = 0

        return {
            "success": bool(result.get("success")),
            "before_type": before_type,
            "before_vectors": before_total,
            "after_type": after_type,
            "after_vectors": after_total,
            "index_dir": str(self.index_dir),
        }


def get_pipeline(index_dir: Optional[str] = None) -> RAGPipeline:
    """Return a pipeline for the requested index directory."""
    return RAGPipeline(index_dir or config.rag_index_dir)
