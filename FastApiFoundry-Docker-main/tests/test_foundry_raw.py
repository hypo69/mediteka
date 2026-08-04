import asyncio
import sys
sys.path.insert(0, '.')

from src.utils.command_agent import CommandAgent

async def test():
    agent = CommandAgent()
    result = await agent.run('foundry', ['service', 'status'])
    print("Exit code:", result.get('exit_code'))
    print("Stdout:", repr(result.get('stdout', '')))
    print("Stderr:", repr(result.get('stderr', '')))

asyncio.run(test())
