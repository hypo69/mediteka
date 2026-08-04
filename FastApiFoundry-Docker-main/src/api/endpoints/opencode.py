# -*- coding: utf-8 -*-
"""OpenCode 1.15.3 integration API."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.models.opencode_client import opencode_client

router = APIRouter(prefix="/opencode", tags=["OpenCode"])


class OpenCodeMessageRequest(BaseModel):
    prompt: str
    session_id: str = ""
    provider_id: str = ""
    model_id: str = ""
    agent: str = ""
    system: str = ""


class OpenCodeConfigPatch(BaseModel):
    updates: Dict[str, Any]


@router.get("/status")
async def opencode_status() -> dict:
    """Return configured settings and OpenCode server health/version."""
    generated = opencode_client.build_opencode_config()
    return {
        "success": True,
        "settings": opencode_client.settings(),
        "health": await opencode_client.health(),
        "docs_url": f"{opencode_client.settings()['base_url']}/doc",
        "generated_config": generated,
    }


@router.post("/start")
async def opencode_start() -> dict:
    """Start `opencode serve` using saved settings."""
    return await opencode_client.start()


@router.post("/stop")
async def opencode_stop() -> dict:
    """Stop an OpenCode server process started by this API."""
    return await opencode_client.stop()


@router.get("/config")
async def opencode_config() -> dict:
    """Proxy OpenCode `GET /config`."""
    return {"success": True, "config": await opencode_client.request("GET", "/config")}


@router.get("/generated-config")
async def opencode_generated_config() -> dict:
    """Return the project-local OpenCode config generated from config.json."""
    return {"success": True, "config": opencode_client.build_opencode_config()}


@router.patch("/config")
async def opencode_patch_config(request: OpenCodeConfigPatch) -> dict:
    """Proxy OpenCode `PATCH /config`."""
    return {"success": True, "config": await opencode_client.request("PATCH", "/config", request.updates)}


@router.get("/providers")
async def opencode_providers() -> dict:
    """Proxy OpenCode provider list."""
    return {"success": True, **await opencode_client.request("GET", "/provider")}


@router.get("/sessions")
async def opencode_sessions() -> dict:
    """Proxy OpenCode session list."""
    return {"success": True, "sessions": await opencode_client.request("GET", "/session")}


@router.post("/sessions")
async def opencode_create_session(body: Optional[Dict[str, Any]] = None) -> dict:
    """Create an OpenCode session."""
    return {"success": True, "session": await opencode_client.request("POST", "/session", body or {})}


@router.get("/sessions/{session_id}/messages")
async def opencode_messages(session_id: str, limit: Optional[int] = None) -> dict:
    """List messages for an OpenCode session."""
    path = f"/session/{session_id}/message"
    if limit:
        path += f"?limit={limit}"
    return {"success": True, "messages": await opencode_client.request("GET", path)}


@router.post("/message")
async def opencode_message(request: OpenCodeMessageRequest) -> dict:
    """Send a prompt to OpenCode and wait for the response."""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required")
    model = None
    if request.provider_id and request.model_id:
        model = {"providerID": request.provider_id, "modelID": request.model_id}
    return await opencode_client.send_message(
        request.prompt,
        session_id=request.session_id,
        model=model,
        agent=request.agent,
        system=request.system,
    )


@router.get("/openapi-url")
async def opencode_openapi_url() -> dict:
    """Return the OpenCode OpenAPI documentation URL."""
    return {"success": True, "url": f"{opencode_client.settings()['base_url']}/doc"}
