# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: llama.cpp Server Management API
# =============================================================================
# Description:
#   Endpoints for launching and stopping llama.cpp server with GGUF models.
#   llama.cpp поднимает OpenAI-совместимый API (/v1/chat/completions),
#   поэтому FastAPI Foundry подключается к нему как к обычному провайдеру.
#
#   Нативные llama-server API (проксируются напрямую):
#     GET  /api/v1/llama/props              — параметры сервера
#     GET  /api/v1/llama/slots              — активные слоты инференса
#     GET  /api/v1/llama/metrics            — Prometheus-метрики
#     POST /api/v1/llama/completion         — нативная генерация (top_k, mirostat, ...)
#     POST /api/v1/llama/tokenize           — токенизация
#     POST /api/v1/llama/detokenize         — детокенизация
#     POST /api/v1/llama/v1/completions     — OpenAI text completion
#     POST /api/v1/llama/v1/embeddings      — эмбеддинги
#     POST /api/v1/llama/v1/chat/completions — OpenAI chat completion
#     GET  /api/v1/llama/v1/models          — загруженные модели
#
#   Управление сервером:
#     GET  /api/v1/llama/status
#     POST /api/v1/llama/start   {"model_path": "D:/models/gemma-2-2b-it-Q6_K.gguf"}
#     POST /api/v1/llama/stop
#     GET  /api/v1/llama/models  — сканирует диск на .gguf файлы
#
# File: src/api/endpoints/llama_cpp.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Added native llama-server API proxy: /props, /slots, /metrics
#   - Added /completion (native, supports top_k/mirostat/repeat_penalty)
#   - Added /tokenize, /detokenize
#   - Added /v1/completions, /v1/embeddings, /v1/chat/completions, /v1/models
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import subprocess
import logging
import os
import aiohttp
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from ...utils.api_utils import api_response_handler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llama", tags=["llama-cpp"])

# Текущий процесс llama.cpp сервера.
# Хранится на уровне модуля — один сервер на весь процесс FastAPI.
_server_process: subprocess.Popen | None = None
_last_error: str | None = None  # Last start/stop error, shown in /status

# Настройки по умолчанию — переопределяются через .env или тело запроса
DEFAULT_HOST    = "127.0.0.1"
DEFAULT_PORT    = 9780
DEFAULT_CTX     = 4096
DEFAULT_THREADS = os.cpu_count() or 4


def _get_server_url() -> str:
    """Собрать URL llama.cpp сервера из config.json.

    Returns:
        str: URL вида http://host:port
    """
    try:
        from ...core.config import config
        port = config.get_section("llama_cpp").get("port", DEFAULT_PORT)
        host = config.get_section("llama_cpp").get("host", DEFAULT_HOST)
    except Exception:
        port = DEFAULT_PORT
        host = DEFAULT_HOST
    return f"http://{host}:{port}"


def _get_server_url_for_model(model_id: str | None = None) -> str:
    """Build llama.cpp server URL for a configured model alias/path."""
    try:
        from ...models.llama_registry import resolve_llama_server
        server = resolve_llama_server(model_id)
        if server:
            return server.url
    except Exception:
        pass
    return _get_server_url()


@router.get("/status")
@api_response_handler
async def llama_status(model: str | None = None) -> dict:
    """Статус llama.cpp сервера."""
    global _server_process
    running_pid = None

    # Проверяем наш процесс
    if _server_process and _server_process.poll() is None:
        running_pid = _server_process.pid

    # Проверяем HTTP доступность
    url = _get_server_url_for_model(model)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=3)) as r:
                reachable = r.status == 200
    except Exception:
        reachable = False

    # Capture stderr from a crashed process (non-blocking)
    process_error: str | None = None
    if _server_process and _server_process.poll() is not None:
        try:
            import select
            if hasattr(select, 'select') and _server_process.stderr:
                # Non-blocking read: only if data is available
                ready, _, _ = select.select([_server_process.stderr], [], [], 0)
                if ready:
                    raw = _server_process.stderr.read(2000)
                    if raw:
                        text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
                        process_error = text.strip()[-500:]
            elif _server_process.stderr:
                # Windows fallback: try non-blocking via os.read
                try:
                    raw = os.read(_server_process.stderr.fileno(), 2000)
                    if raw:
                        process_error = raw.decode("utf-8", errors="replace").strip()[-500:]
                except (OSError, BlockingIOError):
                    pass
        except Exception:
            pass

    # Fetch active model name from /v1/models if server is reachable
    active_model: str | None = None
    if reachable:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{url}/v1/models", timeout=aiohttp.ClientTimeout(total=2)) as r:
                    if r.status == 200:
                        data = await r.json()
                        models = data.get("data", [])
                        if models:
                            raw_id = models[0].get("id", "")
                            active_model = Path(raw_id).name if raw_id else None
        except Exception:
            pass

    return {
        "success": True,
        "running": reachable,
        "loading": (running_pid is not None) and (not reachable),
        "pid": running_pid,
        "url": url,
        "openai_url": f"{url}/v1",
        "active_model": active_model,
        "last_error": process_error or _last_error,
    }


