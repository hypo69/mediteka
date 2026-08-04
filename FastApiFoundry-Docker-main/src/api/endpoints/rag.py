# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: API эндпоинты системы RAG
# =============================================================================
# Описание:
#   Управление системой RAG (Retrieval-Augmented Generation).
#   Включает настройку, поиск, управление индексами и профилями.
#
# Примеры:
#   GET /api/v1/rag/status  - Получение статуса системы
#   POST /api/v1/rag/search - Поиск по векторному индексу
#
# File: src/api/endpoints/rag.py
# Project: Ai Assistant (Docker)
# Package: FastApiFoundrychrome 
# Module: api.endpoints.rag
# Version: 0.6.1
# Changes in 0.6.1:
#   - Updated version to match project
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import faiss

import os
import shutil
from markitdown import MarkItDown
from ...rag.rag_system import rag_system
from ...rag.rag_pipeline import get_pipeline
from ...rag.rag_service import RAGQueryFilters, RAGQueryRequest as ServiceRAGQueryRequest, rag_service, sse
from ...rag.rag_profile_manager import parse_rag_readme
from src.core.config import config as app_config
from src.logger import logger
from ...utils.api_utils import api_response_handler
from ...utils.text_utils import sanitize_for_filesystem

from ...rag.document_ingestor import DocumentIngestor
router = APIRouter(prefix="/rag", tags=["RAG"])


class RAGConfig(BaseModel):
    enabled: bool = False
    index_dir: str = "./rag_index"
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 1000
    top_k: int = 5


class RAGSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    min_score: float = 0.0


class RAGQueryFilterRequest(BaseModel):
    sources: List[str] = Field(default_factory=list)
    document_ids: List[int] = Field(default_factory=list)
    min_score: float = 0.0


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: RAGQueryFilterRequest = Field(default_factory=RAGQueryFilterRequest)
    rerank: bool = True
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: str = ""
    stream: bool = False


class RAGBuildRequest(BaseModel):
    docs_dir: str
    output_dir: str = "./rag_index"
    model: str = "sentence-transformers/all-mpnet-base-v2"
    chunk_size: int = 1000
    overlap: int = 50
    force: bool = False


class ExtractURLRequest(BaseModel):
    url: str
    enable_javascript: bool = False
    process_images: bool = False
    web_page_timeout: int = 30


class RAGSearchResult(BaseModel):
    content: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


@router.get("/status")
@api_response_handler
async def get_rag_status() -> dict:
    """Получение статуса системы RAG.

    Returns:
        dict: Информация о состоянии: enabled, index_dir, model, chunk_size, total_chunks.

    Example:
        >>> status = await get_rag_status()
        >>> print(status['enabled'])
        True
    """
    total_chunks: int = 0
    index_dir: Path = Path(app_config.rag_index_dir)

    # Подсчет количества сегментов (chunks) в индексе
    # Counting of chunks in the index directory
    if index_dir.exists():
        total_chunks = len(list(index_dir.glob("*.json")))

    return {
        "success": True,
        "enabled": app_config.rag_enabled,
        "index_dir": str(index_dir),
        "model": app_config.rag_model,
        "chunk_size": app_config.rag_chunk_size,
        "total_chunks": total_chunks
    }


@router.put("/config")
@api_response_handler
async def update_rag_config(config: RAGConfig) -> dict:
    """Обновление конфигурации системы RAG.

    Args:
        config (RAGConfig): Модель данных с новыми настройками.

    Returns:
        dict: Статус выполнения операции.
    """
    config_path: Path = Path("config.json")
    full_config: dict = {}

    # Чтение и обновление секции rag_system
    # Reading and updating the rag_system section
    full_config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    full_config["rag_system"] = config.model_dump() 
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(full_config, f, indent=2, ensure_ascii=False)
    return {"success": True, "message": "RAG configuration updated"}


@router.post("/search")
@api_response_handler
async def search_rag(request: RAGSearchRequest) -> dict:
    """Выполнение поиска в системе RAG.

    Args:
        request (RAGSearchRequest): Запрос с текстом и параметром top_k.

    Returns:
        dict: Список результатов с контентом и оценками схожести.

    Example:
        >>> res = await search_rag(RAGSearchRequest(query="test", top_k=5, min_score=0.5))
        >>> len(res['results'])
        3
    """
    results: List[Dict[str, Any]] = []
    top_k: int = request.top_k or 5

    # Выполнение поиска через ядро системы
    # Execution of the search through the system core
    results = await rag_system.search(request.query, top_k=top_k)

    # Фильтрация результатов по порогу схожести
    # Filtration of results by the similarity threshold
    if request.min_score > 0:
        # ПОЧЕМУ ВЫБРАН ЭТОТ МЕТОД:
        #   Использование централизованной логики фильтрации из RAGSystem гарантирует 
        #   одинаковое поведение API и внутренних модулей генерации.
        results = rag_system.filter_by_score(results, request.min_score)

    return {"success": True, "results": results[: request.top_k], "total": len(results)}


