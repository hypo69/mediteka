# -*- coding: utf-8 -*-
"""llama.cpp model registry built from config.json.

This module keeps the mapping between a configured GGUF model and the
dedicated llama-server port that serves it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9780


@dataclass(frozen=True)
class LlamaServerConfig:
    alias: str
    model_path: str
    host: str
    port: int
    auto_start: bool = True
    ctx_size: int | None = None
    threads: int | None = None
    n_gpu_layers: int | None = None

    @property
    def model_name(self) -> str:
        return Path(self.model_path).name if self.model_path else self.alias

    @property
    def openai_url(self) -> str:
        return f"http://{self.host}:{self.port}/v1"

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def matches(self, model_id: str) -> bool:
        wanted = _normalize(model_id)
        if not wanted:
            return False
        candidates = {
            _normalize(self.alias),
            _normalize(self.model_path),
            _normalize(self.model_name),
            _normalize(Path(self.model_name).stem),
        }
        return wanted in candidates


def get_configured_llama_servers() -> list[LlamaServerConfig]:
    """Return llama.cpp server entries configured in config.json.

    Supported config shape:

    ```json
    "llama_cpp": {
      "host": "127.0.0.1",
      "port": 9780,
      "models": [
        {"alias": "coder", "model_path": "D:/models/coder.gguf", "port": 9781},
        "D:/models/general.gguf"
      ]
    }
    ```

    If `models` is empty, the legacy single `model_path`/`port` pair is used.
    """
    from ..core.config import config

    cfg = config.get_section("llama_cpp")
    base_host = str(cfg.get("host") or DEFAULT_HOST)
    base_port = int(cfg.get("port") or DEFAULT_PORT)
    base_auto_start = bool(cfg.get("auto_start", True))
    entries = cfg.get("models") or []

    servers: list[LlamaServerConfig] = []
    if entries:
        for index, entry in enumerate(entries):
            parsed = _parse_entry(entry, index, base_host, base_port)
            if parsed:
                servers.append(parsed)
    else:
        model_path = str(cfg.get("model_path") or "").strip()
        if model_path:
            servers.append(
                LlamaServerConfig(
                    alias=str(cfg.get("alias") or cfg.get("name") or Path(model_path).stem),
                    model_path=model_path,
                    host=base_host,
                    port=base_port,
                    auto_start=base_auto_start,
                    ctx_size=_optional_int(cfg.get("ctx_size")),
                    threads=_optional_int(cfg.get("threads")),
                    n_gpu_layers=_optional_int(cfg.get("n_gpu_layers")),
                )
            )

    return servers


def resolve_llama_server(model_id: str | None = None) -> LlamaServerConfig | None:
    """Find the configured llama.cpp server for a requested model ID."""
    servers = get_configured_llama_servers()
    if not servers:
        return None
    if not model_id:
        return servers[0]
    for server in servers:
        if server.matches(model_id):
            return server
    return None


def _parse_entry(entry: Any, index: int, base_host: str, base_port: int) -> LlamaServerConfig | None:
    if isinstance(entry, str):
        model_path = entry.strip()
        if not model_path:
            return None
        return LlamaServerConfig(
            alias=Path(model_path).stem,
            model_path=model_path,
            host=base_host,
            port=base_port + index,
        )

    if not isinstance(entry, dict):
        return None

    model_path = str(entry.get("model_path") or entry.get("path") or "").strip()
    if not model_path:
        return None

    return LlamaServerConfig(
        alias=str(entry.get("alias") or entry.get("name") or Path(model_path).stem),
        model_path=model_path,
        host=str(entry.get("host") or base_host),
        port=int(entry.get("port") or (base_port + index)),
        auto_start=bool(entry.get("auto_start", True)),
        ctx_size=_optional_int(entry.get("ctx_size")),
        threads=_optional_int(entry.get("threads")),
        n_gpu_layers=_optional_int(entry.get("n_gpu_layers")),
    )


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return str(value).replace("\\", "/").strip().lower()