@router.post("/models/copy")
@api_response_handler
async def llama_copy_model(request: dict) -> dict:
    """Скопировать .gguf модель в ~/.models.

    Если модель уже там есть — пропускает копирование.

    Body: {"model_path": "D:/gemma-2-2b-it-Q6_K.gguf"}
    """
    import shutil
    import asyncio

    src = Path(request.get("model_path", ""))
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {src}")

    from ...core.config import config as _cfg
    dest_dir = Path(_cfg.llama_models_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name

    if dest.exists():
        return {"success": True, "path": str(dest), "status": "already_exists"}

    size_gb = round(src.stat().st_size / 1024**3, 2)
    logger.info(f"Копирование {src.name} ({size_gb} GB) → {dest}")

    def _copy():
        shutil.copy2(str(src), str(dest))
        return str(dest)

    try:
        result_path = await asyncio.get_event_loop().run_in_executor(None, _copy)
        logger.info(f"✅ Скопировано: {result_path}")
        return {"success": True, "path": result_path, "status": "copied", "size_gb": size_gb}
    except Exception as e:
        logger.error(f"Ошибка копирования: {e}")
        return {"success": False, "error": str(e)}


@router.post("/start")
@api_response_handler
async def llama_start(request: dict) -> dict:
    """Запустить llama.cpp сервер с указанной GGUF моделью.

    Body:
        model_path:   Путь к .gguf файлу или директории с моделями.
                      Если не указан — берётся из config.json (llama_cpp.model_path → directories.models).
                      Если указана директория — берётся первый .gguf файл в ней.
        port:         Порт (default: 9780)
        ctx_size:     Размер контекста (default: 4096)
        threads:      Количество потоков CPU (default: auto)
        n_gpu_layers: Слоёв на GPU, 0 = только CPU (default: 0)
        host:         Хост (default: 127.0.0.1)
    """
    global _server_process, _last_error

    from ...core.config import config as _config

    # Resolve model_path: request body → config.llama_model_path
    model_path = request.get("model_path", "").strip() or _config.llama_model_path

    src = Path(model_path)

    # If a directory is given — pick the first .gguf inside it
    if src.is_dir():
        gguf_files = sorted(src.glob("*.gguf"))
        if not gguf_files:
            raise HTTPException(status_code=404, detail=f"No .gguf files found in: {src}")
        src = gguf_files[0]
        logger.info(f"📂 Директория моделей: выбран {src.name}")

    if not src.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {src}")

    # Copy to models dir if not already there
    copy_to_models = request.get("copy_to_models", True)
    models_home = Path(_config.llama_models_dir)
    dest = models_home / src.name

    if copy_to_models and not dest.exists():
        import shutil
        models_home.mkdir(parents=True, exist_ok=True)
        logger.info(f"Копирование {src.name} → {dest}")
        shutil.copy2(str(src), str(dest))

    model_path = str(dest) if dest.exists() else str(src)

    # Остановить предыдущий если запущен
    if _server_process and _server_process.poll() is None:
        _server_process.terminate()
        _server_process.wait(timeout=5)
        logger.info("Предыдущий llama.cpp сервер остановлен")

    _llama_cfg = _config.get_section("llama_cpp")

    port         = int(request.get("port") or _llama_cfg.get("port", DEFAULT_PORT))
    host         = request.get("host") or _llama_cfg.get("host", DEFAULT_HOST)
    ctx_size     = int(request.get("ctx_size") or DEFAULT_CTX)
    threads      = int(request.get("threads") or DEFAULT_THREADS)
    n_gpu_layers = int(request.get("n_gpu_layers") or 0)

    # Ищем llama-server в PATH и стандартных местах
    server_bin = _find_llama_server()
    if not server_bin:
        _last_error = "llama-server binary not found. Install llama.cpp: https://github.com/ggerganov/llama.cpp/releases"
        return {"success": False, "error": _last_error}

    cmd = [
        server_bin,
        "--model",       model_path,
        "--host",        host,
        "--port",        str(port),
        "--ctx-size",    str(ctx_size),
        "--threads",     str(threads),
        "--n-gpu-layers", str(n_gpu_layers),
        "--log-disable",
    ]

    try:
        _last_error = None
        _server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            # Do NOT use text=True here — binary mode avoids pipe buffer deadlocks.
            # stderr is read non-blocking in /status only when the process has exited.
        )
        logger.info(f"llama.cpp запущен: {Path(model_path).name} (PID: {_server_process.pid})")
        return {
            "success": True,
            "pid": _server_process.pid,
            "model": Path(model_path).name,
            "url": f"http://{host}:{port}",
            "openai_url": f"http://{host}:{port}/v1",
            "status": "starting"
        }
    except Exception as e:
        _last_error = str(e)
        logger.error(f"Ошибка запуска llama.cpp: {e}")
        return {"success": False, "error": _last_error}


