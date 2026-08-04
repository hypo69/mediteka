#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI Foundry Smoke Check
# =============================================================================
# Описание:
#   Быстрая регрессионная проверка ключевых endpoint'ов.
#
#   Маршруты:
#     - GET  /api/v1/health
#     - POST /api/v1/generate (use_rag=true)
#     - POST /api/v1/ai/generate
#     - POST /api/v1/ai/generate/stream (проверка SSE префикса)
#     - POST /api/v1/agent/run (tool: run_powershell -> Get-Date)
#     - POST /api/v1/agent/run (tool: http_get -> /api/v1/health)
#
#   Требование:
#     - сервер FastAPI должен быть запущен на localhost по умолчанию.
#
# File: smoke_all_endpoints.py
# Project: Ai Assistant (Docker)
# Version: 0.2.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Date: 9 декабря 2025
# =============================================================================

import argparse
import json
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, Optional, Tuple


def _stdout_utf8() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        ...


def _load_default_model(config_path: str) -> str:
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg.get("foundry_ai", {}).get("default_model") or ""
    except Exception:
        return ""


def _http_request_json(url: str, payload: Dict[str, Any], timeout_s: int) -> Tuple[int, Dict[str, Any], str]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read()
        text = raw.decode("utf-8", errors="replace")
        return resp.status, json.loads(text), text


def _http_get_json(url: str, timeout_s: int) -> Tuple[int, Dict[str, Any], str]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read()
        text = raw.decode("utf-8", errors="replace")
        return resp.status, json.loads(text), text


def _http_post_raw(url: str, payload: Dict[str, Any], timeout_s: int) -> Tuple[int, str, bytes]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read()
        return resp.status, resp.headers.get("Content-Type", ""), raw


def _fail(name: str, details: str) -> None:
    print(f"❌ {name}: {details}")
    raise SystemExit(1)


def _pick_model_by_probe(base_url: str, candidates: list, timeout_s: int) -> str:
    # Почему: список `/api/v1/models` включает "подключенные/доступные" модели,
    # но конкретная модель может быть не загружена и не отвечать.
    # Проба через `/api/v1/generate` гарантирует работоспособность выбранной модели.
    for m in candidates[:8]:
        model_id = (m or {}).get("id") if isinstance(m, dict) else str(m or "")
        model_id = (model_id or "").strip()
        if not model_id:
            continue
        probe_payload = {
            "prompt": "OK",
            "model": model_id,
            "temperature": 0.1,
            "max_tokens": 8,
            "use_rag": False,
        }
        try:
            st, data, _ = _http_request_json(f"{base_url}/api/v1/generate", probe_payload, timeout_s=timeout_s)
            if st == 200 and data.get("success", False):
                print(f"✅ Model probe: {model_id}")
                return model_id
        except Exception:
            continue
    return ""


