#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Translator Usage Example
# =============================================================================
# Description:
#   Demonstrates how to use the translator utility for translating
#   user input to English and AI responses back to the original language.
#
# Examples:
#   python examples/translator_example.py
#
# File: examples/translator_example.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.translator import translator


async def main():
    print("🌐 Translator Utility Example\n")

    # Example 1: Translate user input to English
    print("1️⃣ Translate user input → English for AI model")
    user_input = "Объясни квантовую запутанность простыми словами"
    result = await translator.translate_for_model(user_input, provider="mymemory")
    
    if result["success"]:
        print(f"   Original: {user_input}")
        print(f"   English:  {result['translated']}")
        print(f"   Language: {result['source_lang']} → {result['target_lang']}")
        print(f"   Time:     {result['elapsed_ms']}ms\n")
    else:
        print(f"   ❌ Error: {result['error']}\n")

    # Example 2: Translate AI response back to user's language
    print("2️⃣ Translate AI response → User's language")
    ai_response = "Quantum entanglement is a phenomenon where particles become connected."
    result = await translator.translate_response(ai_response, target_lang="ru", provider="mymemory")
    
    if result["success"]:
        print(f"   English:  {ai_response}")
        print(f"   Russian:  {result['translated']}")
        print(f"   Time:     {result['elapsed_ms']}ms\n")
    else:
        print(f"   ❌ Error: {result['error']}\n")

    # Example 3: Detect language
    print("3️⃣ Detect language")
    texts = ["Hello world", "Bonjour le monde", "Привет мир", "Hola mundo"]
    for text in texts:
        result = await translator.detect_language(text)
        if result["success"]:
            print(f"   '{text}' → {result['language_name']} ({result['language']})")
        else:
            print(f"   '{text}' → Error: {result['error']}")
    print()

    # Example 4: Batch translation
    print("4️⃣ Batch translation")
    phrases = ["Good morning", "Thank you", "Goodbye"]
    result = await translator.batch_translate(phrases, target_lang="fr", provider="mymemory")
    
    if result["success"]:
        print(f"   Translated {result['total']} phrases in {result['elapsed_ms']}ms:")
        for i, r in enumerate(result["results"]):
            if r["success"]:
                print(f"   • {phrases[i]} → {r['translated']}")
            else:
                print(f"   • {phrases[i]} → Error: {r['error']}")
    print()

    # Example 5: Try different providers
    print("5️⃣ Compare providers")
    test_text = "Hello, how are you?"
    providers = ["mymemory", "libretranslate"]
    
    for provider in providers:
        result = await translator.translate(test_text, provider=provider, target_lang="es")
        if result["success"]:
            print(f"   {provider:15} → {result['translated']} ({result['elapsed_ms']}ms)")
        else:
            print(f"   {provider:15} → ❌ {result['error']}")

    # Cleanup
    await translator.close()
    print("\n✅ Done")


if __name__ == "__main__":
    asyncio.run(main())
