# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Search for Foundry Models in the System
# =============================================================================
# Description:
#   Utility for searching and analyzing Foundry models in various directories
#
# File: foundry_model_finder.py
# Project: Ai Assistant (Docker)
# Version: 0.4.0
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: December 9, 2025
# =============================================================================

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

def find_foundry_models() -> Dict[str, Any]:
    """Search for Foundry models in the system"""
    
    # Possible paths for models
    search_paths = [
        # Windows
        Path.home() / ".foundry" / "models",
        Path.home() / ".cache" / "foundry",
        Path.home() / "AppData" / "Local" / "foundry",
        Path.home() / "AppData" / "Roaming" / "foundry",
        Path("C:") / "foundry" / "models",
        
        # Linux/macOS
        Path.home() / ".foundry",
        Path.home() / ".local" / "share" / "foundry",
        Path("/opt/foundry/models"),
        Path("/usr/local/foundry/models"),
        
        # Docker volumes
        Path("/models"),
        Path("/app/models"),
        
        # Current directory
        Path(".") / "models",
        Path("..") / "models",
    ]
    
    found_models = []
    model_dirs = []
    
    print("🔍 Searching for Foundry models in the system...")
    print()
    
    for search_path in search_paths:
        if search_path.exists():
            print(f"✅ Directory found: {search_path}")
            model_dirs.append(str(search_path))
            
            # Search for model files
            for item in search_path.rglob("*"):
                if item.is_file():
                    # Typical model files
                    if any(ext in item.name.lower() for ext in [
                        '.bin', '.safetensors', '.gguf', '.ggml', 
                        'pytorch_model', 'model.json', 'config.json'
                    ]):
                        size_mb = item.stat().st_size / (1024 * 1024)
                        if size_mb > 10:  # Only large files (models)
                            found_models.append({
                                "path": str(item),
                                "name": item.name,
                                "size_mb": round(size_mb, 1),
                                "parent_dir": str(item.parent)
                            })
        else:
            print(f"❌ Not found: {search_path}")
    
    print()
    print(f"📊 Directories found: {len(model_dirs)}")
    print(f"📊 Model files found: {len(found_models)}")
    
    return {
        "model_directories": model_dirs,
        "model_files": found_models,
        "total_directories": len(model_dirs),
        "total_files": len(found_models)
    }

def check_foundry_installation() -> Dict[str, Any]:
    """Check Foundry installation"""
    
    print("🔍 Checking Foundry installation...")
    
    # Search for executable files
    executables = []
    
    # Windows
    if sys.platform == "win32":
        possible_exes = [
            "foundry.exe",
            "foundry-server.exe", 
            "foundry-cli.exe"
        ]
        
        # Search in PATH
        for exe in possible_exes:
            import shutil
            if shutil.which(exe):
                executables.append(shutil.which(exe))
        
        # Search in standard directories
        standard_dirs = [
            Path("C:") / "Program Files" / "Foundry",
            Path("C:") / "Program Files (x86)" / "Foundry",
            Path.home() / "AppData" / "Local" / "Programs" / "Foundry"
        ]
        
        for dir_path in standard_dirs:
            if dir_path.exists():
                for exe in possible_exes:
                    exe_path = dir_path / exe
                    if exe_path.exists():
                        executables.append(str(exe_path))
    
    # Linux/macOS
    else:
        import shutil
        for exe in ["foundry", "foundry-server"]:
            if shutil.which(exe):
                executables.append(shutil.which(exe))
    
    print(f"📊 Executable files found: {len(executables)}")
    for exe in executables:
        print(f"  ✅ {exe}")
    
    return {
        "executables": executables,
        "installed": len(executables) > 0
    }

def main():
    """Main function"""
    print("=" * 60)
    print("🔍 FOUNDRY MODEL SEARCH IN THE SYSTEM")
    print("=" * 60)
    print()
    
    # Check installation
    installation = check_foundry_installation()
    print()
    
    # Search for models
    models = find_foundry_models()
    print()
    
    # Output results
    print("=" * 60)
    print("📋 SEARCH RESULTS")
    print("=" * 60)
    
    print(f"🔧 Foundry installed: {'Yes' if installation['installed'] else 'No'}")
    print(f"📁 Model directories found: {models['total_directories']}")
    print(f"📄 Model files found: {models['total_files']}")
    
    if models['model_files']:
        print()
        print("📄 FOUND MODELS:")
        for model in models['model_files'][:10]:  # First 10
            print(f"  📄 {model['name']} ({model['size_mb']} MB)")
            print(f"     📁 {model['parent_dir']}")
    
    if models['model_directories']:
        print()
        print("📁 MODEL DIRECTORIES:")
        for dir_path in models['model_directories']:
            print(f"  📁 {dir_path}")
    
    print()
    print("💡 To run Foundry, use the found model paths")

if __name__ == "__main__":
    main()