@router.post("/stop")
@api_response_handler
async def llama_stop() -> dict:
    """Остановить llama.cpp сервер."""
    global _server_process
    if not _server_process or _server_process.poll() is not None:
        return {"success": True, "message": "Сервер не запущен"}
    try:
        _server_process.terminate()
        _server_process.wait(timeout=10)
        logger.info("llama.cpp сервер остановлен")
        return {"success": True, "message": "Сервер остановлен"}
    except Exception as e:
        _server_process.kill()
        return {"success": True, "message": f"Сервер принудительно остановлен: {e}"}


# ── llama-server native API proxy endpoints ──────────────────────────────────

@router.get("/props")
@api_response_handler
async def llama_props(model: str | None = None) -> dict:
    """Параметры запущенного llama-server: модель, контекст, потоки, n_gpu_layers.

    Проксирует GET /props нативного llama-server API.

    Returns:
        dict: success, props (model_path, n_ctx, n_threads, n_gpu_layers, ...)
    """
    url = _get_server_url_for_model(model)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{url}/props", timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    return {"success": True, "props": await r.json()}
                return {"success": False, "error": f"HTTP {r.status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/slots")
@api_response_handler
async def llama_slots(model: str | None = None) -> dict:
    """Активные слоты инференса llama-server.

    Проксирует GET /slots нативного llama-server API.
    Показывает параллельные запросы в обработке.

    Returns:
        dict: success, slots (list)
    """
    url = _get_server_url_for_model(model)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{url}/slots", timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    return {"success": True, "slots": await r.json()}
                return {"success": False, "error": f"HTTP {r.status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/metrics")
async def llama_metrics(model: str | None = None) -> PlainTextResponse:
    """Prometheus-метрики llama-server: токены/сек, TTFT, очередь.

    Проксирует GET /metrics нативного llama-server API.
    Возвращает text/plain в формате Prometheus.

    Returns:
        Response: text/plain Prometheus metrics или JSON с ошибкой.
    """
    url = _get_server_url_for_model(model)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{url}/metrics", timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    text = await r.text()
                    return PlainTextResponse(content=text)
                return PlainTextResponse(content=f"# HTTP {r.status}\n", status_code=r.status)
    except Exception as e:
        return PlainTextResponse(content=f"# Error: {e}\n", status_code=503)


@router.post("/completion")
@api_response_handler
async def llama_completion(request: dict) -> dict:
    """Нативная генерация llama-server (быстрее, больше параметров).

    Проксирует POST /completion нативного llama-server API.
    Поддерживает top_k, repeat_penalty, mirostat и другие параметры
    недоступные в OpenAI-совместимом /v1/chat/completions.

    Args:
        request: JSON body — любые параметры llama-server /completion.
            prompt (str):          Входной текст (обязательно).
            temperature (float):   Температура (default: 0.7).
            top_k (int):           Top-K sampling (default: 40).
            top_p (float):         Top-P sampling (default: 0.95).
            repeat_penalty (float): Штраф за повторения (default: 1.1).
            n_predict (int):       Макс. токенов (default: 512).
            stop (list[str]):      Стоп-последовательности.
            stream (bool):         Стриминг (default: false).

    Returns:
        dict: success, content, tokens_predicted, tokens_evaluated, ...
    """
    url = _get_server_url_for_model(request.get("model"))
    if not request.get("prompt"):
        return {"success": False, "error": "prompt is required"}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{url}/completion",
                json=request,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    return {"success": True, **data}
                return {"success": False, "error": f"HTTP {r.status}: {await r.text()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/tokenize")
