# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Search for all AI Models in the System
# =============================================================================
# Description:
#   Searching for Foundry, Ollama, HuggingFace, and other AI framework models
#
# File: ai_model_scanner.py
# Project: Ai Assistant (Docker)
# Version: 0.4.0
# Author: hypo69
# License: MIT
# Copyright: © 2026 hypo69
# Date: December 9, 2025
# =============================================================================

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import json

def scan_all_ai_models() -> Dict[str, Any]:
    """Scanning all AI models in the system"""
    
    results = {
        "foundry": {"directories": [], "models": []},
        "ollama": {"directories": [], "models": []},
        "huggingface": {"directories": [], "models": []},
        "other": {"directories": [], "models": []}
    }
    
    # Paths for searching
    search_locations = {
        "foundry": [
            Path.home() / ".foundry",
            Path.home() / ".cache" / "foundry",
            Path("C:") / "foundry" if sys.platform == "win32" else Path("/opt/foundry"),
        ],
        "ollama": [
            Path.home() / ".ollama",
            Path("C:") / "Users" / os.getenv("USERNAME", "") / ".ollama" if sys.platform == "win32" else Path.home() / ".ollama",
            Path("/usr/share/ollama") if sys.platform != "win32" else None,
        ],
        "huggingface": [
            Path.home() / ".cache" / "huggingface",
            Path.home() / ".cache" / "transformers",
            Path.home() / "transformers_cache",
        ]
    }
    
    print("🔍 Scanning for AI models in the system...")
    print()
    
    for framework, paths in search_locations.items():
        print(f"🔍 Searching for {framework.upper()} models...")
        
        for path in paths:
            if path and path.exists():
                print(f"  ✅ Directory found: {path}")
                results[framework]["directories"].append(str(path))
                
                # Scanning files
                try:
                    for item in path.rglob("*"):
                        if item.is_file():
                            size_mb = item.stat().st_size / (1024 * 1024)
                            
                            # Determine model file type
                            if any(ext in item.name.lower() for ext in [
                                '.bin', '.safetensors', '.gguf', '.ggml', 
                                'pytorch_model', 'model.json', 'config.json',
                                '.pt', '.pth', '.onnx'
                            ]):
                                if size_mb > 5:  # Files larger than 5MB
                                    results[framework]["models"].append({
                                        "name": item.name,
                                        "path": str(item),
                                        "size_mb": round(size_mb, 1),
                                        "parent": item.parent.name
                                    })
                except PermissionError:
                    print(f"  ⚠️  No access to {path}")
            else:
                print(f"  ❌ Not found: {path}")
        print()
    
    # Additional search in common locations
    print("🔍 Searching in common directories...")
    common_paths = [
        Path.home() / "models",
        Path.home() / "Downloads",
        Path("C:") / "models" if sys.platform == "win32" else Path("/models"),
        Path(".") / "models",
    ]
    
    for path in common_paths:
        if path.exists():
            print(f"  ✅ Scanning: {path}")
            try:
                for item in path.rglob("*"):
                    if item.is_file():
                        size_mb = item.stat().st_size / (1024 * 1024)
                        if size_mb > 50 and any(ext in item.name.lower() for ext in [
                            '.bin', '.safetensors', '.gguf', '.ggml'
                        ]):
                            results["other"]["models"].append({
                                "name": item.name,
                                "path": str(item),
                                "size_mb": round(size_mb, 1),
                                "parent": item.parent.name
                            })
            except PermissionError:
                print(f"  ⚠️  No access to {path}")
    
    return results

def check_ai_installations() -> Dict[str, bool]:
    """Checking installed AI frameworks"""
    
    installations = {}
    
    # Check via commands
    commands = {
        "foundry": ["foundry", "foundry-server"],
        "ollama": ["ollama"],
        "python": ["python", "python3"],
        "transformers": ["transformers-cli"],
    }
    
    import shutil
    
    for framework, cmds in commands.items():
        found = False
        for cmd in cmds:
            if shutil.which(cmd):
                installations[framework] = True
                found = True
                break
        if not found:
            installations[framework] = False
    
    # Check Python packages
    try:
        import transformers
        installations["transformers_lib"] = True
    except ImportError:
        installations["transformers_lib"] = False
    
    try:
        import torch
        installations["pytorch"] = True
    except ImportError:
        installations["pytorch"] = False
    
    return installations

def main():
    """Main function"""
    print("=" * 70)
    print("🤖 AI MODEL SCANNER IN THE SYSTEM")
    print("=" * 70)
    print()
    
    # Check installations
    installations = check_ai_installations()
    
    print("🔧 INSTALLED FRAMEWORKS:")
    for framework, installed in installations.items():
        status = "✅ Installed" if installed else "❌ Not found"
        print(f"  {framework}: {status}")
    print()
    
    # Scanning models
    results = scan_all_ai_models()
    
    # Output results
    print("=" * 70)
    print("📊 SCAN RESULTS")
    print("=" * 70)
    
    total_models = 0
    for framework, data in results.items():
        model_count = len(data["models"])
        total_models += model_count
        
        if model_count > 0:
            print(f"\n🤖 {framework.upper()}: {model_count} models")
            
            # Show first 5 models
            for model in data["models"][:5]:
                print(f"  📄 {model['name']} ({model['size_mb']} MB)")
                print(f"     📁 {model['parent']}")
            
            if model_count > 5:
                print(f"     ... and {model_count - 5} more models")
    
    print(f"\n📊 TOTAL MODELS FOUND: {total_models}")
    
    if total_models == 0:
        print("\n💡 RECOMMENDATIONS:")
        print("  1. Install Ollama: https://ollama.ai/")
        print("  2. Download models: ollama pull llama2")
        print("  3. Or install Foundry with models")
        print("  4. Check Downloads directories for .gguf files")

if __name__ == "__main__":
    main()