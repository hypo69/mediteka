# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: GUI Installer API Endpoints
# =============================================================================
# Description:
#   REST endpoints consumed by the /install SPA wizard.
#   Provides status checks and action triggers for each installation step.
#
# File: src/api/endpoints/install.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial implementation
# Author: hypo69
# Copyright: Â© 2026 hypo69
# =============================================================================

import subprocess
import sys
import shutil
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(prefix="/install", tags=["install"])

# Two routers exported for separate mounting:
#   page_router  â†’ mounted without prefix  â†’ GET /install
#   api_router   â†’ mounted at /api/v1      â†’ /api/v1/install/*
page_router = APIRouter(tags=["install"])
api_router  = APIRouter(prefix="/install", tags=["install"])

_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _ROOT / ".env"
_INSTALL_SCRIPTS = _ROOT / "scripts" / "Install"


def _run_powershell_script(script: Path, *args: str) -> dict:
    """Start an installer PowerShell script in the background."""
    if not script.exists():
        return {"success": False, "error": f"{script.name} not found"}

    try:
        subprocess.Popen(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script), *args],
            cwd=str(_ROOT),
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _ensure_winget_sync() -> dict:
    """Ensure winget is available before a direct winget command."""
    if shutil.which("winget"):
        try:
            result = subprocess.run(
                ["winget", "--version"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return {"success": True}
        except Exception:
            pass

    script = _INSTALL_SCRIPTS / "Install-Winget.ps1"
    if not script.exists():
        return {"success": False, "error": "Install-Winget.ps1 not found"}

    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script), "-SkipIfExists"],
            cwd=str(_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip() or result.stdout.strip() or "winget install failed"}
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@page_router.get("/install", include_in_schema=False)
async def install_page() -> FileResponse:
    """Serve the GUI installer SPA at /install."""
    return FileResponse(_ROOT / "static" / "gui-install" / "index.html")


# ---------------------------------------------------------------------------
# Step: welcome â€” environment status
# ---------------------------------------------------------------------------

@api_router.get("/status")
async def install_status() -> dict:
    """Return basic environment status for the welcome step.

    Returns:
        dict â€” python version, pip availability, venv presence, requirements flag.
    """
    venv_path = _ROOT / "venv"
    req_file  = _ROOT / "requirements.txt"

    python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    pip_ok = shutil.which("pip") is not None or (venv_path / "Scripts" / "pip.exe").exists()

    # Ð¡Ñ‡Ð¸Ñ‚Ð°ÐµÐ¼ requirements ÑƒÑÑ‚Ð°Ð½Ð¾Ð²Ð»ÐµÐ½Ð½Ñ‹Ð¼Ð¸ ÐµÑÐ»Ð¸ fastapi Ð´Ð¾ÑÑ‚ÑƒÐ¿ÐµÐ½
    try:
        import fastapi  # noqa: F401
        req_ok = True
    except ImportError:
        req_ok = False

    return {
        "success":      True,
        "python":       python_ver,
        "pip":          "ok" if pip_ok else None,
        "venv":         venv_path.exists(),
        "requirements": req_ok,
    }


# ---------------------------------------------------------------------------
# Step: env
# ---------------------------------------------------------------------------

@api_router.get("/env")
async def get_env() -> dict:
    """Read current .env values for the env step.

    Returns:
        dict â€” exists flag and current key values (tokens masked).
    """
    values: dict = {"exists": _ENV_FILE.exists(), "foundry_url": "", "hf_token": "", "hf_models_dir": ""}

    if not _ENV_FILE.exists():
        return {"success": True, **values}

    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key == "FOUNDRY_BASE_URL":
            values["foundry_url"] = val.strip()
        elif key == "HF_TOKEN":
            values["hf_token"] = val.strip()
        elif key == "HF_MODELS_DIR":
            values["hf_models_dir"] = val.strip()

    return {"success": True, **values}


