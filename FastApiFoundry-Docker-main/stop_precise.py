#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Precise Stop for FastAPI Foundry
# =============================================================================
# Description:
#   Improved script to terminate only active FastAPI Foundry processes
#   Avoids killing unnecessary processes
#
# File: stop_precise.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Changes in 0.6.0:
#   - MIT License update
#   - Unified headers and return type hints
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import subprocess
import platform
import sys
import psutil
import os

def find_fastapi_processes() -> list:
    """Find only FastAPI Foundry processes"""
    processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                
                # Look only for our processes
                if any(keyword in cmdline.lower() for keyword in [
                    'run.py',
                    'fastapi-foundry',
                    'uvicorn',
                    'python.*8000'
                ]):
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmdline
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
    except Exception as e:
        print(f"Error scanning processes: {e}")
    
    return processes

def kill_process_by_pid(pid: int) -> bool:
    """Kill process by PID"""
    try:
        if platform.system().lower() == "windows":
            result = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            return result.returncode == 0
        else:
            result = subprocess.run(
                ["kill", "-9", str(pid)], 
                capture_output=True, 
                timeout=5
            )
            return result.returncode == 0
            
    except Exception as e:
        print(f"Error killing PID {pid}: {e}")
        return False

def main() -> int:
    print("🛑 FastAPI Foundry Precise Stop")
    print("=" * 40)
    
    # Find FastAPI Foundry processes
    processes = find_fastapi_processes()
    
    if not processes:
        print("ℹ️ No FastAPI Foundry processes found")
        return 0
    
    print(f"Found {len(processes)} FastAPI Foundry processes:")
    for proc in processes:
        print(f"  PID {proc['pid']}: {proc['name']} - {proc['cmdline'][:80]}...")
    
    print("\nKilling processes...")
    killed_count = 0
    
    for proc in processes:
        pid = proc['pid']
        print(f"🛑 Killing process PID: {pid}")
        
        if kill_process_by_pid(pid):
            print(f"✅ Successfully killed PID {pid}")
            killed_count += 1
        else:
            print(f"❌ Failed to kill PID {pid}")
    
    print("=" * 40)
    print(f"✅ Killed {killed_count}/{len(processes)} processes")
    print("🏁 Done")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)