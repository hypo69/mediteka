import asyncio
import sys
sys.path.insert(0, '.')

from src.utils.command_agent import CommandAgent

async def test():
    agent = CommandAgent()
    status = await agent.parse_foundry_status()
    print("Foundry status:", status)

asyncio.run(test())
