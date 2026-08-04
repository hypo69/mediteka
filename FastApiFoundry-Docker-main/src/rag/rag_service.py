# -*- coding: utf-8 -*-
"""RAG query service: retrieve -> filter/rerank -> prompt -> generate."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional

from src.core.config import config
from src.logger import logger
from src.models.router import detect_backend, route_generate

from .rag_system import rag_system


@dataclass
class RAGQueryFilters:
    """Optional retrieval filters."""

    sources: List[str] = field(default_factory=list)
    document_ids: List[int] = field(default_factory=list)
    min_score: float = 0.0


@dataclass
class RAGQueryRequest:
    """Internal request object for the query service."""

    query: str
    top_k: int = 5
    filters: RAGQueryFilters = field(default_factory=RAGQueryFilters)
    rerank: bool = True
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: str = ""
    stream: bool = False


class RAGService:
    """High-level RAG read path."""

    def __init__(self) -> None:
        self.default_system_prompt = (
            "Ты отвечаешь на вопрос, используя только предоставленный контекст. "
            "Если ответа в контексте нет, скажи это явно. "
            "Сохраняй краткость, но добавляй ссылки на источники, когда они есть."
        )

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[RAGQueryFilters] = None,
        rerank: bool = True,
    ) -> List[Dict[str, Any]]:
        """Retrieve chunks, apply filters and optional lightweight reranking."""
        if not query.strip():
            return []
        filters = filters or RAGQueryFilters()
        fetch_k = max(top_k * 4, top_k)
        results = await rag_system.search(query, top_k=fetch_k)
        results = self._apply_filters(results, filters)
        if rerank:
            results = self._rerank(query, results)
        return results[:top_k]

    def build_prompt(self, query: str, chunks: List[Dict[str, Any]], system_prompt: str = "") -> str:
        """Build a grounded prompt with citations."""
        instruction = system_prompt.strip() or self.default_system_prompt
        context_blocks = []
        for i, chunk in enumerate(chunks, start=1):
            source = chunk.get("source") or chunk.get("path") or "unknown"
            text = chunk.get("text") or chunk.get("content") or ""
            context_blocks.append(f"[{i}] source={source}\n{text}")
        context = "\n\n".join(context_blocks)
        return (
            f"{instruction}\n\n"
            f"Контекст:\n{context or '(контекст не найден)'}\n\n"
            f"Вопрос: {query}\n\n"
            "Ответ:"
        )

    async def query(self, request: RAGQueryRequest) -> Dict[str, Any]:
        """Run a complete non-streaming RAG query."""
        chunks = await self.retrieve(
            request.query,
            top_k=request.top_k,
            filters=request.filters,
            rerank=request.rerank,
        )
        prompt = self.build_prompt(request.query, chunks, request.system_prompt)
        generation = await self._generate(prompt, request)
        return {
            "success": bool(generation.get("success")),
            "answer": generation.get("content", ""),
            "error": generation.get("error"),
            "model": generation.get("model"),
            "usage": generation.get("usage") or {},
            "citations": self._citations(chunks),
            "chunks": chunks,
            "prompt": prompt,
        }

    async def stream_query(self, request: RAGQueryRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream retrieval metadata followed by generated answer deltas."""
        chunks = await self.retrieve(
            request.query,
            top_k=request.top_k,
            filters=request.filters,
            rerank=request.rerank,
        )
        prompt = self.build_prompt(request.query, chunks, request.system_prompt)
        yield {"type": "retrieval", "chunks": chunks, "citations": self._citations(chunks)}

        async for event in self._generate_stream(prompt, request):
            yield event

    def _apply_filters(self, results: List[Dict[str, Any]], filters: RAGQueryFilters) -> List[Dict[str, Any]]:
        sources = {s for s in filters.sources if s}
        document_ids = {int(d) for d in filters.document_ids}
        filtered = []
        for item in results:
            if filters.min_score and float(item.get("score", 0.0)) < filters.min_score:
                continue
            if sources and not self._source_matches(item, sources):
                continue
            if document_ids and int(item.get("document_id", -1)) not in document_ids:
                continue
            filtered.append(item)
        return filtered

    def _rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Lightweight lexical rerank layered on top of vector score."""
        terms = self._terms(query)
        if not terms:
            return results

        scored = []
        for item in results:
            text = (item.get("text") or item.get("content") or "").lower()
            lexical = sum(1 for term in terms if term in text) / max(len(terms), 1)
            vector_score = float(item.get("score", 0.0))
            item = item.copy()
            item["rerank_score"] = (0.75 * vector_score) + (0.25 * lexical)
            scored.append(item)
        return sorted(scored, key=lambda x: x.get("rerank_score", x.get("score", 0.0)), reverse=True)

    async def _generate(self, prompt: str, request: RAGQueryRequest) -> Dict[str, Any]:
        if self._wants_opencode(request.model):
            return await self._generate_opencode(prompt)
        return await route_generate(
            prompt=prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

    async def _generate_stream(self, prompt: str, request: RAGQueryRequest) -> AsyncGenerator[Dict[str, Any], None]:
        if self._wants_opencode(request.model):
            result = await self._generate_opencode(prompt)
            if result.get("success"):
                yield {"type": "delta", "content": result.get("content", "")}
                yield {"type": "done", "model": "opencode"}
            else:
                yield {"type": "error", "error": result.get("error", "opencode error")}
            return

        backend, clean_model = detect_backend(request.model)
        if backend == "foundry":
            from src.models.foundry_client import foundry_client

            async for chunk in foundry_client.generate_stream(
                prompt,
                model=clean_model or None,
                temperature=request.temperature if request.temperature is not None else 0.7,
                max_tokens=request.max_tokens or 2048,
            ):
                yield self._stream_event(chunk, request.model or "foundry")
            return

        if backend == "lmstudio":
            from src.models.lmstudio_client import lmstudio_client

            async for chunk in lmstudio_client.stream_generate(
                prompt,
                model=clean_model,
                temperature=request.temperature if request.temperature is not None else 0.7,
                max_tokens=request.max_tokens or 512,
            ):
                yield self._stream_event(chunk, request.model or "lmstudio")
            return

        result = await self._generate(prompt, request)
        if result.get("success"):
            yield {"type": "delta", "content": result.get("content", "")}
            yield {"type": "done", "model": result.get("model")}
        else:
            yield {"type": "error", "error": result.get("error", "generation error")}

    async def _generate_opencode(self, prompt: str) -> Dict[str, Any]:
        """Call opencode CLI when explicitly requested."""
        opencode_cfg = config.get_section("opencode")
        if not opencode_cfg.get("enabled", False):
            return {"success": False, "error": "opencode is disabled in config"}

        command = str(opencode_cfg.get("command") or "opencode")
        try:
            proc = await asyncio.create_subprocess_exec(
                command,
                "run",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        except Exception as exc:
            logger.error("opencode generation failed: %s", exc)
            return {"success": False, "error": str(exc)}

        if proc.returncode != 0:
            return {"success": False, "error": stderr.decode("utf-8", errors="replace")}
        return {
            "success": True,
            "content": stdout.decode("utf-8", errors="replace"),
            "model": "opencode",
            "usage": {},
        }

    @staticmethod
    def _stream_event(chunk: Dict[str, Any], model: str) -> Dict[str, Any]:
        if not chunk.get("success"):
            return {"type": "error", "error": chunk.get("error", "generation error")}
        if chunk.get("finished"):
            return {"type": "done", "model": model, "usage": chunk.get("usage") or {}}
        return {"type": "delta", "content": chunk.get("content", "")}

    @staticmethod
    def _source_matches(item: Dict[str, Any], sources: Iterable[str]) -> bool:
        source = str(item.get("source") or item.get("path") or "")
        return any(s in source for s in sources)

    @staticmethod
    def _terms(text: str) -> List[str]:
        return [t for t in re.findall(r"[\w\-]+", text.lower()) if len(t) > 2]

    @staticmethod
    def _citations(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations = []
        for i, chunk in enumerate(chunks, start=1):
            citations.append(
                {
                    "id": i,
                    "source": chunk.get("source") or chunk.get("path") or "unknown",
                    "score": chunk.get("score"),
                    "rerank_score": chunk.get("rerank_score"),
                    "document_id": chunk.get("document_id"),
                    "chunk_id": chunk.get("id"),
                }
            )
        return citations

    @staticmethod
    def _wants_opencode(model: Optional[str]) -> bool:
        return bool(model and str(model).lower() in {"opencode", "opencode::default"})


rag_service = RAGService()


def sse(data: Dict[str, Any]) -> str:
    """Serialize a dict as a Server-Sent Event frame."""
    event_type = data.get("type", "message")
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
