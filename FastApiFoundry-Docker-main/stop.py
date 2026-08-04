#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Stopping FastAPI Foundry servers
# =============================================================================
# Description:
#   Simple script to terminate FastAPI Foundry processes
#   Simplified version without excessive logging
#
# File: stop.py
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

def kill_processes_on_ports(ports: list) -> int:
    """Terminate processes on specified ports"""
    print(f"Checking ports: {ports}")
    system = platform.system().lower()
    killed_count = 0
    found_pids = set()  # Use set to avoid duplicates
    
    for port in ports:
        print(f"Checking port {port}...")
        
        if system == "windows":
            try:
                result = subprocess.run(
                    ["netstat", "-ano"], 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f":{port}" in line and "LISTENING" in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                pid = parts[-1]
                                if pid.isdigit() and pid != '0' and pid not in found_pids:
                                    found_pids.add(pid)
                                    print(f"🛑 Killing process PID: {pid}")
                                    
                                    kill_result = subprocess.run(
                                        ["taskkill", "/PID", pid, "/F"], 
                                        capture_output=True, 
                                        text=True,
                                        timeout=5
                                    )
                                    
                                    if kill_result.returncode == 0:
                                        print(f"✅ Killed process PID {pid}")
                                        killed_count += 1
                                    else:
                                        print(f"❌ Failed to kill PID {pid}")
                                        
            except Exception as e:
                print(f"Error checking port {port}: {e}")
        
        else:  # Unix/Linux/macOS
            try:
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"], 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid and pid not in found_pids:
                            found_pids.add(pid)
                            print(f"🛑 Killing process PID: {pid}")
                            subprocess.run(["kill", "-9", pid], capture_output=True, timeout=5)
                            print(f"✅ Killed process PID {pid}")
                            killed_count += 1
                            
            except Exception as e:
                print(f"Error checking port {port}: {e}")
    
    print(f"Total unique processes killed: {killed_count}")
    return killed_count

def main() -> int:
    print("🛑 FastAPI Foundry Stop Script")
    print("=" * 40)
    
    # Default ports - main port only
    ports = [8000]
    
    if len(sys.argv) > 1:
        try:
            ports = [int(p.strip()) for p in sys.argv[1].split(",")]
        except ValueError:
            print("Invalid port format. Use: python stop.py 8000,8001,8002")
            return 1
    
    killed_count = kill_processes_on_ports(ports)
    
    print("=" * 40)
    print(f"✅ Killed {killed_count} processes")
    print("🏁 Done")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())