def _to_service_query(request: RAGQueryRequest) -> ServiceRAGQueryRequest:
    """Convert API request model to service request dataclass."""
    return ServiceRAGQueryRequest(
        query=request.query,
        top_k=max(1, request.top_k),
        filters=RAGQueryFilters(
            sources=request.filters.sources,
            document_ids=request.filters.document_ids,
            min_score=request.filters.min_score,
        ),
        rerank=request.rerank,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        system_prompt=request.system_prompt,
        stream=request.stream,
    )


@router.post("/query")
async def query_rag(request: RAGQueryRequest):
    """Run retrieval + prompt + generation with optional SSE streaming."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query is required")

    service_request = _to_service_query(request)
    if request.stream:
        async def _events():
            async for event in rag_service.stream_query(service_request):
                yield sse(event)

        return StreamingResponse(_events(), media_type="text/event-stream")

    return await rag_service.query(service_request)


@router.post("/rebuild")
@api_response_handler
async def rebuild_rag_index() -> dict:
    """Пересборка векторного индекса.

    Returns:
        dict: Статус запуска процесса пересборки.
    """
    return {"success": True, "message": "RAG index rebuild started (mock)", "chunks_processed": 42}


# Инициализация пайплайна подготовки данных
ingestor = DocumentIngestor(settings=app_config.get_section("text_extractor"))

@router.post("/index")
async def index_document(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Query(None),
    base_name: str = "default",
) -> dict:
    """Индексация одного документа или архива через RAGPipeline.

    Поддерживаемые форматы архивов: zip, tar, tar.gz, tgz, 7z, rar.
    Содержимое архива рекурсивно извлекается и индексируется как единый документ.
    """
    try:
        pipeline = get_pipeline()
        if file:
            result = await pipeline.ingest_upload(file)
        elif url:
            result = await pipeline.ingest_url(url)
        else:
            raise HTTPException(status_code=400, detail="Необходимо предоставить файл или URL")

        if not result.get("length"):
            raise HTTPException(status_code=422, detail="Не удалось извлечь текст из источника")
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Indexing failed"))

        return result

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Ошибка индексации документа: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/stream")
async def index_stream(file: UploadFile = File(...)) -> StreamingResponse:
    """Индексация одного файла/архива с SSE-прогрессом по всему пайплайну.

    Шлёт события вида:
      {"stage": "extract", "message": "..."}
      {"stage": "embed",   "done": 12, "total": 50, "message": "..."}
      {"stage": "index",   "done": true, "message": "..."}
      {"stage": "done",    "success": true, "chunks": 50, "chars": 12345}
      {"stage": "error",   "message": "..."}

    Args:
        file (UploadFile): Файл для индексации.

    Returns:
        StreamingResponse: text/event-stream с JSON-событиями.
    """
    import json as _json

    async def _events():
        pipeline = get_pipeline()
        async for event in pipeline.ingest_upload_stream(file):
            yield f"data: {_json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(_events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/index/batch")
async def index_batch(files: List[UploadFile] = File(...)) -> dict:
    """Пакетная индексация нескольких файлов или архивов за один запрос.

    Args:
        files (List[UploadFile]): Список файлов. Поддерживаются все форматы
            включая zip, tar, tar.gz, tgz, 7z, rar.

    Returns:
        dict: success, indexed, total, results, errors.

    Example:
        POST /api/v1/rag/index/batch
        Content-Type: multipart/form-data
        files=@docs.zip&files=@manual.pdf
    """
    if not files:
        raise HTTPException(status_code=400, detail="Необходимо предоставить хотя бы один файл")

    pipeline = get_pipeline()
    results: List[dict] = []
    errors: List[dict] = []

    for upload in files:
        try:
            result = await pipeline.ingest_upload(upload)
            if result.get("success") and result.get("length"):
                results.append({
                    "file": upload.filename,
                    "length": result["length"],
                    "method": result.get("method"),
                })
            else:
                errors.append({"file": upload.filename, "error": result.get("error", "No text extracted")})
        except HTTPException as e:
            errors.append({"file": upload.filename, "error": e.detail})
        except Exception as e:
            logger.error(f"Ошибка индексации {upload.filename}: {e}", exc_info=True)
            errors.append({"file": upload.filename, "error": str(e)})

    return {
        "success": len(results) > 0,
        "indexed": len(results),
        "total": len(files),
        "results": results,
        "errors": errors,
    }

@router.post("/clear")
@api_response_handler
async def clear_rag_chunks() -> dict:
    """Очистка файлов индекса в настроенной директории.

    Returns:
        dict: Количество удаленных файлов.
    """
    index_dir: Path = Path(app_config.rag_index_dir)
    deleted_count: int = 0
    file: Path = None

    if index_dir.exists():
        # Удаление файлов .index и .json
        for file in index_dir.glob("*"):
            if file.is_file() and file.suffix in (".index", ".json"):
                file.unlink()
                deleted_count += 1

    return {"success": True, "message": f"Cleared {deleted_count} index files", "deleted_count": deleted_count}


@router.get("/dirs")
@api_response_handler
async def list_indexable_dirs() -> dict:
    """Получение списка директорий, доступных для индексации.

    Returns:
        dict: Список путей с количеством найденных текстовых файлов.
    """
    root: Path = Path(".")
    candidates: list = []
    p: Path = None
    count: int = 0

    skip = {"venv", ".git", "__pycache__", "node_modules", "rag_index", ".amazonq"}
    for p in sorted(root.iterdir()):
        if p.is_dir() and p.name not in skip and not p.name.startswith("."):
            count = sum(1 for _ in p.rglob("*") if _.is_file() and _.suffix.lower() in {".md", ".txt", ".html", ".rst"})
            if count > 0:
                candidates.append({"path": str(p), "name": p.name, "files": count})
    return {"success": True, "dirs": candidates}


# ── RAG Profiles ──────────────────────────────────────────────────────────────

def _rag_home() -> Path:
    """Получение домашней директории RAG (~/.aiassistant/rag)."""
    rag_home = Path(app_config.dir_rag).expanduser()
    rag_home.mkdir(parents=True, exist_ok=True)
    return rag_home


def _profile_index_dir(safe_name: str) -> Path:
    """Получение пути к директории профиля."""
    return _rag_home() / safe_name


@router.get("/cwd")
async def get_cwd() -> dict:
    """Получение текущей рабочей директории сервера."""
    return {"success": True, "cwd": str(Path.cwd())}


@router.get("/browse")
async def browse_filesystem(path: str = "") -> dict:
    """Просмотр файловой системы для выбора папок.

    Args:
        path (str): Абсолютный путь для обзора. По умолчанию домашняя папка.

    Returns:
        dict: Список вложенных папок и информация о текущем пути.

    Raises:
        HTTPException: Если путь не существует или не является директорией.
    """
    base = Path(path).expanduser() if path else Path.home()
    if not base.exists() or not base.is_dir():
        return {"success": False, "error": f"Directory not found: {base}"}

    skip = {"__pycache__", "node_modules", ".git", "venv", ".venv"}
    dirs = [{"name": p.name, "path": str(p)} for p in sorted(base.iterdir()) if p.is_dir() and p.name not in skip]

    return {
        "success": True,
        "current": str(base),
        "parent": str(base.parent) if base.parent != base else None,
        "dirs": dirs,
    }


@router.get("/profiles")
async def list_rag_profiles() -> dict:
    """Получение списка всех профилей RAG в директории ~/.aiassistant/rag/.

    Returns:
        dict: success, profiles.
    """
    profiles: list = []
    d: Path = None
    active_dir = Path(app_config.rag_index_dir).expanduser()

    for d in sorted(_rag_home().iterdir()):
        if not d.is_dir():
            continue
        readme = parse_rag_readme(d)
        meta_file = d / "meta.json"
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                meta["has_index"] = (d / "faiss.index").exists()
                meta["title"] = readme["title"]
                meta["description"] = readme["description"]
                meta["readme_path"] = str(d / "README.md")
                meta["active"] = d.resolve() == active_dir.resolve()
                profiles.append(meta)
            except Exception:
                pass
        else:
            profiles.append({
                "name": d.name,
                "safe_name": d.name,
                "title": readme["title"],
                "description": readme["description"],
                "index_dir": str(d),
                "readme_path": str(d / "README.md"),
                "has_index": (d / "faiss.index").exists(),
                "active": d.resolve() == active_dir.resolve(),
            })
    return {"success": True, "profiles": profiles, "root": str(_rag_home())}


@router.post("/profiles/load")
async def load_rag_profile(request: dict) -> dict:
    """Переключение активного профиля RAG.

    Args:
        request (dict): Тело запроса с полем 'name'.

    Returns:
        dict: Результат загрузки и путь к новому индексу.
    """
    config_path: Path = Path("config.json")
    name = (request.get("name") or "").strip()

    if not name:
        return {"success": False, "error": "name is required"}

    profile_dir = _profile_index_dir(sanitize_for_filesystem(name))
    if not profile_dir.exists():
        return {"success": False, "error": f"Profile '{name}' not found"}
    if not (profile_dir / "faiss.index").exists():
        return {"success": False, "error": f"Profile '{name}' has no index yet"}

    cfg = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    cfg.setdefault("rag_system", {})["index_dir"] = str(profile_dir)
    cfg.setdefault("rag_system", {})["enabled"] = True
    config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    app_config.reload_config()

    await rag_system.reload_index(index_dir=str(profile_dir))

    return {"success": True, "message": f"Loaded profile '{name}'", "index_dir": str(profile_dir)}


@router.post("/profiles/{name}/activate")
async def activate_rag_profile(name: str) -> dict:
    """Подключить RAG профиль и сделать его активным."""
    return await load_rag_profile({"name": name})


@router.post("/profiles/deactivate")
async def deactivate_rag_profiles() -> dict:
    """Отключить использование RAG без удаления индексов с диска."""
    config_path: Path = Path("config.json")
    cfg = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    cfg.setdefault("rag_system", {})["enabled"] = False
    config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    app_config.reload_config()
    rag_system.index = None
    rag_system.chunks = []
    rag_system.current_index_dir = None
    rag_system._search_cache = {}
    return {"success": True, "message": "RAG disabled"}


@router.delete("/profiles/{name}")
async def delete_rag_profile(name: str) -> dict:
    """Удаление профиля RAG с диска.

    Args:
        name (str): Имя профиля.

    Returns:
        dict: Статус удаления.
    """
    import shutil
    profile_dir: Path = None
    profile_dir = _profile_index_dir(sanitize_for_filesystem(name))
    if not profile_dir.exists():
        return {"success": False, "error": f"Profile '{name}' not found"}
    shutil.rmtree(profile_dir, ignore_errors=True)
    return {"success": True, "message": f"Profile '{name}' deleted"}


@router.post("/build")
async def build_rag_index(request: RAGBuildRequest) -> dict:
    """Создание векторного индекса из локальной директории.

    Args:
        request (RAGBuildRequest): Параметры сборки (путь, модель, размер чанка).

    Returns:
        dict: Статистика сборки: количество сегментов, признак пересборки.
    """
    docs_dir: Path = Path(request.docs_dir).expanduser()

    if not docs_dir.is_absolute():
        docs_dir = Path.cwd() / docs_dir
    docs_dir = docs_dir.resolve()
    if not docs_dir.exists():
        return {"success": False, "error": f"Directory not found: {docs_dir}"}

    safe_name = sanitize_for_filesystem(docs_dir.name)
    output_dir: Path = rag_system._profile_index_dir(safe_name) # type: ignore
    output_dir.mkdir(parents=True, exist_ok=True)

    index_path = output_dir / "faiss.index"
    index_exists = index_path.exists()

    try:
        from ...rag.indexer import RAGIndexer
    except ImportError as e:
        return {"success": False, "error": f"RAG indexer not available: {e}"}

    try:
        loop = asyncio.get_event_loop()

        def _run() -> tuple[int, bool]:
            indexer = RAGIndexer(model_name=request.model)
            
            # Load existing chunks for incremental check
            existing_chunks = None
            chunks_path = output_dir / "chunks.json"
            if chunks_path.exists() and not request.force:
                try:
                    existing_chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
                except Exception:
                    pass

            indexer.load_model()
            indexer.index_directory(
                docs_dir, 
                chunk_size=request.chunk_size, 
                overlap=request.overlap,
                existing_chunks=existing_chunks
            )
            
            if not indexer.chunks:
                raise ValueError("No indexable documents found")

            # Only rebuild if files changed, force is true, or index missing
            rebuilt = False
            if indexer.has_changes or request.force or not index_exists:
                # Attempt to load existing index to reuse vectors for unchanged chunks
                existing_index = None
                if index_exists and not request.force:
                    try:
                        existing_index = faiss.read_index(str(index_path))
                    except Exception:
                        pass
                
                indexer.create_embeddings(existing_index=existing_index)
                indexer.save_index(output_dir)
                rebuilt = True
            
            return len(indexer.chunks), rebuilt

        chunks_count, was_rebuilt = await loop.run_in_executor(None, _run)

        meta = {
            "name": docs_dir.name, 
            "safe_name": safe_name, 
            "source_dir": str(docs_dir), 
            "index_dir": str(output_dir), 
            "chunks": chunks_count, 
            "model": request.model, 
            "updated_at": datetime.now().isoformat()
        }
        (output_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        readme_path = output_dir / "README.md"
        if not readme_path.exists():
            readme_path.write_text(
                f"# {docs_dir.name}\n\n"
                f"RAG индекс для документов из `{docs_dir}`. "
                "Опишите здесь назначение базы знаний, чтобы оно отображалось в интерфейсе и API.\n",
                encoding="utf-8",
            )

        return {
            "success": True, 
            "chunks": chunks_count, 
            "rebuilt": was_rebuilt,
            "index_dir": str(output_dir), 
            "name": safe_name,
            "message": "Index rebuilt" if was_rebuilt else "Index is up to date"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Text Extraction endpoints ─────────────────────────────────────────────────

@router.post("/extract/file")
async def extract_text_from_file(file: UploadFile = File(...)) -> dict:
    """Извлечение текста из загруженного файла.

    Args:
        file (UploadFile): Файл для обработки.

    Returns:
        dict: Извлеченный текст и метаданные.
    """
    # Обоснование: Переход на DocumentIngestor для унификации обработки файлов.
    # DocumentIngestor теперь обрабатывает все форматы, включая MarkItDown и TextExtractor.
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    try:
        content, source_name, method, meta = await ingestor.process_upload(file)
        return {
            "success": True,
            "filename": source_name,
            "method": method,
            "total_chars": len(content),
            "text": content,
            "metadata": meta
        }
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Processing timeout (300s)")
    except HTTPException:
        raise # Re-raise HTTPExceptions (e.g., 413 from ingestor)
    except Exception as e:
        logger.error(f"Ошибка извлечения текста из файла: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка извлечения текста из файла: {e}")

@router.post("/extract/url")
async def extract_text_from_url(request: ExtractURLRequest) -> dict:
    """Извлечение контента с веб-страницы.

    Args:
        request (ExtractURLRequest): URL и параметры парсинга (JS, изображения).

    Returns:
        dict: Текстовое содержимое страницы.
    """
    url = request.url.strip()
    if not url.startswith(("http://", "https://")):
        return {"success": False, "error": "URL must start with http:// or https://"}

    # Обоснование: Переход на DocumentIngestor для унификации обработки URL.
    try:
        content, source_name, method, meta = await ingestor.process_url(url)
        return {
            "success": True,
            "url": source_name,
            "method": method,
            "total_chars": len(content),
            "text": content,
            "metadata": meta
        }
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Processing timeout (300s)")
    except HTTPException:
        raise # Re-raise HTTPExceptions
    except Exception as e:
        logger.error(f"Ошибка извлечения текста из URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка извлечения текста из URL: {e}")

@router.get("/extract/formats")
async def get_supported_formats() -> dict:
    """Получение списка поддерживаемых форматов для извлечения текста.

    Returns:
        dict: Список расширений.
    """
    # Обоснование: Мы перешли на DocumentIngestor как единую точку входа.
    # Список форматов отражает возможности MarkItDown и кастомного TextExtractor.
    formats = [
        "pdf", "docx", "doc", "odt", "rtf",
        "xlsx", "xls", "csv", "ods",
        "pptx", "ppt",
        "jpg", "png", "tiff", "bmp", "gif", "webp",
        "html", "htm", "md",
        "json", "xml", "yaml",
        "py", "js", "ts", "php", "go", "rs", "c", "cpp", "cs", "java", "sh", "ps1",
        "zip", "rar", "7z", "tar", "gz",
        "eml", "msg", "epub"
    ]
    return {"success": True, "formats": formats}


# ── Incremental Document Management ──────────────────────────────────────────

class DocumentAddRequest(BaseModel):
    title: str
    content: str
    source_path: str = ""


class DocumentUpdateRequest(BaseModel):
    title: str
    content: str


def _get_indexer():
    """Return the IncrementalIndexer singleton."""
    from ...rag.incremental_indexer import get_indexer
    return get_indexer(str(Path(app_config.rag_index_dir).expanduser()))


async def _reload_active_rag_index() -> None:
    """Reload the active FAISS index after an incremental write."""
    await rag_system.reload_index(str(Path(app_config.rag_index_dir).expanduser()))


@router.get("/documents")
@api_response_handler
async def list_documents() -> dict:
    """Список всех документов в хранилище.

    Returns:
        dict: success, documents — список с id, title, chunk_count, updated_at.
    """
    loop = asyncio.get_event_loop()
    docs = await loop.run_in_executor(None, lambda: _get_indexer().store.list_documents())
    return {"success": True, "documents": docs, "total": len(docs)}


@router.post("/documents")
@api_response_handler
async def add_document(request: DocumentAddRequest) -> dict:
    """Добавить документ и проиндексировать его инкрементально.

    Args:
        request (DocumentAddRequest): title, content, source_path.

    Returns:
        dict: success, doc_id, chunks_added.

    Example:
        POST /api/v1/rag/documents
        {"title": "Manual", "content": "..."}
    """
    if not request.title.strip() or not request.content.strip():
        return {"success": False, "error": "title and content are required"}

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: _get_indexer().add_document(request.title, request.content, request.source_path),
    )
    if result["success"]:
        rag_system._search_cache = {}
        await _reload_active_rag_index()
    return result


@router.get("/documents/{doc_id}")
@api_response_handler
async def get_document(doc_id: int) -> dict:
    """Получить документ по id.

    Args:
        doc_id (int): Document id.

    Returns:
        dict: success, document.
    """
    doc = _get_indexer().store.get_document(doc_id)
    if not doc:
        return {"success": False, "error": f"Document {doc_id} not found"}
    return {"success": True, "document": doc}


@router.put("/documents/{doc_id}")
@api_response_handler
async def update_document(doc_id: int, request: DocumentUpdateRequest) -> dict:
    """Обновить документ и переиндексировать если контент изменился.

    Args:
        doc_id (int): Document id.
        request (DocumentUpdateRequest): title, content.

    Returns:
        dict: success, chunks_added, changed.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: _get_indexer().update_document(doc_id, request.title, request.content),
    )
    if result.get("success") and result.get("changed"):
        rag_system._search_cache = {}
        await _reload_active_rag_index()
    return result


