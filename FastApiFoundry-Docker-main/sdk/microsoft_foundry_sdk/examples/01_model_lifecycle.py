# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Example 01 — Model Lifecycle
# =============================================================================
# Description:
#   Demonstrates: initialize manager, list catalog, load model,
#   check status, unload model.
#
# Examples:
#   pip install foundry-local-sdk
#   python sdk/microsoft_foundry_sdk/examples/01_model_lifecycle.py
#
# File: 01_model_lifecycle.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from sdk.microsoft_foundry_sdk import FoundryManager


def main() -> None:
    mgr = FoundryManager(app_name="lifecycle_demo")

    print("1. Initialize Foundry Local")
    ok = mgr.initialize()
    if not ok:
        print("❌ Foundry Local not available. Install: winget install Microsoft.FoundryLocal")
        return

    print("\n2. List available models")
    models = mgr.list_models()
    for m in models:
        print(f"   {m['alias']:40s} {m.get('size', '')}")

    if not models:
        print("   No models in catalog. Download one: foundry model run phi-4")
        return

    # Use first available model
    alias = models[0]["alias"]

    print(f"\n3. Load model: {alias}")
    mgr.load_model(alias)

    print(f"\n4. Check status: {alias}")
    status = mgr.get_model_status(alias)
    print(f"   loaded={status['loaded']}  endpoint={status['endpoint_url']}")

    print(f"\n5. Unload model: {alias}")
    mgr.unload_model(alias)
    print("✅ Done")


if __name__ == "__main__":
    main()
