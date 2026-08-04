# Changelog

## [0.8.0] - 2025-07-14

### Added
- `gui/tray.py` — system tray icon with context menu (Admin | User | Start | Shutdown); menu items enabled/disabled based on FastAPI server state; background poller refreshes state every 5 s
- `gui/Start-Tray.ps1` — PowerShell launcher for tray icon (hidden window, PID tracking, auto-installs pystray + Pillow)
- `start.ps1` — tray icon is launched automatically after FastAPI server becomes available; tray process is stopped in the `finally` cleanup block
