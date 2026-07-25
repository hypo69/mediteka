from mcp.server.fastmcp import FastMCP
import httpx
import json
from pathlib import Path
from src.utils.jjson import j_loads_ns

# Initialize FastMCP server
mcp = FastMCP("FastAPI-Media-Client")

# Load configuration for the FastAPI service
CONFIG_PATH = Path(__file__).parent.parent / 'src' / 'fastapi' / 'config.json'

def get_base_url():
    cfg = j_loads_ns(CONFIG_PATH)
    return f"http://{cfg.host}:{cfg.port}"

@mcp.tool()
async def fastapi_chat(message: str) -> str:
    """Send a message to the FastAPI chat router."""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{get_base_url()}/chat", json={"message": message})
        return response.text

@mcp.tool()
async def fastapi_media_list() -> str:
    """List media from the FastAPI media router."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{get_base_url()}/media")
        return response.text

@mcp.tool()
async def fastapi_qbittorrent_info() -> str:
    """Get qBittorrent info from the FastAPI qbittorrent router."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{get_base_url()}/qbittorrent/torrents")
        return response.text

if __name__ == "__main__":
    mcp.run()