@api_router.post("/env")
async def save_env(body: dict) -> dict:
    """Write .env with provided values.

    Args:
        body (dict): foundry_url, hf_token, hf_models_dir.

    Returns:
        dict â€” success flag.
    """
    lines: list[str] = []

    if _ENV_FILE.exists():
        # Preserve existing lines, update known keys
        existing: dict[str, str] = {}
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                lines.append(line)
                continue
            key, _, val = stripped.partition("=")
            existing[key.strip()] = val.strip()

        existing["FOUNDRY_BASE_URL"] = body.get("foundry_url", existing.get("FOUNDRY_BASE_URL", ""))
        if body.get("hf_token"):
            existing["HF_TOKEN"] = body["hf_token"]
        if body.get("hf_models_dir"):
            existing["HF_MODELS_DIR"] = body["hf_models_dir"]

        lines = [f"{k}={v}" for k, v in existing.items()]
    else:
        lines = [
            f"FOUNDRY_BASE_URL={body.get('foundry_url', 'http://localhost:63995/v1')}",
        ]
        if body.get("hf_token"):
            lines.append(f"HF_TOKEN={body['hf_token']}")
        if body.get("hf_models_dir"):
            lines.append(f"HF_MODELS_DIR={body['hf_models_dir']}")

    _ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"success": True}


# ---------------------------------------------------------------------------
# Step: tesseract
# ---------------------------------------------------------------------------

@api_router.get("/tesseract")
async def tesseract_status() -> dict:
    """Check Tesseract OCR installation status.

    Returns:
        dict â€” installed flag, version string, executable path.
    """
    path = shutil.which("tesseract")
    version = None

    if path:
        try:
            out = subprocess.check_output(["tesseract", "--version"], stderr=subprocess.STDOUT, text=True)
            version = out.splitlines()[0] if out else "unknown"
        except Exception:
            pass

    return {"success": True, "installed": bool(path), "version": version, "path": path}


@api_router.post("/tesseract/install")
async def install_tesseract() -> dict:
    """Trigger Tesseract installation via install script.

    Returns:
        dict â€” success flag or error message.
    """
    return _run_powershell_script(_INSTALL_SCRIPTS / "Install-Tesseract.ps1")


# ---------------------------------------------------------------------------
# Step: foundry
# ---------------------------------------------------------------------------

@api_router.get("/foundry")
async def foundry_status() -> dict:
    """Check Foundry Local installation and service status.

    Returns:
        dict â€” installed flag, version, running flag.
    """
    path = shutil.which("foundry")
    version = None
    running = False

    if path:
        try:
            out = subprocess.check_output(["foundry", "--version"], stderr=subprocess.STDOUT, text=True)
            version = out.strip()
        except Exception:
            pass
        try:
            out = subprocess.check_output(["foundry", "service", "status"], stderr=subprocess.STDOUT, text=True)
            running = "running" in out.lower()
        except Exception:
            pass

    return {"success": True, "installed": bool(path), "version": version, "running": running}