@api_response_handler
async def llama_tokenize(request: dict) -> dict:
    """Токенизация текста через llama-server.

    Проксирует POST /tokenize нативного llama-server API.

    Args:
        request: {"content": "текст для токенизации"}

    Returns:
        dict: success, tokens (list[int])
    """
    url = _get_server_url_for_model(request.get("model"))
    if not request.get("content"):
        return {"success": False, "error": "content is required"}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{url}/tokenize",
                json=request,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    return {"success": True, **data}
                return {"success": False, "error": f"HTTP {r.status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/detokenize")
@api_response_handler
async def llama_detokenize(request: dict) -> dict:
    """Детокенизация (токены → текст) через llama-server.

    Проксирует POST /detokenize нативного llama-server API.

    Args:
        request: {"tokens": [1, 2, 3, ...]}

    Returns:
        dict: success, content (str)
    """
    url = _get_server_url_for_model(request.get("model"))
    if not request.get("tokens"):
        return {"success": False, "error": "tokens is required"}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{url}/detokenize",
                json=request,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    return {"success": True, **data}
                return {"success": False, "error": f"HTTP {r.status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/v1/completions")
@api_response_handler
async def llama_v1_completions(request: dict) -> dict:
    """OpenAI-совместимый text completion через llama-server.

    Проксирует POST /v1/completions llama-server API.

    Args:
        request: OpenAI completions body (prompt, max_tokens, temperature, ...).

    Returns:
        dict: OpenAI-совместимый ответ.
    """
    url = _get_server_url_for_model(request.get("model"))
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{url}/v1/completions",
                json=request,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as r:
                data = await r.json()
                return {"success": r.status == 200, **data} if r.status == 200 else {"success": False, "error": str(data)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/v1/embeddings")
@api_response_handler
async def llama_v1_embeddings(request: dict) -> dict:
    """Получить эмбеддинги через llama-server.

    Проксирует POST /v1/embeddings llama-server API.
    Требует запуска llama-server с флагом --embedding.

    Args:
        request: {"input": "текст или список текстов", "model": "..."}

    Returns:
        dict: success, data (list of embedding vectors), usage.
    """
    url = _get_server_url_for_model(request.get("model"))
    if not request.get("input"):
        return {"success": False, "error": "input is required"}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{url}/v1/embeddings",
                json=request,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    return {"success": True, **data}
                return {"success": False, "error": f"HTTP {r.status}: {await r.text()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/v1/chat/completions")
@api_response_handler
async def llama_v1_chat_completions(request: dict) -> dict:
    """OpenAI-совместимый chat completion через llama-server.

    Проксирует POST /v1/chat/completions llama-server API.
    Используется router.py для генерации через llama:: префикс.

    Args:
        request: OpenAI chat completions body (messages, model, temperature, ...).

    Returns:
        dict: OpenAI-совместимый ответ.
    """
    url = _get_server_url_for_model(request.get("model"))
    if not request.get("messages"):
        return {"success": False, "error": "messages is required"}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{url}/v1/chat/completions",
                json=request,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    return {"success": True, **data}
                return {"success": False, "error": f"HTTP {r.status}: {await r.text()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/v1/models")
@api_response_handler
async def llama_v1_models(model: str | None = None) -> dict:
    """Список моделей загруженных в llama-server (OpenAI-совместимый).

    Проксирует GET /v1/models llama-server API.

    Returns:
        dict: success, data (list of model objects), model_name (str, первая модель).
    """
    url = _get_server_url_for_model(model)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{url}/v1/models", timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    data = await r.json()
                    models = data.get("data", [])
                    model_name = models[0]["id"] if models else None
                    return {"success": True, "data": models, "model_name": model_name}
                return {"success": False, "error": f"HTTP {r.status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Disk model scan ───────────────────────────────────────────────────────────

@router.get("/models")
@api_response_handler
async def llama_scan_models(extra_dir: str = "") -> dict:
    """Сканировать .gguf файлы в ~/.models, ~/.ai-assist/gguf_models, ~/.lmstudio/models и опциональном extra_dir.

    Основные директории: ~/.models, ~/.ai-assist/gguf_models, ~/.lmstudio/models
    Дополнительная: extra_dir из query-параметра (например D:\ если модель ещё не скопирована)
    """
    from ...core.config import config as _cfg
    models_home = Path(_cfg.llama_models_dir)
    default_models_dir = Path.home() / ".models"
    aiassistant_gguf_dir = Path.home() / ".aiassistant" / "gguf_models"
    lmstudio_dir = Path.home() / ".lmstudio" / "models"
    lmstudio_community_dir = lmstudio_dir / "lmstudio-community"
    search_dirs = [
        models_home,
        default_models_dir,
        aiassistant_gguf_dir,
        lmstudio_dir,
        lmstudio_community_dir,
    ]

    if extra_dir:
        search_dirs.insert(0, Path(extra_dir))

    normalized_dirs = []
    seen_dirs = set()
    for d in search_dirs:
        expanded = Path(d).expanduser()
        key = str(expanded).lower()
        if key in seen_dirs:
            continue
        seen_dirs.add(key)
        normalized_dirs.append(expanded)

    found = []
    seen = set()  # избежать дубликатов
    for d in normalized_dirs:
        if not d.exists():
            continue
        try:
            for gguf in d.rglob("*.gguf"):
                if str(gguf) in seen:
                    continue
                seen.add(str(gguf))
                found.append({
                    "name":    gguf.name,
                    "path":    str(gguf),
                    "size_gb": round(gguf.stat().st_size / 1024**3, 2),
                    "dir":     str(gguf.parent),
                })
        except PermissionError:
            continue

    found.sort(key=lambda x: x["name"])
    return {
        "success":     True,
        "models":      found,
        "count":       len(found),
        "search_dirs": [str(d) for d in normalized_dirs],
        "existing_search_dirs": [str(d) for d in normalized_dirs if d.exists()],
        "missing_search_dirs": [str(d) for d in normalized_dirs if not d.exists()],
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_llama_server() -> str | None:
    """Find llama-server executable.

    Search order:
        1. LLAMA_SERVER_PATH env var (explicit path)
        2. PATH (shutil.which)
        3. bin/<bin_version>/ from config.json
        4. Any subdirectory of bin/ (fallback scan)
        5. Standard Windows install locations

    Returns:
        str | None: Full path to binary or None.
    """
    import shutil

    # 1. Explicit path from .env
    explicit = os.getenv("LLAMA_SERVER_PATH", "")
    if explicit and Path(explicit).exists():
        return explicit

    # 2. PATH
    for name in ("llama-server", "llama-server.exe"):
        found = shutil.which(name)
        if found:
            return found

    # 3. bin/<bin_version>/ from config.json (primary — version-aware)
    bin_dir = Path(__file__).parents[3] / "bin"
    try:
        from ...core.config import config as _cfg
        bin_version = _cfg.get_section("llama_cpp").get("bin_version", "")
        if bin_version:
            versioned_dir = bin_dir / bin_version
            for name in ("llama-server.exe", "llama-server"):
                candidate = versioned_dir / name
                if candidate.exists():
                    logger.info(f"✅ llama-server found via config bin_version: {candidate}")
                    return str(candidate)
    except Exception:
        pass

    # 4. Fallback: scan all subdirs of bin/
    if bin_dir.exists():
        for d in sorted(bin_dir.iterdir(), reverse=True):  # newest first by name
            if not d.is_dir():
                continue
            for name in ("llama-server.exe", "llama-server"):
                candidate = d / name
                if candidate.exists():
                    logger.info(f"✅ llama-server found via bin/ scan: {candidate}")
                    return str(candidate)

    # 5. Standard Windows locations
    for c in [
        Path("C:/llama.cpp/llama-server.exe"),
        Path("C:/Program Files/llama.cpp/llama-server.exe"),
        Path(os.getenv("LOCALAPPDATA", "")) / "llama.cpp" / "llama-server.exe",
    ]:
        if c.exists():
            return str(c)

    return None
