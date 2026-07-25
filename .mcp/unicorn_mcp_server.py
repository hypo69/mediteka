from mcp.server.fastmcp import FastMCP
import subprocess
from pathlib import Path
import os

# Initialize FastMCP server
mcp = FastMCP("Unicorn-Manager")

UNICORN_SCRIPT = Path(__file__).parent.parent / 'Run-Unicorn.ps1'

@mcp.tool()
async def unicorn_start() -> str:
    """Start the Run-Unicorn.ps1 service."""
    # Run in background
    subprocess.Popen(["powershell", "-NoProfile", "-Command", f"& '{UNICORN_SCRIPT}'"], shell=True)
    return "Unicorn service start initiated."

@mcp.tool()
async def unicorn_stop() -> str:
    """Stop the Unicorn service (finds and kills the process)."""
    # This is a simplified stop mechanism assuming process name
    # In a real scenario, you'd track PID
    os.system("taskkill /F /IM uvicorn.exe /T") 
    return "Attempted to stop Unicorn service."

@mcp.tool()
async def unicorn_status() -> str:
    """Check if the Unicorn service process is running."""
    # Simplified check
    result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq uvicorn.exe"], capture_output=True, text=True)
    if "uvicorn.exe" in result.stdout:
        return "Unicorn service is running."
    return "Unicorn service is not running."

if __name__ == "__main__":
    mcp.run()
