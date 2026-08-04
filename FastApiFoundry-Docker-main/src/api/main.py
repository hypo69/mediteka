# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Foundry Main Entry Point
# =============================================================================
# Description:
#   Creates the FastAPI app instance, attaches the WebSocket endpoint,
#   and optionally exports API docs in dev mode.
#   Entry point for uvicorn: src.api.main:app
#
# File: main.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Changes in 0.6.1:
#   - Removed duplicate rag_router inclusion (already registered in app.py)
#   - Fixed import: use logging.getLogger instead of src.logger
#   - Fixed uvicorn __main__ block: use config properties (api_host, api_port)
#   - Removed reference to non-existent settings alias
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
import os

from fastapi import WebSocket, WebSocketDisconnect

from .app import create_app
from .docs_generator import export_to_markdown
from .websocket_manager import manager

logger = logging.getLogger(__name__)

# Application instance
app = create_app()

# Export API docs in dev mode
if os.getenv("ENVIRONMENT") == "dev" or True:
    try:
        logger.info("Generating API documentation...")
        export_to_markdown(app)
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")


@app.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    """WebSocket endpoint with room-based routing.

    Args:
        websocket (WebSocket): WebSocket connection object.
        room (str): Room name for subscription (foundry, rag, system).
    """
    await manager.connect(websocket, room)
    try:
        while True:
            # Keep connection alive by waiting for incoming data
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
    except Exception as e:
        logger.error(f"WebSocket error in room '{room}': {e}")
        manager.disconnect(websocket, room)


if __name__ == "__main__":
    import uvicorn
    from ..core.config import config

    uvicorn.run(
        "src.api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.api_reload,
        workers=config.api_workers,
        log_level=config.api_log_level.lower(),
    )
