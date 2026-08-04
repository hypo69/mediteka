# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: HuggingFace Local Model Client
# =============================================================================
# Description:
#   Client for working with local HuggingFace models.
#   Supports downloading via huggingface_hub, loading into memory,
#   and inference via transformers pipeline.
#
#   Architecture:
#     HuggingFace Transformers is a library, not a service.
#     There is no external HTTP server to connect to — the model runs
#     inside the FastAPI process itself via transformers.pipeline.
#
#     Workflow:
#       download_model()  →  snapshot_download() → ~/.cache/huggingface/hub/
#       load_model()      →  AutoModelForCausalLM.from_pretrained() → RAM/VRAM
#       generate()        →  pipeline(formatted_prompt) → response
#       list_downloaded() →  scan_cache_dir() → list of cached repos
#
#   Key design decisions:
#     - scan_cache_dir() is used for listing (official HF API, not filesystem parsing)
#     - snapshot_download(local_files_only=True) is used for path resolution
#     - apply_chat_template() is applied when the tokenizer supports it
#     - All blocking operations run in executor to avoid blocking the event loop
#
# Examples:
#   >>> from src.models.hf_client import hf_client
#   >>> await hf_client.download_model("Qwen/Qwen2.5-0.5B-Instruct")
#   >>> result = await hf_client.generate("Hello", model_id="Qwen/Qwen2.5-0.5B-Instruct")
#
# File: src/models/hf_client.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - list_downloaded(): replaced manual filesystem scan with scan_cache_dir()
#     (official HF API); filesystem scan kept as fallback
#   - load_model(): replaced manual snapshot directory search with
#     snapshot_download(local_files_only=True); old search kept as fallback
#   - generate(): apply tokenizer.apply_chat_template() for instruction-tuned
#     models when tokenizer.chat_template is set; raw prompt used as fallback
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _get_models_dir() -> Path:
    """Return HuggingFace models directory.

    Priority:
        1. ``directories.hf_models`` from config.json
        2. ``HF_MODELS_DIR`` environment variable (legacy)
        3. ``~/.cache/huggingface/hub`` default (standard HuggingFace cache)

    Returns:
        Path: Resolved absolute path to the models directory.
    """
    try:
        from ..core.config import config
        cfg_dir = config.dir_hf_models
        if cfg_dir and not cfg_dir.startswith("${"):
            return Path(cfg_dir).expanduser()
    except Exception:
        pass
    raw = os.environ.get("HF_MODELS_DIR", "")
    if raw and not raw.startswith("${"):
        return Path(raw).expanduser()
    return Path.home() / ".cache" / "huggingface" / "hub"


HF_MODELS_DIR = _get_models_dir()

# Standard HuggingFace cache — same as HF_MODELS_DIR default, kept for explicit reference
HF_CACHE_DIR = Path.home() / ".cache" / "huggingface" / "hub"

# Models loaded into memory: {model_id: {"pipeline": Pipeline, "tokenizer": Tokenizer}}
# Stored at module level — one instance for the entire FastAPI process.
_loaded_models: dict = {}


def _check_transformers() -> bool:
    """Check availability of the transformers library.

    Returns:
        bool: True if installed, False otherwise.
    """
    try:
        import transformers  # noqa
        return True
    except ImportError:
        return False


def _check_huggingface_hub() -> bool:
    """Check availability of the huggingface_hub library.

    Returns:
        bool: True if installed, False otherwise.
    """
    try:
        import huggingface_hub  # noqa
        return True
    except ImportError:
        return False


