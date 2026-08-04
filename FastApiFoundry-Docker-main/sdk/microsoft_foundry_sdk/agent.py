# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Agent — Microsoft Agent Framework Integration
# =============================================================================
# Description:
#   Wrapper around ChatAgent from agent-framework package.
#   Connects Foundry Local model with MCP tools via Agent Framework.
#   Supports streaming, tool calls, and multi-turn threads.
#
# File: agent.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

logger = logging.getLogger(__name__)

AGENT_FRAMEWORK_AVAILABLE = False
try:
    from agent_framework import ChatAgent
    from agent_framework.openai import OpenAIChatClient
    from openai import AsyncOpenAI
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ agent-framework not installed. Run: pip install agent-framework --pre")


class FoundryAgent:
    """AI Agent powered by Foundry Local + Microsoft Agent Framework.

    Connects a local Foundry model with MCP tools. The agent automatically
    decides which tools to call based on user input.

    Example:
        >>> agent = FoundryAgent(
        ...     base_url="http://localhost:50477/v1",
        ...     model_id="phi-4",
        ...     instructions="You are a helpful assistant.",
        ... )
        >>> async with agent:
        ...     response = await agent.run("List files in current directory")
        ...     print(response)
    """

    def __init__(
        self,
        base_url: str,
        model_id: str,
        api_key: str = "local",
        instructions: str = "You are a helpful AI assistant.",
        tools: Optional[List[Any]] = None,
    ) -> None:
        self.base_url = base_url
        self.model_id = model_id
        self.api_key = api_key
        self.instructions = instructions
        self.tools = tools or []
        self._agent = None
        self._thread = None

    async def __aenter__(self) -> "FoundryAgent":
        if not AGENT_FRAMEWORK_AVAILABLE:
            raise RuntimeError("agent-framework not installed. Run: pip install agent-framework --pre")

        openai_client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)
        chat_client = OpenAIChatClient(async_client=openai_client, model_id=self.model_id)

        self._agent = ChatAgent(
            chat_client=chat_client,
            instructions=self.instructions,
            tools=self.tools if self.tools else None,
        )
        await self._agent.__aenter__()
        self._thread = self._agent.get_new_thread()
        logger.info(f"✅ FoundryAgent started: model={self.model_id}")
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._agent:
            await self._agent.__aexit__(*args)
            await asyncio.sleep(0.5)  # Allow async cleanup

    async def run(self, message: str) -> str:
        """Run agent with a single message, return full response.

        Args:
            message: User input text.

        Returns:
            str: Full agent response text.
        """
        if not self._agent:
            return "❌ Agent not initialized. Use 'async with FoundryAgent(...) as agent:'"

        result = []
        async for chunk in self._agent.run_stream([message], thread=self._thread):
            if chunk.text:
                result.append(chunk.text)
        return "".join(result)

    async def stream(self, message: str) -> AsyncGenerator[str, None]:
        """Stream agent response token by token.

        Args:
            message: User input text.

        Yields:
            str: Text chunks as they arrive.
        """
        if not self._agent:
            yield "❌ Agent not initialized."
            return

        async for chunk in self._agent.run_stream([message], thread=self._thread):
            if chunk.text:
                yield chunk.text

    def new_thread(self) -> None:
        """Start a new conversation thread (clears history)."""
        if self._agent:
            self._thread = self._agent.get_new_thread()

    def add_tool(self, tool: Any) -> None:
        """Add a tool (MCP or custom) to the agent.

        Args:
            tool: Tool object compatible with agent-framework.
        """
        self.tools.append(tool)
