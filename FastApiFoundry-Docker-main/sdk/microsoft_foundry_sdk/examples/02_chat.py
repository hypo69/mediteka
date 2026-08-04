# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Example 02 — Chat Interface (single-turn + multi-turn + stream)
# =============================================================================
# Description:
#   Demonstrates: single message, multi-turn history, streaming, clear history.
#
# Examples:
#   python sdk/microsoft_foundry_sdk/examples/02_chat.py
#
# File: 02_chat.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from sdk.microsoft_foundry_sdk import FoundryManager, FoundryChat


def main() -> None:
    mgr = FoundryManager(app_name="chat_demo")
    if not mgr.initialize():
        print("❌ Foundry Local not available")
        return

    models = mgr.list_models()
    if not models:
        print("❌ No models available")
        return

    alias = models[0]["alias"]
    mgr.load_model(alias)
    client = mgr.get_chat_client(alias)
    if not client:
        print("❌ Could not get chat client")
        return

    chat = FoundryChat(
        client=client,
        model_id=alias,
        system_prompt="You are a concise assistant. Answer in 1-2 sentences.",
        temperature=0.7,
        max_tokens=256,
    )

    # Single-turn
    print("=== Single-turn ===")
    r = chat.send("What is Python?")
    print(f"Response: {r['content']}")
    print(f"Tokens: {r['usage']['total_tokens']}")

    # Multi-turn (history preserved)
    print("\n=== Multi-turn ===")
    chat.send("My name is Alex.")
    r2 = chat.send("What is my name?")
    print(f"Response: {r2['content']}")

    # Streaming
    print("\n=== Streaming ===")
    print("Response: ", end="", flush=True)
    for chunk in chat.stream("Count from 1 to 5."):
        print(chunk, end="", flush=True)
    print()

    # Clear history
    chat.clear_history()
    print(f"\nHistory cleared. Length: {len(chat.history)}")
    print("✅ Done")


if __name__ == "__main__":
    main()
