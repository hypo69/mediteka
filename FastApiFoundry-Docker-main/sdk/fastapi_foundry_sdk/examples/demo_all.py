# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Foundry SDK — Full Demo
# =============================================================================
# Description:
#   Demonstrates all FastAPIFoundryClient capabilities:
#   health, models, generate, batch, RAG, config, HF, llama, Ollama, MCP.
#
# Examples:
#   # Start server first: venv\Scripts\python.exe run.py
#   python sdk/fastapi_foundry_sdk/examples/demo_all.py
#
# File: demo_all.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from sdk.fastapi_foundry_sdk import FastAPIFoundryClient

BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:9696")
API_KEY = os.getenv("API_KEY", "")


async def main() -> None:
    async with FastAPIFoundryClient(base_url=BASE_URL, api_key=API_KEY or None) as client:

        # 1. Health
        print("=== 1. Health ===")
        h = await client.health()
        print(f"  status={h.get('status')}  foundry={h.get('foundry_status')}  rag={h.get('rag_status')}")

        # 2. Models
        print("\n=== 2. Models ===")
        m = await client.list_models()
        models = m.get("models", [])
        print(f"  Total: {len(models)}")
        for model in models[:3]:
            print(f"  - {model.get('id', model)}")

        # 3. Generate (Foundry)
        print("\n=== 3. Generate (Foundry) ===")
        r = await client.generate(
            prompt="What is Python? Answer in one sentence.",
            temperature=0.5,
            max_tokens=100,
        )
        if r.get("success"):
            print(f"  {r['content']}")
        else:
            print(f"  ⚠️ {r.get('error', 'Foundry not available')}")

        # 4. Generate with RAG
        print("\n=== 4. Generate with RAG ===")
        r_rag = await client.generate(
            prompt="How to configure RAG in FastAPI Foundry?",
            use_rag=True,
            max_tokens=200,
        )
        if r_rag.get("success"):
            print(f"  {r_rag['content'][:200]}...")
        else:
            print(f"  ⚠️ {r_rag.get('error')}")

        # 5. Batch generate
        print("\n=== 5. Batch Generate ===")
        batch = await client.batch_generate(
            prompts=["What is FastAPI?", "What is FAISS?", "What is llama.cpp?"],
            max_tokens=80,
        )
        results = batch.get("results", [])
        print(f"  Total: {batch.get('total')}  Succeeded: {batch.get('succeeded')}")
        for i, res in enumerate(results[:2]):
            if res.get("success"):
                print(f"  [{i}] {res['content'][:80]}...")

        # 6. RAG search
        print("\n=== 6. RAG Search ===")
        rag = await client.rag_search("how to start FastAPI Foundry", top_k=3)
        for chunk in rag.get("results", [])[:2]:
            print(f"  score={chunk.get('score', 0):.3f}  {chunk.get('source', '')} — {chunk.get('section', '')}")

        # 7. Config
        print("\n=== 7. Config ===")
        cfg = await client.get_config()
        foundry_cfg = cfg.get("foundry", cfg.get("foundry_ai", {}))
        print(f"  default_model={foundry_cfg.get('default_model')}")
        print(f"  temperature={foundry_cfg.get('temperature')}")

        # Patch config
        await client.patch_config({"foundry_ai.temperature": 0.7})
        print("  ✅ Config patched")

        # 8. HuggingFace
        print("\n=== 8. HuggingFace ===")
        hf = await client.hf_list_models()
        hf_models = hf.get("models", [])
        print(f"  Downloaded HF models: {len(hf_models)}")

        # 9. llama.cpp
        print("\n=== 9. llama.cpp ===")
        llama = await client.llama_status()
        print(f"  llama status: {llama.get('status', llama)}")

        # 10. Ollama
        print("\n=== 10. Ollama ===")
        ollama = await client.ollama_models()
        print(f"  Ollama models: {len(ollama.get('models', []))}")

        # 11. MCP status
        print("\n=== 11. MCP Status ===")
        mcp = await client.mcp_status()
        print(f"  MCP: {mcp}")

        print("\n✅ All done!")


if __name__ == "__main__":
    asyncio.run(main())
