# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Models List Example
# =============================================================================
# Description:
#   Shows available, loaded and cached Foundry models via FastAPI Foundry API.
#
# Examples:
#   python foundry_models_list.py
#
# File: foundry_models_list.py
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from SANDBOX.Alrix010.sdk import FoundryClient


def main():
    with FoundryClient("http://localhost:9696") as client:

        # Available models (catalog)
        available = client._request("GET", "/api/v1/foundry/models/available")
        print(f"\n📋 Available models ({available.get('source', '')}):")
        for m in available.get("models", []):
            cached_mark = "✅" if m.get("cached") else "  "
            print(f"  {cached_mark} {m['id']:<55} {m.get('size', ''):<10} [{m.get('type', '').upper()}]")

        # Loaded models (running in Foundry service)
        loaded = client._request("GET", "/api/v1/foundry/models/loaded")
        print(f"\n🟢 Loaded models ({loaded.get('count', 0)}):")
        for m in loaded.get("models", []):
            print(f"     {m['id']}")
        if not loaded.get("models"):
            print("     (none)")

        # Cached models (downloaded to disk)
        cached = client._request("GET", "/api/v1/foundry/models/cached")
        print(f"\n💾 Cached on disk ({cached.get('count', 0)}):")
        for model_id in cached.get("models", []):
            print(f"     {model_id}")
        if not cached.get("models"):
            print("     (none)")


if __name__ == "__main__":
    main()
