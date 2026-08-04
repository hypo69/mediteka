import asyncio
import sys
sys.path.insert(0, '.')

from src.api.endpoints.health import _check_foundry_status

async def test():
    status = await _check_foundry_status()
    print("Foundry status:", status)

asyncio.run(test())
