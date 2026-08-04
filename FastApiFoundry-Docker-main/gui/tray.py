# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Tray Icon for AI Assistant
# =============================================================================
# Description:
#   Tray icon with context menu: Admin | User | Start | Shutdown.
#   Reflects FastAPI server state (running/stopped).
#   Admin opens browser at localhost:9696.
#   User checks server state: focuses window if running, starts via Start-User.ps1 if not.
#   Start launches start.ps1 (when server is stopped).
#   Shutdown stops the FastAPI server.
#
# File: gui/tray.py
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import sys
import time
import threading
import subprocess
import webbrowser
import urllib.request
import urllib.error

import pystray
from PIL import Image

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
APP_URL    = "http://localhost:9696"
HEALTH_URL = f"{APP_URL}/api/v1/health"
ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_PATH  = os.path.join(ROOT, "icon.ico")
START_PS1  = os.path.join(ROOT, "start.ps1")
START_USER = os.path.join(ROOT, "gui", "Start-User.ps1")
PID_FILE   = os.path.join(os.environ.get("TEMP", ROOT), "fastapi-foundry.pid")

_icon: pystray.Icon | None = None


def _is_server_running() -> bool:
    """Check FastAPI server availability via health endpoint."""
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def _load_image() -> Image.Image:
    """Load tray icon image."""
    if os.path.exists(ICON_PATH):
        return Image.open(ICON_PATH)
    # Fallback: simple colored square
    img = Image.new("RGB", (64, 64), color=(0, 120, 212))
    return img


def _run_ps1(script: str) -> None:
    """Run a PowerShell script in a new minimized window."""
    subprocess.Popen(
        ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", script],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        cwd=ROOT,
    )


def _focus_or_open_browser() -> None:
    """Focus existing browser window or open new one (best-effort on Windows)."""
    try:
        import ctypes
        # EnumWindows to find a window with localhost:9696 in title — not reliable,
        # so we just open the URL; the OS/browser handles focus if already open.
        webbrowser.open(APP_URL)
    except Exception:
        webbrowser.open(APP_URL)


# ---------------------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------------------

def on_admin(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
    """Open admin interface in browser."""
    webbrowser.open(APP_URL)


def on_user(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
    """Open user (pywebview) interface; start it if not running."""
    if _is_server_running():
        _focus_or_open_browser()
    else:
        threading.Thread(target=_run_ps1, args=(START_USER,), daemon=True).start()


def on_start(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
    """Start FastAPI server via start.ps1."""
    threading.Thread(target=_run_ps1, args=(START_PS1,), daemon=True).start()


def on_shutdown(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
    """Stop FastAPI server by PID file."""
    _stop_server()


def on_quit(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
    """Remove tray icon and exit."""
    _icon.stop()


def _stop_server() -> None:
    """Kill FastAPI process by PID file."""
    if not os.path.exists(PID_FILE):
        return
    try:
        pid = int(open(PID_FILE).read().strip())
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Dynamic menu builder
# ---------------------------------------------------------------------------

def _build_menu() -> pystray.Menu:
    running = _is_server_running()
    return pystray.Menu(
        pystray.MenuItem("Admin", on_admin, enabled=running),
        pystray.MenuItem("User",  on_user,  enabled=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Start",    on_start,    enabled=not running),
        pystray.MenuItem("Shutdown", on_shutdown, enabled=running),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit tray", on_quit),
    )


# ---------------------------------------------------------------------------
# Background state poller — refreshes menu every 5 s
# ---------------------------------------------------------------------------

def _poll_state(icon: pystray.Icon) -> None:
    while True:
        time.sleep(5)
        try:
            icon.menu = _build_menu()
            icon.update_menu()
        except Exception:
            break


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    global _icon
    image = _load_image()
    _icon = pystray.Icon(
        name="ai_assist",
        icon=image,
        title="AI Assistant",
        menu=_build_menu(),
    )
    threading.Thread(target=_poll_state, args=(_icon,), daemon=True).start()
    _icon.run()


if __name__ == "__main__":
    main()
