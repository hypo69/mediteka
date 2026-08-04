#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Process name: FastAPI Foundry Diagnostics
# =============================================================================
# Description:
#   System status check and problem diagnostics
#
# File: diagnose.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Changes in 0.6.0:
#   - MIT License update
#   - Unified headers and return type hints
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import sys
import os
import json
import socket
import requests
import subprocess
from pathlib import Path

def check_python() -> None:
    """Python Check"""
    print("🐍 Python:")
    print(f"   Version: {sys.version}")
    print(f"   Path: {sys.executable}")
    print(f"   Platform: {sys.platform}")

def check_dependencies() -> None:
    """Dependency Check"""
    print("\n📦 Dependencies:")
    
    required = ['uvicorn', 'fastapi', 'requests']
    for package in required:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - NOT INSTALLED")

def check_config() -> None:
    """Configuration Check"""
    print("\n⚙️ Configuration:")
    
    config_path = Path("config.json")
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("   ✅ config.json found and valid")
            
            # Check main sections
            if 'fastapi_server' in config:
                port = config['fastapi_server'].get('port', 9696)
                print(f"   📌 FastAPI port: {port}")
            
            if 'foundry_ai' in config:
                foundry_url = config['foundry_ai'].get('base_url', 'N/A')
                print(f"   🤖 Foundry URL: {foundry_url}")
                
        except Exception as e:
            print(f"   ❌ Error reading config.json: {e}")
    else:
        print("   ⚠️ config.json not found")

def check_ports() -> None:
    """Port Check"""
    print("\n🔌 Ports:")
    
    # Check FastAPI ports
    for port in [9696, 9697, 9698]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', port))
            if result == 0:
                print(f"   🔴 {port} - BUSY")
            else:
                print(f"   ✅ {port} - free")
    
    # Check Foundry ports
    foundry_ports = [50477, 63157, 50478, 50479]
    for port in foundry_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', port))
            if result == 0:
                print(f"   🤖 {port} - possible Foundry")
                # Checking if it's actually Foundry
                try:
                    response = requests.get(f"http://localhost:{port}/v1/models", timeout=2)
                    if response.status_code == 200:
                        print(f"      ✅ Foundry API working")
                    else:
                        print(f"      ⚠️ Port busy, but not Foundry API")
                except:
                    print(f"      ⚠️ Port busy, but HTTP unavailable")

def check_processes() -> None:
    """Process Check"""
    print("\n🔄 Processes:")
    
    try:
        # Search for Foundry processes
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Inference.Service.Agent*'], 
                              capture_output=True, text=True, shell=True)
        if 'Inference.Service.Agent' in result.stdout:
            print(f"   ✅ Foundry Agent process found (Port check: {find_foundry_port() or 'Not responsive'})")
        else:
            print("   ❌ Foundry Agent process not found")
            
        # Search for Python processes with uvicorn
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, shell=True)
        if 'python.exe' in result.stdout:
            print("   🐍 Python processes found")
        else:
            print("   ⚠️ Python processes not found")
            
    except Exception as e:
        print(f"   ❌ Error checking processes: {e}")

def check_files() -> None:
    """File Check"""
    print("\n📁 Files:")
    
    important_files = [
        'run.py',
        'config.json',
        'src/api/main.py',
        'src/api/app.py',
        'requirements.txt'
    ]
    
    for file_path in important_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - NOT FOUND")

def check_environment() -> None:
    """Environment Variable Check"""
    print("\n🌍 Environment Variables:")
    
    env_vars = ['FOUNDRY_BASE_URL']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var} = {value}")
        else:
            print(f"   ⚠️ {var} not set")

def main() -> None:
    """Main Diagnostics Function"""
    print("🔍 FastAPI Foundry - Diagnostics")
    print("=" * 50)
    
    check_python()
    check_dependencies()
    check_config()
    check_ports()
    check_processes()
    check_files()
    check_environment()
    
    print("\n" + "=" * 50)
    print("📋 Recommendations:")
    print("   1. If Foundry is not found: run 'foundry service start'")
    print("   2. If ports are busy: use './stop.py' to clear them")
    print("   3. If dependencies are missing: 'pip install -r requirements.txt'")
    print("   4. To launch, use: './start_simple.ps1'")

if __name__ == "__main__":
    main()