class HFClient:
    """Client for local HuggingFace models.

    Responsible for:
    - Downloading models via ``huggingface_hub.snapshot_download`` to ``HF_MODELS_DIR``
    - Listing cached models via ``huggingface_hub.scan_cache_dir`` (official API)
    - Loading into memory via ``transformers.pipeline``
    - Inference via loaded pipeline with chat template support
    - Unloading from memory with CUDA cache clearing

    Global singleton ``hf_client`` is created at module level and shared
    across the entire FastAPI process.

    Example:
        >>> from src.models.hf_client import hf_client
        >>> hf_client.download_model("Qwen/Qwen2.5-0.5B-Instruct")
        {"success": True, "model_id": "Qwen/Qwen2.5-0.5B-Instruct", "path": "..."}
        >>> hf_client.load_model("Qwen/Qwen2.5-0.5B-Instruct", device="auto")
        {"success": True, "model_id": "Qwen/Qwen2.5-0.5B-Instruct", "device": "cpu"}
        >>> import asyncio
        >>> asyncio.run(hf_client.generate("Hello", model_id="Qwen/Qwen2.5-0.5B-Instruct"))
        {"success": True, "content": "...", "model": "Qwen/Qwen2.5-0.5B-Instruct"}
    """

    def download_model(self, model_id: str, token: Optional[str] = None,
                       progress_callback: Optional[object] = None) -> dict:
        """Download model via huggingface_hub.snapshot_download.

        Token is taken from HF_TOKEN in .env.
        Model is saved in HF_MODELS_DIR/<author>--<name>.

        Args:
            model_id: e.g., 'mistralai/Mistral-7B-Instruct-v0.3'.
            token:    Optional overriding token.
            progress_callback: Optional callable receiving progress event dicts.

        Returns:
            dict: {"success": bool, "model_id": str, "path": str, "error": str}
        """
        if not _check_huggingface_hub():
            return {"success": False, "error": "huggingface_hub is not installed. Run: pip install huggingface_hub"}

        from huggingface_hub import snapshot_download

        hf_token = token or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
        save_dir = HF_MODELS_DIR / model_id.replace("/", "--")
        save_dir.mkdir(parents=True, exist_ok=True)

        logger.info("📥 Downloading %s → %s", model_id, save_dir)

        try:
            if progress_callback:
                from huggingface_hub import list_repo_files, hf_hub_download

                try:
                    files = list(list_repo_files(model_id, token=hf_token or None))
                    skip = {".msgpack", ".h5"}
                    skip_prefix = ("flax_model", "tf_model")
                    files = [
                        f for f in files
                        if not any(f.endswith(s) for s in skip)
                        and not any(f.startswith(p) for p in skip_prefix)
                    ]
                except Exception:
                    files = []

                total_files = len(files)
                for idx, filename in enumerate(files, 1):
                    progress_callback({
                        "type": "file_start",
                        "filename": filename,
                        "file_index": idx,
                        "total_files": total_files,
                    })
                    try:
                        hf_hub_download(
                            repo_id=model_id,
                            filename=filename,
                            local_dir=str(save_dir),
                            token=hf_token or None,
                        )
                    except Exception as fe:
                        logger.warning("Skip %s: %s", filename, fe)
                    progress_callback({
                        "type": "file_done",
                        "filename": filename,
                        "file_index": idx,
                        "total_files": total_files,
                    })
                path = str(save_dir)
            else:
                path = snapshot_download(
                    repo_id=model_id,
                    local_dir=str(save_dir),
                    token=hf_token or None,
                    ignore_patterns=["*.msgpack", "*.h5", "flax_model*", "tf_model*"],
                )
            logger.info("✅ %s downloaded: %s", model_id, path)
            return {"success": True, "model_id": model_id, "path": path}
        except Exception as e:
            err = str(e)
            logger.error("❌ Error downloading %s: %s", model_id, err)
            if "401" in err or "403" in err or "gated" in err.lower() or "access" in err.lower():
                err = f"Access denied. Accept the license at huggingface.co/{model_id} and set HF_TOKEN"
            return {"success": False, "error": err}

    def load_model(self, model_id: str, device: str = "auto") -> dict:
        """Load model into memory for inference.

        Uses ``snapshot_download(local_files_only=True)`` to resolve the correct
        local snapshot path via the official HuggingFace API. Falls back to manual
        snapshot directory search if the API call fails.

        Args:
            model_id: Model ID (e.g. 'Qwen/Qwen2.5-0.5B-Instruct') or local path.
            device:   'auto', 'cpu', or 'cuda'.

        Returns:
            dict: {"success": bool, "model_id": str, "device": str}
        """
        if not _check_transformers():
            return {"success": False, "error": "transformers is not installed. Run: pip install transformers accelerate"}

        if model_id in _loaded_models:
            return {"success": True, "model_id": model_id, "status": "already_loaded"}

        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

            # ── Resolve local path ────────────────────────────────────────────
            # Primary: snapshot_download(local_files_only=True) — official HF API.
            # Returns the correct snapshot path without any network request.
            local_path: Optional[str] = None
            local_files_only = False

            try:
                from huggingface_hub import snapshot_download as _sd
                local_path = _sd(
                    repo_id=model_id,
                    local_files_only=True,
                    cache_dir=str(HF_CACHE_DIR),
                )
                local_files_only = True
                logger.info("Resolved %s via snapshot_download(local_files_only=True): %s", model_id, local_path)
            except Exception as e:
                logger.debug("snapshot_download(local_files_only=True) failed for %s: %s — trying fallback", model_id, e)

            # Fallback: manual snapshot directory search (legacy behaviour)
            if not local_path:
                dir_name = f"models--{model_id.replace('/', '--')}"
                for base in (HF_MODELS_DIR, HF_CACHE_DIR):
                    candidate = base / dir_name / "snapshots"
                    if candidate.exists():
                        dirs = [s for s in candidate.iterdir() if s.is_dir()]
                        if dirs:
                            # Sort by name (hash dirs are content-addressed, newest last)
                            local_path = str(sorted(dirs)[-1])
                            local_files_only = True
                            logger.info("Resolved %s via filesystem fallback: %s", model_id, local_path)
                            break

            model_path = local_path or model_id
            hf_token = None if local_files_only else (os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN"))

            logger.info("Loading %s from %s", model_id, "local: " + model_path if local_files_only else "HuggingFace Hub")

            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            tokenizer = AutoTokenizer.from_pretrained(
                model_path, token=hf_token, local_files_only=local_files_only
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch_dtype,
                device_map=device,
                token=hf_token,
                local_files_only=local_files_only,
            )

            pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

            _loaded_models[model_id] = {"pipeline": pipe, "tokenizer": tokenizer}
            actual_device = str(next(model.parameters()).device)
            logger.info("✅ Model %s loaded on %s", model_id, actual_device)
            return {"success": True, "model_id": model_id, "device": actual_device}

        except Exception as e:
            logger.error("❌ Error loading %s: %s", model_id, e)
            return {"success": False, "error": str(e)}

    def unload_model(self, model_id: str) -> dict:
        """Unload model from memory and free RAM/VRAM.

        Args:
            model_id: ID of the loaded model.

        Returns:
            dict: {"success": bool, "model_id": str}
        """
        if model_id not in _loaded_models:
            return {"success": False, "error": f"Model {model_id} is not loaded"}
        try:
            import gc
            import torch
            del _loaded_models[model_id]
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("✅ Model %s unloaded", model_id)
            return {"success": True, "model_id": model_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate(self, prompt: str, model_id: str,
                       max_new_tokens: int = 512,
                       temperature: float = 0.7) -> dict:
        """Generate text via a loaded HuggingFace model.

        Applies ``tokenizer.apply_chat_template()`` when the tokenizer supports it
        (i.e. ``tokenizer.chat_template`` is set). This is required for correct
        behaviour with instruction-tuned models (Qwen, Llama, Gemma, Mistral, etc.).
        Falls back to the raw prompt for base models without a chat template.

        Args:
            prompt:         User input text.
            model_id:       ID of the model to use (must be loaded).
            max_new_tokens: Maximum number of new tokens to generate.
            temperature:    Sampling temperature (0 = greedy, >0 = sampling).

        Returns:
            dict: {"success": bool, "content": str, "model": str}

        Example:
            >>> result = await hf_client.generate(
            ...     "Explain quantum entanglement",
            ...     model_id="Qwen/Qwen2.5-0.5B-Instruct",
            ... )
            >>> result["content"]
            'Quantum entanglement is...'
        """
        if model_id not in _loaded_models:
            load_result = await asyncio.get_event_loop().run_in_executor(
                None, self.load_model, model_id
            )
            if not load_result["success"]:
                return {"success": False, "error": f"Model not loaded: {load_result['error']}"}

        try:
            pipe      = _loaded_models[model_id]["pipeline"]
            tokenizer = _loaded_models[model_id]["tokenizer"]

            # ── Apply chat template ───────────────────────────────────────────
            # Instruction-tuned models require the prompt to be wrapped in their
            # specific chat format (e.g. <|im_start|>user\n...<|im_end|>).
            # apply_chat_template() handles this correctly for all supported models.
            # Raw prompt is used as fallback for base models without a template.
            if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
                messages = [{"role": "user", "content": prompt}]
                formatted_prompt = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
                logger.debug("Chat template applied for %s", model_id)
            else:
                formatted_prompt = prompt
                logger.debug("No chat template for %s — using raw prompt", model_id)

            def _run() -> str:
                outputs = pipe(
                    formatted_prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0,
                    pad_token_id=pipe.tokenizer.eos_token_id,
                    return_full_text=False,
                )
                return outputs[0]["generated_text"]

            content = await asyncio.get_event_loop().run_in_executor(None, _run)
            return {"success": True, "content": content, "model": model_id}

        except Exception as e:
            logger.error("❌ Error generating with %s: %s", model_id, e)
            return {"success": False, "error": str(e)}

    def list_downloaded(self) -> list:
        """List models downloaded to the local HuggingFace cache.

        Uses ``huggingface_hub.scan_cache_dir()`` (official API) to enumerate
        cached repositories. Falls back to manual filesystem scan if the API
        call fails (e.g. older huggingface_hub version or corrupted cache).

        Scans both ``HF_MODELS_DIR`` and ``~/.cache/huggingface/hub`` when they
        differ, deduplicating results by model ID.

        Returns:
            list: [{"id": str, "path": str, "loaded": bool, "size_mb": float, "source": str}]

        Example:
            >>> hf_client.list_downloaded()
            [{"id": "Qwen/Qwen2.5-0.5B-Instruct", "path": "...", "loaded": False,
              "size_mb": 987.3, "source": "/home/user/.cache/huggingface/hub"}]
        """
        # ── Primary: scan_cache_dir() — official HuggingFace API ─────────────
        # Returns CacheInfo with .repos (list of CachedRepoInfo).
        # Each repo has: repo_id, size_on_disk, nb_snapshots, last_accessed,
        # last_modified, refs, revisions.
        try:
            from huggingface_hub import scan_cache_dir

            results: list = []
            seen: set = set()

            for cache_dir in {HF_MODELS_DIR, HF_CACHE_DIR}:
                if not cache_dir.exists():
                    continue
                try:
                    cache_info = scan_cache_dir(cache_dir=str(cache_dir))
                except Exception as e:
                    logger.debug("scan_cache_dir failed for %s: %s", cache_dir, e)
                    continue

                for repo in cache_info.repos:
                    if repo.repo_id in seen:
                        continue
                    seen.add(repo.repo_id)

                    # Resolve the path of the latest revision snapshot
                    path = str(cache_dir)
                    try:
                        revisions = sorted(repo.revisions, key=lambda r: r.last_modified, reverse=True)
                        if revisions and revisions[0].snapshot_path:
                            path = str(revisions[0].snapshot_path)
                    except Exception:
                        pass

                    results.append({
                        "id":      repo.repo_id,
                        "path":    path,
                        "loaded":  repo.repo_id in _loaded_models,
                        "size_mb": round(repo.size_on_disk / 1024 / 1024, 1),
                        "source":  str(cache_dir),
                    })

            if results:
                return sorted(results, key=lambda x: x["id"])

            # scan_cache_dir returned no results — fall through to filesystem scan
            logger.debug("scan_cache_dir returned no repos, falling back to filesystem scan")

        except ImportError:
            logger.debug("scan_cache_dir not available in this huggingface_hub version — using filesystem scan")
        except Exception as e:
            logger.warning("scan_cache_dir failed: %s — falling back to filesystem scan", e)

        # ── Fallback: manual filesystem scan (legacy behaviour) ───────────────
        # Used when scan_cache_dir() is unavailable or returns nothing.
        def _dir_size_mb(d: Path) -> float:
            try:
                return round(sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1024 / 1024, 1)
            except Exception:
                return 0.0

        def _scan_dir(base: Path, source: str) -> list:
            if not base.exists():
                return []
            items = []
            for d in base.iterdir():
                if not d.is_dir() or not d.name.startswith("models--"):
                    continue
                model_id = d.name[len("models--"):].replace("--", "/", 1)
                snapshots_dir = d / "snapshots"
                if snapshots_dir.exists():
                    snapshot_dirs = sorted(s for s in snapshots_dir.iterdir() if s.is_dir())
                    path = str(snapshot_dirs[-1]) if snapshot_dirs else str(d)
                else:
                    path = str(d)
                items.append({
                    "id":      model_id,
                    "path":    path,
                    "loaded":  model_id in _loaded_models,
                    "size_mb": _dir_size_mb(d),
                    "source":  source,
                })
            return items

        seen_fs: set = set()
        results_fs: list = []
        for model in _scan_dir(HF_MODELS_DIR, str(HF_MODELS_DIR)):
            if model["id"] not in seen_fs:
                seen_fs.add(model["id"])
                results_fs.append(model)
        if HF_CACHE_DIR != HF_MODELS_DIR:
            for model in _scan_dir(HF_CACHE_DIR, str(HF_CACHE_DIR)):
                if model["id"] not in seen_fs:
                    seen_fs.add(model["id"])
                    results_fs.append(model)

        return sorted(results_fs, key=lambda x: x["id"])

    def list_loaded(self) -> list:
        """List models currently loaded into memory.

        Returns:
            list: [{"id": str, "status": "loaded"}]
        """
        return [{"id": k, "status": "loaded"} for k in _loaded_models]


hf_client = HFClient()