@api_router.post("/foundry/install")
async def install_foundry() -> dict:
    """Install Foundry Local via winget.

    Returns:
        dict â€” success flag or error message.
    """
    winget_result = _ensure_winget_sync()
    if not winget_result.get("success"):
        return winget_result
    try:
        subprocess.Popen(
            ["winget", "install", "Microsoft.FoundryLocal",
             "--accept-source-agreements", "--accept-package-agreements"],
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Step: ollama
# ---------------------------------------------------------------------------

@api_router.get("/ollama")
async def ollama_status() -> dict:
    """Check Ollama installation and local server status."""
    path = shutil.which("ollama")
    version = None
    running = False
    url = "http://localhost:11434"

    if path:
        try:
            out = subprocess.check_output(["ollama", "--version"], stderr=subprocess.STDOUT, text=True)
            version = out.strip()
        except Exception:
            pass

    try:
        import urllib.request
        with urllib.request.urlopen(f"{url}/api/version", timeout=2) as resp:
            running = resp.status == 200
    except Exception:
        running = False

    return {
        "success": True,
        "installed": bool(path),
        "version": version,
        "running": running,
        "url": url,
        "openai_url": f"{url}/v1",
    }


@api_router.post("/ollama/install")
async def install_ollama() -> dict:
    """Install Ollama via scripts/Install/Install-Ollama.ps1."""
    return _run_powershell_script(_INSTALL_SCRIPTS / "Install-Ollama.ps1", "-SkipIfExists")


@api_router.post("/foundry/start")
async def start_foundry() -> dict:
    """Start the Foundry Local service.

    Returns:
        dict â€” success flag or error message.
    """
    try:
        subprocess.Popen(["foundry", "service", "start"])
        # Wait a moment for the service to start, then check if it's running
        import time
        time.sleep(3)
        
        # Check if Foundry is now running
        path = shutil.which("foundry")
        if path:
            try:
                out = subprocess.check_output(["foundry", "service", "status"], stderr=subprocess.STDOUT, text=True)
                running = "running" in out.lower()
                if running:
                    # Try to find the port
                    import socket
                    import psutil
                    for proc in psutil.process_iter(['pid', 'name', 'connections']):
                        try:
                            for conn in proc.connections():
                                if conn.laddr and conn.laddr.port and conn.status == psutil.CONN_LISTEN:
                                    port = conn.laddr.port
                                    try:
                                        import urllib.request
                                        req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/models", timeout=2)
                                        with urllib.request.urlopen(req) as resp:
                                            if resp.status == 200:
                                                return {"success": True, "port": port}
                                    except Exception:
                                        pass
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    return {"success": True, "port": None, "message": "Service started but port detection failed"}
                else:
                    return {"success": False, "error": "Service started but not running"}
            except Exception as e:
                return {"success": False, "error": f"Failed to verify service: {str(e)}"}
        else:
            return {"success": False, "error": "Foundry CLI not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.post("/foundry/stop")
async def stop_foundry() -> dict:
    """Stop the Foundry Local service.

    Returns:
        dict â€” success flag or error message.
    """
    try:
        subprocess.Popen(["foundry", "service", "stop"])
        # Wait a moment for the service to stop
        import time
        time.sleep(2)
        
        # Verify the service is stopped
        path = shutil.which("foundry")
        if path:
            try:
                out = subprocess.check_output(["foundry", "service", "status"], stderr=subprocess.STDOUT, text=True)
                running = "running" in out.lower()
                if not running:
                    return {"success": True, "message": "Service stopped successfully"}
                else:
                    return {"success": False, "error": "Service still running"}
            except Exception as e:
                return {"success": False, "error": f"Failed to verify service: {str(e)}"}
        else:
            return {"success": False, "error": "Foundry CLI not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Step: models
# ---------------------------------------------------------------------------

_DEFAULT_MODELS = [
    {"id": "qwen3-0.6b-generic-cpu:4",  "name": "Qwen3 0.6B (CPU)",  "size": "~0.5 GB"},
    {"id": "phi-3.5-mini-generic-cpu:4", "name": "Phi-3.5 Mini (CPU)", "size": "~2 GB"},
    {"id": "mistral-7b-generic-cpu:4",   "name": "Mistral 7B (CPU)",   "size": "~4 GB"},
]


@api_router.get("/models")
async def models_status() -> dict:
    """Return list of available default models to download.

    Returns:
        dict â€” available models list.
    """
    return {"success": True, "available": _DEFAULT_MODELS}


@api_router.post("/models/download")
async def download_model(body: dict) -> dict:
    """Trigger foundry model load for the selected model.

    Args:
        body (dict): model_id â€” Foundry model identifier.

    Returns:
        dict â€” success flag or error message.
    """
    model_id = body.get("model_id", "")
    if not model_id:
        return {"success": False, "error": "model_id is required"}

    if not shutil.which("foundry"):
        return {"success": False, "error": "foundry CLI not found"}

    try:
        subprocess.Popen(["foundry", "model", "load", model_id])
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