def main() -> int:
    """Основная функция."""
    _stdout_utf8()

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=9696, type=int)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--model", default="", help="Optional model id. If empty, auto-pick from /api/v1/models")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"

    # Почему: дефолтная модель из config.json может быть не загружена в Foundry.
    # Автоподбор модели из /api/v1/models делает smoke-check стабильнее.
    picked_model: str = args.model.strip()
    if not picked_model:
        _ = _load_default_model(args.config)

    timeouts = {
        "health": 10,
        "generate": 120,
        "ai_generate": 120,
        "ai_stream": 30,
        "agent_run": 180,
    }

    print("🧪 FastAPI Foundry smoke check")
    print(f"🌐 Base URL: {base_url}")

    # pick model from /api/v1/models
    try:
        st, models_resp, _ = _http_get_json(f"{base_url}/api/v1/models", timeout_s=10)
        candidates = []
        if st == 200 and isinstance(models_resp, dict):
            candidates = models_resp.get("models") or []
    except Exception:
        candidates = []

    model_to_use: str = ""
    if picked_model:
        model_to_use = picked_model
    else:
        model_to_use = _pick_model_by_probe(base_url, candidates, timeout_s=30)

        if not model_to_use:
            model_to_use = _load_default_model(args.config) or ""

    if not model_to_use:
        _fail("model_pick", "No working model id available (check Foundry + loaded models)")

    print(f"🤖 Model to use: {model_to_use}")

    # 1) health
    try:
        st, data, _ = _http_get_json(f"{base_url}/api/v1/health", timeout_s=timeouts["health"])
        if st != 200:
            _fail("health", f"HTTP {st}")
        if "status" not in data:
            _fail("health", "missing field: status")
        print(f"✅ health: status={data.get('status')}")
    except Exception as e:
        _fail("health", str(e))

    # 2) generate (use_rag)
    generate_payload = {
        "prompt": "Explain RAG in two sentences at a high level.",
        "model": model_to_use,
        "temperature": 0.2,
        "max_tokens": 64,
        "use_rag": True,
        "top_k": 3,
    }
    try:
        st, data, _ = _http_request_json(f"{base_url}/api/v1/generate", generate_payload, timeout_s=timeouts["generate"])
        if st != 200:
            _fail("generate", f"HTTP {st}")
        if not data.get("success", False):
            _fail("generate", f"success=false error={data.get('error')}")
        print("✅ generate: OK")
    except Exception as e:
        _fail("generate", str(e))

    # 3) ai/generate
    ai_payload = {
        "prompt": "Give a short answer: what is RAG?",
        "model": model_to_use,
        "temperature": 0.2,
        "max_tokens": 64,
        "use_rag": False,
    }
    try:
        st, data, _ = _http_request_json(f"{base_url}/api/v1/ai/generate", ai_payload, timeout_s=timeouts["ai_generate"])
        if st != 200:
            _fail("ai/generate", f"HTTP {st}")
        if not data.get("success", False):
            _fail("ai/generate", f"success=false error={data.get('error')}")
        print("✅ ai/generate: OK")
    except Exception as e:
        _fail("ai/generate", str(e))

    # 4) ai/generate/stream (SSE)
    stream_payload = {
        "prompt": "Stream test. Reply with the word STREAM and nothing else.",
        "model": model_to_use,
        "temperature": 0.2,
        "max_tokens": 16,
    }
    try:
        st, ct, raw = _http_post_raw(f"{base_url}/api/v1/ai/generate/stream", stream_payload, timeout_s=timeouts["ai_stream"])
        if st != 200:
            _fail("ai/generate/stream", f"HTTP {st}")
        if "text/event-stream" not in ct:
            _fail("ai/generate/stream", f"unexpected Content-Type: {ct}")
        if b"data:" not in raw:
            _fail("ai/generate/stream", "missing 'data:' in first chunk")
        print("✅ ai/generate/stream: OK")
    except Exception as e:
        _fail("ai/generate/stream", str(e))

    # 5) agent run_powershell
    agent_payload_tool = {
        "message": "If a tool is available, call run_powershell with script Get-Date. Then answer with only the tool output.",
        "agent": "powershell",
        "model": model_to_use,
        "temperature": 0.2,
        "max_tokens": 256,
        "max_iterations": 3,
    }
    try:
        st, data, _ = _http_request_json(f"{base_url}/api/v1/agent/run", agent_payload_tool, timeout_s=timeouts["agent_run"])
        if st != 200:
            _fail("agent/run_powershell", f"HTTP {st}")
        if not data.get("success", False):
            _fail("agent/run_powershell", f"success=false error={data.get('error')}")
        tool_calls = data.get("tool_calls") or []
        if len(tool_calls) < 1:
            _fail("agent/run_powershell", "no tool_calls")
        if tool_calls[0].get("tool") != "run_powershell":
            _fail("agent/run_powershell", f"unexpected tool: {tool_calls[0].get('tool')}")
        print("✅ agent/run_powershell: OK")
    except Exception as e:
        _fail("agent/run_powershell", str(e))

    # 6) agent http_get
    agent_payload_http_get = {
        "message": "Call http_get for url http://127.0.0.1:9696/api/v1/health and return only the tool output.",
        "agent": "powershell",
        "model": model_to_use,
        "temperature": 0.2,
        "max_tokens": 256,
        "max_iterations": 3,
    }
    try:
        st, data, _ = _http_request_json(f"{base_url}/api/v1/agent/run", agent_payload_http_get, timeout_s=timeouts["agent_run"])
        if st != 200:
            _fail("agent/http_get", f"HTTP {st}")
        if not data.get("success", False):
            _fail("agent/http_get", f"success=false error={data.get('error')}")
        tool_calls = data.get("tool_calls") or []
        if len(tool_calls) < 1:
            _fail("agent/http_get", "no tool_calls")
        if tool_calls[0].get("tool") != "http_get":
            _fail("agent/http_get", f"unexpected tool: {tool_calls[0].get('tool')}")
        print("✅ agent/http_get: OK")
    except Exception as e:
        _fail("agent/http_get", str(e))

    print("🎉 Smoke check completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

