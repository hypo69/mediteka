# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Local Chat Interface
# =============================================================================
# Description:
#   Chat wrapper over OpenAI-compatible client from Foundry Local SDK.
#   Supports single-turn, multi-turn history, streaming, and system prompts.
#
# File: chat.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
from typing import Any, Dict, Generator, List, Optional

logger = logging.getLogger(__name__)


class FoundryChat:
    """OpenAI-compatible chat interface for Foundry Local models.

    Wraps the client returned by model.get_chat_client().
    Maintains conversation history for multi-turn sessions.

    Example:
        >>> from sdk.microsoft_foundry_sdk import FoundryManager, FoundryChat
        >>> mgr = FoundryManager()
        >>> mgr.initialize()
        >>> mgr.load_model("phi-4")
        >>> client = mgr.get_chat_client("phi-4")
        >>> chat = FoundryChat(client, model_id="phi-4")
        >>> response = chat.send("What is Python?")
        >>> print(response["content"])
    """

    def __init__(
        self,
        client: Any,
        model_id: str,
        system_prompt: str = "You are a helpful AI assistant.",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> None:
        self._client = client
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._history: List[Dict[str, str]] = []

    def send(self, message: str) -> Dict[str, Any]:
        """Send a message and get a response. Maintains history.

        Args:
            message: User message text.

        Returns:
            dict: success, content, model, usage.
        """
        if not message or not message.strip():
            return {"success": False, "error": "Empty message"}

        self._history.append({"role": "user", "content": message})
        messages = [{"role": "system", "content": self.system_prompt}] + self._history

        try:
            response = self._client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            content = response.choices[0].message.content
            self._history.append({"role": "assistant", "content": content})
            return {
                "success": True,
                "content": content,
                "model": self.model_id,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }
        except Exception as e:
            logger.error(f"❌ Chat send failed: {e}")
            return {"success": False, "error": str(e)}

    def stream(self, message: str) -> Generator[str, None, None]:
        """Stream a response token by token.

        Args:
            message: User message text.

        Yields:
            str: Text chunks as they arrive.
        """
        if not message or not message.strip():
            return

        self._history.append({"role": "user", "content": message})
        messages = [{"role": "system", "content": self.system_prompt}] + self._history
        full_response = ""

        try:
            stream = self._client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                full_response += delta
                yield delta
            self._history.append({"role": "assistant", "content": full_response})
        except Exception as e:
            logger.error(f"❌ Chat stream failed: {e}")

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._history = []

    @property
    def history(self) -> List[Dict[str, str]]:
        """Return current conversation history (without system prompt)."""
        return list(self._history)