@router.delete("/documents/{doc_id}")
@api_response_handler
async def delete_document(doc_id: int) -> dict:
    """Удалить документ и деактивировать его чанки.

    Args:
        doc_id (int): Document id.

    Returns:
        dict: success.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: _get_indexer().delete_document(doc_id))
    if result.get("success"):
        rag_system._search_cache = {}
        await _reload_active_rag_index()
    return result


@router.post("/documents/{doc_id}/reindex")
@api_response_handler
async def reindex_document(doc_id: int) -> dict:
    """Принудительно переиндексировать один документ.

    Args:
        doc_id (int): Document id.

    Returns:
        dict: success, chunks_added.
    """
    indexer = _get_indexer()
    doc = indexer.store.get_document(doc_id)
    if not doc:
        return {"success": False, "error": f"Document {doc_id} not found"}

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: indexer.update_document(doc_id, doc["title"], doc["content"]),
    )
    rag_system._search_cache = {}
    if result.get("success"):
        await _reload_active_rag_index()
    return result


@router.post("/compact")
@api_response_handler
async def compact_index() -> dict:
    """Перестроить FAISS индекс из активных чанков (удалить мёртвые векторы).

    Returns:
        dict: success, vectors_before, vectors_after.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: _get_indexer().compact())
    rag_system._search_cache = {}
    if result.get("success"):
        await _reload_active_rag_index()
    return result


@router.post("/migrate/index-id-map")
@api_response_handler
async def migrate_to_index_id_map() -> dict:
    """Migrate legacy FAISS/chunks.json profile to SQLite-backed IndexIDMap."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: get_pipeline().migrate_to_index_id_map())
    if result.get("success"):
        await _reload_active_rag_index()
    return result


@router.get("/documents/stats")
@api_response_handler
async def get_document_stats() -> dict:
    """Статистика хранилища документов и FAISS индекса.

    Returns:
        dict: documents, active_chunks, inactive_chunks, faiss_vectors, compact_recommended.
    """
    loop = asyncio.get_event_loop()
    stats = await loop.run_in_executor(None, lambda: _get_indexer().get_stats())
    return {"success": True, **stats}
