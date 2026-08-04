# -*- coding: utf-8 -*-
"""OpenCode 1.15.x HTTP/CLI integration client."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp

from src.core.config import config
from src.logger import logger


class OpenCodeClient:
    """Small client for `opencode serve` and the OpenCode HTTP API."""

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None

    def _settings(self, include_secret: bool = False) -> Dict[str, Any]:
        cfg = config.get_section("opencode")
        host = cfg.get("host", "127.0.0.1")
        port = int(cfg.get("port", 4096))
        connect_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
        base_url = cfg.get("base_url") or f"http://{connect_host}:{port}"
        if "://0.0.0.0" in str(base_url):
            base_url = str(base_url).replace("://0.0.0.0", "://127.0.0.1", 1)
        if "://[::]" in str(base_url):
            base_url = str(base_url).replace("://[::]", "://127.0.0.1", 1)
        custom = config.get_section("custom")
        fastapi = config.get_section("fastapi_server")
        api_base_url = (
            custom.get("base_url")
            or cfg.get("api_base_url")
            or f"http://localhost:{int(fastapi.get('port', 9696))}/v1"
        )
        api_key = custom.get("api_key") or cfg.get("api_key") or "none"
        llama_cfg = config.get_section("llama_cpp")
        default_model = (
            config.get_section("foundry_ai").get("default_model")
            or cfg.get("model")
            or (f"llama::{llama_cfg.get('model_path')}" if llama_cfg.get("model_path") else "")
            or "default"
        )
        model_id = self._to_openai_model_id(str(default_model))
        password = cfg.get("password") or os.getenv("OPENCODE_SERVER_PASSWORD") or ""
        runtime_config_home = Path(cfg.get("runtime_config_home") or ".opencode-runtime")
        settings = {
            "enabled": cfg.get("enabled", True),
            "target_version": cfg.get("target_version", "1.15.3"),
            "base_url": str(base_url).rstrip("/"),
            "host": host,
            "connect_host": connect_host,
            "port": port,
            "command": cfg.get("command", "opencode"),
            "username": cfg.get("username") or os.getenv("OPENCODE_SERVER_USERNAME") or "opencode",
            "password_configured": bool(password),
            "auto_start": cfg.get("auto_start", False),
            "cors": cfg.get("cors", []),
            "provider_id": cfg.get("provider_id", "ai_assist"),
            "provider_name": cfg.get("provider_name", "FastAPI Foundry"),
            "api_base_url": str(api_base_url).rstrip("/"),
            "api_key_configured": bool(api_key and api_key != "none"),
            "default_model": str(default_model),
            "model_id": model_id,
            "config_path": str(Path("opencode.json").resolve()),
            "runtime_config_home": str(runtime_config_home.resolve()),
        }
        if include_secret:
            settings["password"] = password
            settings["api_key"] = api_key
        return settings

    def settings(self) -> Dict[str, Any]:
        return self._settings(include_secret=False)

    @staticmethod
    def _to_openai_model_id(model_id: str) -> str:
        if "::" not in model_id:
            return model_id
        return model_id.replace("::", "-", 1)

    def build_opencode_config(self) -> Dict[str, Any]:
        """Build a valid project-local opencode.json from config.json."""
        s = self._settings(include_secret=True)
        provider_id = s["provider_id"]
        model_id = s["model_id"]
        return {
            "$schema": "https://opencode.ai/config.json",
            "provider": {
                provider_id: {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": s["provider_name"],
                    "options": {
                        "baseURL": s["api_base_url"],
                        "apiKey": s["api_key"],
                    },
                    "models": {
                        model_id: {
                            "name": s["default_model"],
                        }
                    },
                }
            },
            "model": f"{provider_id}/{model_id}",
            "small_model": f"{provider_id}/{model_id}",
        }

    def write_opencode_config(self) -> Dict[str, Any]:
        """Write the generated OpenCode config into the project root."""
        path = Path("opencode.json")
        data = self.build_opencode_config()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {"path": str(path.resolve()), "config": data}

    def _headers(self) -> Dict[str, str]:
        s = self._settings(include_secret=True)
        if not s.get("password"):
            return {}
        token = base64.b64encode(f"{s['username']}:{s['password']}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    async def health(self) -> Dict[str, Any]:
        try:
            data = await self.request("GET", "/global/health")
            return {"success": True, **data, "base_url": self.settings()["base_url"], "running_pid": self.pid}
        except Exception as exc:
            return {"success": False, "error": str(exc), "base_url": self.settings()["base_url"], "running_pid": self.pid}

    async def request(self, method: str, path: str, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        s = self.settings()
        url = f"{s['base_url']}/{path.lstrip('/')}"
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout, headers=self._headers()) as session:
            async with session.request(method, url, json=json_body) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    raise RuntimeError(f"OpenCode HTTP {resp.status}: {text}")
                if not text:
                    return {}
                try:
                    return await resp.json()
                except Exception:
                    return {"text": text}

    async def start(self) -> Dict[str, Any]:
        s = self._settings(include_secret=True)
        if not s["enabled"]:
            return {"success": False, "error": "OpenCode is disabled in config"}

        generated = self.write_opencode_config()

        current = await self.health()
        if current.get("success"):
            return {"success": True, "message": "OpenCode already running", "opencode_config": generated["path"], **current}

        command = str(s["command"])
        resolved_command = shutil.which(command) or shutil.which(f"{command}.cmd") or command
        if sys.platform.startswith("win") and resolved_command.lower().endswith((".cmd", ".bat")):
            args = [
                "cmd.exe",
                "/c",
                resolved_command,
                "serve",
                "--hostname",
                str(s["host"]),
                "--port",
                str(s["port"]),
            ]
        else:
            args = [
                resolved_command,
                "serve",
                "--hostname",
                str(s["host"]),
                "--port",
                str(s["port"]),
            ]
        for origin in s.get("cors") or []:
            if origin:
                args.extend(["--cors", str(origin)])

        env = os.environ.copy()
        env["OPENAI_BASE_URL"] = s["api_base_url"]
        env["OPENAI_API_KEY"] = s["api_key"]
        Path(s["runtime_config_home"]).mkdir(parents=True, exist_ok=True)
        env["XDG_CONFIG_HOME"] = s["runtime_config_home"]
        if s.get("password"):
            env["OPENCODE_SERVER_PASSWORD"] = s["password"]
            env["OPENCODE_SERVER_USERNAME"] = s["username"]

        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0

        try:
            self._process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=str(Path.cwd()),
                creationflags=creationflags,
            )
        except Exception as exc:
            logger.error("Failed to start OpenCode: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "exception_type": type(exc).__name__,
                "exception_repr": repr(exc),
                "command": args,
                "runtime_config_home": s["runtime_config_home"],
            }

        for _ in range(20):
            await asyncio.sleep(0.5)
            if self._process.returncode is not None:
                stdout = ""
                stderr = ""
                try:
                    out_bytes, err_bytes = self._process.communicate(timeout=1)
                    stdout = (out_bytes or b"").decode("utf-8", errors="replace").strip()
                    stderr = (err_bytes or b"").decode("utf-8", errors="replace").strip()
                except Exception:
                    pass
                return {
                    "success": False,
                    "error": "OpenCode exited before becoming healthy",
                    "exit_code": self._process.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                    "opencode_config": generated["path"],
                }
            health = await self.health()
            if health.get("success"):
                return {"success": True, "message": "OpenCode started", "opencode_config": generated["path"], **health}

        return {"success": False, "error": "OpenCode did not become healthy in time", "pid": self.pid, "opencode_config": generated["path"]}

    async def stop(self) -> Dict[str, Any]:
        if self._process and self._process.returncode is None:
            if sys.platform.startswith("win"):
                stopper = subprocess.Popen(
                    [
                    "taskkill",
                    "/PID",
                    str(self._process.pid),
                    "/T",
                    "/F",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                await asyncio.to_thread(stopper.wait)
            else:
                self._process.terminate()
            try:
                await asyncio.to_thread(self._process.wait, timeout=10)
            except asyncio.TimeoutError:
                self._process.kill()
                await asyncio.to_thread(self._process.wait)
            except subprocess.TimeoutExpired:
                self._process.kill()
                await asyncio.to_thread(self._process.wait)
            return {"success": True, "message": "OpenCode process stopped"}
        return {"success": False, "error": "No OpenCode process was started by this API"}

    async def send_message(
        self,
        prompt: str,
        session_id: str = "",
        model: Optional[Dict[str, str]] = None,
        agent: str = "",
        system: str = "",
    ) -> Dict[str, Any]:
        sid = session_id.strip()
        if not sid:
            session = await self.request("POST", "/session", {"title": prompt[:80]})
            sid = session.get("id") or session.get("sessionID") or ""
        if not sid:
            raise RuntimeError("OpenCode did not return a session id")

        body: Dict[str, Any] = {
            "parts": [{"type": "text", "text": prompt}],
        }
        if model:
            body["model"] = model
        if agent:
            body["agent"] = agent
        if system:
            body["system"] = system

        message = await self.request("POST", f"/session/{sid}/message", body)
        return {"success": True, "session_id": sid, "message": message}

    @property
    def pid(self) -> Optional[int]:
        return self._process.pid if self._process else None


opencode_client = OpenCodeClient()
